"""Interpret MagGo / charger session TLV (cmd 4a00 etc.)."""

from __future__ import annotations

from dataclasses import dataclass

from .client import DeviceIdentity


@dataclass
class ParsedTelemetry:
    """Normalized fields for Home Assistant sensors."""

    pad_1_power_w: float | None = None
    pad_2_power_w: float | None = None
    pad_3_power_w: float | None = None
    power_out_w: float | None = None
    battery_percent: int | None = None
    charging: bool | None = None
    raw_keys: tuple[str, ...] = ()


def _le_u16(data: bytes, begin: int, end: int) -> int | None:
    if len(data) < end:
        return None
    return int.from_bytes(data[begin:end], "little", signed=False)


def _pad_power_w(data: bytes | None) -> float | None:
    """Classic MagGo pad TLV (8 bytes): power at [6:8] in 0.01 W."""
    if not data or len(data) < 8:
        return None
    raw = _le_u16(data, 6, 8)
    if raw is None:
        return None
    return raw / 100.0


def _status_byte(data: bytes | None) -> int | None:
    if not data or len(data) < 2:
        return None
    # Common shape: 04 <status> …
    if data[0] == 0x04:
        return data[1]
    return data[0]


def parse_telemetry(tlv: dict[str, bytes]) -> ParsedTelemetry:
    pad1 = _pad_power_w(tlv.get("a2"))
    pad2 = _pad_power_w(tlv.get("a3"))
    pad3 = _pad_power_w(tlv.get("a4"))

    # Observed MagGo/“Charging” 4a00 report:
    # a5/a6/a7 look like 04 <flags…> power-ish little-endian tails
    def _alt_power(key: str) -> float | None:
        data = tlv.get(key)
        if not data or len(data) < 4:
            return None
        # try last 2 bytes as 0.01 W
        raw = _le_u16(data, len(data) - 2, len(data))
        if raw is None or raw in (0, 0xFFFF):
            return None
        value = raw / 100.0
        if value > 200:
            return None
        return value

    if pad1 is None:
        pad1 = _alt_power("a5")
    if pad2 is None:
        pad2 = _alt_power("a6")
    if pad3 is None:
        pad3 = _alt_power("a7")

    powers = [p for p in (pad1, pad2, pad3) if p is not None]
    power_out = round(sum(powers), 2) if powers else None

    battery = None
    if "bb" in tlv and len(tlv["bb"]) >= 2:
        battery = tlv["bb"][1]
    elif "bb" in tlv and tlv["bb"]:
        battery = tlv["bb"][0]

    # a1 often carries a status nibble for charger reports (0x31 seen while idle/active)
    charging = None
    if "a1" in tlv and tlv["a1"]:
        charging = tlv["a1"][-1] != 0

    return ParsedTelemetry(
        pad_1_power_w=pad1,
        pad_2_power_w=pad2,
        pad_3_power_w=pad3,
        power_out_w=power_out,
        battery_percent=battery,
        charging=charging,
        raw_keys=tuple(sorted(tlv.keys())),
    )


def identity_as_dict(identity: DeviceIdentity) -> dict[str, str | None]:
    return {
        "product_name": identity.product_name,
        "firmware": identity.firmware,
        "serial": identity.serial,
        "mac_or_id": identity.mac_or_id,
    }
