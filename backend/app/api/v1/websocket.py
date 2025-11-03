"""WebSocket endpoints for real-time updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Active WebSocket connections per conversation
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        """Accept new WebSocket connection."""
        await websocket.accept()

        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()

        self.active_connections[conversation_id].add(websocket)
        logger.info(
            f"WebSocket connected for conversation {conversation_id}. "
            f"Total connections: {len(self.active_connections[conversation_id])}"
        )

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        """Remove WebSocket connection."""
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].discard(websocket)

            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

        logger.info(f"WebSocket disconnected from conversation {conversation_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection."""
        await websocket.send_json(message)

    async def broadcast(self, message: dict, conversation_id: str):
        """Broadcast message to all connections for a conversation."""
        if conversation_id not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[conversation_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                disconnected.add(connection)

        # Clean up disconnected websockets
        for connection in disconnected:
            self.disconnect(connection, conversation_id)


manager = ConnectionManager()


@router.websocket("/conversations/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time conversation updates.

    Events sent to client:
    - message_added: New message in conversation
    - workflow_started: FAA workflow triggered
    - resolution_generated: AI resolution ready for review
    - evaluation_complete: Evaluation scores available
    - status_changed: Conversation status updated

    Client can send:
    - ping: Keep-alive
    - subscribe: Subscribe to specific event types
    """
    await manager.connect(websocket, conversation_id)

    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "event": "connected",
                "conversation_id": conversation_id,
                "message": "WebSocket connection established",
            },
            websocket,
        )

        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                event_type = message.get("type")

                if event_type == "ping":
                    await manager.send_personal_message(
                        {"event": "pong", "timestamp": message.get("timestamp")},
                        websocket,
                    )

                elif event_type == "subscribe":
                    # Handle subscription to specific events
                    events = message.get("events", [])
                    logger.info(
                        f"Client subscribed to events: {events} "
                        f"for conversation {conversation_id}"
                    )
                    await manager.send_personal_message(
                        {
                            "event": "subscribed",
                            "events": events,
                        },
                        websocket,
                    )

                else:
                    logger.warning(f"Unknown WebSocket message type: {event_type}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)
        logger.info(f"Client disconnected from conversation {conversation_id}")

    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        manager.disconnect(websocket, conversation_id)


async def broadcast_event(conversation_id: str, event_type: str, data: dict):
    """
    Broadcast event to all connected clients for a conversation.

    This function should be called from other parts of the application
    when events occur (e.g., new message, workflow complete).

    Example:
        await broadcast_event(
            conversation_id="conv_123",
            event_type="resolution_generated",
            data={"resolution_id": "res_456", "status": "pending_review"}
        )
    """
    message = {
        "event": event_type,
        "conversation_id": conversation_id,
        "data": data,
    }
    await manager.broadcast(message, conversation_id)
