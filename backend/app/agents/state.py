"""Agent state definitions for LangGraph workflow."""

from typing import TypedDict, Annotated, Literal
from datetime import datetime
import operator


class Citation(TypedDict):
    """Citation structure."""
    source: str
    url: str
    snippet: str
    confidence: float


class SearchResult(TypedDict):
    """Search result structure."""
    source: Literal["fidelity", "mygps"]
    title: str
    url: str
    content: str
    relevance_score: float


class EvaluationScores(TypedDict):
    """Evaluation metrics."""
    accuracy: int  # 1-5
    relevancy: int  # 1-5
    factual_grounding: int  # 1-5
    guardrail_passed: bool
    feedback: str


class ConversationMessage(TypedDict):
    """Single conversation message."""
    role: Literal["customer", "rep", "system"]
    content: str
    timestamp: datetime


class AgentState(TypedDict):
    """
    Main agent state for LangGraph workflow.

    This state is passed between all nodes in the graph and tracks
    the complete resolution generation pipeline.
    """
    # Input
    conversation_id: str
    transcript: Annotated[list[ConversationMessage], operator.add]  # Append-only
    trigger_detected: bool

    # Query Processing
    optimized_query: str
    query_metadata: dict  # Keywords, entities, intent

    # Search Phase
    search_results: list[SearchResult]
    search_errors: Annotated[list[str], operator.add]  # Track search failures

    # Resolution Generation
    resolution_text: str
    citations: list[Citation]
    generation_timestamp: datetime

    # Evaluation Phase
    evaluation_scores: EvaluationScores
    evaluation_passed: bool

    # Retry Logic
    retry_count: int
    feedback_history: Annotated[list[str], operator.add]  # Feedback from each retry

    # Human Review
    rep_action: Literal["pending", "approved", "edited", "rejected"]
    rep_edited_text: str
    rep_feedback: str

    # Metadata
    started_at: datetime
    completed_at: datetime
    total_tokens_used: int
    error_message: str


class WorkflowOutput(TypedDict):
    """Final output from the agent workflow."""
    conversation_id: str
    resolution: str
    citations: list[Citation]
    evaluation_scores: EvaluationScores
    retry_count: int
    status: Literal["success", "failed", "max_retries_exceeded"]
    execution_time_seconds: float


def create_initial_state(conversation_id: str, transcript: list[ConversationMessage]) -> AgentState:
    """Create initial agent state."""
    return AgentState(
        conversation_id=conversation_id,
        transcript=transcript,
        trigger_detected=False,
        optimized_query="",
        query_metadata={},
        search_results=[],
        search_errors=[],
        resolution_text="",
        citations=[],
        generation_timestamp=datetime.utcnow(),
        evaluation_scores=EvaluationScores(
            accuracy=0,
            relevancy=0,
            factual_grounding=0,
            guardrail_passed=False,
            feedback=""
        ),
        evaluation_passed=False,
        retry_count=0,
        feedback_history=[],
        rep_action="pending",
        rep_edited_text="",
        rep_feedback="",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        total_tokens_used=0,
        error_message=""
    )
