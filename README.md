# llama-notifications

A privacy-preserving, secure multi-channel notification service with ML-accelerated prioritization and intelligent delivery.

## Installation

```bash
pip install -e .
```

## Usage

```python
from llama_notifications import LlamaNotificationsClient

# Initialize the client
client = LlamaNotificationsClient(api_key="your-api-key")
result = client.query("your query")
print(result)
```

## Features

- Fast and efficient
- Easy to use API
- Comprehensive documentation

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/nikjois/llama-notifications.git
cd llama-notifications

# Install development dependencies
pip install -e ".[dev]"
```

### Testing

```bash
pytest
```

## License

MIT

## Author

Nik Jois (nikjois@llamasearch.ai)
