"""Resolution management endpoints."""

from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime

from app.schemas.resolution import (
    ResolutionResponse,
    ResolutionUpdate,
    ResolutionApproval,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{resolution_id}", response_model=ResolutionResponse)
async def get_resolution(resolution_id: str):
    """
    Get resolution details by ID.
    """
    logger.info(f"Fetching resolution: {resolution_id}")

    # TODO: Implement database retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Resolution {resolution_id} not found",
    )


@router.get("/conversation/{conversation_id}", response_model=List[ResolutionResponse])
async def get_resolutions_by_conversation(conversation_id: str):
    """
    Get all resolutions generated for a conversation.

    This includes all retry attempts and their evaluation scores.
    """
    logger.info(f"Fetching resolutions for conversation {conversation_id}")

    # TODO: Implement database retrieval
    return []


@router.patch("/{resolution_id}", response_model=ResolutionResponse)
async def update_resolution(resolution_id: str, update: ResolutionUpdate):
    """
    Update resolution text (when rep edits the AI-generated response).
    """
    logger.info(f"Updating resolution {resolution_id}")

    # TODO: Implement resolution update and version tracking
    return ResolutionResponse(
        id=resolution_id,
        conversation_id="conv_123",
        resolution_text=update.edited_text,
        citations=[],
        evaluation_scores={
            "accuracy": 4,
            "relevancy": 4,
            "factual_grounding": 4,
            "guardrail_passed": True,
        },
        retry_count=0,
        status="edited",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.post("/{resolution_id}/approve", status_code=status.HTTP_200_OK)
async def approve_resolution(resolution_id: str, approval: ResolutionApproval):
    """
    Rep approves the resolution for sending to customer.

    This records the rep's decision and can trigger analytics/feedback loops.
    """
    logger.info(
        f"Resolution {resolution_id} approved by rep {approval.rep_id} "
        f"(action: {approval.action})"
    )

    # TODO: Record approval, update status, trigger feedback
    return {
        "resolution_id": resolution_id,
        "action": approval.action,
        "approved_by": approval.rep_id,
        "approved_at": datetime.utcnow(),
        "feedback": approval.feedback,
    }


@router.post("/{resolution_id}/feedback")
async def submit_feedback(
    resolution_id: str,
    rating: int,
    feedback_text: str = None,
):
    """
    Rep submits feedback on resolution quality.

    This helps improve the system over time.
    """
    logger.info(f"Feedback submitted for resolution {resolution_id}: {rating}/5")

    # TODO: Store feedback for model fine-tuning/evaluation
    return {
        "resolution_id": resolution_id,
        "rating": rating,
        "feedback": feedback_text,
        "submitted_at": datetime.utcnow(),
    }
