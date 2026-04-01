"""Scan the local network for comma devices via SSH port probing."""

from __future__ import annotations

import asyncio
import socket
import struct
from dataclasses import dataclass
from typing import List

# comma 3x exposes SSH on port 8022; comma 4 uses the standard port 22.
COMMA_PORTS = {
    8022: "comma 3x",
    22: "comma 4",
}

_SCAN_TIMEOUT = 1.5  # seconds per connection attempt


@dataclass
class FoundDevice:
    ip: str
    port: int
    device_type: str


def _get_local_ip_and_prefix() -> tuple[str, int]:
    """Return (local_ip, prefix_length) for the default route interface."""
    # Connect to a public address to determine which local IP is used for LAN traffic.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(0.5)
        try:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        except OSError:
            local_ip = "127.0.0.1"

    # Try to read the prefix length from /proc/net/fib_trie or fall back to /24.
    prefix = 24
    try:
        import fcntl
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s2:
            for iface in _list_interfaces():
                try:
                    addr = socket.inet_ntoa(
                        fcntl.ioctl(s2.fileno(), 0x8915, struct.pack("256s", iface.encode()))[20:24]
                    )
                    if addr == local_ip:
                        mask_bytes = fcntl.ioctl(s2.fileno(), 0x891B, struct.pack("256s", iface.encode()))[20:24]
                        mask_int = int.from_bytes(mask_bytes, "big")
                        prefix = bin(mask_int).count("1")
                        break
                except OSError:
                    continue
    except Exception:
        pass

    return local_ip, prefix


def _list_interfaces() -> list[str]:
    """List network interface names from /proc/net/dev."""
    try:
        with open("/proc/net/dev") as f:
            lines = f.readlines()[2:]  # skip header lines
        return [line.split(":")[0].strip() for line in lines]
    except OSError:
        return []


def _subnet_ips(local_ip: str, prefix: int) -> list[str]:
    """Generate all host IPs in the subnet (skip network and broadcast)."""
    ip_int = int.from_bytes(socket.inet_aton(local_ip), "big")
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    network = ip_int & mask
    host_bits = 32 - prefix

    # Only scan /24 or smaller to keep it fast.
    if host_bits > 8:
        host_bits = 8
        network = ip_int & (0xFFFFFFFF << host_bits) & 0xFFFFFFFF

    count = (1 << host_bits) - 2  # exclude network and broadcast
    return [
        socket.inet_ntoa(struct.pack("!I", network + i))
        for i in range(1, count + 1)
    ]


async def _probe(ip: str, port: int, timeout: float) -> FoundDevice | None:
    """Try to open a TCP connection to ip:port. Return a FoundDevice on success."""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        return FoundDevice(ip=ip, port=port, device_type=COMMA_PORTS[port])
    except (OSError, asyncio.TimeoutError):
        return None


async def scan_network(timeout: float = _SCAN_TIMEOUT) -> List[FoundDevice]:
    """Scan the local /24 subnet for comma devices.

    Probes each host on ports 8022 and 22 concurrently.
    Returns a list of discovered devices sorted by IP.
    """
    local_ip, prefix = _get_local_ip_and_prefix()
    if local_ip.startswith("127."):
        return []

    ips = _subnet_ips(local_ip, prefix)

    tasks = [
        _probe(ip, port, timeout)
        for ip in ips
        for port in COMMA_PORTS
    ]

    results = await asyncio.gather(*tasks)
    devices = [r for r in results if r is not None]

    # Deduplicate: if an IP responds on both ports, prefer 8022 (comma 3x).
    seen: dict[str, FoundDevice] = {}
    for d in devices:
        if d.ip not in seen or d.port == 8022:
            seen[d.ip] = d

    return sorted(seen.values(), key=lambda d: socket.inet_aton(d.ip))
