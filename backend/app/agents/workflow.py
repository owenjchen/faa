"""Main LangGraph workflow for FAA agent."""

from typing import Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
from langfuse import Langfuse

from app.agents.state import AgentState, WorkflowOutput
from app.agents.nodes.trigger_detection import trigger_detection_node
from app.agents.nodes.query_formulation import query_formulation_node
from app.agents.nodes.search import parallel_search_node
from app.agents.nodes.resolution import resolution_generation_node
from app.agents.nodes.evaluation import evaluation_node
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def quality_gate(state: AgentState) -> Literal["retry", "present", "failed"]:
    """
    Determine next step based on evaluation scores.

    Returns:
        - "retry": Scores below threshold and retries available
        - "present": Scores meet threshold or max retries reached
        - "failed": Unrecoverable error occurred
    """
    if state.get("error_message"):
        logger.error(f"Workflow failed: {state['error_message']}")
        return "failed"

    scores = state["evaluation_scores"]
    min_score = settings.EVALUATION_MIN_SCORE
    max_retries = settings.EVALUATION_MAX_RETRIES

    # Check if all metrics meet threshold
    all_passed = (
        scores["accuracy"] >= min_score
        and scores["relevancy"] >= min_score
        and scores["factual_grounding"] >= min_score
        and scores["guardrail_passed"]
    )

    if all_passed:
        logger.info(f"Quality gate passed for conversation {state['conversation_id']}")
        return "present"

    # Check retry limit
    if state["retry_count"] < max_retries:
        logger.warning(
            f"Quality gate failed. Retry {state['retry_count'] + 1}/{max_retries}. "
            f"Scores: {scores}"
        )
        return "retry"

    # Max retries reached
    logger.error(
        f"Max retries ({max_retries}) reached for conversation {state['conversation_id']}. "
        f"Final scores: {scores}"
    )
    return "present"  # Present to rep anyway for human review


def increment_retry(state: AgentState) -> AgentState:
    """Increment retry counter and add feedback to history."""
    state["retry_count"] += 1
    feedback = state["evaluation_scores"].get("feedback", "No specific feedback")
    state["feedback_history"].append(
        f"Retry {state['retry_count']}: {feedback}"
    )
    logger.info(f"Incrementing retry count to {state['retry_count']}")
    return state


def finalize_output(state: AgentState) -> AgentState:
    """Mark workflow as completed and calculate execution time."""
    state["completed_at"] = datetime.utcnow()
    execution_time = (state["completed_at"] - state["started_at"]).total_seconds()
    logger.info(
        f"Workflow completed for {state['conversation_id']} "
        f"in {execution_time:.2f}s with {state['retry_count']} retries"
    )
    return state


def build_workflow() -> StateGraph:
    """
    Build the main LangGraph workflow.

    Workflow steps:
    1. Trigger Detection: Check if activation phrase detected
    2. Query Formulation: Optimize search query from transcript
    3. Parallel Search: Search fidelity.com + myGPS
    4. Resolution Generation: Generate customer-ready response
    5. Evaluation: Score quality metrics
    6. Quality Gate: Pass/retry/fail decision
    7. Present to Rep: Final output for human review

    Returns:
        Compiled StateGraph workflow
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("trigger_detection", trigger_detection_node)
    workflow.add_node("query_formulation", query_formulation_node)
    workflow.add_node("search", parallel_search_node)
    workflow.add_node("generate_resolution", resolution_generation_node)
    workflow.add_node("evaluate", evaluation_node)
    workflow.add_node("increment_retry", increment_retry)
    workflow.add_node("finalize", finalize_output)

    # Set entry point
    workflow.set_entry_point("trigger_detection")

    # Define edges
    workflow.add_conditional_edges(
        "trigger_detection",
        lambda state: "continue" if state["trigger_detected"] else "skip",
        {
            "continue": "query_formulation",
            "skip": END  # No trigger detected, exit early
        }
    )

    workflow.add_edge("query_formulation", "search")
    workflow.add_edge("search", "generate_resolution")
    workflow.add_edge("generate_resolution", "evaluate")

    # Quality gate decision
    workflow.add_conditional_edges(
        "evaluate",
        quality_gate,
        {
            "retry": "increment_retry",
            "present": "finalize",
            "failed": "finalize"
        }
    )

    # Retry loop back to query formulation with updated feedback
    workflow.add_edge("increment_retry", "query_formulation")

    # Finalize and end
    workflow.add_edge("finalize", END)

    return workflow


# Global workflow instance
_workflow_graph = None


def get_workflow() -> StateGraph:
    """Get or create the compiled workflow graph."""
    global _workflow_graph
    if _workflow_graph is None:
        logger.info("Compiling LangGraph workflow...")
        workflow = build_workflow()
        _workflow_graph = workflow.compile()
        logger.info("Workflow compiled successfully")
    return _workflow_graph


async def run_workflow(
    conversation_id: str,
    transcript: list[dict],
    langfuse_client: Langfuse | None = None
) -> WorkflowOutput:
    """
    Execute the complete agent workflow.

    Args:
        conversation_id: Unique conversation identifier
        transcript: List of conversation messages
        langfuse_client: Optional Langfuse client for observability

    Returns:
        WorkflowOutput with resolution, citations, and metadata
    """
    from app.agents.state import create_initial_state

    logger.info(f"Starting workflow for conversation {conversation_id}")

    # Initialize state
    initial_state = create_initial_state(conversation_id, transcript)

    # Get compiled workflow
    graph = get_workflow()

    # Execute workflow
    try:
        # Run the graph
        final_state = await graph.ainvoke(initial_state)

        # Extract output
        execution_time = (
            final_state["completed_at"] - final_state["started_at"]
        ).total_seconds()

        output = WorkflowOutput(
            conversation_id=conversation_id,
            resolution=final_state["resolution_text"],
            citations=final_state["citations"],
            evaluation_scores=final_state["evaluation_scores"],
            retry_count=final_state["retry_count"],
            status="success" if final_state["evaluation_passed"] else (
                "max_retries_exceeded" if final_state["retry_count"] >= settings.EVALUATION_MAX_RETRIES
                else "failed"
            ),
            execution_time_seconds=execution_time
        )

        # Log to Langfuse if available
        if langfuse_client:
            langfuse_client.trace(
                name="faa_workflow",
                input={"conversation_id": conversation_id, "transcript": transcript},
                output=output,
                metadata={
                    "retry_count": final_state["retry_count"],
                    "evaluation_scores": final_state["evaluation_scores"],
                    "execution_time": execution_time
                }
            )

        logger.info(f"Workflow completed successfully: {output['status']}")
        return output

    except Exception as e:
        logger.exception(f"Workflow execution failed: {str(e)}")
        raise


# Example usage
if __name__ == "__main__":
    import asyncio
    from app.agents.state import ConversationMessage

    async def test_workflow():
        """Test the workflow with sample data."""
        sample_transcript = [
            ConversationMessage(
                role="customer",
                content="I'm having trouble accessing my 401k account online.",
                timestamp=datetime.utcnow()
            ),
            ConversationMessage(
                role="rep",
                content="I understand. Let me take a look at that for you.",
                timestamp=datetime.utcnow()
            )
        ]

        result = await run_workflow(
            conversation_id="test-123",
            transcript=sample_transcript
        )
        print(f"Workflow result: {result}")

    asyncio.run(test_workflow())
