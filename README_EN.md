# O1-API: Efficient AI Conversation API 🚀

[English](README_EN.md) | [中文](README.md)

[![](https://img.shields.io/github/license/leezhuuuuu/o1-api.svg)](LICENSE)
![](https://img.shields.io/github/stars/leezhuuuuu/o1-api.svg)
![](https://img.shields.io/github/forks/leezhuuuuu/o1-api.svg)

## Overview 🌟

O1-API is a Flask-based web application that provides an efficient AI conversation API interface. The project's key features include handling continuous dialogues, supporting streaming output, and flexibly adjusting output formats based on configuration. This makes O1-API an ideal tool for AI developers and researchers, especially suitable for scenarios requiring highly customized conversation experiences.

## Tech Stack 🛠️

- **Backend Framework**: Flask (Python)
- **Concurrency Handling**: threading
- **External Requests**: requests
- **Configuration Management**: YAML
- **Streaming Output**: Server-Sent Events (SSE)

## Features 🌈

- **Continuous Dialogue Support**: Maintains conversation history for context understanding.
- **Streaming and Non-Streaming Output**: Supports both output modes to meet different needs.
- **Configurable Output Format**: Easily manage output styles through YAML configuration file.
- **Bearer Token Authentication**: Ensures secure API access.
- **Error Retry Mechanism**: Improves system stability and reliability.
- **Flexible Prompt System**: Supports custom system prompts.

## Environment Requirements 🖥️

- Python 3.7+

## Quick Start 🚀

### 1. Clone the Project

```bash
git clone https://github.com/leezhuuuuu/o1-api.git
cd o1-api
```

### 2. Install Dependencies

```bash
pip install flask requests pyyaml
```

### 3. Configuration File

Edit the `config.yaml` file to configure your API parameters. Example configuration:

```yaml
api_bearer_token: "your_api_bearer_token_here"
model_provider_api_key: "your_model_provider_api_key_here"
default_api_url: "https://api.example.com/v1/chat/completions"
default_model: "example-model-name"
stream_status_feedback: true
use_regex_processing: true  # Controls output format
```

### 4. Start the Project

```bash
python app.py
```

The service will start on `http://0.0.0.0:18888`.

## Usage Guide 📖

### Sending Conversation Requests

Send a POST request to the `/v1/chat/completions` endpoint with the following JSON data:

```json
{
    "conversation_id": "unique_conversation_id",
    "messages": [
        {"role": "user", "content": "Your question"}
    ],
    "stream": true or false
}
```

Ensure to include the correct Bearer Token in the request header.

## API Endpoint 🌐

### `POST /v1/chat/completions`

Handles conversation requests.

#### Request Headers

```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

#### Request Body

```json
{
    "conversation_id": "unique_conversation_id",
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ],
    "stream": false
}
```

#### Response

For non-streaming requests, returns a JSON format response.
For streaming requests, returns an SSE format data stream.

## Error Handling 🚨

- **401 Unauthorized**: Invalid Bearer Token.
- **500 Internal Server Error**: Server internal error.

## Configuration Management ⚙️

Flexible configuration through `config.yaml` file:
- API authentication information
- Model parameters
- Output format control
- Streaming status feedback, etc.

## License 📄

This project is licensed under the Apache 2.0 License. See the [LICENSE](https://github.com/leezhuuuuu/o1-api/blob/main/LICENSE) file for details.

## Contributions 🤝

Contributions are welcome! Please submit issues or pull requests.

## Author ✍️

- leezhuuuuu

## Acknowledgements 🙏

- Flask
- Requests
- PyYAML

## GitHub Star History

[![Star History Chart](https://api.star-history.com/svg?repos=leezhuuuuu/o1-api&type=Date)](https://star-history.com/#leezhuuuuu/o1-api&Date)
