"""
Tests for the NotificationService class.

This module contains comprehensive tests for the NotificationService
with mocking of external services and ML components.
"""

import datetime
import json
import os
import uuid
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from llama_notifications.service import (
    ChannelType,
    DeliveryStatus,
    EncryptionType,
    NotificationContent,
    NotificationRequest,
    NotificationService,
    Priority,
    RecipientInfo,
    UserPreferences,
)


# Fixtures for commonly used test objects
@pytest.fixture
def sample_recipient():
    """Create a sample recipient for testing."""
    return RecipientInfo(
        user_id="test-user-123",
        push_token="test-push-token",
        phone="+15555555555",
        email="test@example.com",
        public_key="mock-public-key-data",
        preferences=UserPreferences(
            user_id="test-user-123",
            preferred_channels=[ChannelType.PUSH, ChannelType.EMAIL],
            do_not_disturb={ChannelType.SMS: [(22, 8)]},  # 10 PM to 8 AM
            encrypted_only=False,
        ),
    )


@pytest.fixture
def sample_content():
    """Create sample notification content for testing."""
    return NotificationContent(
        title="Test Notification",
        body="This is a test notification message.",
        data={"key1": "value1", "key2": "value2"},
        action_buttons=[{"id": "btn1", "text": "Accept"}, {"id": "btn2", "text": "Reject"}],
    )


@pytest.fixture
def notification_service():
    """Create a notification service instance for testing."""
    with patch("llama_notifications.service.PushNotificationProvider") as mock_push, patch(
        "llama_notifications.service.SMSProvider"
    ) as mock_sms, patch("llama_notifications.service.EmailProvider") as mock_email, patch(
        "llama_notifications.service.SpamFilter"
    ) as mock_spam, patch(
        "llama_notifications.service.PriorityRouter"
    ) as mock_router, patch(
        "llama_notifications.service.ContextAnalyzer"
    ) as mock_analyzer:

        # Configure mocks
        mock_push_instance = MagicMock()
        mock_push_instance.initialize.return_value = True
        mock_push.return_value = mock_push_instance

        mock_sms_instance = MagicMock()
        mock_sms_instance.initialize.return_value = True
        mock_sms.return_value = mock_sms_instance

        mock_email_instance = MagicMock()
        mock_email_instance.initialize.return_value = True
        mock_email.return_value = mock_email_instance

        mock_spam_instance = MagicMock()
        mock_spam_instance.is_spam.return_value = (False, 0.1)
        mock_spam.return_value = mock_spam_instance

        mock_router_instance = MagicMock()
        mock_router_instance.calculate_priority.return_value = Priority.NORMAL
        mock_router.return_value = mock_router_instance

        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.get_optimal_channels.return_value = [
            (ChannelType.PUSH, 0.8),
            (ChannelType.EMAIL, 0.6),
            (ChannelType.SMS, 0.4),
        ]
        mock_analyzer.return_value = mock_analyzer_instance

        service = NotificationService()

        # Setup for testing
        service.providers[ChannelType.PUSH] = mock_push_instance
        service.providers[ChannelType.SMS] = mock_sms_instance
        service.providers[ChannelType.EMAIL] = mock_email_instance

        yield service


