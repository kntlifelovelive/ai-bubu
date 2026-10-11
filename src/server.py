"""HTTP server for ai-bubu.

A small local server that exposes a chat API.
It binds to a loopback address only (127.0.0.1 by default). Starting
on a public host (0.0.0.0, *, any address) fails at startup.
All input is validated by the security layer before use.
"""

import json
import logging
import socket
import socketserver
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional

import src.config as config_module
from src.config import Config, ConfigError, load_config
from src.memory import get_memory_info, memory_safe
from src.model import get_model_manager, ModelManager
from src.security import AccessDenied, SecurityConfig, SecurityValidator

logger = logging.getLogger("ai-bubu")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [ai-bubu] %(message)s"))
    logger.addHandler(handler)


class ConfigHandler(BaseHTTPRequestHandler):
    """HTTP request handler with validation and routing."""

    config: Config = None
    validator: SecurityValidator = None
    manager: ModelManager = None

    @classmethod
    def set_globals(cls, config: Config, validator: SecurityValidator, manager: ModelManager) -> None:
        cls.config = config
        cls.validator = validator
        cls.manager = manager

    def log_message(self, format: str, *args: object) -> None:
        """Log to stderr instead of keeping a file."""
        logger.info(format, *args)

    def _send_json(self, status: int, data: Any) -> None:
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self, max_size: int) -> bytes:
        """Read the request body, enforcing a size limit."""
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
        """Handle POST requests.

        The size of the body is validated from the Content-Length
        header here (to reject oversized requests early). Handlers
        then read the body once via _read_body, which applies the
        same limit — the header is never consumed here so the body
        is available to the handler.
        """
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

            payload = json.loads(self._read_body(self.config.security_max_request_size_bytes).decode("utf-8"))
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
            # Log the technical detail server-side; do not leak it to
            # the client, which could reveal internal state.
            logger.exception("Internal error while handling chat request")
            self._send_json(500, {"error": "An internal error occurred"})

    def _handle_load(self) -> None:
        try:
            self._validate_auth()
            payload = json.loads(
                self._read_body(self.config.security_max_request_size_bytes).decode("utf-8")
            )
            path = payload.get("model", self.config.model_path)
            if not path:
                self._send_json(400, {"error": "No model path provided"})
                return
            state = self.manager.load(path, self.config)
            if state.error:
                self._send_json(422, {"error": state.error})
            else:
                self._send_json(200, {"status": "loaded"})
        except AccessDenied as error:
            self._send_json(403, {"error": str(error)})
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
        except Exception as error:
            logger.exception("Internal error while loading model")
            self._send_json(500, {"error": "An internal error occurred"})

    def _handle_unload(self) -> None:
        try:
            self._validate_auth()
            self.manager.unload()
            self._send_json(200, {"status": "unloaded"})
        except AccessDenied as error:
            self._send_json(403, {"error": str(error)})
        except Exception as error:
            logger.exception("Internal error while unloading model")
            self._send_json(500, {"error": "An internal error occurred"})

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
    """Create an HTTP server bound to the configured host/port.

    Raises:
        RuntimeError: if the configured host would bind to a public
            network interface. ai-bubu only binds to IPv4 loopback
            (127.0.0.1 by default) and rejects any unsafe host before
            opening a socket.
    """
    socketserver.TCPServer.allow_reuse_address = True

    # Validate the bind target BEFORE opening any socket. This makes
    # localhost-only the enforced default, not a documentation note.
    validator = SecurityValidator(
        SecurityConfig(
            max_request_size_bytes=config.security_max_request_size_bytes,
            max_prompt_tokens=config.security_max_prompt_tokens,
            max_response_tokens=config.model_max_tokens,
        )
    )
    try:
        validated_host = validator.check_host(config.server_host)
    except AccessDenied as error:
        raise RuntimeError(
            f"Refusing to bind to a public interface ({config.server_host}): {error}"
        ) from error

    server = HTTPServer((validated_host, config.server_port), ConfigHandler)
    ConfigHandler.set_globals(config, validator, get_model_manager())
    return server


def run_server(config: Config | None = None, background: bool = False) -> None:
    """Start the server. Blocks while running."""
    config = config or load_config()
    try:
        server = make_server(config)
    except RuntimeError as error:
        logger.exception("Server startup failed: %s", error)
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
    except ConfigError as error:
        logger.exception("Configuration error: %s", error)
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
    address = f"{server.server_address[0]}:{server.server_address[1]}"
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
