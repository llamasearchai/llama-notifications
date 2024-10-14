#!/usr/bin/env python3
"""
Llama Notifications - Python package for LlamaSearch AI
"""

from setuptools import setup, find_packages

setup(
    name="llama_notifications",
    version="0.1.0",
    description="A privacy-preserving, secure multi-channel notification service with ML-accelerated prioritization and intelligent delivery.",
    long_description="""# llama-notifications

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
""",
    long_description_content_type="text/markdown",
    author="Nik Jois",
    author_email="nikjois@llamasearch.ai",
    url="https://github.com/llamasearchai/llama-notifications",
    project_urls={
        "Documentation": "https://github.com/llamasearchai/llama-notifications",
        "Bug Tracker": "https://github.com/llamasearchai/llama-notifications/issues",
        "Source Code": "https://github.com/llamasearchai/llama-notifications",
    },
    packages='src.llama_notifications',
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)
