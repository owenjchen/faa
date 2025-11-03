"""Evaluation node - scores resolution quality using LLM-as-judge."""

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from app.agents.state import AgentState, EvaluationScores
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class EvaluationOutput(BaseModel):
    """Structured output for evaluation."""
    accuracy: int = Field(description="Accuracy score (1-5): Does the resolution correctly address the query?", ge=1, le=5)
    relevancy: int = Field(description="Relevancy score (1-5): Is the information pertinent to the customer's question?", ge=1, le=5)
    factual_grounding: int = Field(description="Factual grounding score (1-5): Are all claims supported by cited sources?", ge=1, le=5)
    citation_quality: int = Field(description="Citation quality (1-5): Are citations specific, relevant, and properly formatted?", ge=1, le=5)
    clarity: int = Field(description="Clarity score (1-5): Is the response clear, well-organized, and easy to understand?", ge=1, le=5)
    feedback: str = Field(description="Specific feedback on what to improve if scores are below threshold")


EVALUATION_PROMPT = """You are an expert quality evaluator for customer service responses at Fidelity Investments.

Your task is to evaluate the quality of an AI-generated response based on multiple criteria.

## Original Customer Query:
{query}

## Search Results Used:
{search_results_summary}

## Generated Resolution:
{resolution}

## Evaluation Criteria (1-5 scale):

1. **Accuracy (1-5)**: Does the resolution correctly and completely address the customer's query?
   - 5: Perfect answer, fully addresses all aspects
   - 4: Good answer, addresses main points
   - 3: Acceptable, addresses query but may miss details
   - 2: Partially correct, missing key information
   - 1: Incorrect or misleading

2. **Relevancy (1-5)**: Is the information pertinent to what the customer asked?
   - 5: Highly relevant, no extraneous information
   - 4: Mostly relevant, minor tangents
   - 3: Generally relevant but includes unnecessary info
   - 2: Partially relevant, significant off-topic content
   - 1: Not relevant to the query

3. **Factual Grounding (1-5)**: Are all factual claims supported by the provided sources?
   - 5: Every claim is cited and verifiable
   - 4: Most claims cited, minor unsupported details
   - 3: Key claims cited but some gaps
   - 2: Limited citations, many unsupported claims
   - 1: No citations or incorrect information

4. **Citation Quality (1-5)**: Are citations specific, relevant, and properly formatted?
   - 5: Perfect inline citations with [Source: URL] format
   - 4: Good citations, minor formatting issues
   - 3: Adequate citations but could be more specific
   - 2: Poor citation formatting or relevance
   - 1: Missing or incorrect citations

5. **Clarity (1-5)**: Is the response clear, well-organized, and customer-friendly?
   - 5: Exceptionally clear and well-structured
   - 4: Clear and easy to understand
   - 3: Understandable but could be clearer
   - 2: Confusing or poorly organized
   - 1: Very unclear or hard to understand

## Instructions:
- Evaluate each criterion independently
- Be strict but fair in your scoring
- Provide specific, actionable feedback if any score is below 4
- Consider that a score of 3 is the minimum acceptable threshold

Return your evaluation in JSON format.
"""


