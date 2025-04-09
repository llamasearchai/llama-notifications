"""
Handles formatting and packaging of notification messages for delivery.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from .message import Message, NotificationChannel

# Configure logging
logger = logging.getLogger(__name__)

class PackageManager:
    """
    Formats a notification Message into a payload dictionary suitable for sending.

    This is a basic implementation. Future versions could tailor the payload
    based on the specific channel or add channel-specific fields.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the PackageManager.

        Args:
            config (Dict[str, Any]): Configuration options (currently unused, placeholder).
        """
        self.config = config if config is not None else {}
        logger.info("PackageManager initialized.")

    def package_message(self, message: Message, channel: NotificationChannel) -> Dict[str, Any]:
        """
        Packages the message content into a dictionary payload.

        Args:
            message (Message): The notification message object.
            channel (NotificationChannel): The target delivery channel (used for logging/potential future logic).

        Returns:
            Dict[str, Any]: A dictionary representing the packaged notification payload.
        """
        logger.debug(f"Packaging message for channel '{channel}' to {message.recipient}")

        # Start with the basic message data converted to a dictionary
        payload = message.to_dict()

        # Add a packaging timestamp
        payload["packaged_at"] = datetime.now(timezone.utc).isoformat()

        # --- Placeholder for future channel-specific formatting --- 
        # if channel == "email":
        #     payload['html_body'] = self._generate_html(message.body)
        # elif channel == "push":
        #     payload['aps'] = { 'alert': { 'title': message.subject, 'body': message.body } }
        #     payload['custom_data'] = message.metadata
        # elif channel == "sms":
        #     # SMS might just use the body directly
        #     payload = { 'to': message.recipient, 'body': message.body } 

        logger.debug(f"Packaged payload for '{channel}': {payload}")
        return payload

    # Example placeholder for a formatting function
    # def _generate_html(self, text_body: str) -> str:
    #     # Simple conversion to basic HTML
    #     escaped_body = html.escape(text_body)
    #     return f"<p>{escaped_body.replace('\n', '<br>')}</p>"
