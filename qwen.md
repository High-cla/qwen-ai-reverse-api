# Qwen AI Reverse API — Project Documentation

> **Fork**: [High-cla/qwen-ai-reverse-api](https://github.com/High-cla/qwen-ai-reverse-api) (`feat/opencode-responses-api`)
> **Upstream**: [Wu-jiyan/qwen-ai-reverse-api](https://github.com/Wu-jiyan/qwen-ai-reverse-api)
> **Python**: 3.8+ | **License**: MIT

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [File Structure](#file-structure)
4. [Fork Unique Features](#fork-unique-features)
5. [API Endpoints](#api-endpoints)
6. [Deployment Guide](#deployment-guide)
7. [OpenCode Integration](#opencode-integration)
8. [Configuration Reference](#configuration-reference)

---

## Project Overview

A reverse-engineered API wrapper for Qwen AI (`chat.qwen.ai`) that exposes an **OpenAI-compatible interface**. This fork extends the upstream with **OpenAI Responses API support**, **model validation endpoints**, and **automatic model prefix stripping** — specifically designed for compatibility with OpenCode and modern OpenAI SDKs.

### Key Features

| Feature | Description |
|---------|-------------|
| 🔌 **OpenAI Compatible** | Drop-in replacement — works with OpenAI SDK, curl, any HTTP client |
| 🚀 **Streaming (SSE)** | Real-time streaming with `reasoning_content` for thinking process |
| 💬 **Context Support** | Multi-turn conversation with in-memory session persistence |
| 🎨 **Image Generation** | Qwen image gen tool calls → OpenAI `tool_calls` format |
| 🔄 **Token Rotation** | Multi-JWT random load balancing (comma-separated tokens) |
| ✅ **Token Health Check** | `POST/GET /v1/tokens/health` for token validity verification |
| 🌐 **Vless Proxy Pool** | Subscription-based proxy management with health testing |
| **🆕 Responses API** | `POST /v1/responses` — OpenAI's latest API format |
| **🆕 Model Validation** | `GET /v1/models/{model_id}` — per-model SDK verification |
| **🆕 Prefix Stripping** | Auto-removes `openai/` provider prefix from model names |

---

## Architecture

```
┌─────────────────────────────────────────┐
│          Client (OpenAI SDK / curl)      │
│  POST /v1/chat/completions              │
│  POST /v1/responses            ← NEW    │
│  GET  /v1/models/{model_id}    ← NEW    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│        FastAPI Server (server.py)        │
│  • Request validation & routing          │
│  • Model prefix stripping (openai/ → "") │
│  • Random token selection                │
│  • ChatSessionManager (24h TTL)          │
└──────┬──────────────────────┬────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐    ┌──────────────────┐
│ QwenAiClient │    │  Proxy Pool      │
│ (client.py)  │    │ (vless_proxy.py) │
└──────┬───────┘    └────────┬─────────┘
       │                     │
       ▼                     ▼
┌──────────────┐    ┌──────────────────┐
│QwenAiAdapter │    │ Subscription     │
│ (adapter.py) │    │ Manager + Storage│
└──────┬───────┘    └──────────────────┘
       │
       ▼
┌──────────────────┐
│ chat.qwen.ai API │
│ (HTTP + SSE)     │
└──────────────────┘
```

---

## File Structure

```
qwen-ai-reverse-api/
├── qwen.md                    # This documentation
├── README.md                  # User-facing README
├── server.py                  # FastAPI app (all endpoints)
├── start_server.py            # CLI entry point (uvicorn)
├── start-all.cmd              # Windows venv launcher (Python 3.14)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
│
├── qwen_ai/                   # Core SDK module
│   ├── __init__.py
│   ├── client.py              # QwenAiClient — high-level chat interface
│   ├── adapter.py             # QwenAiAdapter — HTTP layer for chat.qwen.ai
│   ├── stream_handler.py      # SSE → OpenAI chunk conversion
│   ├── tool_parser.py         # XML tool call parsing
│   ├── vless_proxy.py         # Vless proxy pool & subscription manager
│   ├── subscription.py        # Subscription URL parsing
│   ├── node_storage.py        # Persistent node storage (JSON)
│   └── node_tester.py         # Concurrent node health testing
│
├── register_account.py        # Auto-registration tool
├── get_jwt.py                 # JWT acquisition tool
├── PROXY_SETUP.md             # Proxy configuration guide
└── docs/                      # Screenshots
```

---

## Fork Unique Features

Our fork (`feat/opencode-responses-api`) adds the following capabilities **not present** in the upstream or jamesc0der's fork:

### 1. OpenAI Responses API (`POST /v1/responses`)

Compatible with the latest OpenAI SDKs that use the `responses` API format instead of `chat.completions`.

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-jwt-token"
)

# Uses POST /v1/responses internally
response = client.responses.create(
    model="qwen3.6-plus",
    input="Hello, how are you?"
)

print(response.output[0].content[0].text)
```

**Input handling** — accepts multiple formats:
- Plain string → `{"role": "user", "content": "..."}`
- Simple message list → `[{"role": "user", "content": "..."}]`
- Responses API format → `[{"role": "user", "content": [{"type": "input_text", "text": "..."}]}]`

**Response format** — mirrors OpenAI's official structure:
```json
{
  "id": "resp_1712345678",
  "object": "response",
  "created_at": 1712345678,
  "model": "qwen3.6-plus",
  "status": "completed",
  "output": [{
    "type": "message",
    "role": "assistant",
    "content": [{"type": "output_text", "text": "..."}]
  }],
  "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}
}
```

### 2. Model Validation Endpoint (`GET /v1/models/{model_id}`)

Enables OpenAI SDKs that verify a specific model exists before making requests. Accepts model IDs with or without a provider prefix.

```http
GET /v1/models/qwen3.6-plus
GET /v1/models/openai/qwen3.6-plus
GET /v1/models/qwen3.6-plus-preview-think
```

Returns standard `ModelInfo` format:
```json
{"id": "openai/qwen3.6-plus", "object": "model", "created": 1712345678, "owned_by": "qwen-ai"}
```

Returns `404` for unsupported model IDs.

### 3. Model Prefix Auto-Stripping

In both `/v1/chat/completions` and `/v1/responses`, provider prefixes like `openai/` are automatically removed:

| Request model | Normalized to |
|---------------|---------------|
| `openai/qwen3.6-plus` | `qwen3.6-plus` |
| `qwen3.5-flash` | `qwen3.5-flash` |
| `openai/qwen3.5-max-2026-03-08` | `qwen3.5-max-2026-03-08` |

This is handled by a simple `split("/", 1)[1]` operation — only the first `/`-separated prefix is stripped.

### 4. Unsupported Model Rejection

Models not in `SUPPORTED_MODELS` return **HTTP 400** with a descriptive error, rather than silently failing or returning blank responses as in the upstream.

### 5. Windows venv Launcher

`start-all.cmd` launches the server using a Python 3.14 venv, suitable for Windows deployments:

```batch
@echo off
cd /d "%~dp0"
.\venv\Scripts\python.exe start_server.py
```

---

## API Endpoints

### Chat Completions

```http
POST /v1/chat/completions
Authorization: Bearer <JWT>
Content-Type: application/json
```

```json
{
  "model": "qwen3.6-plus",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 2048,
  "top_p": 0.9
}
```

Supports streaming (`text/event-stream`) and non-streaming. The `reasoning_content` field in the response delta exposes Qwen's thinking process.

### Responses API

```http
POST /v1/responses
Authorization: Bearer <JWT>
Content-Type: application/json
```

```json
{
  "model": "qwen3.6-plus",
  "input": "Hello, how are you?",
  "stream": false
}
```

### Models

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models` | GET | List all supported models |
| `/v1/models/{model_id}` | GET | Get specific model (SDK validation) |

### Utilities

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/tokens/health` | POST | Check JWT token(s) validity |
| `/v1/tokens/health` | GET | Same, via query param `?tokens=...` |
| `/health` | GET | Server health check |
| `/` | GET | Service info + endpoint list |

### Proxy Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/proxy/stats` | GET | Pool statistics |
| `/v1/proxy/nodes` | GET | List nodes (with pattern filter) |
| `/v1/proxy/refresh` | POST | Refresh subscriptions + test |
| `/v1/proxy/test` | POST | Test specific nodes |

### Supported Models

| Model | Variants |
|-------|----------|
| qwen3.7-max | `-fast`, `-think` |
| qwen3.6-plus | `-fast`, `-think`, `-preview` |
| qwen3.5-plus | `-fast`, `-think`, `-omni-plus` |
| qwen3.5-flash | `-fast`, `-think`, `-omni-flash` |
| qwen3.5-max-preview | `-fast`, `-think` |
| qwen3.5-max-2026-03-08 | — |
| qwen3-max | `-fast`, `-think` |
| qwen3-coder | `-fast`, `-think` |
| qwen2.5-max | — |
| qwen3.6-max-preview | `-fast`, `-think` |
| qwen3.6-27b | `-fast`, `-think` |
| qwen3.5-397b-a17b | — |
| qwen3.5-122b-a10b | — |
| qwen3.5-27b | — |
| qwen3.5-35b-a3b | — |
| qwen3-235b-a22b-2507 | — |
| qwen3-vl-235b-a22b | — |
| qwen3-omni-flash | — |

---

## Deployment Guide

### Prerequisites

- Python 3.8+ (3.14 recommended for Windows venv)
- JWT token from [chat.qwen.ai](https://chat.qwen.ai) (see README.md for detailed acquisition steps)

### Quick Start (Windows)

```batch
:: 1. Clone
git clone https://github.com/High-cla/qwen-ai-reverse-api.git
cd qwen-ai-reverse-api

:: 2. Create venv (Python 3.14)
py -3.14 -m venv venv

:: 3. Activate & install
venv\Scripts\activate
pip install -r requirements.txt

:: 4. Configure
copy .env.example .env
:: Edit .env — set QWEN_TOKENS="your-jwt-token"

:: 5. Start
start-all.cmd
:: or: python start_server.py --port 8000
```

### Quick Start (Linux/macOS)

```bash
# 1. Clone & setup
git clone https://github.com/High-cla/qwen-ai-reverse-api.git
cd qwen-ai-reverse-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env — set QWEN_TOKENS="your-jwt-token"

# 3. Start
python start_server.py --port 8000
```

### Server Options

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | Listen port |
| `--reload` | off | Auto-reload on code change |
| `--no-proxy` | off | Disable proxy pool |

### Verify

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6-plus","messages":[{"role":"user","content":"Hello"}]}'

curl http://localhost:8000/v1/models/qwen3.6-plus
```

---

## OpenCode Integration

This fork was designed to be used as an OpenAI-compatible provider in **OpenCode** and similar AI CLI tools.

### Method 1: Direct Configuration

Configure OpenCode to use your local Qwen API as an OpenAI-compatible provider:

```json
// opencode.json or provider config
{
  "name": "qwen-local",
  "apiKey": "your-jwt-token",
  "baseUrl": "http://localhost:8000/v1",
  "models": {
    "default": ["qwen3.6-plus"],
    "fetch": true   // auto-discovers models via GET /v1/models
  }
}
```

The `GET /v1/models` endpoint returns the full list of supported models, enabling auto-discovery.

### Method 2: OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-jwt-token"
)

# Chat Completions API
response = client.chat.completions.create(
    model="qwen3.6-plus",
    messages=[{"role": "user", "content": "Hello"}]
)

# Responses API (newer SDKs)
response = client.responses.create(
    model="qwen3.6-plus",
    input="Hello"
)
```

### Method 3: Provider Prefix Compatibility

When tools send `openai/qwen3.6-plus` as the model name, the prefix is automatically stripped. No client-side modification needed.

---

## Configuration Reference

### `.env` File

```bash
# Required
QWEN_TOKENS="jwt1,jwt2,jwt3"     # Comma-separated JWT tokens

# Optional: Auto-delete chat records
AUTO_DELETE_CHAT=false

# Optional: Proxy
ENABLE_PROXY=false
VLESS_SUBSCRIPTION_URLS=""
VLESS_SUBSCRIPTION_PATTERNS="CF优选-电信"
VLESS_AUTO_REFRESH_ON_START=true

# Optional: Network
HOST="0.0.0.0"
PORT="8000"
HTTP_PROXY=""
HTTPS_PROXY=""
```

### Token Rotation

Multiple JWT tokens can be provided as a comma-separated string. The server selects one randomly per request for load balancing.

```bash
QWEN_TOKENS="eyJhbGciOiJIUzI1NiIs...,eyJhbGciOiJSUzI1NiIs..."
```

### Chat Sessions

Sessions persist in memory for 24 hours. Use `chat_id` from a previous response to continue a conversation. Set `AUTO_DELETE_CHAT=true` to automatically clean up sessions.

---

## License

MIT License — see [LICENSE](LICENSE).

> **Disclaimer**: This project is a reverse engineering of Qwen AI's web API for educational purposes. Comply with Qwen AI's Terms of Service.
