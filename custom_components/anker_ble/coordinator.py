"""Data update coordinator for Anker BLE."""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ADDRESS,
    CONF_LISTEN_SECONDS,
    CONF_POLL_INTERVAL,
    DEFAULT_LISTEN_SECONDS,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)
from .protocol.client import AnkerBleClient
from .protocol.telemetry import identity_as_dict, parse_telemetry

_LOGGER = logging.getLogger(__name__)


class AnkerBleCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls an Anker BLE device: connect → confer → subscribe → snapshot."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.address: str = entry.data[CONF_ADDRESS]
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

    async def _async_update_data(self) -> dict[str, Any]:
        client = AnkerBleClient(self.address)
        try:
            snapshot = await client.poll_session(
                listen_seconds=self.listen_seconds,
                subscribe=True,
            )
        except Exception as err:
            raise UpdateFailed(f"Anker BLE poll failed for {self.address}: {err}") from err

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
