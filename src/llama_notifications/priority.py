"""
Provides simple rule-based priority adjustment for notifications.
"""

import logging
import re
from typing import Dict, Any

from .message import Message, NotificationPriority # Use the standard Message and Priority types

# Configure logging
logger = logging.getLogger(__name__)

# Define keywords that might increase priority
URGENCY_KEYWORDS = {
    "urgent", "important", "critical", "emergency", "immediate",
    "alert", "warning", "attention", "asap", "now", "fail", "error",
    "deadline", "reminder", "expiring", "expires", "action required"
}

# Mapping from string priorities to numerical levels for comparison/adjustment
PRIORITY_LEVELS: Dict[NotificationPriority, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3
}

# Reverse mapping to get string from numerical level
LEVEL_TO_PRIORITY: Dict[int, NotificationPriority] = {
    v: k for k, v in PRIORITY_LEVELS.items()
}

class PriorityManager:
    """
    Adjusts the priority of a notification based on simple rules.
    Checks for urgency keywords and specific metadata flags.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the PriorityManager.

        Args:
            config (Dict[str, Any]): Configuration options (currently unused, placeholder).
        """
        self.config = config if config is not None else {}
        logger.info("PriorityManager initialized.")

    def get_adjusted_priority(self, message: Message) -> NotificationPriority:
        """
        Calculates an adjusted priority based on message content and metadata.

        Starts with the priority set in the message and adjusts it based on rules:
        - Increases priority if urgency keywords are found in subject/body.
        - Increases priority if metadata flags like `is_critical` are set.
        - Priority is capped at 'critical'.

        Args:
            message (Message): The notification message object.

        Returns:
            NotificationPriority: The adjusted priority level string.
        """

        current_priority_str = message.priority
        current_level = PRIORITY_LEVELS.get(current_priority_str, PRIORITY_LEVELS["medium"])
        adjusted_level = current_level

        logger.debug(f"Original priority for msg to {message.recipient}: {current_priority_str} (Level {current_level})")

        # Rule 1: Check for urgency keywords in subject or body
        text_content = f"{message.subject.lower()} {message.body.lower()}"
        found_keywords = {keyword for keyword in URGENCY_KEYWORDS if keyword in text_content}

        if found_keywords:
            logger.debug(f"Found urgency keywords: {found_keywords}. Increasing priority level.")
            adjusted_level = min(current_level + 1, PRIORITY_LEVELS["critical"]) # Increase level by 1, cap at critical

        # Rule 2: Check for explicit metadata flags (examples)
        if message.metadata:
            if message.metadata.get("is_urgent") is True or message.metadata.get("is_critical") is True:
                logger.debug("Found 'is_urgent' or 'is_critical' flag in metadata. Setting priority to critical.")
                adjusted_level = PRIORITY_LEVELS["critical"] # Set directly to critical
            elif message.metadata.get("is_important") is True:
                 if adjusted_level < PRIORITY_LEVELS["high"]:
                     logger.debug("Found 'is_important' flag in metadata. Increasing priority level to high.")
                     adjusted_level = max(adjusted_level, PRIORITY_LEVELS["high"]) # Ensure at least high

        # --- Add more rules as needed --- 

        # Get the final priority string
        final_priority = LEVEL_TO_PRIORITY.get(adjusted_level, "medium")

        if final_priority != current_priority_str:
            logger.info(f"Adjusted priority for msg to {message.recipient}: {current_priority_str} -> {final_priority}")
        else:
             logger.debug(f"Priority remained unchanged: {final_priority}")

        return final_priority
