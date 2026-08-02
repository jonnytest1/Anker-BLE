"""Anker BLE Home Assistant integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import AnkerBleCoordinator
from .frontend import async_setup_frontend
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.IMAGE,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up shared frontend assets once."""
    await async_setup_frontend(hass)
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Anker BLE from a config entry.

    Setup must not block on a successful BLE poll — otherwise the entry stays
    in “Initializing” while the charger is offline / held by the phone app.
    """
    await async_setup_frontend(hass)
    async_setup_services(hass)

    coordinator = AnkerBleCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # First poll in the background; entities stay unavailable until it succeeds.
    hass.async_create_task(
        coordinator.async_request_refresh(),
        name=f"{DOMAIN}_{entry.entry_id}_first_poll",
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Anker BLE config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        async_unload_services(hass)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
