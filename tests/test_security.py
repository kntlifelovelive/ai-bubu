"""Tests for src/security.py."""

import os
import sys
import unittest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, SRC_DIR)

from src.security import AccessDenied, SecurityConfig, SecurityValidator


class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.validator = SecurityValidator()

    def test_valid_prompt_is_accepted(self):
        self.assertEqual(
            self.validator.check_prompt("Hello, how are you?"),
            "Hello, how are you?",
        )

    def test_empty_prompt_is_rejected(self):
        with self.assertRaises(AccessDenied):
            self.validator.check_prompt("")

    def test_none_prompt_is_rejected(self):
        with self.assertRaises(AccessDenied):
            self.validator.check_prompt(None)

    def test_shell_command_in_prompt_is_rejected(self):
        with self.assertRaises(AccessDenied):
            self.validator.check_prompt("hello; rm -rf /")

    def test_generation_length_accepts_small(self):
        v = SecurityValidator(SecurityConfig(max_response_tokens=10))
        self.assertEqual(v.check_generation_length(5), 5)
    def test_generation_length_rejects_large(self):
        v = SecurityValidator(SecurityConfig(max_response_tokens=10))
        with self.assertRaises(AccessDenied):
            v.check_generation_length(50)

    def test_generation_length_zero_rejected(self):
        v = SecurityValidator(SecurityConfig(max_response_tokens=10))
        with self.assertRaises(AccessDenied):
            v.check_generation_length(0)

    def test_public_host_rejected(self):
        with self.assertRaises(AccessDenied):
            self.validator.check_host("0.0.0.0")

    def test_localhost_allowed(self):
        self.assertTrue(self.validator.is_allowed_host("127.0.0.1"))
        self.assertTrue(self.validator.is_allowed_host("::1"))
        self.assertFalse(self.validator.is_allowed_host("192.168.1.5"))

    def test_request_too_big_rejected(self):
        v = SecurityValidator(SecurityConfig(max_request_size_bytes=100))
        with self.assertRaises(AccessDenied):
            v.check_request_size(9999)


if __name__ == "__main__":
    unittest.main()