class TestNotificationService:
    """Tests for the NotificationService class."""

    def test_service_initialization(self, notification_service):
        """Test that the service initializes correctly."""
        assert notification_service is not None
        assert len(notification_service.providers) == 3
        assert ChannelType.PUSH in notification_service.providers
        assert ChannelType.SMS in notification_service.providers
        assert ChannelType.EMAIL in notification_service.providers

    def test_send_notification_basic(self, notification_service, sample_recipient, sample_content):
        """Test basic notification sending."""
        # Configure mock provider to return success
        mock_provider = notification_service.providers[ChannelType.PUSH]
        mock_result = MagicMock()
        mock_result.status = DeliveryStatus.SENT
        mock_result.receipt_id = "mock-receipt-123"
        mock_provider.send.return_value = mock_result

        # Create request
        request = NotificationRequest(
            notification_id="test-notification-123",
            recipient=sample_recipient,
            content=sample_content,
            channels=[ChannelType.PUSH],
            priority=Priority.NORMAL,
            encryption=EncryptionType.NONE,
        )

        # Send notification
        results = notification_service.send(request)

        # Verify results
        assert len(results) == 1
        assert results[0].status == DeliveryStatus.SENT
        assert results[0].notification_id == "test-notification-123"
        assert mock_provider.send.called

        # Verify notification is stored
        assert "test-notification-123" in notification_service.notifications

        # Verify receipt is stored
        assert "mock-receipt-123" in notification_service.receipts

    def test_spam_filtering(self, notification_service, sample_recipient, sample_content):
        """Test that spam notifications are rejected."""
        # Configure spam filter to detect spam
        notification_service.spam_filter.is_spam.return_value = (True, 0.95)

        # Create request
        request = NotificationRequest(
            notification_id="spam-notification-123",
            recipient=sample_recipient,
            content=sample_content,
            channels=[ChannelType.PUSH],
            priority=Priority.NORMAL,
        )

        # Send notification
        results = notification_service.send(request)

        # Verify results
        assert len(results) == 1
        assert results[0].status == DeliveryStatus.FAILED
        assert "spam" in results[0].error.lower()

        # Verify no provider was called
        for provider in notification_service.providers.values():
            assert not provider.send.called

    def test_priority_routing(self, notification_service, sample_recipient, sample_content):
        """Test that priority is calculated if not specified."""
        # Configure priority router
        notification_service.priority_router.calculate_priority.return_value = Priority.HIGH

        # Create request without explicit priority
        request = NotificationRequest(
            notification_id="priority-test-notification",
            recipient=sample_recipient,
            content=sample_content,
            channels=[ChannelType.PUSH],
            priority=Priority.NORMAL,  # Will be overridden
        )

        # Mock provider response
        mock_provider = notification_service.providers[ChannelType.PUSH]
        mock_result = MagicMock()
        mock_result.status = DeliveryStatus.SENT
        mock_provider.send.return_value = mock_result

        # Send notification
        notification_service.send(request)

        # Verify priority router was called
        assert notification_service.priority_router.calculate_priority.called

    def test_context_aware_channel_selection(
        self, notification_service, sample_recipient, sample_content
    ):
        """Test that channels are selected based on context if not specified."""
        # Configure channel providers to return success
        for provider in notification_service.providers.values():
            mock_result = MagicMock()
            mock_result.status = DeliveryStatus.SENT
            mock_result.receipt_id = f"mock-receipt-{uuid.uuid4()}"
            provider.send.return_value = mock_result

        # Create request without explicit channels
        request = NotificationRequest(
            notification_id="channel-selection-test",
            recipient=sample_recipient,
            content=sample_content,
            channels=[],  # Empty channels to trigger context-aware selection
            priority=Priority.NORMAL,
        )

        # Send notification
        results = notification_service.send(request)

        # Verify context analyzer was called
        assert notification_service.context_analyzer.get_optimal_channels.called

        # Verify results - should use channels with score > 0.3
        assert len(results) > 0

    def test_encryption(self, notification_service, sample_recipient, sample_content):
        """Test that content is encrypted when specified."""
        # Configure provider to return success
        mock_provider = notification_service.providers[ChannelType.PUSH]
        mock_result = MagicMock()
        mock_result.status = DeliveryStatus.SENT
        mock_provider.send.return_value = mock_result

        # Mock encryption service
        mock_encrypt = MagicMock(return_value="ENCRYPTED_CONTENT")
        notification_service.encryption_service.encrypt = mock_encrypt

        # Create request with encryption
        request = NotificationRequest(
            notification_id="encrypted-notification",
            recipient=sample_recipient,
            content=sample_content,
            channels=[ChannelType.PUSH],
            encryption=EncryptionType.AES256,
        )

        # Send notification
        notification_service.send(request)

        # Verify encryption was called
        assert mock_encrypt.called

    def test_scheduled_notification(self, notification_service, sample_recipient, sample_content):
        """Test that scheduled notifications are handled correctly."""
        # Create future-scheduled request
        future_time = datetime.datetime.now() + datetime.timedelta(hours=1)
        request = NotificationRequest(
            notification_id="scheduled-notification",
            recipient=sample_recipient,
            content=sample_content,
            channels=[ChannelType.PUSH],
            scheduled_time=future_time,
        )

        # Send notification
        results = notification_service.send(request)

        # Verify results
        assert len(results) == 1
        assert results[0].status == DeliveryStatus.PENDING

        # Verify no provider was called yet
        for provider in notification_service.providers.values():
            assert not provider.send.called

        # Verify notification is stored
        assert request.notification_id in notification_service.notifications

        # Now process scheduled notifications, but time hasn't arrived yet
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime.now()
            processed = notification_service.process_scheduled_notifications()
            assert processed == 0

        # Now simulate time passing and process again
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = future_time + datetime.timedelta(minutes=5)

            # Configure provider to return success
            mock_provider = notification_service.providers[ChannelType.PUSH]
            mock_result = MagicMock()
            mock_result.status = DeliveryStatus.SENT
            mock_provider.send.return_value = mock_result

            # Now process scheduled notification
            processed = notification_service.process_scheduled_notifications()

            # Verify provider was called
            assert processed == 1
            assert mock_provider.send.called

    def test_dnd_handling(self, notification_service, sample_recipient, sample_content):
        """Test that DND preferences are respected."""
        # Create recipient with active DND for push
        recipient = sample_recipient
        recipient.preferences.do_not_disturb = {
            ChannelType.PUSH: [(0, 23)]  # All day DND for testing
        }

        # Mock is_dnd_active to return True for PUSH
        recipient.preferences.is_dnd_active = MagicMock(
            side_effect=lambda channel: channel == ChannelType.PUSH
        )

        # Create normal priority request
        request = NotificationRequest(
            notification_id="dnd-test-notification",
            recipient=recipient,
            content=sample_content,
            channels=[ChannelType.PUSH, ChannelType.EMAIL, ChannelType.SMS],
            priority=Priority.NORMAL,
            context={"reason": "dnd_test"},
        )

        # Send notification
        result = notification_service.send_notification(request)

        # Assertions
        assert result.success
        assert len(result.results) == 2  # Should skip PUSH due to DND
        assert result.results[0].channel == ChannelType.EMAIL
        assert result.results[1].channel == ChannelType.SMS
