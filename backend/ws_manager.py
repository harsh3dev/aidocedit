import asyncio
import json
from typing import Dict, Optional
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.pending_feedback: Dict[str, Dict] = {}
        self.feedback_events: Dict[str, asyncio.Event] = {}

    async def connect(self, document_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[document_id] = websocket

    def disconnect(self, document_id: str):
        if document_id in self.active_connections:
            del self.active_connections[document_id]

    async def send_section_content(self, document_id: str, section_id: str, section_name: str, content_html: str, is_editable: bool = True):
        if document_id in self.active_connections:
            try:
                if hasattr(content_html, 'content'):
                    content_html = content_html.content

                if isinstance(content_html, str) and '```' in content_html:
                    content_html = content_html.replace('```html', '').replace('```', '').strip()

                if not isinstance(content_html, str):
                    content_html = str(content_html)

                data = {
                    "type": "section_content",
                    "section_id": section_id,
                    "section_name": section_name,
                    "content": content_html,
                    "is_editable": is_editable
                }
                await self.active_connections[document_id].send_text(json.dumps(data))
            except Exception as e:
                print(f"Error sending section content: {e}")

    async def receive_feedback(self, document_id: str, section_id: str):
        if document_id not in self.active_connections:
            return None

        try:
            if section_id not in self.feedback_events:
                self.feedback_events[section_id] = asyncio.Event()

            await self.feedback_events[section_id].wait()

            feedback = self.pending_feedback.get(section_id)
            if section_id in self.pending_feedback:
                del self.pending_feedback[section_id]
            if section_id in self.feedback_events:
                del self.feedback_events[section_id]
            return feedback
        except Exception as e:
            print(f"Error receiving feedback: {e}")
            return None

    async def process_feedback(self, section_id: str, feedback_data: Dict):
        self.pending_feedback[section_id] = feedback_data

        if section_id in self.feedback_events:
            print(f"Processing feedback event for section {section_id}")
            self.feedback_events[section_id].set()
        else:
            print(f"Creating new feedback event for section {section_id}")
            self.feedback_events[section_id] = asyncio.Event()
            self.feedback_events[section_id].set()

    async def send_document_complete(self, document_id: str):
        """Send a document completion message to the client"""
        if document_id in self.active_connections:
            try:
                data = {
                    "type": "document_complete"
                }
                await self.active_connections[document_id].send_text(json.dumps(data))
                print(f"Sent document_complete message for document {document_id}")
            except Exception as e:
                print(f"Error sending document completion message: {e}")

    async def send_stream_end(self, document_id: str):
        """Send a stream end message to the client"""
        if document_id in self.active_connections:
            try:
                data = {
                    "type": "stream_end"
                }
                await self.active_connections[document_id].send_text(json.dumps(data))
                print(f"Sent stream_end message for document {document_id}")
            except Exception as e:
                print(f"Error sending stream end message: {e}")

ws_manager = WebSocketManager()

def stream_to_websocket(document_id: str, section_id: str, section_name: str, content_html: str, is_editable: bool = True):
    """Synchronous wrapper for streaming to websocket"""
    try:
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if hasattr(content_html, 'content'):
            content_html = content_html.content

        if isinstance(content_html, str) and '```' in content_html:
            content_html = content_html.replace('```html', '').replace('```', '').strip()

        if not isinstance(content_html, str):
            content_html = str(content_html)

        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                ws_manager.send_section_content(document_id, section_id, section_name, content_html),
                loop
            )

            try:
                future.result(timeout=5.0)
            except asyncio.TimeoutError:
                print(f"WebSocket streaming timed out for section {section_name}")
            except Exception as e:
                print(f"Error in WebSocket streaming: {str(e)}")
        else:
            loop.run_until_complete(ws_manager.send_section_content(document_id, section_id, section_name, content_html))
    except Exception as e:
        print(f"Error in stream_to_websocket: {str(e)}")

def send_document_complete(document_id: str):
    """Synchronous wrapper for sending document completion message"""
    try:
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                ws_manager.send_document_complete(document_id),
                loop
            )

            try:
                future.result(timeout=5.0)
            except asyncio.TimeoutError:
                print(f"WebSocket document complete timed out for document {document_id}")
            except Exception as e:
                print(f"Error in WebSocket document complete: {str(e)}")
        else:
            loop.run_until_complete(ws_manager.send_document_complete(document_id))
    except Exception as e:
        print(f"Error in send_document_complete: {str(e)}")

def send_stream_end(document_id: str):
    """Synchronous wrapper for sending stream end message"""
    try:
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                ws_manager.send_stream_end(document_id),
                loop
            )

            try:
                future.result(timeout=5.0)
            except asyncio.TimeoutError:
                print(f"WebSocket stream end timed out for document {document_id}")
            except Exception as e:
                print(f"Error in WebSocket stream end: {str(e)}")
        else:
            loop.run_until_complete(ws_manager.send_stream_end(document_id))
    except Exception as e:
        print(f"Error in send_stream_end: {str(e)}")

def wait_for_feedback_from_ws(section_id: str, timeout: int = 30) -> Optional[Dict]:
    """Synchronous wrapper for waiting for feedback"""
    try:
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        print(f"Waiting for feedback for section {section_id}")

        document_ids = list(ws_manager.active_connections.keys())
        if not document_ids:
            print("No active WebSocket connections found")
            return {"feedback_type": "end", "edited_content": None}

        document_id = document_ids[0]

        if section_id in ws_manager.pending_feedback:
            print(f"Found pending feedback for section {section_id}")
            feedback = ws_manager.pending_feedback.get(section_id)
            if feedback:
                del ws_manager.pending_feedback[section_id]
                return feedback

        if loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    ws_manager.receive_feedback(document_id, section_id),
                    loop
                )
                feedback = future.result(timeout=timeout)
                if feedback:
                    print(f"Received feedback via future: {feedback}")
                    return feedback
            except asyncio.TimeoutError:
                print(f"Timeout waiting for feedback for section {section_id}")
            except Exception as e:
                print(f"Error waiting for feedback: {str(e)}")
        else:
            try:
                feedback = loop.run_until_complete(
                    asyncio.wait_for(
                        ws_manager.receive_feedback(document_id, section_id),
                        timeout=timeout
                    )
                )
                if feedback:
                    print(f"Received feedback via run_until_complete: {feedback}")
                    return feedback
            except asyncio.TimeoutError:
                print(f"Timeout waiting for feedback for section {section_id}")
            except Exception as e:
                print(f"Error waiting for feedback: {str(e)}")

        print("No feedback received after timeout, ending workflow")
        return {"feedback_type": "end", "edited_content": None}
    except Exception as e:
        print(f"Error in wait_for_feedback_from_ws: {str(e)}")
        return {"feedback_type": "end", "edited_content": None}
