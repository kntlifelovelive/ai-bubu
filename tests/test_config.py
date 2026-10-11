"""Tests for src/config.py."""

import json
import os
import sys
import tempfile
import unittest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, SRC_DIR)

from src.config import Config, load_config


class TestConfig(unittest.TestCase):
    def test_default_config_is_localhost(self):
        config = load_config(path="/nonexistent/path.yaml")
        self.assertEqual(config.server_host, "127.0.0.1")
        self.assertEqual(config.server_port, 5001)

    def test_default_config_has_size_limits(self):
        config = load_config(path="/nonexistent/path.yaml")
        self.assertEqual(config.security_max_request_size_bytes, 1048576)
        self.assertEqual(config.security_max_prompt_tokens, 4096)
        self.assertEqual(config.model_max_tokens, 512)

    def test_custom_config_is_loaded(self):
        sample = {
            "server": {"host": "127.0.0.1", "port": 6000},
            "model": {"path": "/tmp/model.gguf", "max_tokens": 256},
            "security": {"max_prompt_tokens": 2048},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
server:
  host: 127.0.0.1
  port: 6000
model:
  path: /tmp/model.gguf
  max_tokens: 256
security:
  max_prompt_tokens: 2048
""")
            path = f.name
        try:
            config = load_config(path=path)
            self.assertEqual(config.server_port, 6000)
            self.assertEqual(config.model_path, "/tmp/model.gguf")
            self.assertEqual(config.security_max_prompt_tokens, 2048)
        finally:
            os.unlink(path)

    def test_config_to_dict(self):
        config = Config(server_port=6000)
        data = config.to_dict()
        self.assertEqual(data["server"]["port"], 6000)

    def test_minimal_yaml(self):
        sample = "model:\n  path: /home/user/model.gguf\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(sample)
            path = f.name
        try:
            config = load_config(path=path)
            self.assertEqual(config.model_path, "/home/user/model.gguf")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
