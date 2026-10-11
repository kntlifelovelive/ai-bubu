"""Memory monitoring for ai-bubu.

Tracks RAM usage by reading /proc/meminfo. Used to decide
whether the model can stay loaded or should be unloaded.
"""

import os
from dataclasses import dataclass


@dataclass
class MemoryInfo:
    """Memory statistics from the system."""

    total_bytes: int
    available_bytes: int
    used_bytes: int
    used_percent: float

    @property
    def total_gb(self) -> float:
        """Total RAM in gigabytes."""
        return self.total_bytes / (1024 ** 3)

    @property
    def available_gb(self) -> float:
        """Available RAM in gigabytes."""
        return self.available_bytes / (1024 ** 3)


def read_meminfo() -> dict[str, int]:
    """Read /proc/meminfo and return key values in bytes."""
    values: dict[str, int] = {}
    path = "/proc/meminfo"

    if not os.path.exists(path):
        return values

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) >= 2 and parts[1].endswith(":"):
                key = parts[0].rstrip(":")
                try:
                    values[key] = int(parts[1]) * 1024  # kB -> bytes
                except ValueError:
                    continue

    return values


def get_memory_info() -> MemoryInfo:
    """Get current memory statistics.

    Returns a MemoryInfo with sane defaults if /proc/meminfo
    cannot be read.
    """
    info = read_meminfo()

    total = info.get("MemTotal", 8 * 1024 * 1024 * 1024)
    available = info.get("MemAvailable", total // 4)
    buffers = info.get("Buffers", 0)
    cached = info.get("Cached", 0)

    used = total - available - buffers - cached
    if used < 0:
        used = total - available

    used_percent = (used / total) * 100 if total > 0 else 0.0

    return MemoryInfo(
        total_bytes=total,
        available_bytes=available,
        used_bytes=used,
        used_percent=round(used_percent, 1),
    )


def memory_safe(memory_percent: float) -> bool:
    """Check whether memory use is below the threshold.

    Args:
        memory_percent: Max allowed RAM usage percent.

    Returns:
        True if safe to continue loading/running the model.
    """
    info = get_memory_info()
    return info.used_percent < memory_percent


def report_memory(memory_percent: float | None = None) -> None:
    """Print a one-line memory summary."""
    percent = memory_percent if memory_percent is not None else 75
    info = get_memory_info()
    status = "OK" if memory_safe(percent) else "LOW MEMORY"
    print(
        f"memory={status} "
        f"total={info.total_gb:.1f}GB "
        f"available={info.available_gb:.1f}GB "
        f"used={info.used_percent:.0f}%"
    )


if __name__ == "__main__":
    report_memory()
