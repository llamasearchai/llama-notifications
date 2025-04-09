"""
Provides simple rule-based spam score calculation for notifications.
"""

import logging
import re
from typing import Dict, Any

from .message import Message # Use the standard Message class

# Configure logging
logger = logging.getLogger(__name__)

# Basic list of words often found in spam
SPAM_KEYWORDS = {
    "free", "discount", "limited time", "offer", "click here", "click now",
    "exclusive", "win", "winner", "prize", "claim", "urgent", "act now",
    "guaranteed", "congratulations", "selected", "cash", "money", "credit",
    "buy", "purchase", "order", "sale", "deal", "subscribe", "trial",
    "viagra", "pharmacy", "loan", "refinance", "mortgage", "unsubscribe",
    "$$$", "!!!", "earn extra cash", "work from home"
}

# Simple regex for detecting multiple links
URL_PATTERN = re.compile(r"http[s]?://")

class SpamFilter:
    """
    Calculates a simple spam score for a notification message based on rules.
    Checks for spam keywords, excessive capitalization, and multiple URLs.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the SpamFilter.

        Args:
            config (Dict[str, Any]): Configuration options. 
                                       Example: {'threshold': 0.7, 'keyword_weight': 0.5, ...}
                                       (Currently unused placeholder).
        """
        self.config = config if config is not None else {}
        # Example: Load threshold from config if needed later
        # self.threshold = self.config.get('threshold', 0.7)
        logger.info("SpamFilter initialized.")

    def calculate_spam_score(self, message: Message) -> float:
        """
        Calculates a spam score between 0.0 (likely not spam) and 1.0 (likely spam).

        Applies simple rules:
        - Adds points for spam keywords found in subject/body.
        - Adds points for excessive capitalization.
        - Adds points for multiple URLs.
        - Score is capped at 1.0.

        Args:
            message (Message): The notification message object.

        Returns:
            float: A score indicating the likelihood of the message being spam.
        """
        score = 0.0
        text_content = f"{message.subject.lower()} {message.body.lower()}"
        subject_len = max(len(message.subject), 1)
        body_len = max(len(message.body), 1)

        # Rule 1: Spam Keywords (Weight: ~0.5)
        keyword_count = sum(1 for keyword in SPAM_KEYWORDS if keyword in text_content)
        score += min(keyword_count / 5.0, 1.0) * 0.5 # Increase score by up to 0.5 based on keywords
        if keyword_count > 0:
             logger.debug(f"Spam score += {min(keyword_count / 5.0, 1.0) * 0.5:.2f} due to keywords ({keyword_count} found).")

        # Rule 2: Excessive Capitalization (Weight: ~0.3)
        caps_count = sum(1 for char in message.subject + message.body if 'A' <= char <= 'Z')
        total_len = subject_len + body_len
        caps_ratio = caps_count / total_len if total_len > 0 else 0
        if caps_ratio > 0.3: # If more than 30% caps
            caps_penalty = min((caps_ratio - 0.3) * 2, 1.0) * 0.3 # Add up to 0.3 to score
            score += caps_penalty
            logger.debug(f"Spam score += {caps_penalty:.2f} due to high caps ratio ({caps_ratio:.2f}).")

        # Rule 3: Multiple URLs (Weight: ~0.2)
        url_count = len(URL_PATTERN.findall(message.subject)) + len(URL_PATTERN.findall(message.body))
        if url_count > 1:
            url_penalty = min((url_count - 1) / 4.0, 1.0) * 0.2 # Add up to 0.2 for multiple URLs
            score += url_penalty
            logger.debug(f"Spam score += {url_penalty:.2f} due to multiple URLs ({url_count} found).")

        # --- Add more rules as needed --- 
        # Example: Check sender reputation (if available in metadata)
        # sender_rep = message.metadata.get('sender_reputation')
        # if sender_rep == 'poor': score += 0.2

        # Cap score at 1.0
        final_score = min(score, 1.0)

        logger.debug(f"Calculated spam score for msg to {message.recipient}: {final_score:.4f}")
        return final_score

    def is_spam(self, message: Message, threshold: float = 0.7) -> bool:
         """
         Convenience method to check if the message exceeds a spam threshold.

         Args:
             message (Message): The notification message object.
             threshold (float): The score threshold above which the message is considered spam.
                                Defaults to 0.7.

         Returns:
             bool: True if the calculated score exceeds the threshold, False otherwise.
         """
         score = self.calculate_spam_score(message)
         is_spam_flag = score > threshold
         logger.info(f"Spam check for msg to {message.recipient}: Score={score:.4f}, Threshold={threshold}, IsSpam={is_spam_flag}")
         return is_spam_flag
