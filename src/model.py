"""Model manager for ai-bubu.

Handles loading, running, and unloading the language model.
In this phase it is a skeleton: the real inference backend
will be plugged in during Phase 2.

Security notes (read before Phase 2 integration):
- All model paths are canonicalized and symlinks are rejected before
  any file is touched. Do not relax this in Phase 2.
- The model file is validated (existence, extension, size) WITHOUT
  reading it into memory. Phase 2 must keep this guarantee.
- The memory guard must be enforced BEFORE the backend reads the file.
- The backend must never be invoked with shell=True. User input
  (prompts) must never be interpolated into a command line; always
  pass arguments as a list. The prompt filter in src/security.py is
  NOT a security boundary and must not be relied upon for command
  execution protection.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Generator, Optional

import src.config as config_module
import src.memory as memory

DEFAULTS = {
    "model": {
        "path": None,
        "max_tokens": 512,
        "idle_timeout_seconds": 300,
        "model_dir": None,
        "max_size_bytes": None,
    },
}


@dataclass
class ModelState:
    """Current state of the model."""

    loaded: bool = False
    path: Optional[str] = None
    load_time_seconds: Optional[float] = None
    last_used_at: float = field(default_factory=time.time)
    error: Optional[str] = None


class ModelManager:
    """Manages the lifecycle of one loaded model.

    Features:
    - One model in memory at a time
    - Idle timeout auto-unload
    - No inference yet (Phase 2)
    - Strict path and size validation (Phase 1 security fixes)
    """

    def __init__(self) -> None:
        self.state = ModelState()

    def is_loaded(self) -> bool:
        """Return True if a model is currently loaded."""
        return self.state.loaded and self.state.error is None

    def load(self, path: str, conf: config_module.Config | None = None) -> ModelState:
        """Load a model from disk.

        In Phase 1 this is a stub: the model file is validated but
        never read into RAM. In Phase 2 the real backend goes here,
        and it MUST honor the path, size, and memory checks below.

        Args:
            path: The model file path from the config or the client.
            conf: The loaded configuration; used to resolve the allowed
                model directory and the model size limit.

        Returns:
            ModelState describing success or a plain-language error.
        """
        self.state = ModelState()

        if not path:
            self.state.error = "Model path is empty"
            return self.state

        # Canonicalize the path (resolves .., ., and symlink components).
        real_path = os.path.realpath(path)

        # Reject symlinks: they can point to arbitrary files and bypass
        # any directory allowlist.
        if os.path.islink(path):
            self.state.error = "Symlinked model paths are not allowed"
            return self.state

        if not os.path.exists(real_path):
            self.state.error = "Model file not found"
            return self.state

        if os.path.isdir(real_path):
            self.state.error = "Model path points to a directory"
            return self.state

        # Validate the extension of the resolved file.
        if not real_path.lower().endswith((".gguf", ".safetensors", ".bin")):
            self.state.error = (
                "Only .gguf, .safetensors, and .bin models are supported"
            )
            return self.state

        # Enforce the configured allowed model directory (if any).
        model_dir = None
        if conf is not None:
            model_dir = getattr(conf, "model_dir", None)
        if model_dir:
            real_model_dir = os.path.realpath(model_dir)
            if not (
                real_path.startswith(real_model_dir + os.sep)
                or real_path == real_model_dir
            ):
                self.state.error = (
                    "Model path is outside the allowed model directory"
                )
                return self.state

        # Validate the file size WITHOUT reading the file into memory
        # (os.stat only returns metadata).
        try:
            file_size = os.path.getsize(real_path)
        except OSError:
            self.state.error = "Could not stat model file"
            return self.state

        max_size = None
        if conf is not None:
            max_size = getattr(conf, "model_max_size_bytes", None)
        if max_size is None or max_size < 1:
            # Derive a safe cap from available RAM: never load a model
            # larger than half of total RAM.
            try:
                mem = memory.get_memory_info()
                max_size = mem.total_bytes // 2
            except Exception:
                max_size = 4 * 1024 * 1024 * 1024  # 4 GB fallback

        if file_size > max_size:
            self.state.error = (
                f"Model file too large (limit {max_size} bytes)"
            )
            return self.state

        # Enforce the configured memory safety limit before the loader
        # consumes RAM. In Phase 1 the loader is a stub and reads no
        # model data, but the guard is exercised now so Phase 2 inherits
        # it. If the host is already above the configured limit, refuse
        # to run the model (fail closed).
        if conf is not None and not memory.memory_safe(
            conf.memory_max_usage_percent
        ):
            self.state.error = "Insufficient memory to load model"
            return self.state

        # Phase 2: replace the block below with the real backend load,
        # e.g. llama.cpp, using subprocess with shell=False and an
        # argument list. User prompts must never be interpolated here.
        start = time.monotonic()
        time.sleep(0.01)
        elapsed = time.monotonic() - start

        self.state = ModelState(
            loaded=True,
            path=None,  # Do not echo the resolved path: avoid filesystem
            load_time_seconds=round(elapsed, 3),
            last_used_at=time.time(),
        )
        return self.state

    def unload(self) -> ModelState:
        """Unload the current model and free memory.

        In Phase 2 this will release the model from RAM.
        """
        self.state = ModelState()
        return self.state

    def last_used(self) -> float:
        """Time of last use (epoch seconds)."""
        return self.state.last_used_at

    def update_last_used(self) -> None:
        """Record that the model was just used."""
        self.state.last_used_at = time.time()

    def check_idle(self, idle_timeout_seconds: int) -> bool:
        """Check whether the model is idle and should unload.

        Returns True if the model should be unloaded.
        """
        if not self.is_loaded():
            return False
        elapsed = time.time() - self.state.last_used_at
        return elapsed > idle_timeout_seconds

    def complete(
        self, prompt: str, max_tokens: int
    ) -> Generator[str, None, None]:
        """Generate a completion for the prompt.

        This phase returns a fixed response. Phase 2 will
        stream real inference results.
        """
        self.update_last_used()
        yield "[ai-bubu placeholder - inference engine coming in Phase 2]"

    def error_message(self) -> str:
        """Return a user-friendly error message."""
        if self.state.error:
            return self.state.error
        if not self.is_loaded():
            return "No model loaded. Use /model/load to load one first."
        return "Unknown error"


# Global singleton used by the server
_global_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get the global model manager singleton."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ModelManager()
    return _global_manager
