"""Security and permission layer for ai-bubu.

Every input from a client passes through this layer before
it is used. If validation fails, the request is rejected.
"""

from dataclasses import dataclass
from typing import NamedTuple

import ipaddress


class AccessDenied(Exception):
    """Raised when a request fails security validation."""


class SecurityConfig(NamedTuple):
    """Security settings."""

    max_request_size_bytes: int = 1048576
    max_prompt_tokens: int = 4096
    max_response_tokens: int = 512
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "::1")
    blocked_patterns: tuple[str, ...] = (
        "rm -rf",
        "rm --",
        "sudo",
        "curl ",
        "wget ",
        "pip install",
        "apt-get",
        "yum install",
        "dnf install",
        "chmod ",
        "chown ",
        "mkfs",
        ":() { :;};",
        "/dev/",
        "passwd",
        "useradd",
        "userdel",
    )


class SecurityValidator:
    """Validate all inputs from clients."""

    def __init__(self, config: SecurityConfig | None = None) -> None:
        self.config = config or SecurityConfig()

    def check_request_size(self, content_length: int | None) -> int:
        """Validate the request body size.

        Raises:
            AccessDenied: if the request is too big.
        """
        if content_length is None:
            raise AccessDenied("Content-Length header is missing")
        if content_length > self.config.max_request_size_bytes:
            raise AccessDenied(
                f"Request too large: {content_length} bytes "
                f"(max {self.config.max_request_size_bytes})"
            )
        return content_length

    def check_prompt(self, prompt: str | None) -> str:
        """Validate and sanitize user prompt input.

        Raises:
            AccessDenied: if the prompt is empty, too long,
                or contains suspicious patterns.
        """
        if prompt is None:
            raise AccessDenied("Prompt is missing")
        if not prompt.strip():
            raise AccessDenied("Prompt is empty")
        if len(prompt) > self.config.max_prompt_tokens * 10:
            raise AccessDenied("Prompt too long")

        for pattern in self.config.blocked_patterns:
            if pattern.lower() in prompt.lower():
                raise AccessDenied(
                    f"Prompt contains unsafe content: {pattern}"
                )
        return prompt.strip()

    def check_generation_length(self, num_tokens: int | None) -> int:
        """Validate the requested generation length."""
        if num_tokens is None:
            return self.config.max_response_tokens
        if num_tokens < 1:
            raise AccessDenied("Generation length must be at least 1")
        if num_tokens > self.config.max_response_tokens:
            raise AccessDenied(
                f"Request too large: {num_tokens} tokens "
                f"(max {self.config.max_response_tokens})"
            )
        return num_tokens

    def check_host(self, host: str) -> str:
        """Validate the bind host is not publicly exposed.

        Raises:
            AccessDenied: if the host would expose the API to the
                public network.
        """
        host = host.strip().lower()
        if host in ("0.0.0.0", "*", "[::]"):
            raise AccessDenied(
                "Host must not be 0.0.0.0 or * (public exposure)"
            )
        try:
            addr = ipaddress.ip_address(host)
            if addr.is_unspecified or addr.is_any:
                raise AccessDenied("Host must not be unspecified")
            if addr.is_multicast:
                raise AccessDenied("Host must not be multicast")
        except ValueError:
            pass
        return host

    def is_allowed_host(self, client_ip: str) -> bool:
        """Check whether a client IP is allowed to connect.

        By default only localhost is allowed.
        """
        try:
            ip = ipaddress.ip_address(client_ip)
            return ip.is_loopback
        except ValueError:
            return False
