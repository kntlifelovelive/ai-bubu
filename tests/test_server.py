"""Tests for src/server.py (no pytest dependency)."""

import json
import os
import socket
import sys
import threading
import time
import unittest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, SRC_DIR)

from src.config import Config
from src.model import get_model_manager
from src.server import ConfigHandler, make_server


def _socket_open(host, port, timeout=0.2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect_ex((host, port))
        return True
    except Exception:
        return False
    finally:
        sock.close()


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = Config(server_host="127.0.0.1", server_port=0)
        cls.server = make_server(cls.config)
        cls.host, cls.port = cls.server.server_address
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()
        for _ in range(50):
            if _socket_open(cls.host, cls.port):
                break
            time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def _get(self, path):
        request = f"GET {path} HTTP/1.1\r\nHost: localhost\r\n\r\n"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((self.host, self.port))
        sock.sendall(request.encode("utf-8"))
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        sock.close()
        return response

    def _post(self, path, data):
        body = json.dumps(data).encode("utf-8")
        request = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: localhost\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n\r\n"
        ).encode("utf-8") + body
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((self.host, self.port))
        sock.sendall(request)
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        sock.close()
        return response

    def test_health_returns_json(self):
        response = self._get("/health")
        body = response.split(b"\r\n\r\n", 1)[-1]
        data = json.loads(body.decode("utf-8"))
        self.assertIn("status", data)

    def test_unknown_path_returns_404(self):
        response = self._get("/unknown")
        body = response.split(b"\r\n\r\n", 1)[-1]
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data.get("error"), "Not found")

    def test_chat_without_model_returns_503(self):
        response = self._post("/v1/chat/completions", {"prompt": "hi"})
        status_line = response.split(b"\r\n", 1)[0]
        status = int(status_line.split(b" ", 2)[1])
        self.assertEqual(status, 503)

    def test_load_missing_model_returns_422(self):
        response = self._post("/model/load", {"model": "/tmp/x.gguf"})
        status_line = response.split(b"\r\n", 1)[0]
        status = int(status_line.split(b" ", 2)[1])
        self.assertEqual(status, 422)

    def test_empty_body_chat_rejected(self):
        response = self._post("/v1/chat/completions", {})
        body = response.split(b"\r\n\r\n", 1)[-1]
        data = json.loads(body.decode("utf-8"))
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
