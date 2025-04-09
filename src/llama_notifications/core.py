"""
Core notification sending logic.
"""
import logging
from typing import Dict, Any, Optional

from .message import Message, NotificationPriority
from .config import NotificationConfig
from .priority import PriorityManager     # Import manager classes
from .spam_filter import SpamFilter
from .context import ContextManager
from .package import PackageManager
from .security import SecurityManager


class Notifier:
    """
    Handles the processing and sending of notifications.

    Orchestrates the use of configuration, priority, filtering,
    context, security, and packaging modules.
    """

    def __init__(self, config_overrides: Optional[Dict[str, Any]] = None):
        """
        Initializes the Notifier and its component managers.

        Args:
            config_overrides (Optional[Dict[str, Any]]): Configuration overrides dictionary.
                                                         These are merged with default settings.
        """
        self.config = NotificationConfig(config_overrides)
        self.logger = logging.getLogger(__name__)
        log_level_str = self.config.get("log_level", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level_str, logging.INFO))
        # Set level for the root logger of the package as well, affects child loggers
        pkg_logger = logging.getLogger("llama_notifications")
        pkg_logger.setLevel(getattr(logging, log_level_str, logging.INFO))
         # Ensure handlers are present for the package logger if needed
        if not pkg_logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            pkg_logger.addHandler(handler)
            pkg_logger.propagate = False # Prevent duplicate messages in root logger if it also has handlers


        # Initialize managers, passing relevant config sections
        self.context_manager = ContextManager(self.config.get('context', {}))
        self.priority_manager = PriorityManager(self.config.get('priority', {}))
        self.spam_filter = SpamFilter(self.config.get('spam_filter', {}))
        self.package_manager = PackageManager(self.config.get('package', {}))
        self.security_manager = SecurityManager(self.config.get('security', {}))

        self.logger.info("Notifier initialized with all managers.")


    def send(self, message: Message) -> Dict[str, Any]:
        """
        Processes and attempts to send a notification message through integrated managers.

        Args:
            message (Message): The notification message object.

        Returns:
            Dict[str, Any]: A dictionary indicating success status and potentially an error message.
        """
        self.logger.info(f"Processing notification request for {message.recipient} via {message.channel}")
        self.logger.debug(f"Original message: {message.to_dict()}")

        try:
            # 1. Get Context (currently simple)
            context = self.context_manager.get_context(message)
            self.logger.debug(f"Extracted context: {context}")

            # 2. Determine Adjusted Priority
            adjusted_priority: NotificationPriority = self.priority_manager.get_adjusted_priority(message)
            # Update message priority if adjusted (optional, depends on desired behavior)
            # message.priority = adjusted_priority
            self.logger.debug(f"Adjusted priority: {adjusted_priority}")

            # 3. Check Spam Score and potentially block
            spam_threshold = self.config.get('spam_filter.threshold', 0.8) # Get threshold from config
            is_spam = self.spam_filter.is_spam(message, threshold=spam_threshold)
            if is_spam:
                 error_msg = f"Message flagged as spam (score > {spam_threshold}). Aborting send."
                 self.logger.warning(error_msg)
                 return {"success": False, "error": error_msg, "reason": "spam_detected"}

            # 4. Package the message for the channel
            # Note: We use the original message channel here. Context analysis *could* change it,
            # but the simplified ContextManager doesn't do that currently.
            payload = self.package_manager.package_message(message, message.channel)
            self.logger.debug(f"Packaged payload: {payload}")

            # 5. Apply Security (Placeholder Encryption)
            # Example: Encrypt only the body for now
            if "body" in payload:
                 payload["body"] = self.security_manager.encrypt(payload["body"])
                 self.logger.debug("Applied placeholder encryption to payload body.")

            # 6. Select Delivery Mechanism (Placeholder)
            # In a real system, this would involve channel providers based on message.channel
            # and self.config (e.g., SMTP settings, Twilio credentials, FCM keys)
            channel_config = self.config.get(f"channels.{message.channel}")
            if not channel_config:
                error_msg = f"Channel '{message.channel}' is not configured."
                self.logger.error(error_msg)
                return {"success": False, "error": error_msg, "reason": "channel_not_configured"}

            provider = channel_config.get("provider", "unknown")
            self.logger.info(f"Selected channel '{message.channel}' (Provider: {provider}) for delivery.")

            # 7. Attempt Delivery (Placeholder Simulation)
            self.logger.info(f"[Placeholder] Attempting delivery via {provider}...")
            # Simulate sending the `payload` using the configured provider for the channel
            print(f"[Placeholder] Sending via {message.channel}/{provider}: Payload={payload}") # Keep print for visibility

            # Simulate success for now
            self.logger.info(f"Notification request processed successfully for {message.recipient}.")
            return {"success": True, "channel_used": message.channel, "provider_used": provider}

        except Exception as e:
            self.logger.error(f"Error processing notification for {message.recipient}: {e}", exc_info=True)
            return {"success": False, "error": str(e), "reason": "processing_error"}
