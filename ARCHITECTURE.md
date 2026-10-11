# Architecture - ai-bubu

## Overview

ai-bubu is a layered local AI server. Each layer has one clear job
and talks to the next layer through well-defined interfaces.
This makes the code easy to read, test, and change.

```
+--------------------------------------------------+
|              Client tools (curl, etc.)           |
+--------------------------------------------------+
                     | HTTP (localhost only)
                     v
+--------------------------------------------------+
|  src/server.py      HTTP server                  |
|   - listens on 127.0.0.1:5001                    |
|   - routes requests to model layer                 |
+--------------------------------------------------+
                     | Python calls
                     v
+--------------------------------------------------+
|  src/security.py    Security / permission layer  |
|   - validates all input (prompt, size, timeout)  |
|   - rejects dangerous patterns                   |
+--------------------------------------------------+
                     | Python calls
                     v
+--------------------------------------------------+
|  src/model.py       Model manager                |
|   - loads model from disk                        |
|   - runs inference on CPU                        |
|   - unloads when idle                            |
+--------------------------------------------------+
                     | Python calls
                     v
+--------------------------------------------------+
|  src/memory.py      Memory monitor               |
|   - reads /proc/meminfo                          |
|   - enforces RAM limits                          |
+--------------------------------------------------+
                     | reads
                     v
+--------------------------------------------------+
|  Model file (gguf on disk)                       |
+--------------------------------------------------+
```

## Layers

### 1. HTTP Server (`src/server.py`)

A small HTTP server using Python's built-in `http.server`.
It runs on `127.0.0.1` by default (never on `0.0.0.0`).

Endpoints:
- `GET /health` - health check for systemd
- `POST /v1/chat/completions` - chat completion API (Ollama-like)
- `POST /model/load` - load a model manually
- `POST /model/unload` - unload the model

### 2. Security Layer (`src/security.py`)

All input from clients passes through this layer before use:
- Prompt length limit (default 4096 tokens)
- Maximum request size (default 1 MB)
- Maximum generation length
- Blocks shell-like or code-executing patterns
- Rate limiting per client IP

### 3. Model Manager (`src/model.py`)

Loads and unloads the model:
- Supports GGUF format (works with llama.cpp backend)
- Runs inference on CPU with memory limits
- Auto-unloads after idle timeout
- Keeps only one model in memory

### 4. Memory Monitor (`src/memory.py`)

Reads `/proc/meminfo` to track RAM usage:
- Total RAM, free RAM, available RAM
- Enforces a safety limit (default 6 GB used max)
- Triggers model unload when low on memory

### 5. Configuration (`config/config.yaml`)

All settings come from one config file:
```yaml
server:
  host: "127.0.0.1"
  port: 5001
model:
  path: "/home/user/models/tiny-model.gguf"
  max_tokens: 512
  idle_timeout_seconds: 300
security:
  max_prompt_tokens: 4096
  max_request_size_bytes: 1048576
memory:
  max_usage_percent: 75
```

## Design Rules

1. **No external dependencies at startup** - use only Python stdlib
   for the server and config layers.
2. **CPU first** - the core works without a GPU.
3. **One model at a time** - simpler memory management.
4. **No network access** - never connects out for model downloads.
5. **No sudo needed** - runs as a normal user.
6. **Fail closed** - if something is unsure, reject the request.
