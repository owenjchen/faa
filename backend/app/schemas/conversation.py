"""Conversation-related Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    role: Literal["customer", "rep", "system"]
    content: str = Field(..., min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str
    conversation_id: str
    role: Literal["customer", "rep", "system"]
    content: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    rep_id: str
    customer_id: Optional[str] = None
    channel: Literal["voice", "chat", "email"] = "chat"
    metadata: Optional[dict] = None


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: str
    rep_id: str
    customer_id: Optional[str]
    channel: Literal["voice", "chat", "email"]
    status: Literal["active", "completed", "escalated"]
    started_at: datetime
    completed_at: Optional[datetime] = None
    messages: List[MessageResponse]
    metadata: Optional[dict] = None

    model_config = {"from_attributes": True}


class TriggerWorkflowRequest(BaseModel):
    """Schema for manually triggering the FAA workflow."""
    rep_id: str
    force: bool = False  # Force trigger even if no trigger phrase detected
