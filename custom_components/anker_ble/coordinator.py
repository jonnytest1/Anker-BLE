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
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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

# How long to wait for an advertisement before failing a poll.
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

    async def _async_get_ble_device(self) -> BLEDevice:
        """Resolve a connectable BLEDevice from HA's scanner cache (with wait)."""
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
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
            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, self.address, connectable=True
            )
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

        raise UpdateFailed(
            f"Anker BLE device {self.address} was not seen by any Bluetooth scanner "
            f"for {_SCAN_WAIT_SECONDS:.0f}s. Keep the charger powered and near Home "
            f"Assistant (or an ESPHome Bluetooth proxy), and close the Anker phone app. "
            f"{detail}".strip()
        )

    async def _async_update_data(self) -> dict[str, Any]:
        ble_device = await self._async_get_ble_device()
        name = self.entry.data.get(CONF_NAME) or ble_device.name or self.address
        client = AnkerBleClient(ble_device)
        try:
            snapshot = await client.poll_session(
                listen_seconds=self.listen_seconds,
                subscribe=True,
                use_retry_connector=True,
                connect_name=str(name),
            )
        except Exception as err:
            raise UpdateFailed(
                f"Anker BLE poll failed for {self.address}: {err}"
            ) from err

        parsed = parse_telemetry(snapshot.telemetry)
        return {
            "address": self.address,
            "identity": identity_as_dict(snapshot.identity),
            "telemetry_cmd": snapshot.telemetry_cmd,
            "notifications": snapshot.notifications,
            "parsed": asdict(parsed),
            "tlv_keys": list(snapshot.telemetry.keys()),
            "online": True,
        }
