"""
Neural network based spam filter for notifications.

This module provides a spam detection system for notifications that uses
neural networks to identify potentially unwanted or malicious content.
It leverages MLX acceleration when available for improved performance.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

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
logger = logging.getLogger("llama_notifications.ml.spam_filter")


@dataclass
class NotificationContent:
    """Content of a notification."""

    title: str
    body: str
    data: Dict[str, Any] = field(default_factory=dict)
    media_urls: List[str] = field(default_factory=list)
    action_buttons: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_sensitive: bool = False


class SpamFeatureExtractor:
    """Extracts features from notification content for spam analysis."""

    def __init__(self):
        """Initialize the feature extractor."""
        # Spam trigger words (simplified list for demonstration)
        self.spam_words = {
            "free",
            "discount",
            "limited time",
            "offer",
            "click now",
            "exclusive",
            "win",
            "winner",
            "prize",
            "claim",
            "urgent",
            "important",
            "act now",
            "guaranteed",
            "congratulations",
            "selected",
            "cash",
            "money",
            "credit",
            "buy",
            "purchase",
            "order",
            "sale",
            "deal",
            "subscribe",
            "trial",
        }

        # URL pattern for detecting links
        self.url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )

    def extract_features(self, content: NotificationContent) -> List[float]:
        """
        Extract features from notification content for spam detection.

        Args:
            content: The notification content to analyze

        Returns:
            List of numerical features for spam detection
        """
        features = []

        # Basic length features
        features.append(min(len(content.title) / 100, 1.0))
        features.append(min(len(content.body) / 1000, 1.0))

        # Word count features
        title_words = content.title.lower().split()
        body_words = content.body.lower().split()
        features.append(min(len(title_words) / 20, 1.0))
        features.append(min(len(body_words) / 200, 1.0))

        # Character features
        features.append(content.title.count("!") / max(len(content.title), 1))
        features.append(content.body.count("!") / max(len(content.body), 1))
        features.append(content.title.count("$") / max(len(content.title), 1))
        features.append(content.body.count("$") / max(len(content.body), 1))
        features.append(content.title.count("%") / max(len(content.title), 1))
        features.append(content.body.count("%") / max(len(content.body), 1))

        # Capitalization features
        title_caps_ratio = sum(1 for c in content.title if c.isupper()) / max(len(content.title), 1)
        body_caps_ratio = sum(1 for c in content.body if c.isupper()) / max(len(content.body), 1)
        features.append(title_caps_ratio)
        features.append(body_caps_ratio)

        # All caps word counts
        title_all_caps = sum(1 for word in title_words if word.isupper() and len(word) > 1)
        body_all_caps = sum(1 for word in body_words if word.isupper() and len(word) > 1)
        features.append(title_all_caps / max(len(title_words), 1))
        features.append(body_all_caps / max(len(body_words), 1))

        # URL features
        title_urls = len(self.url_pattern.findall(content.title))
        body_urls = len(self.url_pattern.findall(content.body))
        features.append(min(title_urls, 5) / 5)
        features.append(min(body_urls, 10) / 10)

        # External media URLs
        features.append(min(len(content.media_urls), 5) / 5)

        # Spam word presence
        title_spam_words = sum(1 for word in title_words if word in self.spam_words)
        body_spam_words = sum(1 for word in body_words if word in self.spam_words)
        features.append(title_spam_words / max(len(title_words), 1))
        features.append(body_spam_words / max(len(body_words), 1))

        # Action button count
        features.append(min(len(content.action_buttons), 5) / 5)

        # Button spam words
        button_spam_count = 0
        for button in content.action_buttons:
            if "text" in button:
                button_text = button["text"].lower()
                button_spam_count += sum(
                    1 for word in button_text.split() if word in self.spam_words
                )
        features.append(min(button_spam_count, 5) / 5)

        # Additional data features
        has_tracking_params = 0
        for key in content.data.keys():
            if key.lower() in {
                "tracking",
                "track",
                "source",
                "campaign",
                "ref",
                "referrer",
            }:
                has_tracking_params = 1
                break
        features.append(float(has_tracking_params))

        # Ensure we have a fixed-length feature vector
        # Pad with zeros if needed
        while len(features) < 32:
            features.append(0.0)

        # Truncate if too long
        features = features[:32]

        return features


class SimpleNeuralNetwork:
    """
    A simple neural network for spam detection.

    This is a simplified implementation for demonstration purposes.
    In a real system, this would use a properly trained neural network.
    """

    def __init__(self, input_size: int = 32, hidden_size: int = 16):
        """
        Initialize the neural network.

        Args:
            input_size: Number of input features
            hidden_size: Size of hidden layer
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = 1

        # Initialize weights
        if MLX_AVAILABLE:
            # Use MLX for weight initialization
            rng = mx.random.normal
            self.w1 = rng((input_size, hidden_size))
            self.b1 = mx.zeros((hidden_size,))
            self.w2 = rng((hidden_size, self.output_size))
            self.b2 = mx.zeros((self.output_size,))
        else:
            # Use NumPy as fallback
            self.w1 = np.random.normal(0, 0.1, (input_size, hidden_size))
            self.b1 = np.zeros((hidden_size,))
            self.w2 = np.random.normal(0, 0.1, (hidden_size, self.output_size))
            self.b2 = np.zeros((self.output_size,))

        self.initialized = True
        logger.info("Initialized simple neural network for spam detection")

    def _sigmoid(self, x):
        """Sigmoid activation function."""
        if MLX_AVAILABLE:
            # Use MLX implementation
            return 1.0 / (1.0 + mx.exp(-x))
        else:
            # Use NumPy implementation
            return 1.0 / (1.0 + np.exp(-x))

    def _relu(self, x):
        """ReLU activation function."""
        if MLX_AVAILABLE:
            # Use MLX implementation
            return mx.maximum(0, x)
        else:
            # Use NumPy implementation
            return np.maximum(0, x)

    def forward(self, x):
        """
        Forward pass through the network.

        Args:
            x: Input features

        Returns:
            Network output (spam score)
        """
        if MLX_AVAILABLE:
            # Convert to MLX array if not already
            if not isinstance(x, type(mx.array([0]))):
                x = mx.array(x)

            # Forward pass
            hidden = self._relu(mx.matmul(x, self.w1) + self.b1)
            output = self._sigmoid(mx.matmul(hidden, self.w2) + self.b2)

            # Convert to scalar
            return float(output[0])
        else:
            # NumPy implementation
            if not isinstance(x, np.ndarray):
                x = np.array(x)

            # Forward pass
            hidden = self._relu(np.dot(x, self.w1) + self.b1)
            output = self._sigmoid(np.dot(hidden, self.w2) + self.b2)

            # Convert to scalar
            return float(output[0])


