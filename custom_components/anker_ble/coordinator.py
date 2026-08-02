"""Data update coordinator for Anker BLE."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict
from datetime import timedelta
from typing import Any

from bleak.backends.device import BLEDevice
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_ADDRESS,
    CONF_LISTEN_SECONDS,
    CONF_NAME,
    CONF_POLL_INTERVAL,
    DEFAULT_LISTEN_SECONDS,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)
from .protocol.client import AnkerBleClient
from .protocol.telemetry import identity_as_dict, parse_telemetry

_LOGGER = logging.getLogger(__name__)

# How long to wait for an advertisement before treating the poll as offline.
_SCAN_WAIT_SECONDS = 20.0


def _empty_snapshot(address: str, name: str | None = None) -> dict[str, Any]:
    """Placeholder data so entities can load before the first successful poll."""
    identity: dict[str, str | None] = {
        "product_name": name,
        "firmware": None,
        "serial": name if name and name.startswith("ASHD") else None,
        "mac_or_id": address,
    }
    return {
        "address": address,
        "identity": identity,
        "telemetry_cmd": None,
        "notifications": 0,
        "parsed": {},
        "tlv_keys": [],
        "online": False,
        "last_error": None,
    }


class AnkerBleCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls an Anker BLE device: connect → confer → subscribe → snapshot."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.address: str = format_mac(entry.data[CONF_ADDRESS])
        poll = entry.options.get(
            CONF_POLL_INTERVAL,
            entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
        )
        self.listen_seconds: float = float(
            entry.options.get(
                CONF_LISTEN_SECONDS,
                entry.data.get(CONF_LISTEN_SECONDS, DEFAULT_LISTEN_SECONDS),
            )
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.address}",
            update_interval=timedelta(seconds=int(poll)),
        )
        # Avoid blocking setup / “Initializing” on BLE reachability.
        self.data = _empty_snapshot(self.address, entry.data.get(CONF_NAME))

    def _lookup_ble_device(self) -> BLEDevice | None:
        """Prefer a connectable cache entry; fall back to any sighting."""
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device:
            return ble_device
        return bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=False
        )

    async def _async_get_ble_device(self) -> BLEDevice:
        """Resolve a BLEDevice from HA's scanner cache (with wait)."""
        ble_device = self._lookup_ble_device()
        if ble_device:
            return ble_device

        _LOGGER.debug(
            "Device %s not in scanner cache — waiting up to %.0fs for advertisement",
            self.address,
            _SCAN_WAIT_SECONDS,
        )
        deadline = time.monotonic() + _SCAN_WAIT_SECONDS
        while time.monotonic() < deadline:
            await asyncio.sleep(0.5)
            ble_device = self._lookup_ble_device()
            if ble_device:
                return ble_device

        detail = ""
        try:
            reachability = getattr(
                bluetooth, "async_address_reachability_diagnostics", None
            )
            if callable(reachability):
                detail = str(reachability(self.hass, self.address))
        except TypeError:
            detail = ""
        except Exception:  # noqa: BLE001
            detail = ""

        raise RuntimeError(
            f"not seen by any Bluetooth scanner for {_SCAN_WAIT_SECONDS:.0f}s. "
            f"Keep the charger powered and near Home Assistant (or an ESPHome "
            f"Bluetooth proxy), and close the Anker phone app. {detail}".strip()
        )

    def _offline_snapshot(self, error: str) -> dict[str, Any]:
        """Keep identity visible; clear live telemetry and mark offline.

        Must not raise UpdateFailed — that flips last_update_success and makes
        every entity Unavailable until the next lucky poll.
        """
        prev = self.data or _empty_snapshot(
            self.address, self.entry.data.get(CONF_NAME)
        )
        identity = dict(prev.get("identity") or {})
        name = self.entry.data.get(CONF_NAME)
        if name:
            identity.setdefault("product_name", name)
            if name.startswith("ASHD"):
                identity.setdefault("serial", name)
        identity.setdefault("mac_or_id", self.address)
        return {
            "address": self.address,
            "identity": identity,
            "telemetry_cmd": prev.get("telemetry_cmd"),
            "notifications": 0,
            "parsed": {},
            "tlv_keys": [],
            "online": False,
            "last_error": error,
        }

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            ble_device = await self._async_get_ble_device()
            name = self.entry.data.get(CONF_NAME) or ble_device.name or self.address
            client = AnkerBleClient(ble_device)
            snapshot = await client.poll_session(
                listen_seconds=self.listen_seconds,
                subscribe=True,
                use_retry_connector=True,
                connect_name=str(name),
            )
        except Exception as err:  # noqa: BLE001 — BLE stack raises many types
            _LOGGER.warning("Anker BLE poll failed for %s: %s", self.address, err)
            return self._offline_snapshot(str(err))

        parsed = parse_telemetry(snapshot.telemetry)
        identity = identity_as_dict(snapshot.identity)
        # Preserve serial/name hints from the config entry when confer omits them.
        name = self.entry.data.get(CONF_NAME)
        if name:
            identity.setdefault("product_name", name)
            if name.startswith("ASHD"):
                identity.setdefault("serial", name)

        return {
            "address": self.address,
            "identity": identity,
            "telemetry_cmd": snapshot.telemetry_cmd,
            "notifications": snapshot.notifications,
            "parsed": asdict(parsed),
            "tlv_keys": list(snapshot.telemetry.keys()),
            "online": True,
            "last_error": None,
        }
