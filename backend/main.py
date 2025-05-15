from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine, Base
from models import Document
from schemas import DocumentCreate
from ws_manager import ws_manager
import uuid

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
        while True:
            message = await websocket.receive_text()
            print(f"Received feedback for doc {document_id}: {message}")
    except WebSocketDisconnect:
        ws_manager.disconnect(document_id)
