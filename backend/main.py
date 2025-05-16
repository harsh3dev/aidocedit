import uuid
import traceback
import asyncio
from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine, Base
from models import Document
from schemas import DocumentCreate
from ws_manager import ws_manager
from agent.src.graph import document_graph
from langchain_core.runnables import RunnableConfig
from agent.src.state import AgentState

import json

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

@app.post("/generate/")
async def create_document(data: DocumentCreate, db: AsyncSession = Depends(get_db)):
    new_doc = Document(
        user_query=data.userQuery,
        template_type=data.selectedTemplate,
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    return {"document_id": new_doc.id}

@app.websocket("/ws/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    await ws_manager.connect(document_id, websocket)

    try:
        
        message = await websocket.receive_text()
        try:
            data = json.loads(message)
            
            user_query = data.get("query") or data.get("userQuery", "General Information Request")
            selected_template = data.get("template_type") or data.get("selectedTemplate", "general")
            print(f"Received request - query: {user_query}, template: {selected_template}")
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

        config = RunnableConfig(configurable={
            "thread_id": str(uuid.uuid4()),
            "recursion_limit": 50  
        })

        
        task = asyncio.create_task(run_in_executor(None, stream_graph, initial_state, config))
        
        
        while True:
            try:                
                feedback_message = await websocket.receive_text()
                print(f"Received raw feedback message: {feedback_message}")
                
                feedback_data = json.loads(feedback_message)
                
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
    """Run a function in an executor and return its result as a coroutine."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func, *args)


def stream_graph(initial_state: AgentState, config: RunnableConfig):
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if isinstance(initial_state, dict):
            initial_state = AgentState(**initial_state)

        config = RunnableConfig(configurable={
            **config.get("configurable", {}),
            "recursion_limit": 50,  
        })

        for event in document_graph.stream(initial_state, config=config):
            print("[Graph Event]", event)
    except Exception as e:
        print(f"ERROR: LangGraph execution failed: {str(e)}")
        traceback.print_exc()
