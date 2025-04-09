"""Tests for core Notifier functionality and manager integration."""

import pytest
import logging
from unittest.mock import patch, MagicMock

from llama_notifications import Notifier, Message, NotificationConfig
from llama_notifications.priority import PriorityManager
from llama_notifications.spam_filter import SpamFilter
from llama_notifications.context import ContextManager
from llama_notifications.package import PackageManager
from llama_notifications.security import SecurityManager

# Test Message Data
TEST_MSG_EMAIL = Message(
    recipient="test@example.com",
    subject="Test Subject",
    body="Test Body",
    channel="email",
    priority="medium",
    metadata={"user_id": "u123"}
)

TEST_MSG_SMS = Message(
    recipient="+15551234567",
    subject="SMS Test",
    body="Short SMS body.",
    channel="sms",
    priority="high"
)

@pytest.fixture
def notifier_instance():
    """Provides a standard Notifier instance for tests."""
    # Use minimal config, rely on defaults mostly
    config_overrides = {
        "log_level": "DEBUG", # Use debug for more verbose test output
        "channels": {
            "email": {"provider": "test_smtp"},
            "sms": {"provider": "test_twilio"}
        }
    }
    return Notifier(config_overrides=config_overrides)

def test_notifier_initialization(notifier_instance):
    """Test that Notifier initializes itself and managers correctly."""
    assert isinstance(notifier_instance.config, NotificationConfig)
    assert isinstance(notifier_instance.context_manager, ContextManager)
    assert isinstance(notifier_instance.priority_manager, PriorityManager)
    assert isinstance(notifier_instance.spam_filter, SpamFilter)
    assert isinstance(notifier_instance.package_manager, PackageManager)
    assert isinstance(notifier_instance.security_manager, SecurityManager)
    assert notifier_instance.logger.level == logging.DEBUG

def test_send_successful_flow(notifier_instance, caplog):
    """Test the basic successful send flow through all managers."""
    notifier = notifier_instance
    caplog.set_level(logging.DEBUG)

    # Mock manager methods to ensure they are called and return expected types
    with patch.object(notifier.context_manager, 'get_context', return_value=TEST_MSG_EMAIL.metadata) as mock_get_context, \
         patch.object(notifier.priority_manager, 'get_adjusted_priority', return_value='medium') as mock_get_priority, \
         patch.object(notifier.spam_filter, 'is_spam', return_value=False) as mock_is_spam, \
         patch.object(notifier.package_manager, 'package_message', return_value=TEST_MSG_EMAIL.to_dict()) as mock_package, \
         patch.object(notifier.security_manager, 'encrypt', return_value=f"ENC:{TEST_MSG_EMAIL.body}") as mock_encrypt:

        result = notifier.send(TEST_MSG_EMAIL)

        mock_get_context.assert_called_once_with(TEST_MSG_EMAIL)
        mock_get_priority.assert_called_once_with(TEST_MSG_EMAIL)
        mock_is_spam.assert_called_once_with(TEST_MSG_EMAIL, threshold=pytest.approx(0.8)) # Check default threshold
        mock_package.assert_called_once_with(TEST_MSG_EMAIL, "email")
        mock_encrypt.assert_called_once()

        assert result["success"] is True
        assert result["channel_used"] == "email"
        assert result["provider_used"] == "test_smtp"
        assert "Processing notification request" in caplog.text
        assert "Adjusted priority: medium" in caplog.text
        assert "Applied placeholder encryption" in caplog.text
        assert "Selected channel 'email' (Provider: test_smtp)" in caplog.text
        assert "[Placeholder] Attempting delivery via test_smtp" in caplog.text

def test_send_spam_detected(notifier_instance, caplog):
    """Test that sending is aborted if spam is detected."""
    notifier = notifier_instance
    caplog.set_level(logging.INFO)

    with patch.object(notifier.spam_filter, 'is_spam', return_value=True) as mock_is_spam:
        result = notifier.send(TEST_MSG_EMAIL)

        mock_is_spam.assert_called_once()
        assert result["success"] is False
        assert result["reason"] == "spam_detected"
        assert "Message flagged as spam" in caplog.text
        assert "Aborting send" in caplog.text

def test_send_channel_not_configured(notifier_instance, caplog):
    """Test sending fails if the channel isn't in the config."""
    notifier = notifier_instance
    caplog.set_level(logging.ERROR)

    unknown_channel_msg = Message(
        recipient="foo@bar.com", subject="X", body="Y", channel="webhook"
    )

    result = notifier.send(unknown_channel_msg)

    assert result["success"] is False
    assert result["reason"] == "channel_not_configured"
    assert "Channel 'webhook' is not configured" in caplog.text

def test_send_handles_processing_exception(notifier_instance, caplog):
    """Test that exceptions during manager processing are caught."""
    notifier = notifier_instance
    caplog.set_level(logging.ERROR)

    # Make one of the managers raise an unexpected error
    with patch.object(notifier.package_manager, 'package_message', side_effect=ValueError("Packaging failed!")):
        result = notifier.send(TEST_MSG_SMS)

        assert result["success"] is False
        assert result["reason"] == "processing_error"
        assert result["error"] == "Packaging failed!"
        assert "Error processing notification" in caplog.text
        assert "Packaging failed!" in caplog.text
