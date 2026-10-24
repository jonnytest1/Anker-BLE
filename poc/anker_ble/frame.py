"""FF09 frame encode/decode and TLV parsing."""

from __future__ import annotations

from dataclasses import dataclass


HEADER = bytes.fromhex("ff09")


def xor_checksum(data: bytes) -> bytes:
    value = 0
    for byte in data:
        value ^= byte
    return bytes([value])


@dataclass(frozen=True)
class Frame:
    pattern: bytes
    cmd: bytes
    payload: bytes

    def build(self) -> bytes:
        if len(self.pattern) != 3:
            raise ValueError("pattern must be 3 bytes")
        if len(self.cmd) != 2:
            raise ValueError("cmd must be 2 bytes")
        length = 2 + 2 + 3 + 2 + len(self.payload) + 1
        packet = HEADER + \
            length.to_bytes(2, "little") + self.pattern + \
            self.cmd + self.payload
        return packet + xor_checksum(packet)


def split_frame(packet: bytes) -> Frame:
    if len(packet) < 10:
        raise ValueError(f"packet too short: {len(packet)}")
    if packet[:2] != HEADER:
        raise ValueError(f"bad header: {packet[:2].hex()}")
    length = int.from_bytes(packet[2:4], "little")
    if length != len(packet):
        raise ValueError(
            f"length mismatch: encoded={length} actual={len(packet)}")
    if packet[-1:] != xor_checksum(packet[:-1]):
        raise ValueError("checksum mismatch")
    return Frame(pattern=packet[4:7], cmd=packet[7:9], payload=packet[9:-1])


def parse_tlv(payload: bytes) -> dict[str, bytes]:
    """Parse Anker TLV: <id:1><len:1><data:len> (optional leading 0x00)."""
    data = bytearray(payload)
    out: dict[str, bytes] = {}
    if data.startswith(b"\x00"):
        data.pop(0)
    while data:
        param_id = f"{data.pop(0):02x}"
        if not data:
            out[param_id] = b""
            break
        param_len = data.pop(0)
        if len(data) < param_len:
            raise ValueError(f"truncated TLV for id={param_id}")
        out[param_id] = bytes(data[:param_len])
        del data[:param_len]
    return out


def tlv_to_str(params: dict[str, bytes]) -> str:
    parts = []
    for key, value in params.items():
        parts.append(f"{key}={value.hex()}")
    return ", ".join(parts)
