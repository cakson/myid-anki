#!/usr/bin/env python3
"""Run Codex where macOS has no usable system DNS configuration.

This process-local CONNECT tunnel resolves only OpenAI service hosts with `dig`.
It does not intercept TLS or change system network settings.
"""

from __future__ import annotations

import argparse
import ipaddress
import os
import re
import select
import socket
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

ALLOWED_HOSTS = ("chatgpt.com", "openai.com")


def system_resolver() -> str:
    for line in Path("/etc/resolv.conf").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == "nameserver":
            return str(ipaddress.ip_address(parts[1]))
    raise RuntimeError("No nameserver found in /etc/resolv.conf; pass --resolver")


def resolve(host: str, resolver: str) -> list[str]:
    result = subprocess.run(
        ["dig", f"@{resolver}", host, "A", "+short", "+time=2", "+tries=1"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    addresses = []
    for line in result.stdout.splitlines():
        try:
            addresses.append(str(ipaddress.IPv4Address(line)))
        except ipaddress.AddressValueError:
            continue
    return addresses


def handler_type(resolver: str):
    class ConnectHandler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            client = self.request
            client.settimeout(15)
            data = b""
            while b"\r\n\r\n" not in data and len(data) < 16384:
                block = client.recv(4096)
                if not block:
                    return
                data += block
            header, separator, remainder = data.partition(b"\r\n\r\n")
            if not separator:
                return
            first = header.split(b"\r\n", 1)[0].decode("ascii", "replace")
            match = re.fullmatch(r"CONNECT ([A-Za-z0-9.-]+):443 HTTP/1\.[01]", first)
            if match is None:
                client.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
                return
            host = match.group(1).lower()
            if not any(host == domain or host.endswith("." + domain) for domain in ALLOWED_HOSTS):
                client.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n")
                return
            upstream = None
            for address in resolve(host, resolver):
                try:
                    upstream = socket.create_connection((address, 443), timeout=10)
                    break
                except OSError:
                    continue
            if upstream is None:
                client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                return
            with upstream:
                client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                if remainder:
                    upstream.sendall(remainder)
                client.settimeout(None)
                upstream.settimeout(None)
                peers = (client, upstream)
                while True:
                    ready, _, _ = select.select(peers, (), (), 120)
                    if not ready:
                        return
                    for source in ready:
                        try:
                            payload = source.recv(65536)
                            if not payload:
                                return
                            (upstream if source is client else client).sendall(payload)
                        except OSError:
                            return

    return ConnectHandler


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-bin", default="codex", help="Codex CLI binary to invoke")
    parser.add_argument("--resolver", help="DNS server IP; defaults to /etc/resolv.conf")
    parser.add_argument("--cert-file", default="/etc/ssl/cert.pem")
    parser.add_argument("codex_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.codex_args or args.codex_args[0] != "--":
        parser.error("pass Codex arguments after --")
    resolver = args.resolver or system_resolver()
    with Server(("127.0.0.1", 0), handler_type(resolver)) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        proxy = f"http://127.0.0.1:{server.server_address[1]}"
        env = os.environ.copy()
        env.update(
            HTTPS_PROXY=proxy,
            HTTP_PROXY=proxy,
            ALL_PROXY=proxy,
            SSL_CERT_FILE=args.cert_file,
        )
        try:
            return subprocess.run([args.codex_bin, *args.codex_args[1:]], env=env).returncode
        finally:
            server.shutdown()
            worker.join(timeout=2)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"curation Codex launcher: {exc}", file=sys.stderr)
        sys.exit(1)
