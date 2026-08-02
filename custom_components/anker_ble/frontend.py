"""Frontend static assets + Lovelace card registration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN
from .product_art import STATIC_URL_PREFIX

_LOGGER = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"
CARD_JS = "anker-ble-card.js"
CARD_URL = f"{STATIC_URL_PREFIX}/{CARD_JS}"
_DATA_KEY = f"{DOMAIN}_frontend"


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Register /anker_ble_static and the Lovelace card (once)."""
    if hass.data.get(_DATA_KEY):
        return

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(STATIC_URL_PREFIX, str(STATIC_DIR), cache_headers=False),
        ]
    )

    # Load as ES module (es5=False → frontend_extra_module_url).
    add_extra_js_url(hass, CARD_URL)

    async def _register_resource(_now=None) -> None:
        try:
            from homeassistant.components.lovelace.resources import (
                ResourceStorageCollection,
            )

            lovelace = hass.data.get("lovelace")
            if lovelace is None:
                return
            resources = lovelace.get("resources")
            if resources is None or not isinstance(resources, ResourceStorageCollection):
                return
            await resources.async_get_info()
            if any(item.get("url") == CARD_URL for item in resources.async_items()):
                return
            await resources.async_create_item({"res_type": "module", "url": CARD_URL})
            _LOGGER.info("Registered Lovelace resource %s", CARD_URL)
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Could not auto-register Lovelace resource", exc_info=True)

    async_call_later(hass, 5, _register_resource)
    hass.data[_DATA_KEY] = True
    _LOGGER.debug("Anker BLE static path %s → %s", STATIC_URL_PREFIX, STATIC_DIR)
