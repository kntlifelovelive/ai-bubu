"""Tests for src/model.py."""

import os
import sys
import unittest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, SRC_DIR)

from src.model import ModelManager, get_model_manager


class TestModel(unittest.TestCase):
    def test_starts_unloaded(self):
        m = ModelManager()
        self.assertFalse(m.is_loaded())

    def test_load_nonexistent_fails(self):
        m = ModelManager()
        state = m.load("/nonexistent/model.gguf")
        self.assertFalse(state.loaded)
        self.assertIsNotNone(state.error)

    def test_load_bad_extension_fails(self):
        m = ModelManager()
        state = m.load("/tmp/model.exe")
        self.assertFalse(state.loaded)

    def test_unload_cleans_state(self):
        m = ModelManager()
        m.unload()
        self.assertFalse(m.is_loaded())

    def test_complete_generates_placeholder(self):
        m = ModelManager()
        chunks = list(m.complete("hi", 5))
        self.assertGreaterEqual(len(chunks), 1)
        self.assertIn("placeholder", "".join(chunks))

    def test_get_manager_is_singleton(self):
        a = get_model_manager()
        b = get_model_manager()
        self.assertIs(a, b)


if __name__ == "__main__":
    unittest.main()
