"""Tests for src/memory.py."""

import os
import sys
import unittest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, SRC_DIR)

from src.memory import MemoryInfo, get_memory_info, read_meminfo


class TestMemory(unittest.TestCase):
    def test_read_meminfo_returns_dict(self):
        values = read_meminfo()
        self.assertIsInstance(values, dict)

    def test_get_memory_info(self):
        info = get_memory_info()
        self.assertIsInstance(info, MemoryInfo)
        self.assertGreater(info.total_bytes, 0)
        self.assertGreaterEqual(info.used_percent, 0.0)
        self.assertLessEqual(info.used_percent, 100.0)

    def test_memory_safe_returns_bool(self):
        from src.memory import memory_safe

        result = memory_safe(75)
        self.assertIsInstance(result, bool)

    def test_memory_info_gb(self):
        info = MemoryInfo(
            total_bytes=8589934592,
            available_bytes=4294967296,
            used_bytes=4294967296,
            used_percent=50.0,
        )
        self.assertAlmostEqual(info.total_gb, 8.0, places=3)
        self.assertAlmostEqual(info.available_gb, 4.0, places=3)


if __name__ == "__main__":
    unittest.main()
