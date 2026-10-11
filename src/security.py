"""Security and permission layer for ai-bubu.

Every input from a client passes through this layer before
it is used. If validation fails, the request is rejected.
"""

from dataclasses import dataclass
from typing import NamedTuple

import ipaddress
import socket


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
        """Validate the bind host resolves to an IPv4 loopback address.

        ai-bubu's server stack is IPv4-only and binds to loopback
        addresses only (127.0.0.1 by default). Binding to any
        non-loopback address (including LAN addresses, IPv6 loopback,
        or the public Internet) is rejected before any socket is
        opened, so localhost-only is enforced at startup.

        Raises:
            AccessDenied: if the host would expose the API to any
                non-loopback network interface.
        """
        host = host.strip()
        if host in ("0.0.0.0", "*", "[::]", "[::1]"):
            raise AccessDenied(
                "Host must not be 0.0.0.0, * or [::]"
            )
        try:
            addr = ipaddress.ip_address(host)
        except ValueError:
            # Resolve hostnames to IPv4 only; require loopback.
            try:
                infos = socket.getaddrinfo(host, None, socket.AF_INET)
            except socket.gaierror:
                raise AccessDenied(f"Cannot resolve host: {host}")
            if not infos:
                raise AccessDenied(f"Host does not resolve to an IPv4 address: {host}")
            for info in infos:
                resolved = info[4][0]
                r = ipaddress.ip_address(resolved)
                if not r.is_loopback:
                    raise AccessDenied(
                        f"Host resolves to non-loopback address {resolved}; "
                        "only IPv4 loopback (127.0.0.1) is allowed for binding"
                    )
        else:
            # Only IPv4 loopback is supported by this server.
            if addr.version != 4 or addr.is_multicast or not addr.is_loopback:
                raise AccessDenied(
                    "Only the IPv4 loopback address (127.0.0.1) is allowed; "
                    f"got {host}"
                )
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
