# O1-API: 高效的模拟gpt-4-o1思维对话 API 🚀

[English](README_EN.md) | [中文](README.md)

[![](https://img.shields.io/github/license/leezhuuuuu/o1-api.svg)](LICENSE)
![](https://img.shields.io/github/stars/leezhuuuuu/o1-api.svg)
![](https://img.shields.io/github/forks/leezhuuuuu/o1-api.svg)

## 概述 🌟

 O1-API 是一个基于 Flask 的 Web 应用程序,提供高效的模拟gpt-4-o1思维对话 API 接口。该项目的特点是能够处理连续对话,支持流式输出,并能根据配置灵活调整输出格式。这使得 O1-API 成为 AI 开发者和研究人员的理想工具,特别适用于需要高度定制化对话体验的场景。

## 技术栈 🛠️

- **后端框架**: Flask (Python)
- **并发处理**: threading
- **外部请求**: requests
- **配置管理**: YAML
- **流式输出**: Server-Sent Events (SSE)

## 特性 🌈

- **连续对话支持**: 维护对话历史,实现上下文理解。
- **流式和非流式输出**: 支持两种输出模式,满足不同需求。
- **可配置的输出格式**: 通过 YAML 配置文件轻松管理输出样式。
- **Bearer Token 认证**: 确保 API 的安全访问。
- **错误重试机制**: 提高系统的稳定性和可靠性。
- **灵活的提示词系统**: 支持自定义系统提示词。

## 运行环境 🖥️

- Python 3.7+

## 快速开始 🚀

### 1. 克隆项目

```bash
git clone https://github.com/leezhuuuuu/o1-api.git
cd o1-api
```

### 2. 安装依赖

```bash
pip install flask requests pyyaml
```

### 3. 配置文件

编辑 `config.yaml` 文件,配置您的 API 参数。示例配置如下:

```yaml
api_bearer_token: "your_api_bearer_token_here"
model_provider_api_key: "your_model_provider_api_key_here"
default_api_url: "https://api.example.com/v1/chat/completions"
default_model: "example-model-name"
stream_status_feedback: true
use_regex_processing: true  # 控制输出格式
```

### 4. 启动项目

```bash
python app.py
```

服务将在 `http://0.0.0.0:18888` 上启动。

## 使用指南 📖

### 发送对话请求

向 `/v1/chat/completions` 端点发送 POST 请求,包含以下 JSON 数据:

```json
{
    "conversation_id": "unique_conversation_id",
    "messages": [
        {"role": "user", "content": "你的问题"}
    ],
    "stream": true或false
}
```

请确保在请求头中包含正确的 Bearer Token。

## API 端点 🌐

### `POST /v1/chat/completions`

处理对话请求。

#### 请求头

```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

#### 请求体

```json
{
    "conversation_id": "unique_conversation_id",
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ],
    "stream": false
}
```

#### 响应

对于非流式请求,返回 JSON 格式的响应。
对于流式请求,返回 SSE 格式的数据流。

## 错误处理 🚨

- **401 Unauthorized**: 无效的 Bearer Token。
- **500 Internal Server Error**: 服务器内部错误。

## 配置管理 ⚙️

通过 `config.yaml` 文件可以灵活配置:
- API 认证信息
- 模型参数
- 输出格式控制
- 流式状态反馈等

## 许可证 📄

本项目基于 Apache 2.0 许可证。详见 [LICENSE](https://github.com/leezhuuuuu/o1-api/blob/main/LICENSE) 文件。

## 贡献 🤝

欢迎贡献！请提交问题或拉取请求。

## 作者 ✍️

- leezhuuuuu

## 致谢 🙏

- Flask
- Requests
- PyYAML

## GitHub Star History

[![Star History Chart](https://api.star-history.com/svg?repos=leezhuuuuu/o1-api&type=Date)](https://star-history.com/#leezhuuuuu/o1-api&Date)
