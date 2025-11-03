"""Resolution-related Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class Citation(BaseModel):
    """Schema for a citation."""
    source: str
    url: str
    snippet: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class EvaluationScores(BaseModel):
    """Schema for evaluation scores."""
    accuracy: int = Field(..., ge=1, le=5)
    relevancy: int = Field(..., ge=1, le=5)
    factual_grounding: int = Field(..., ge=1, le=5)
    guardrail_passed: bool
    feedback: Optional[str] = None


class ResolutionResponse(BaseModel):
    """Schema for resolution response."""
    id: str
    conversation_id: str
    resolution_text: str
    citations: List[Citation]
    evaluation_scores: dict
    retry_count: int
    status: Literal["pending_review", "approved", "edited", "rejected"]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ResolutionUpdate(BaseModel):
    """Schema for updating a resolution."""
    edited_text: str = Field(..., min_length=1)
    rep_id: str
    edit_reason: Optional[str] = None


class ResolutionApproval(BaseModel):
    """Schema for approving/rejecting a resolution."""
    rep_id: str
    action: Literal["approve", "reject", "edit"]
    feedback: Optional[str] = None
