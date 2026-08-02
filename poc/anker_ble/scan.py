"""Scan for Anker / Solix-style BLE devices."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .uuids import (
    EXTRA_IDENTIFIER_UUIDS,
    IDENTIFIER_UUID,
    NAME_HINTS,
    UUID_FAMILIES,
    match_uuid_family,
    normalize_uuid,
)

log = logging.getLogger(__name__)


@dataclass
class DiscoveredDevice:
    address: str
    name: str | None
    rssi: int
    service_uuids: list[str] = field(default_factory=list)
    manufacturer_data: dict[int, bytes] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    family: str | None = None
    device: BLEDevice | None = field(default=None, repr=False)

    @property
    supported(self) -> bool:
        return bool(self.reasons)


def _name_matches(name: str | None) -> bool:
    if not name:
        return False
    lowered = name.lower()
    return any(hint in lowered for hint in NAME_HINTS)


def classify(
    device: BLEDevice, adv: AdvertisementData
) -> DiscoveredDevice | None:
    uuids = [normalize_uuid(u) for u in (adv.service_uuids or [])]
    reasons: list[str] = []

    id_set = {normalize_uuid(u) for u in EXTRA_IDENTIFIER_UUIDS}
    hit_ids = sorted(set(uuids) & id_set)
    if normalize_uuid(IDENTIFIER_UUID) in uuids:
        reasons.append("adv:FF09")
    elif hit_ids:
        reasons.append(f"adv:{hit_ids[0][:8]}")

    family = match_uuid_family(uuids)
    if family:
        reasons.append(f"family:{family}")

    if _name_matches(adv.local_name or device.name):
        reasons.append("name")

    if not reasons:
        return None

    return DiscoveredDevice(
        address=device.address,
        name=adv.local_name or device.name,
        rssi=adv.rssi if adv.rssi is not None else -127,
        service_uuids=uuids,
        manufacturer_data=dict(adv.manufacturer_data or {}),
        reasons=reasons,
        family=family,
        device=device,
    )


async def scan_devices(
    timeout: float = 8.0,
    adapter: str | None = None,
) -> list[DiscoveredDevice]:
    """Passive scan; keep strongest sighting per address."""
    found: dict[str, DiscoveredDevice] = {}

    def _callback(device: BLEDevice, adv: AdvertisementData) -> None:
        hit = classify(device, adv)
        if hit is None:
            return
        prev = found.get(hit.address)
        if prev is None or hit.rssi > prev.rssi:
            found[hit.address] = hit
            log.info(
                "found %s  rssi=%s  name=%r  reasons=%s",
                hit.address,
                hit.rssi,
                hit.name,
                ",".join(hit.reasons),
            )

    scanner_kwargs: dict = {"detection_callback": _callback}
    if adapter:
        scanner_kwargs["adapter"] = adapter

    async with BleakScanner(**scanner_kwargs):
        await asyncio.sleep(timeout)

    devices = sorted(found.values(), key=lambda d: d.rssi, reverse=True)
    log.info("scan done: %d supported device(s)", len(devices))
    return devices


def describe_gatt_targets(family: str | None) -> dict[str, str] | None:
    if family and family in UUID_FAMILIES:
        return UUID_FAMILIES[family]
    return UUID_FAMILIES["8C85"]
