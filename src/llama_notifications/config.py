"""
Configuration management for LlamaNotifications
"""
from typing import Dict, Any, Optional


class NotificationConfig:
    """Handles notification-specific configuration with defaults."""

    DEFAULT_CONFIG: Dict[str, Any] = {
        "default_channel": "email", # Example: Default channel if not specified
        "default_priority": "medium", # Example: Default priority
        "channels": { # Example structure for channel-specific settings
            "email": {
                "provider": "smtp", # e.g., smtp, sendgrid, mailgun
                "host": "localhost",
                "port": 25,
                "timeout": 30,
                "retries": 2,
            },
            "sms": {
                "provider": "twilio", # e.g., twilio, nexmo
                "timeout": 15,
                "retries": 3,
            }
            # Add other channels like push, webhook, slack...
        },
        "spam_filter": {
            "enabled": True,
            "threshold": 0.8,
        },
        "security": {
            "encryption_required": False,
        },
        "log_level": "INFO",
    }

    def __init__(self, config_overrides: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration overrides.

        Overrides are deeply merged with the default configuration.
        """
        # Start with a deep copy of defaults
        # Note: A proper deep merge might be needed for nested dicts like 'channels'
        # This is a simple update for now.
        self.config = {k: v for k, v in self.DEFAULT_CONFIG.items()} # Simple copy
        if config_overrides:
            # Simple top-level update (doesn't deep merge nested dicts)
            self.config.update(config_overrides)
            # TODO: Implement deep merge if necessary for nested structures like channels
            self._deep_merge_placeholder(self.config, config_overrides)

        # Placeholder for a potential deep merge function
    def _deep_merge_placeholder(self, base: Dict, updates: Dict):
         # This is where a recursive merge would go if needed.
         # For now, self.config.update() handles only top-level keys.
         pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'channels.email.host')."""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    # Handle cases where intermediate keys are not dicts
                    return default
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation.

        Note: This is a simplified version and won't create nested dictionaries.
        It only updates existing keys at any level.
        """
        keys = key.split('.')
        current_level = self.config
        try:
            for i, k in enumerate(keys):
                if i == len(keys) - 1:
                    if isinstance(current_level, dict):
                         current_level[k] = value
                    else:
                         # Cannot set value if path is not a dictionary
                         raise TypeError(f"Cannot set value at '{key}', intermediate path is not a dictionary.")
                elif isinstance(current_level, dict) and k in current_level:
                    current_level = current_level[k]
                else:
                    # Key not found or path is not a dictionary
                     raise KeyError(f"Cannot set value at '{key}', key '{k}' not found or path invalid.")
        except (KeyError, TypeError) as e:
            # Log or handle the error appropriately
            print(f"Error setting config key '{key}': {e}") # Replace with logging


    def to_dict(self) -> Dict[str, Any]:
        """Return a copy of the configuration dictionary."""
        return self.config.copy() # Return a copy to prevent external modification
