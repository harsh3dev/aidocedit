import uuid
import traceback
import asyncio
import json
from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine, Base
from models import Document, Section, is_document_content_generated_async
from schemas import DocumentCreate
from ws_manager import ws_manager, send_document_complete
from agent.src.graph import document_graph
from langchain_core.runnables import RunnableConfig
from agent.src.state import AgentState
from templates import TEMPLATE_SECTIONS
from sqlalchemy import text, select
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        try:
            check_column_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'content_generated'
            """)
            result = await conn.execute(check_column_query)
            column_exists = result.fetchone() is not None

            if not column_exists:
                print("Adding content_generated column to documents table...")
                await conn.execute(
                    text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_generated VARCHAR DEFAULT 'false'")
                )
                print("Column added successfully!")
        except Exception as e:
            print(f"Error checking/adding content_generated column: {e}")

@app.get("/templates/")
async def get_templates():
    return {"templates": list(TEMPLATE_SECTIONS.keys())}

@app.post("/generate/")
async def create_document(data: DocumentCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_doc = Document(
            user_query=data.userQuery,
            template_type=data.selectedTemplate
        )
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        return {"document_id": new_doc.id}
    except Exception as e:
        print(f"Error creating document: {str(e)}")
        await db.rollback()
        return await create_document_fallback(data, db)

async def create_document_fallback(data: DocumentCreate, db: AsyncSession = Depends(get_db)):
    try:
        query = text("INSERT INTO documents (user_query, template_type) VALUES (:user_query, :template_type) RETURNING id")
        result = await db.execute(
            query,
            {"user_query": data.userQuery, "template_type": data.selectedTemplate}
        )
        document_id = result.scalar_one()
        await db.commit()
        print(f"Document created with fallback method, ID: {document_id}")
        return {"document_id": document_id}
    except Exception as e:
        print(f"Error in fallback document creation: {str(e)}")
        await db.rollback()
        raise

@app.websocket("/ws/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str, db: AsyncSession = Depends(get_db)):
    try:
        doc_id_int = int(document_id)
        stmt = select(Document).where(Document.id == doc_id_int)
        result = await db.execute(stmt)
        document = result.scalars().first()

        if not document:
            await websocket.accept()
            await websocket.send_json({"type": "error", "message": "Document not found"})
            return

        user_query = document.user_query
        selected_template = document.template_type
        print(f"Using document from DB - query: {user_query}, template: {selected_template}")

        content_generated = await is_document_content_generated_async(document_id)
        if content_generated:
            # Accept the connection first
            await websocket.accept()
            print(f"Content already generated for document {document_id}, sending document_complete")
            
            # No need to connect to the WebSocket manager as we'll just send the data and close
            await websocket.send_json({"type": "document_complete"})

            stmt = select(Section).where(Section.document_id == doc_id_int)
            result = await db.execute(stmt)
            sections = result.scalars().all()

            for section in sections:
                await websocket.send_json({
                    "type": "section_content",
                    "section_id": str(section.id),
                    "section_name": section.section_name,
                    "content": section.content,
                    "is_editable": True
                })
            
            await websocket.send_json({"type": "stream_end"})
            return
            
        # Only connect to WebSocket manager if content isn't already generated
        await ws_manager.connect(document_id, websocket)

        message = await websocket.receive_text()
        try:
            data = json.loads(message)
            print(f"Received init message: {data}")
        except json.JSONDecodeError:
            await websocket.send_text("Invalid initial JSON payload")
            return

        initial_state = AgentState(
            document_id=document_id,
            query=user_query,
            template_type=selected_template,
            section_names=[],
            current_section_index=0,
            current_section_content="",
            current_section_id=None,
            feedback=None,
            last_feedback_type="continue",
            messages=[],
            sections=[],
            search_results=[],
            final_html_sections=[],
            latest_feedback=None,
            section_approved=False
        )        
        
        config = RunnableConfig(
            configurable={
                "thread_id": str(uuid.uuid4())
            },
            recursion_limit=100
        )

        task = asyncio.create_task(run_in_executor(None, stream_graph, initial_state, config))

        while True:
            try:
                feedback_message = await websocket.receive_text()
                print(f"Received raw feedback message: {feedback_message}")
                feedback_data = json.loads(feedback_message)

                content_generated = await is_document_content_generated_async(document_id)
                if content_generated:
                    print(f"Content already generated for document {document_id}, not processing feedback for LangGraph")
                    if "section_id" in feedback_data:
                        await websocket.send_json({"type": "feedback_received", "section_id": feedback_data.get("section_id")})
                    continue

                if "section_id" in feedback_data and "feedback_type" in feedback_data:
                    section_id = feedback_data.get("section_id")
                    print(f"Received feedback for section {section_id}: {feedback_data}")
                    await ws_manager.process_feedback(section_id, feedback_data)
                else:
                    print(f"Received message without proper feedback format: {feedback_data}")
            except json.JSONDecodeError as e:
                print(f"Invalid feedback JSON received: {e}")
            except WebSocketDisconnect:
                ws_manager.disconnect(document_id)
                break
            except Exception as e:
                print(f"Error processing feedback: {str(e)}")
                traceback.print_exc()
    except WebSocketDisconnect:
        ws_manager.disconnect(document_id)

async def run_in_executor(executor, func, *args):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return await loop.run_in_executor(executor, func, *args)

def stream_graph(initial_state: AgentState, config: RunnableConfig):
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if isinstance(initial_state, dict):
            original_document_id = initial_state.get("document_id")
            initial_state = AgentState(**initial_state)
        else:
            original_document_id = initial_state.document_id
            
        # Ensure recursion_limit is set in config
        if "recursion_limit" not in config:
            config["recursion_limit"] = 100
            
        print(f"Using recursion limit: {config.get('recursion_limit', 'default')}")
        for event in document_graph.stream(initial_state, config=config):
            print("[Graph Event]", event)

        if original_document_id:
            send_document_complete(original_document_id)
    except Exception as e:
        print(f"ERROR: LangGraph execution failed: {str(e)}")
        traceback.print_exc()
