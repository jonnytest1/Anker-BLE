"""Services for Anker BLE."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import AnkerBleCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_REFRESH = "refresh"

SERVICE_REFRESH_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    }
)


def _coordinators_for_entities(
    hass: HomeAssistant, entity_ids: list[str]
) -> list[AnkerBleCoordinator]:
    registry = er.async_get(hass)
    entry_ids: set[str] = set()
    for entity_id in entity_ids:
        ent = registry.async_get(entity_id)
        if ent is None or ent.platform != DOMAIN or ent.config_entry_id is None:
            continue
        entry_ids.add(ent.config_entry_id)

    coordinators: list[AnkerBleCoordinator] = []
    domain_data = hass.data.get(DOMAIN) or {}
    for entry_id in entry_ids:
        coordinator = domain_data.get(entry_id)
        if isinstance(coordinator, AnkerBleCoordinator):
            coordinators.append(coordinator)
    return coordinators


async def _async_handle_refresh(hass: HomeAssistant, call: ServiceCall) -> None:
    entity_ids: list[str] = call.data[ATTR_ENTITY_ID]
    coordinators = _coordinators_for_entities(hass, entity_ids)
    if not coordinators:
        _LOGGER.warning(
            "anker_ble.refresh: no Anker BLE devices found for %s", entity_ids
        )
        return
    for coordinator in coordinators:
        _LOGGER.debug("Manual refresh requested for %s", coordinator.address)
        await coordinator.async_request_refresh()


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register integration services once."""
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        return

    async def handle_refresh(call: ServiceCall) -> None:
        await _async_handle_refresh(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH,
        handle_refresh,
        schema=SERVICE_REFRESH_SCHEMA,
    )


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Remove services when the last entry unloads."""
    if hass.data.get(DOMAIN):
        return
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