class SpamFilter:
    """Neural network based spam filter for notifications."""

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the spam filter.

        Args:
            model_path: Optional path to pre-trained model weights
        """
        self.feature_extractor = SpamFeatureExtractor()
        self.model = SimpleNeuralNetwork()
        self.model_loaded = True

        # Load model weights if provided
        if model_path:
            self._load_weights(model_path)

        logger.info("Spam filter initialized")

    def _load_weights(self, model_path: str) -> bool:
        """
        Load model weights from file.

        Args:
            model_path: Path to model weights file

        Returns:
            True if successful, False otherwise
        """
        try:
            # In a real implementation, this would load actual weights
            # This is just a simulation
            logger.info(f"Loading spam filter weights from {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load spam filter weights: {e}")
            return False

    def is_spam(self, content: NotificationContent) -> Tuple[bool, float]:
        """
        Check if notification content is spam.

        Args:
            content: The notification content to check

        Returns:
            Tuple of (is_spam, confidence_score)
        """
        # Extract features
        features = self.feature_extractor.extract_features(content)

        # Run through model
        spam_score = self.model.forward(features)

        # Rule-based additions (for demonstration)
        # These would normally be learned by the model
        title_lower = content.title.lower()
        body_lower = content.body.lower()

        # Check for common spam phrases
        spam_phrases = [
            "double your money",
            "get rich quick",
            "work from home",
            "earn extra cash",
            "limited time offer",
            "act now",
            "exclusive deal",
            "congratulations you won",
        ]

        for phrase in spam_phrases:
            if phrase in title_lower or phrase in body_lower:
                spam_score += 0.2

        # Cap score at 1.0
        spam_score = min(spam_score, 1.0)

        # Determine spam status (threshold can be adjusted)
        is_spam = spam_score > 0.7

        if is_spam:
            logger.warning(f"Spam detected: {content.title} (score: {spam_score:.4f})")
        else:
            logger.debug(f"Legitimate notification: {content.title} (score: {spam_score:.4f})")

        return is_spam, spam_score
