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
    battery_percent: float | None = None
    charging: bool | None = None
    raw_keys: tuple[str, ...] = ()

    power_usba: PortTelemetry | None = None
    usbc1_tel: PortTelemetry | None = None
    usbc2_tel: PortTelemetry | None = None
    temperature_c: float | None = None


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


def _battery_percent(data: bytes | None) -> float | None:
    """Decode battery percentage from the observed a2 TLV pattern."""
    if not data or len(data) < 3 or data[0] != 0x04:
        return None

    whole = data[1]
    fraction = data[2]

    if whole > 100 or fraction > 99:
        return None

    return round(whole + fraction / 100.0, 2)


def _output_power_w(data: bytes | None) -> float | None:
    """Working hypothesis: a6 contains output power in tenths of a watt."""
    if not data or len(data) < 4 or data[0] != 0x04:
        return None

    raw = _le_u16(data, 2, 4)
    if raw is None:
        return None

    return raw / 10.0


@dataclass
class PortTelemetry:
   # value_1: int | None  # bytes [1:3]
    voltage_v: float | None  # bytes [3:5]
    current_a: float | None  # Hypothesis: raw / 10
    power_w: float | None  # bytes [6:8], tenths of a watt (hypothesis)
    value_4: int | None  # bytes [8:10]
    raw: bytes


def _parse_port_telemetry(data: bytes | None) -> PortTelemetry | None:
    if not data or data[0] != 0x04:
        return None
    raw_voltage = _le_u16(data, 2, 4)
    raw_current = _le_u16(data, 4, 6)
    raw_power = _le_u16(data, 6, 8)

    return PortTelemetry(
        voltage_v=raw_voltage / 10.0 if raw_voltage is not None else None,
        current_a=raw_current / 10.0 if raw_current is not None else None,
        power_w=raw_power / 10.0 if raw_power is not None else None,
        value_4=_le_u16(data, 8, 10),
        raw=data,
    )


def parse_telemetry_fixed(tlv: dict[str, bytes]) -> ParsedTelemetry:

    #
    # a1: charging/status (current heuristic: last byte != 0)
    # a2: battery percentage (observed: 04 <whole> <fraction>)
    # a5: input power (W)
    # a6: output power (W)

    # a1: status/flags; one bit or value likely indicates charging (not decoded yet)
    # a2: battery percentage (04 <whole %> <fraction>, tentatively)
    # a5: input power
    # a6: overall output power
    # a8: USB-C 1 telemetry (voltage/current/power)
    # a9: USB-C 2 telemetry (voltage/current/power)
    # ac: USB-A telemetry (voltage/current/power)
    # af temp

    pad1 = None
    pad2 = None
    pad3 = None

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
        return round(float(value * 10)*1000)/1000

    if pad1 is None:
        pad1 = _alt_power("a5")
    if pad2 is None:
        pad2 = _alt_power("a6")
    if pad3 is None:
        pad3 = _alt_power("a7")

    powers = [p for p in (pad1, pad2, pad3) if p is not None]
    power_out = round(sum(powers), 2) if powers else None

    battery = _battery_percent(tlv.get("a2"))

    # a1 often carries a status nibble for charger reports (0x31 seen while idle/active)
    charging = None
    if "a1" in tlv and tlv["a1"]:
        charging = tlv["a1"][-1] != 0

    usbc1_tel = _parse_port_telemetry(tlv.get("a8"))
    usbc2_tel = _parse_port_telemetry(tlv.get("a9"))
    power_usba = _parse_port_telemetry(tlv.get("ac"))   # tlv.get("ac")
    temperature_c = None
    if "af" in tlv and len(tlv["af"]) >= 2:
        temperature_c = tlv["af"][1]
    return ParsedTelemetry(
        pad_1_power_w=pad1,
        pad_2_power_w=pad2,
        pad_3_power_w=pad3,
        power_out_w=power_out,
        usbc1_tel=usbc1_tel,
        usbc2_tel=usbc2_tel,
        power_usba=power_usba,
        battery_percent=battery,
        temperature_c=temperature_c,
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
