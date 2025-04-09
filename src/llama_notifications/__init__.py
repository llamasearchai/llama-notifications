"""
LlamaNotifications - System for managing and delivering notifications.
"""

from .core import Notifier
from .message import Message
from .config import NotificationConfig
from .priority import PriorityManager
from .spam_filter import SpamFilter
from .context import ContextManager
from .package import PackageManager
from .security import SecurityManager
# Keep other potential exports commented for now
# from .security import SecurityManager
# ... etc

__version__ = "0.1.1" # Bump version slightly due to refactor

__all__ = [
    "Notifier",
    "Message",
    "NotificationConfig",
    "PriorityManager",
    "SpamFilter",
    "ContextManager",
    "PackageManager",
    "SecurityManager",
    # Add other core classes here when ready
]
