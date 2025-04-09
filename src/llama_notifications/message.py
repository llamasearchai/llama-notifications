\"\"\"
Defines the data structure for a notification message.
\"\"\"

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal

# Define common channel types, can be expanded
NotificationChannel = Literal["email", "sms", "push", "webhook", "slack", "teams"]
# Define common priority levels
NotificationPriority = Literal["low", "medium", "high", "critical"]

@dataclass
class Message:
    \"\"\"
    Represents a notification message to be sent.

    Attributes:
        recipient (str): The primary recipient identifier (e.g., email address, phone number, user ID).
        subject (str): The subject line or title of the notification.
        body (str): The main content/body of the notification.
        channel (NotificationChannel): The intended delivery channel (e.g., \'email\', \'sms\').
        priority (NotificationPriority): The priority level of the message. Defaults to \'medium\'.
        sender (Optional[str]): Identifier for the sender (e.g., service name, email address). Defaults to None.
        metadata (Optional[Dict[str, Any]]): Optional dictionary for additional context or parameters specific
                                              to the channel or processing modules. Defaults to None.
    \"\"\"
    recipient: str
    subject: str
    body: str
    channel: NotificationChannel
    priority: NotificationPriority = "medium"
    sender: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        # Basic validation can be added here if needed
        if not self.recipient:
            raise ValueError("Message recipient cannot be empty.")
        if not self.channel:
            raise ValueError("Message channel cannot be empty.")

    def to_dict(self) -> Dict[str, Any]:
        \"\"\"Converts the message object to a dictionary.\"\"\"
        return {
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "channel": self.channel,
            "priority": self.priority,
            "sender": self.sender,
            "metadata": self.metadata,
        } 