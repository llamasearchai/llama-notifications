# llama-notifications

[![PyPI version](https://img.shields.io/pypi/v/llama_notifications.svg)](https://pypi.org/project/llama_notifications/)
[![License](https://img.shields.io/github/license/llamasearchai/llama-notifications)](https://github.com/llamasearchai/llama-notifications/blob/main/LICENSE)
[![Python Version](https://img.shields.io/pypi/pyversions/llama_notifications.svg)](https://pypi.org/project/llama_notifications/)
[![CI Status](https://github.com/llamasearchai/llama-notifications/actions/workflows/llamasearchai_ci.yml/badge.svg)](https://github.com/llamasearchai/llama-notifications/actions/workflows/llamasearchai_ci.yml)

**Llama Notifications (llama-notifications)** provides a system for managing and delivering notifications within the LlamaSearch AI ecosystem. It aims to support features like prioritizing messages, filtering spam, considering context, securing delivery, and packaging notifications.

## Key Features

- **Notification Delivery:** Core logic for sending notifications (currently placeholder in `core.py`).
- **Priority Management:** Intended module for handling priorities (`priority.py`).
- **Spam Filtering:** Intended module for spam detection (`spam_filter.py`).
- **Context Awareness:** Intended module for context handling (`context.py`).
- **Packaging:** Intended module for formatting notifications (`package.py`).
- **Security:** Intended module for secure delivery (`security.py`).
- **Core Module:** Orchestrates notification generation and delivery (`core.py`, defines `Notifier`).
- **Message Structure:** Defines the notification data (`message.py`, defines `Message`).
- **Configuration:** Intended module for configuration (`config.py`).

## Installation

```bash
pip install llama-notifications
# Or install directly from GitHub for the latest version:
# pip install git+https://github.com/llamasearchai-dev/llama-notifications.git # Updated URL
```

## Usage Example (Basic)

This example shows the basic structure. Note that the actual sending logic is currently a placeholder.

```python
import logging
from llama_notifications import Notifier, Message

# Basic logging setup
logging.basicConfig(level=logging.INFO)

# Initialize the notifier (config is currently a placeholder)
notifier = Notifier(config={})

# Create a message object
notification_message = Message(
    recipient="user@example.com",
    subject="Your Weekly Summary",
    body="Hello! Here is your summary report.",
    channel="email", # Specify the channel (e.g., 'email', 'sms')
    priority="medium" # Optional, defaults to medium
)

# Attempt to send the notification
try:
    result = notifier.send(notification_message)
    if result.get("success"):
        print(f"Notification request processed for {notification_message.recipient}.")
    else:
        print(f"Failed to process notification request: {result.get('error', 'Unknown error')}")
except Exception as e:
    print(f"An error occurred: {e}")

```

## Architecture Overview

```mermaid
graph TD
    A[Application / Service] -- Triggers Notification --> B{Core Notification Manager (core.py)};
    B -- Uses --> C{Context Module (context.py)};
    B -- Uses --> D{Priority Module (priority.py)};
    B -- Uses --> E{Spam Filter (spam_filter.py)};
    B -- Uses --> F{Packaging Module (package.py)};
    B -- Uses --> G{Security Module (security.py)};

    C --> B;
    D --> B;
    E --> B;
    F --> B;
    G --> B;

    B -- Selects Channel & Sends --> H{Delivery Channel Interface};
    H --> I[Email Gateway];
    H --> J[SMS Gateway];
    H --> K[Push Notification Service];
    H --> L[...];

    M[Configuration (config.py)] -- Configures --> B;
    M -- Configures --> C; M -- Configures --> D; M -- Configures --> E;
    M -- Configures --> F; M -- Configures --> G; M -- Configures --> H;

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style I fill:#ccf,stroke:#333,stroke-width:1px
    style J fill:#ccf,stroke:#333,stroke-width:1px
    style K fill:#ccf,stroke:#333,stroke-width:1px
```

1.  **Trigger:** An application or service signals the need to send a notification.
2.  **Core Notifier:** (`Notifier` in `core.py`) Receives the request (`Message` object).
3.  **Processing Modules (Intended):** It *should* leverage context, priority, spam filtering, packaging, and security modules to prepare the notification. (Currently, these modules exist but are not integrated into `Notifier.send`).
4.  **Channel Selection (Intended):** Based on configuration and message details, it *should* select the appropriate delivery channel(s).
5.  **Delivery (Intended):** The notification *should* be sent via the chosen channel interface (e.g., Email, SMS, Push).
6.  **Configuration (Intended):** (`config.py`) *Should* define available channels, priorities, spam rules, etc.

## Configuration

*(Configuration details are TBD as the system is refined.)*

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/llamasearchai-dev/llama-notifications.git # Updated URL
cd llama-notifications

# Install in editable mode with development dependencies
# Assumes pyproject.toml is correctly configured
pip install -e ".[dev]"
```

### Testing

```bash
# Using hatch environments defined in pyproject.toml
hatch run test
# Or with coverage:
hatch run test-cov
# Alternatively, run pytest directly if hatch is not used:
# pytest tests/
```

### Linting & Formatting

```bash
# Using hatch
hatch run lint
hatch run format
# Alternatively, run tools directly:
# ruff check .
# ruff format .
# black .
# isort .
# mypy src/
```

### Contributing

Contributions are welcome! Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) and submit a Pull Request against the `main` branch.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Developed by the LlamaSearch AI Dev Team (llamasearchai-dev).*
