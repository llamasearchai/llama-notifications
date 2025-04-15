"""
llama_notifications: Privacy-preserving multi-channel notification service.

A comprehensive notification delivery system with MLX-accelerated processing,
Neural Engine spam filtering, end-to-end encryption, and context-aware delivery.

Features:
- Multi-channel support (Push, SMS, Email)
- MLX-accelerated priority routing
- Neural Engine spam filtering
- End-to-end encryption
- TEE-protected processing
- GDPR-compliant receipt handling
- Context-aware delivery

Example usage:
    from llama_notifications.service import (
        NotificationService, NotificationRequest, NotificationContent,
        RecipientInfo, ChannelType
    )

    # Initialize service
    service = NotificationService()

    # Create and send notification
    recipient = RecipientInfo(user_id="user123", email="user@example.com")
    content = NotificationContent(title="Hello", body="Test notification")
    request = NotificationRequest(recipient=recipient, content=content,
                                 channels=[ChannelType.EMAIL])
    results = service.send(request)
"""

# Import main components for easier access
from .package import (
    ChannelType,
    DeliveryStatus,
    EncryptionType,
    NotificationContent,
    NotificationRequest,
    Priority,
    RecipientInfo,
    UserPreferences,
)

__version__ = "0.1.0"
__author__ = "Nik Jois"
__email__ = "nikjois@llamasearch.ai" = "Nik Jois"
__email__ = "nikjois@llamasearch.ai" = "Nik Jois"
