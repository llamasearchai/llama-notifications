"""
Context analysis for optimal notification delivery.

This module provides context-aware channel selection for notifications,
considering factors like user preferences, time of day, device activity,
and notification content to determine the optimal delivery channel.
"""

import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logger = logging.getLogger("llama_notifications.ml.context")


class ChannelType(Enum):
    """Notification channel types supported by the system."""

    PUSH = 1
    SMS = 2
    EMAIL = 3


class UserPreferences:
    """User notification preferences."""

    def __init__(
        self,
        user_id: str,
        preferred_channels: List[ChannelType],
        do_not_disturb: Dict[ChannelType, List[Tuple[int, int]]] = None,
        timezone: str = "UTC",
        language: str = "en",
    ):
        """
        Initialize user preferences.

        Args:
            user_id: User identifier
            preferred_channels: List of preferred channels in order of preference
            do_not_disturb: Dict mapping channels to lists of (start_hour, end_hour) ranges
            timezone: User's timezone
            language: User's preferred language
        """
        self.user_id = user_id
        self.preferred_channels = preferred_channels
        self.do_not_disturb = do_not_disturb or {}
        self.timezone = timezone
        self.language = language

    def is_dnd_active(self, channel: ChannelType) -> bool:
        """
        Check if Do Not Disturb is currently active for a channel.

        Args:
            channel: The channel type to check

        Returns:
            True if DND is active, False otherwise
        """
        if channel not in self.do_not_disturb:
            return False

        # Get current hour in user's timezone
        now = datetime.now(timezone.utc)
        user_tz = datetime.now(tz=timezone.utc)  # Placeholder, should use proper timezone
        current_hour = user_tz.hour

        # Check if current hour falls within any DND period
        for start_hour, end_hour in self.do_not_disturb.get(channel, []):
            if start_hour <= end_hour:
                # Simple range (e.g., 22-06)
                if start_hour <= current_hour < end_hour:
                    return True
            else:
                # Overnight range (e.g., 22-06)
                if current_hour >= start_hour or current_hour < end_hour:
                    return True

        return False


