"""Conversation management endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import datetime

from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    TriggerWorkflowRequest,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Conversation",
    description="Create a new conversation session when a rep starts interacting with a customer",
    response_description="The created conversation with unique ID",
    responses={
        201: {
            "description": "Conversation created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "conv_20241103120000",
                        "rep_id": "rep_12345",
                        "customer_id": "cust_67890",
                        "channel": "chat",
                        "status": "active",
                        "started_at": "2024-11-03T12:00:00Z",
                        "messages": []
                    }
                }
            }
        }
    }
)
async def create_conversation(conversation: ConversationCreate):
    """
    Create a new conversation session.

    This endpoint should be called when a service representative starts a new customer interaction.
    It initializes a conversation that can be used to track messages and trigger the FAA workflow.

    **Parameters:**
    - **rep_id**: Unique identifier for the service representative
    - **customer_id**: Optional unique identifier for the customer
    - **channel**: Communication channel (voice, chat, or email)
    - **metadata**: Optional additional metadata for the conversation

    **Returns:**
    - Newly created conversation with a unique ID
    - Empty messages list (messages are added separately)
    - Initial status set to "active"
    """
    logger.info(f"Creating new conversation for rep: {conversation.rep_id}")

    # TODO: Implement database storage
    return ConversationResponse(
        id="conv_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        rep_id=conversation.rep_id,
        customer_id=conversation.customer_id,
        channel=conversation.channel,
        status="active",
        started_at=datetime.utcnow(),
        messages=[],
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """
    Get conversation details by ID.
    """
    logger.info(f"Fetching conversation: {conversation_id}")

    # TODO: Implement database retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Conversation {conversation_id} not found",
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(conversation_id: str, message: MessageCreate):
    """
    Add a message to an existing conversation.

    This endpoint receives messages from both customer and rep.
    Messages are stored and can trigger the FAA workflow if conditions are met.
    """
    logger.info(
        f"Adding {message.role} message to conversation {conversation_id}"
    )

    # TODO: Implement message storage and trigger detection
    return MessageResponse(
        id="msg_" + datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
        conversation_id=conversation_id,
        role=message.role,
        content=message.content,
        timestamp=datetime.utcnow(),
    )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(conversation_id: str, limit: int = 100, offset: int = 0):
    """
    Get messages for a conversation with pagination.
    """
    logger.info(
        f"Fetching messages for conversation {conversation_id} "
        f"(limit: {limit}, offset: {offset})"
    )

    # TODO: Implement database retrieval with pagination
    return []


@router.post("/{conversation_id}/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_workflow(conversation_id: str, request: TriggerWorkflowRequest):
    """
    Manually trigger the FAA workflow for a conversation.

    This can be used when the rep explicitly requests AI assistance,
    bypassing automatic trigger detection.
    """
    logger.info(
        f"Manual workflow trigger for conversation {conversation_id} "
        f"by rep {request.rep_id}"
    )

    # TODO: Trigger the LangGraph workflow asynchronously
    from app.agents.workflow import run_workflow

    # This would typically be sent to a task queue (Celery)
    # For now, just acknowledge the request
    return {
        "message": "Workflow triggered successfully",
        "conversation_id": conversation_id,
        "status": "processing",
    }


@router.patch("/{conversation_id}/status")
async def update_conversation_status(
    conversation_id: str,
    status: str,
):
    """
    Update conversation status (active, completed, escalated).
    """
    logger.info(f"Updating conversation {conversation_id} status to {status}")

    # TODO: Implement status update
    return {
        "conversation_id": conversation_id,
        "status": status,
        "updated_at": datetime.utcnow(),
    }


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation (soft delete for audit purposes).
    """
    logger.info(f"Deleting conversation {conversation_id}")

    # TODO: Implement soft delete
    return None
