"""Trigger detection node - identifies activation phrases in conversation."""

import re
from app.agents.state import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Activation phrases that trigger the FAA workflow
TRIGGER_PHRASES = [
    r"let me take a look",
    r"let me check",
    r"i'll look into",
    r"i'll check that",
    r"looking into",
    r"checking that for you",
    r"one moment please",
    r"give me a moment",
    r"let me find that",
    r"searching for",
]


def detect_trigger_phrase(text: str) -> bool:
    """
    Check if text contains any trigger phrases.

    Args:
        text: Message content to check

    Returns:
        True if trigger detected, False otherwise
    """
    text_lower = text.lower()
    for pattern in TRIGGER_PHRASES:
        if re.search(pattern, text_lower):
            return True
    return False


def trigger_detection_node(state: AgentState) -> AgentState:
    """
    Detect if activation phrase is present in recent messages.

    The FAA workflow should only activate when the rep indicates
    they're going to research something (e.g., "let me take a look").

    Args:
        state: Current agent state with transcript

    Returns:
        Updated state with trigger_detected flag
    """
    logger.info(f"Checking trigger for conversation {state['conversation_id']}")

    # Check last 3 rep messages
    rep_messages = [
        msg["content"] for msg in state["transcript"]
        if msg["role"] == "rep"
    ][-3:]

    trigger_found = False
    for message in rep_messages:
        if detect_trigger_phrase(message):
            trigger_found = True
            logger.info(f"Trigger detected in message: '{message}'")
            break

    if not trigger_found:
        logger.info("No trigger phrase detected, workflow will exit")

    state["trigger_detected"] = trigger_found
    return state
