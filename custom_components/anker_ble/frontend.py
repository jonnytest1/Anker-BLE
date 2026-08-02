"""Frontend static assets + Lovelace card registration."""

from __future__ import annotations

import json
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
_DATA_KEY = f"{DOMAIN}_frontend"


def _card_version() -> str:
    try:
        manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
        return str(manifest.get("version", "0"))
    except Exception:  # noqa: BLE001
        return "0"


def card_url() -> str:
    return f"{STATIC_URL_PREFIX}/{CARD_JS}?v={_card_version()}"


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Register /anker_ble_static and the Lovelace card (once)."""
    if hass.data.get(_DATA_KEY):
        return

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(STATIC_URL_PREFIX, str(STATIC_DIR), cache_headers=False),
        ]
    )

    url = card_url()
    # Load as ES module (es5=False → frontend_extra_module_url).
    add_extra_js_url(hass, url)

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
            existing = [
                item
                for item in resources.async_items()
                if str(item.get("url", "")).startswith(f"{STATIC_URL_PREFIX}/{CARD_JS}")
            ]
            if existing:
                # Refresh URL to bust browser cache after upgrades.
                item = existing[0]
                if item.get("url") != url:
                    await resources.async_update_item(item["id"], {"url": url})
                return
            await resources.async_create_item({"res_type": "module", "url": url})
            _LOGGER.info("Registered Lovelace resource %s", url)
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Could not auto-register Lovelace resource", exc_info=True)

    async_call_later(hass, 5, _register_resource)
    hass.data[_DATA_KEY] = True
    _LOGGER.debug("Anker BLE static path %s → %s", STATIC_URL_PREFIX, STATIC_DIR)