class RecipientContext:
    """Context information about a notification recipient."""

    def __init__(
        self,
        user_id: str,
        preferences: Optional[UserPreferences] = None,
        push_enabled: bool = True,
        push_token: Optional[str] = None,
        sms_enabled: bool = True,
        phone: Optional[str] = None,
        email_enabled: bool = True,
        email: Optional[str] = None,
        device_active: bool = False,
        last_active: Optional[int] = None,
        notification_history: Optional[Dict[ChannelType, List[Dict[str, Any]]]] = None,
    ):
        """
        Initialize recipient context.

        Args:
            user_id: User identifier
            preferences: User notification preferences
            push_enabled: Whether push notifications are enabled
            push_token: Push notification token
            sms_enabled: Whether SMS notifications are enabled
            phone: Phone number for SMS
            email_enabled: Whether email notifications are enabled
            email: Email address
            device_active: Whether user's device is currently active
            last_active: Timestamp of last activity
            notification_history: Recent notification history by channel
        """
        self.user_id = user_id
        self.preferences = preferences
        self.push_enabled = push_enabled
        self.push_token = push_token
        self.sms_enabled = sms_enabled
        self.phone = phone
        self.email_enabled = email_enabled
        self.email = email
        self.device_active = device_active
        self.last_active = last_active
        self.notification_history = notification_history or {}

    def has_channel(self, channel: ChannelType) -> bool:
        """
        Check if the recipient has a specific channel available.

        Args:
            channel: The channel to check

        Returns:
            True if channel is available, False otherwise
        """
        if channel == ChannelType.PUSH:
            return self.push_enabled and bool(self.push_token)
        elif channel == ChannelType.SMS:
            return self.sms_enabled and bool(self.phone)
        elif channel == ChannelType.EMAIL:
            return self.email_enabled and bool(self.email)
        else:
            return False

    def get_enabled_channels(self) -> List[ChannelType]:
        """
        Get all enabled channels for the recipient.

        Returns:
            List of enabled channels
        """
        channels = []

        if self.has_channel(ChannelType.PUSH):
            channels.append(ChannelType.PUSH)

        if self.has_channel(ChannelType.SMS):
            channels.append(ChannelType.SMS)

        if self.has_channel(ChannelType.EMAIL):
            channels.append(ChannelType.EMAIL)

        return channels

    def get_recent_notifications(
        self, channel: Optional[ChannelType] = None, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent notifications for the recipient.

        Args:
            channel: Optional channel to filter by
            hours: Time window in hours

        Returns:
            List of recent notifications
        """
        now = time.time()
        cutoff = now - (hours * 3600)

        if channel:
            # Get notifications for specific channel
            return [
                n
                for n in self.notification_history.get(channel, [])
                if n.get("timestamp", 0) >= cutoff
            ]
        else:
            # Get notifications across all channels
            all_notifications = []
            for channel_notifications in self.notification_history.values():
                all_notifications.extend(
                    [n for n in channel_notifications if n.get("timestamp", 0) >= cutoff]
                )
            return all_notifications


class NotificationContext:
    """Context information about a notification."""

    def __init__(
        self,
        notification_id: str,
        title: str,
        body: str,
        priority_level: int,
        time_sensitive: bool = False,
        category: Optional[str] = None,
        interaction_required: bool = False,
        expires_at: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize notification context.

        Args:
            notification_id: Unique notification identifier
            title: Notification title
            body: Notification body
            priority_level: Priority level (0-3)
            time_sensitive: Whether notification is time-sensitive
            category: Notification category
            interaction_required: Whether user interaction is required
            expires_at: Expiration timestamp
            metadata: Additional metadata
        """
        self.notification_id = notification_id
        self.title = title
        self.body = body
        self.priority_level = priority_level
        self.time_sensitive = time_sensitive
        self.category = category
        self.interaction_required = interaction_required
        self.expires_at = expires_at
        self.metadata = metadata or {}

    def is_expired(self) -> bool:
        """
        Check if notification has expired.

        Returns:
            True if expired, False otherwise
        """
        if not self.expires_at:
            return False

        return time.time() >= self.expires_at


class EnvironmentContext:
    """Context information about the notification environment."""

    def __init__(
        self,
        current_time: Optional[int] = None,
        network_type: Optional[str] = None,
        network_quality: Optional[float] = None,
        battery_level: Optional[float] = None,
        low_power_mode: bool = False,
        location_type: Optional[str] = None,
        app_state: Optional[str] = None,
    ):
        """
        Initialize environment context.

        Args:
            current_time: Current timestamp
            network_type: Network type (e.g., 'wifi', 'cellular', 'offline')
            network_quality: Network quality score (0-1)
            battery_level: Device battery level (0-1)
            low_power_mode: Whether device is in low power mode
            location_type: Location type (e.g., 'home', 'work', 'traveling')
            app_state: Application state (e.g., 'foreground', 'background', 'closed')
        """
        self.current_time = current_time or time.time()
        self.network_type = network_type
        self.network_quality = network_quality
        self.battery_level = battery_level
        self.low_power_mode = low_power_mode
        self.location_type = location_type
        self.app_state = app_state

    def is_device_constrained(self) -> bool:
        """
        Check if device is operating under constrained conditions.

        Returns:
            True if device is constrained, False otherwise
        """
        if self.low_power_mode:
            return True

        if self.battery_level is not None and self.battery_level < 0.15:
            return True

        if self.network_quality is not None and self.network_quality < 0.3:
            return True

        return False

    def is_connected(self) -> bool:
        """
        Check if device has network connectivity.

        Returns:
            True if connected, False otherwise
        """
        return self.network_type not in (None, "offline")


class ChannelEvaluator:
    """Evaluates channels based on contextual factors."""

    def evaluate_channel(
        self,
        channel: ChannelType,
        recipient_context: RecipientContext,
        notification_context: NotificationContext,
        environment_context: EnvironmentContext,
    ) -> float:
        """
        Evaluate a channel for the given context.

        Args:
            channel: The channel to evaluate
            recipient_context: Recipient context
            notification_context: Notification context
            environment_context: Environment context

        Returns:
            Score for the channel (0-1)
        """
        # Start with base score
        score = 0.5

        # Check basic availability
        if not recipient_context.has_channel(channel):
            return 0.0

        # Check user preferences
        preferences = recipient_context.preferences
        if preferences:
            if channel in preferences.preferred_channels:
                # Boost score based on preference order
                preference_index = preferences.preferred_channels.index(channel)
                preference_boost = 0.3 * (
                    1.0 - (preference_index / len(preferences.preferred_channels))
                )
                score += preference_boost

            # Check DND status - apply large penalty if active
            if preferences.is_dnd_active(channel):
                # Allow high priority to override DND with smaller penalty
                if notification_context.priority_level >= 2:  # HIGH or URGENT
                    score -= 0.3
                else:
                    score -= 0.8

        # Channel-specific factors
        if channel == ChannelType.PUSH:
            # Push notifications are best for immediate, interactive content
            # when the device is available

            # Device active bonus
            if recipient_context.device_active:
                score += 0.2

            # Recent activity bonus
            if (
                recipient_context.last_active and time.time() - recipient_context.last_active < 3600
            ):  # Within last hour
                score += 0.1

            # App state consideration
            if environment_context.app_state == "foreground":
                score += 0.2
            elif environment_context.app_state == "background":
                score += 0.1

            # Battery/network considerations
            if environment_context.is_device_constrained():
                score -= 0.1

            # Interaction considerations
            if notification_context.interaction_required:
                score += 0.2

        elif channel == ChannelType.SMS:
            # SMS is good for urgent, short messages that need attention
            # even when the app isn't active

            # Priority boost for SMS
            if notification_context.priority_level >= 2:  # HIGH or URGENT
                score += 0.3

            # Time sensitivity boost
            if notification_context.time_sensitive:
                score += 0.2

            # Message length penalty (SMS works better for short messages)
            message_length = len(notification_context.title) + len(notification_context.body)
            if message_length > 300:
                score -= 0.2

            # Network considerations
            if environment_context.network_type == "offline":
                score += 0.2  # SMS can work without data connection

        elif channel == ChannelType.EMAIL:
            # Email is best for longer, non-urgent content

            # Priority penalty for email (not ideal for urgent messages)
            if notification_context.priority_level >= 2:  # HIGH or URGENT
                score -= 0.2

            # Message length bonus (email works better for longer messages)
            message_length = len(notification_context.title) + len(notification_context.body)
            if message_length > 300:
                score += 0.2

            # Non-immediate content bonus
            if not notification_context.time_sensitive:
                score += 0.2

            # Network quality consideration
            if environment_context.network_quality and environment_context.network_quality < 0.5:
                score -= 0.1

        # Normalize score between 0 and 1
        score = max(0.0, min(score, 1.0))

        return score


class ContextAnalyzer:
    """Analyzes context for optimal notification delivery."""

    def __init__(self):
        """Initialize the context analyzer."""
        self.channel_evaluator = ChannelEvaluator()
        logger.info("Context analyzer initialized")

    def get_optimal_channels(
        self,
        recipient_context: RecipientContext,
        notification_context: NotificationContext,
        environment_context: Optional[EnvironmentContext] = None,
        min_score_threshold: float = 0.3,
    ) -> List[Tuple[ChannelType, float]]:
        """
        Determine optimal channels based on context.

        Args:
            recipient_context: Context of the recipient
            notification_context: Context of the notification
            environment_context: Context of the environment
            min_score_threshold: Minimum score threshold for channels

        Returns:
            List of (channel, score) tuples sorted by score
        """
        # Use default environment context if not provided
        if environment_context is None:
            environment_context = EnvironmentContext()

        # Get available channels
        available_channels = recipient_context.get_enabled_channels()

        # Evaluate each channel
        channel_scores = []
        for channel in available_channels:
            score = self.channel_evaluator.evaluate_channel(
                channel, recipient_context, notification_context, environment_context
            )

            # Filter by threshold
            if score >= min_score_threshold:
                channel_scores.append((channel, score))

        # Sort by score (descending)
        channel_scores.sort(key=lambda x: x[1], reverse=True)

        logger.debug(
            f"Channel scores for notification {notification_context.notification_id}: {channel_scores}"
        )
        return channel_scores

    def explain_channel_selection(
        self,
        recipient_context: RecipientContext,
        notification_context: NotificationContext,
        environment_context: Optional[EnvironmentContext] = None,
    ) -> Dict[str, Any]:
        """
        Explain the channel selection process.

        Args:
            recipient_context: Context of the recipient
            notification_context: Context of the notification
            environment_context: Context of the environment

        Returns:
            Dictionary with explanation of channel selection
        """
        # Use default environment context if not provided
        if environment_context is None:
            environment_context = EnvironmentContext()

        # Get channel scores
        channel_scores = self.get_optimal_channels(
            recipient_context,
            notification_context,
            environment_context,
            min_score_threshold=0.0,  # Include all channels in explanation
        )

        # Generate explanations for each channel
        explanations = {}
        for channel, score in channel_scores:
            factors = []

            # Basic availability
            if not recipient_context.has_channel(channel):
                factors.append(
                    {
                        "factor": "availability",
                        "impact": "negative",
                        "description": f"Channel {channel.name} is not available for this user",
                    }
                )
                continue

            # User preferences
            preferences = recipient_context.preferences
            if preferences:
                if channel in preferences.preferred_channels:
                    preference_index = preferences.preferred_channels.index(channel)
                    factors.append(
                        {
                            "factor": "user_preference",
                            "impact": "positive",
                            "description": f"User has {channel.name} as preference #{preference_index+1}",
                        }
                    )

                if preferences.is_dnd_active(channel):
                    if notification_context.priority_level >= 2:
                        factors.append(
                            {
                                "factor": "do_not_disturb",
                                "impact": "negative",
                                "description": f"DND is active for {channel.name}, but overridden by HIGH priority",
                            }
                        )
                    else:
                        factors.append(
                            {
                                "factor": "do_not_disturb",
                                "impact": "negative",
                                "description": f"DND is active for {channel.name}",
                            }
                        )

            # Channel-specific factors
            if channel == ChannelType.PUSH:
                if recipient_context.device_active:
                    factors.append(
                        {
                            "factor": "device_active",
                            "impact": "positive",
                            "description": "User's device is currently active",
                        }
                    )

                if environment_context.app_state == "foreground":
                    factors.append(
                        {
                            "factor": "app_state",
                            "impact": "positive",
                            "description": "App is in foreground",
                        }
                    )

                if environment_context.is_device_constrained():
                    factors.append(
                        {
                            "factor": "device_constraints",
                            "impact": "negative",
                            "description": "Device has battery or network constraints",
                        }
                    )

            elif channel == ChannelType.SMS:
                if notification_context.priority_level >= 2:
                    factors.append(
                        {
                            "factor": "priority",
                            "impact": "positive",
                            "description": "HIGH priority notification suitable for SMS",
                        }
                    )

                message_length = len(notification_context.title) + len(notification_context.body)
                if message_length > 300:
                    factors.append(
                        {
                            "factor": "message_length",
                            "impact": "negative",
                            "description": "Message is too long for optimal SMS delivery",
                        }
                    )

            elif channel == ChannelType.EMAIL:
                if notification_context.priority_level >= 2:
                    factors.append(
                        {
                            "factor": "priority",
                            "impact": "negative",
                            "description": "HIGH priority notification less suitable for Email",
                        }
                    )

                message_length = len(notification_context.title) + len(notification_context.body)
                if message_length > 300:
                    factors.append(
                        {
                            "factor": "message_length",
                            "impact": "positive",
                            "description": "Longer message well-suited for Email",
                        }
                    )

            explanations[channel.name] = {"score": score, "factors": factors}

        return {
            "notification_id": notification_context.notification_id,
            "channel_explanations": explanations,
            "recommended_channels": [channel.name for channel, _ in channel_scores if _ >= 0.3],
        }
