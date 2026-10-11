"""Configuration loader for ai-bubu.

Reads settings from a YAML file. Falls back to safe defaults
if the file is missing or invalid.
"""

import os
from dataclasses import dataclass, field


DEFAULTS = {
    "server": {
        "host": "127.0.0.1",
        "port": 5001,
    },
    "model": {
        "path": None,
        "max_tokens": 512,
        "idle_timeout_seconds": 300,
    },
    "security": {
        "max_request_size_bytes": 1048576,
        "max_prompt_tokens": 4096,
    },
    "memory": {
        "max_usage_percent": 75,
    },
}

CONFIG_PATH = os.environ.get("AIBUBU_CONFIG", "config/config.yaml")


@dataclass
class Config:
    """All configuration for the server."""

    server_host: str = DEFAULTS["server"]["host"]
    server_port: int = DEFAULTS["server"]["port"]
    model_path: str | None = DEFAULTS["model"]["path"]
    model_max_tokens: int = DEFAULTS["model"]["max_tokens"]
    model_idle_timeout_seconds: int = DEFAULTS["model"]["idle_timeout_seconds"]
    security_max_request_size_bytes: int = DEFAULTS["security"]["max_request_size_bytes"]
    security_max_prompt_tokens: int = DEFAULTS["security"]["max_prompt_tokens"]
    memory_max_usage_percent: int = DEFAULTS["memory"]["max_usage_percent"]

    def to_dict(self) -> dict:
        """Return settings as a plain dictionary."""
        return {
            "server": {"host": self.server_host, "port": self.server_port},
            "model": {
                "path": self.model_path,
                "max_tokens": self.model_max_tokens,
                "idle_timeout_seconds": self.model_idle_timeout_seconds,
            },
            "security": {
                "max_request_size_bytes": self.security_max_request_size_bytes,
                "max_prompt_tokens": self.security_max_prompt_tokens,
            },
            "memory": {"max_usage_percent": self.memory_max_usage_percent},
        }


def load_config(path: str | None = None) -> Config:
    """Load configuration from a YAML file or use defaults.

    Args:
        path: Optional path to the config file. Defaults to
            AIBUBU_CONFIG environment variable, or 'config/config.yaml'.

    Returns:
        A Config object with safe defaults.
    """
    path = path or os.environ.get("AIBUBU_CONFIG", CONFIG_PATH)
    config = Config()

    if not os.path.exists(path):
        return config

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = _load_yaml(handle.read())
    except (OSError, ValueError) as error:
        print(f"WARNING: could not read {path}: {error}")
        print("Using safe defaults.")
        return config

    if not isinstance(data, dict):
        print("WARNING: config file must be a YAML mapping.")
        return config

    config = _merge(config, data, DEFAULTS)
    return config


def _load_yaml(text: str) -> dict:
    """Minimal YAML parsing (only plain mappings, no external deps)."""
    result: dict = {}
    current_path: list[str] = []
    indent_stack: list[int] = [-1]

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        content = line.lstrip()

        while indent_stack and indent <= indent_stack[-1]:
            indent_stack.pop()
            if current_path:
                current_path.pop()

        if ":" in content:
            key, _, value = content.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if value == "" or value.startswith("#"):
                nested: dict = {}
                result[key] = nested
                current_path.append(key)
                indent_stack.append(indent)
            else:
                parent = _get_parent(result, current_path)
                parent[key] = _parse_value(value)
        elif content.startswith("- "):
            item = content[2:].strip()
            parent = _get_parent(result, current_path)
            if not isinstance(parent, dict) or current_path[-1] not in parent:
                parent[current_path[-1]] = []
            parent[current_path[-1]].append(_parse_value(item))

    return result


def _get_parent(data: dict, path: list[str]) -> dict:
    current = data
    for key in path:
        current = current.setdefault(key, {})
    if not isinstance(current, dict):
        return data
    return current


def _parse_value(value: str) -> object:
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() in ("null", "~", ""):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _merge(base: Config, data: dict, defaults: dict) -> Config:
    """Merge loaded data on top of defaults into a Config object."""
    merged = _deep_merge(dict(defaults), data)

    return Config(
        server_host=merged["server"]["host"],
        server_port=merged["server"]["port"],
        model_path=merged["model"].get("path"),
        model_max_tokens=merged["model"].get("max_tokens", defaults["model"]["max_tokens"]),
        model_idle_timeout_seconds=merged["model"].get(
            "idle_timeout_seconds", defaults["model"]["idle_timeout_seconds"]
        ),
        security_max_request_size_bytes=merged["security"].get(
            "max_request_size_bytes", defaults["security"]["max_request_size_bytes"]
        ),
        security_max_prompt_tokens=merged["security"].get(
            "max_prompt_tokens", defaults["security"]["max_prompt_tokens"]
        ),
        memory_max_usage_percent=merged["memory"].get(
            "max_usage_percent", defaults["memory"]["max_usage_percent"]
        ),
    )


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override on top of base recursively."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
