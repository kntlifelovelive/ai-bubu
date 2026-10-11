"""HTTP server for ai-bubu.

A small local server that exposes a chat API.
It binds to localhost by default and never to the public
network. All input is validated by the security layer first.
"""

import json
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional

from src.config import Config, load_config
from src.memory import get_memory_info, memory_safe
from src.model import get_model_manager, ModelManager
from src.security import AccessDenied, SecurityConfig, SecurityValidator


class ConfigHandler(BaseHTTPRequestHandler):
    """HTTP request handler with validation and routing."""

    config: Config = None
    validator: SecurityValidator = None
    manager: ModelManager = None

    @classmethod
    def set_globals(cls, config: Config, manager: ModelManager) -> None:
        cls.config = config
        cls.validator = SecurityValidator(
            SecurityConfig(
                max_request_size_bytes=config.security_max_request_size_bytes,
                max_prompt_tokens=config.security_max_prompt_tokens,
                max_response_tokens=config.model_max_tokens,
            )
        )
        cls.manager = manager

    def log_message(self, format: str, *args: object) -> None:
        """Log to stderr instead of keeping a file."""
        print(f"[server] {args[0]}")

    def _send_json(self, status: int, data: Any) -> None:
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self, max_size: int) -> bytes:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > max_size:
            raise AccessDenied(f"Request too large: {length} bytes")
        if length > 0:
            return self.rfile.read(length)
        return b""

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/health":
            self._handle_health()
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        """Handle POST requests."""
        try:
            max_size = self.config.security_max_request_size_bytes
            length = int(self.headers.get("Content-Length", 0) or 0)
            if length > max_size:
                raise AccessDenied(
                    f"Request too large: {length} bytes"
                )
        except AccessDenied as error:
            self._send_json(413, {"error": str(error)})
            return

        if self.path == "/v1/chat/completions":
            self._handle_chat()
        elif self.path == "/model/load":
            self._handle_load()
        elif self.path == "/model/unload":
            self._handle_unload()
        else:
            self._send_json(404, {"error": "Not found"})

    def _handle_health(self) -> None:
        memory = get_memory_info()
        safe = memory_safe(self.config.memory_max_usage_percent)
        self._send_json(
            200,
            {
                "status": "ok" if safe else "degraded",
                "model_loaded": self.manager.is_loaded(),
                "memory_available_gb": round(memory.available_gb, 1),
            },
        )

    def _handle_chat(self) -> None:
        try:
            self._validate_auth()
            if not self.manager.is_loaded():
                self._send_json(503, {"error": self.manager.error_message()})
                return

            payload = json.loads(self._read_body(1024 * 1024).decode("utf-8"))
            prompt = payload.get("prompt", payload.get("messages", [{}]))
            if isinstance(prompt, list):
                messages = prompt
                prompt_text = ""
                for msg in messages:
                    role = msg.get("role", "user")
                    text = msg.get("content", "")
                    if role == "user":
                        prompt_text = text
                prompt = prompt_text
            prompt = self.validator.check_prompt(prompt)
            max_tokens = self.validator.check_generation_length(
                payload.get("max_tokens", None)
            )

            completion = ""
            for chunk in self.manager.complete(prompt, max_tokens):
                completion += chunk

            self._send_json(
                200,
                {
                    "choices": [
                        {"message": {"role": "assistant", "content": completion}}
                    ],
                    "usage": {
                        "prompt_tokens": len(prompt),
                        "completion_tokens": len(completion),
                    },
                },
            )
        except AccessDenied as error:
            self._send_json(403, {"error": str(error)})
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
        except Exception as error:
            self._send_json(500, {"error": f"Internal error: {error}"})

    def _handle_load(self) -> None:
        payload = json.loads(self._read_body(1024 * 1024).decode("utf-8"))
        path = payload.get("model", self.config.model_path)
        if not path:
            self._send_json(400, {"error": "No model path provided"})
            return
        state = self.manager.load(path)
        if state.error:
            self._send_json(422, {"error": state.error})
        else:
            self._send_json(200, {"status": "loaded", "path": state.path})

    def _handle_unload(self) -> None:
        self.manager.unload()
        self._send_json(200, {"status": "unloaded"})

    def _validate_auth(self) -> None:
        # Development only: localhost clients.
        client_ip = (
            self.client_address[0]
            if isinstance(self.client_address, tuple)
            else ""
        )
        if not self.validator.is_allowed_host(client_ip):
            raise AccessDenied(f"Connection not allowed from {client_ip}")


def make_server(config: Config) -> HTTPServer:
    """Create an HTTP server bound to the configured host/port."""
    socketserver.TCPServer.allow_reuse_address = True
    server = HTTPServer((config.server_host, config.server_port), ConfigHandler)
    ConfigHandler.set_globals(config, get_model_manager())
    return server


def run_server(config: Config | None = None, background: bool = False) -> None:
    """Start the server. Blocks while running."""
    config = config or load_config()
    server = make_server(config)
    address = f"{config.server_host}:{config.server_port}"
    print(f"ai-bubu starting on {address}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


def main() -> None:
    """Entry point when run as `python -m src.server`."""
    run_server()


if __name__ == "__main__":
    main()
