"""
MLX-accelerated priority routing for notifications.

This module provides intelligent prioritization of notifications
based on content analysis, user engagement patterns, and contextual factors.
It uses MLX acceleration when available for improved performance.
"""

import logging
import re
from enum import Enum
from typing import Any, Dict, Optional

# Try to import MLX
try:
    import mlx.core as mx
    import mlx.nn as nn

    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    # Create minimal simulation for environments without MLX
    import numpy as np

    class MXSimulation:
        def array(self, data):
            return np.array(data)

        def random(self):
            class Random:
                def normal(self, shape):
                    return np.random.normal(size=shape)

            return Random()

    class mx:
        core = MXSimulation()


# Configure logging
logger = logging.getLogger("llama_notifications.ml.priority")


class Priority(Enum):
    """Priority levels for notifications."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class NotificationRequest:
    """Simplified request class for the priority router."""

    def __init__(
        self,
        notification_id: str,
        content_title: str,
        content_body: str,
        recipient_id: str,
        context: Dict[str, Any] = None,
    ):
        """
        Initialize a simplified notification request.

        Args:
            notification_id: The notification ID
            content_title: Notification title
            content_body: Notification body
            recipient_id: Recipient user ID
            context: Additional context information
        """
        self.notification_id = notification_id
        self.content_title = content_title
        self.content_body = content_body
        self.recipient_id = recipient_id
        self.context = context or {}


class ContextFeatureExtractor:
    """Extracts features from notification context for priority routing."""

    def __init__(self):
        """Initialize the feature extractor."""
        # Keywords indicating urgency
        self.urgency_keywords = {
            "urgent",
            "important",
            "critical",
            "emergency",
            "immediate",
            "alert",
            "warning",
            "attention",
            "asap",
            "now",
            "fast",
            "quickly",
            "deadline",
            "reminder",
            "expiring",
            "expires",
        }

        # Patterns for time references
        self.time_patterns = [
            re.compile(r"in \d+ (minute|minutes|min|mins)"),
            re.compile(r"in \d+ (hour|hours|hr|hrs)"),
            re.compile(r"in \d+ (second|seconds|sec|secs)"),
            re.compile(r"today at \d+"),
            re.compile(r"by \d+:\d+"),
            re.compile(r"due (in|at|by)"),
        ]

    def extract_features(self, request: NotificationRequest) -> Dict[str, float]:
        """
        Extract priority-related features from the notification request.

        Args:
            request: The notification request

        Returns:
            Dictionary of feature names to values
        """
        features = {}

        # Extract text features
        title = request.content_title.lower()
        body = request.content_body.lower()
        combined_text = f"{title} {body}"

        # Check for explicit priority in context
        priority_from_context = request.context.get("priority", None)
        if priority_from_context is not None:
            if isinstance(priority_from_context, (int, float)):
                features["explicit_priority"] = min(float(priority_from_context), 1.0)
            elif (
                isinstance(priority_from_context, str)
                and priority_from_context.upper() in Priority.__members__
            ):
                priority_enum = Priority[priority_from_context.upper()]
                features["explicit_priority"] = (
                    float(priority_enum.value) / 3.0
                )  # Normalize to [0,1]
        else:
            features["explicit_priority"] = 0.0

        # Urgency keywords
        urgency_count = sum(1 for word in combined_text.split() if word in self.urgency_keywords)
        features["urgency_keywords"] = min(urgency_count / 5.0, 1.0)  # Cap at 1.0

        # Time sensitivity
        time_references = sum(
            1 for pattern in self.time_patterns if pattern.search(combined_text) is not None
        )
        features["time_references"] = min(time_references / 3.0, 1.0)  # Cap at 1.0

        # Context-provided features
        features["time_sensitivity"] = float(request.context.get("time_sensitivity", 0.5))
        features["user_engagement"] = float(request.context.get("user_engagement", 0.5))
        features["content_importance"] = float(request.context.get("content_importance", 0.5))
        features["user_relationship"] = float(request.context.get("user_relationship", 0.5))

        # Check for explicit time criticality
        features["is_time_critical"] = (
            1.0 if request.context.get("is_time_critical", False) else 0.0
        )

        # Security and safety related
        features["is_security_related"] = (
            1.0 if request.context.get("is_security_related", False) else 0.0
        )
        features["is_safety_related"] = (
            1.0 if request.context.get("is_safety_related", False) else 0.0
        )

        # Business impact
        features["business_impact"] = float(request.context.get("business_impact", 0.5))

        # App usage context
        features["app_active"] = 1.0 if request.context.get("app_active", False) else 0.0
        features["recent_interaction"] = (
            1.0 if request.context.get("recent_interaction", False) else 0.0
        )

        # Validate and normalize all features to [0,1]
        for key in features:
            features[key] = max(0.0, min(features[key], 1.0))

        return features


class PriorityRouter:
    """MLX-accelerated priority routing for notifications."""

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the priority router.

        Args:
            model_path: Optional path to model weights file
        """
        self.feature_extractor = ContextFeatureExtractor()
        self.model_loaded = False
        self.feature_weights = None

        # Initialize or load model
        self._initialize_model(model_path)

    def _initialize_model(self, model_path: Optional[str] = None) -> None:
        """
        Initialize the priority model.

        Args:
            model_path: Optional path to model weights file
        """
        if self.model_loaded:
            return

        if model_path:
            # In a real implementation, this would load actual model weights
            logger.info(f"Loading priority model from {model_path}")
            # Simulated loading
            self.model_loaded = True
            return

        # No model provided, initialize with default weights
        logger.info("Initializing priority model with default weights")

        # In a real implementation, these weights would be learned from data
        # These are simplified default weights for demonstration
        if MLX_AVAILABLE:
            # Create MLX arrays for weights
            self.feature_weights = {
                "explicit_priority": mx.array([2.0]),
                "urgency_keywords": mx.array([1.2]),
                "time_references": mx.array([1.0]),
                "time_sensitivity": mx.array([1.5]),
                "user_engagement": mx.array([0.8]),
                "content_importance": mx.array([1.0]),
                "user_relationship": mx.array([0.7]),
                "is_time_critical": mx.array([2.5]),
                "is_security_related": mx.array([2.0]),
                "is_safety_related": mx.array([2.0]),
                "business_impact": mx.array([1.0]),
                "app_active": mx.array([0.3]),
                "recent_interaction": mx.array([0.5]),
            }
        else:
            # Use regular Python dictionary with float values
            self.feature_weights = {
                "explicit_priority": 2.0,
                "urgency_keywords": 1.2,
                "time_references": 1.0,
                "time_sensitivity": 1.5,
                "user_engagement": 0.8,
                "content_importance": 1.0,
                "user_relationship": 0.7,
                "is_time_critical": 2.5,
                "is_security_related": 2.0,
                "is_safety_related": 2.0,
                "business_impact": 1.0,
                "app_active": 0.3,
                "recent_interaction": 0.5,
            }

        self.model_loaded = True

    def _calculate_weighted_score(self, features: Dict[str, float]) -> float:
        """
        Calculate weighted priority score.

        Args:
            features: Extracted features

        Returns:
            Priority score
        """
        score = 0.0
        total_weight = 0.0

        for feature_name, feature_value in features.items():
            if feature_name in self.feature_weights:
                weight = self.feature_weights[feature_name]

                if MLX_AVAILABLE and isinstance(weight, type(mx.array([0]))):
                    weight_value = float(weight[0])
                else:
                    weight_value = float(weight)

                score += feature_value * weight_value
                total_weight += weight_value

        # Normalize by total weight
        if total_weight > 0:
            normalized_score = score / total_weight
        else:
            normalized_score = 0.5  # Default to NORMAL if no weights

        return normalized_score

    def calculate_priority(self, request: NotificationRequest) -> Priority:
        """
        Calculate optimal priority for a notification.

        Args:
            request: The notification request

        Returns:
            Calculated priority level
        """
        # Make sure model is initialized
        if not self.model_loaded:
            self._initialize_model()

        # Handle override for time-critical notifications
        if request.context.get("is_time_critical", False):
            logger.info(
                f"Notification {request.notification_id} marked as time-critical, assigning URGENT priority"
            )
            return Priority.URGENT

        # Extract features
        features = self.feature_extractor.extract_features(request)

        # Calculate score
        score = self._calculate_weighted_score(features)

        # Determine priority based on score
        if score > 0.8:
            priority = Priority.URGENT
        elif score > 0.6:
            priority = Priority.HIGH
        elif score > 0.3:
            priority = Priority.NORMAL
        else:
            priority = Priority.LOW

        logger.debug(
            f"Calculated priority for {request.notification_id}: {priority.name} (score: {score:.4f})"
        )
        return priority

    def explain_priority(self, request: NotificationRequest) -> Dict[str, Any]:
        """
        Explain the priority calculation.

        Args:
            request: The notification request

        Returns:
            Dictionary with explanation of priority calculation
        """
        # Make sure model is initialized
        if not self.model_loaded:
            self._initialize_model()

        # Extract features
        features = self.feature_extractor.extract_features(request)

        # Calculate priority
        priority = self.calculate_priority(request)

        # Calculate feature contributions
        contributions = {}
        total_contribution = 0.0

        for feature_name, feature_value in features.items():
            if feature_name in self.feature_weights:
                weight = self.feature_weights[feature_name]

                if MLX_AVAILABLE and isinstance(weight, type(mx.array([0]))):
                    weight_value = float(weight[0])
                else:
                    weight_value = float(weight)

                contribution = feature_value * weight_value
                contributions[feature_name] = contribution
                total_contribution += contribution

        # Normalize contributions
        if total_contribution > 0:
            for feature_name in contributions:
                contributions[feature_name] /= total_contribution

        # Create explanation
        explanation = {
            "priority": priority.name,
            "features": features,
            "contributions": contributions,
            "top_factors": sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:3],
        }

        return explanation