def evaluation_node(state: AgentState) -> AgentState:
    """
    Evaluate resolution quality using LLM-as-judge.

    This node:
    1. Takes the generated resolution and search results
    2. Uses a separate LLM instance to evaluate quality
    3. Scores on multiple dimensions (1-5 scale)
    4. Checks against external guardrails (if configured)
    5. Provides feedback for improvement if scores are low

    Args:
        state: Current agent state with resolution_text and search_results

    Returns:
        Updated state with evaluation_scores and evaluation_passed flag
    """
    query = state.get("optimized_query", "")
    resolution = state.get("resolution_text", "")
    search_results = state.get("search_results", [])

    if not resolution:
        logger.error("No resolution available for evaluation")
        state["error_message"] = "No resolution to evaluate"
        return state

    logger.info(f"Evaluating resolution for query: '{query}'")

    try:
        # Initialize separate LLM for evaluation (to avoid bias)
        llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            temperature=0.2,  # Low temperature for consistent evaluation
            max_tokens=1000,
        )

        # Create search results summary
        search_summary = "\n".join([
            f"- [{result['source']}] {result['title']}: {result['url']}"
            for result in search_results[:5]  # Top 5 for context
        ])

        # Create prompt
        prompt = ChatPromptTemplate.from_template(EVALUATION_PROMPT)

        # Create chain with structured output
        parser = JsonOutputParser(pydantic_object=EvaluationOutput)
        chain = prompt | llm | parser

        # Execute evaluation
        result = chain.invoke({
            "query": query,
            "search_results_summary": search_summary or "No search results available",
            "resolution": resolution
        })

        # Check external guardrails (if configured)
        guardrail_passed = _check_external_guardrails(resolution, query)

        # Create evaluation scores
        scores = EvaluationScores(
            accuracy=result["accuracy"],
            relevancy=result["relevancy"],
            factual_grounding=result["factual_grounding"],
            guardrail_passed=guardrail_passed,
            feedback=result.get("feedback", "")
        )

        # Check if evaluation passed
        min_score = settings.EVALUATION_MIN_SCORE
        evaluation_passed = (
            scores["accuracy"] >= min_score
            and scores["relevancy"] >= min_score
            and scores["factual_grounding"] >= min_score
            and scores["guardrail_passed"]
        )

        # Update state
        state["evaluation_scores"] = scores
        state["evaluation_passed"] = evaluation_passed

        logger.info(
            f"Evaluation completed. Scores: Accuracy={scores['accuracy']}, "
            f"Relevancy={scores['relevancy']}, Factual={scores['factual_grounding']}, "
            f"Guardrails={'PASS' if guardrail_passed else 'FAIL'}, "
            f"Overall={'PASS' if evaluation_passed else 'FAIL'}"
        )

        # Log feedback if evaluation failed
        if not evaluation_passed:
            logger.warning(f"Evaluation failed. Feedback: {scores['feedback']}")

        return state

    except Exception as e:
        logger.exception(f"Evaluation failed: {str(e)}")
        state["error_message"] = f"Evaluation error: {str(e)}"

        # Default to failed evaluation on error
        state["evaluation_scores"] = EvaluationScores(
            accuracy=1,
            relevancy=1,
            factual_grounding=1,
            guardrail_passed=False,
            feedback=f"Evaluation system error: {str(e)}"
        )
        state["evaluation_passed"] = False

        return state


def _check_external_guardrails(resolution: str, query: str) -> bool:
    """
    Check resolution against external guardrail APIs.

    This function can be extended to call external services that check for:
    - Compliance violations
    - Harmful content
    - Privacy concerns
    - Regulatory requirements

    Args:
        resolution: Generated resolution text
        query: Original query

    Returns:
        True if all guardrails pass, False otherwise
    """
    # TODO: Integrate with external guardrail services
    # For now, perform basic checks

    try:
        # Basic content checks
        forbidden_phrases = [
            "I don't know",
            "I cannot",
            "I'm not sure",
            # Add more as needed
        ]

        # Check for forbidden phrases (with some flexibility)
        text_lower = resolution.lower()
        has_forbidden = any(phrase in text_lower for phrase in forbidden_phrases)

        if has_forbidden:
            logger.warning("Resolution contains uncertain language")
            return False

        # Check for minimum length (should be substantive)
        if len(resolution) < 100:
            logger.warning("Resolution is too short")
            return False

        # Check for citations
        if "[Source:" not in resolution:
            logger.warning("Resolution lacks proper citations")
            return False

        # All basic checks passed
        return True

    except Exception as e:
        logger.error(f"Guardrail check failed: {str(e)}")
        return False  # Fail safe: reject on error


# Export for use in workflow
__all__ = ["evaluation_node"]
