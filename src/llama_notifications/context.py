"""
Provides simple context extraction from notification messages.
"""

import logging
from typing import Dict, Any, Optional

from .message import Message # Use the standard Message class

# Configure logging
logger = logging.getLogger(__name__)

class ContextManager:
    """
    Extracts and potentially processes context information from a Message object.

    Currently, this is a basic implementation that primarily focuses on
    extracting information present within the message itself (e.g., metadata).
    Future versions could integrate external data sources for richer context.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the ContextManager.

        Args:
            config (Dict[str, Any]): Configuration options (currently unused, placeholder).
        """
        self.config = config if config is not None else {}
        logger.info("ContextManager initialized.")

    def get_context(self, message: Message) -> Dict[str, Any]:
        """
        Extracts context information relevant to the notification message.

        Currently, this mainly returns the metadata attached to the message.
        It could be expanded to parse the body or subject for specific context clues.

        Args:
            message (Message): The notification message object.

        Returns:
            Dict[str, Any]: A dictionary containing extracted context information.
                          Defaults to the message's metadata.
        """

        # Start with metadata provided in the message
        extracted_context = message.metadata.copy() if message.metadata else {}

        logger.debug(f"Extracted initial context for msg to {message.recipient}: {extracted_context}")

        # --- Placeholder for future enhancements --- 
        # Example: Parse body for mentions (@user) or tags (#project)
        # mentions = self._extract_mentions(message.body)
        # if mentions: extracted_context['mentions'] = mentions

        # Example: Add message priority to context if not already present
        # if 'priority' not in extracted_context:
        #     extracted_context['priority'] = message.priority

        # Example: Check for sensitive content hints (simple keyword check)
        # sensitive_keywords = {'password', 'secret', 'confidential'}
        # if any(keyword in message.subject.lower() or keyword in message.body.lower() for keyword in sensitive_keywords):
        #     extracted_context['is_sensitive_content'] = True

        logger.debug(f"Final context for msg to {message.recipient}: {extracted_context}")
        return extracted_context

    # Example placeholder for a more complex parsing function
    # def _extract_mentions(self, text: str) -> List[str]:
    #     # Basic regex for @mentions
    #     return re.findall(r"@(\w+)", text)
