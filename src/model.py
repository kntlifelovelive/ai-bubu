"""Model manager for ai-bubu.

Handles loading, running, and unloading the language model.
In this phase it is a skeleton: the real inference backend
will be plugged in during Phase 2.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Callable, Generator, Optional


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
    """

    def __init__(self) -> None:
        self.state = ModelState()

    def is_loaded(self) -> bool:
        """Return True if a model is currently loaded."""
        return self.state.loaded and self.state.error is None

    def load(self, path: str) -> ModelState:
        """Load a model from disk.

        In Phase 2 this will load a GGUF file into the
        inference engine. For now it validates the path
        and simulates a load time.
        """
        self.state = ModelState()

        if not path:
            self.state.error = "Model path is empty"
            return self.state

        if not os.path.exists(path):
            self.state.error = f"Model file not found: {path}"
            return self.state

        if not path.lower().endswith((".gguf", ".safetensors", ".bin")):
            self.state.error = (
                "Only .gguf, .safetensors, and .bin models are supported"
            )
            return self.state

        start = time.monotonic()
        # Phase 2: replace with real loading, e.g. llama.cpp
        time.sleep(0.01)
        elapsed = time.monotonic() - start

        self.state = ModelState(
            loaded=True,
            path=path,
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
