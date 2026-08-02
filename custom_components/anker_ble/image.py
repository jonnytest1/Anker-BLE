"""Image entities serving Anker product artwork."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_ADDRESS, DOMAIN
from .coordinator import AnkerBleCoordinator
from .product_art import art_for_identity, static_image_url
from .sensor import AnkerBleEntity

STATIC_IMAGES = Path(__file__).parent / "static" / "images"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AnkerBleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AnkerBleDeviceImage(hass, coordinator, entry)])


class AnkerBleDeviceImage(AnkerBleEntity, ImageEntity):
    """Product photo from the Anker app asset pack."""

    _attr_translation_key = "device_image"
    _attr_content_type = "image/png"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: AnkerBleCoordinator,
        entry: ConfigEntry,
    ) -> None:
        AnkerBleEntity.__init__(self, coordinator, entry)
        ImageEntity.__init__(self, hass)
        self._attr_unique_id = f"{entry.data[CONF_ADDRESS]}_device_image"
        self._cached_key: str | None = None
        self._cached_bytes: bytes | None = None
        self._load_bytes()

    def _art(self):
        identity = self._identity()
        return art_for_identity(
            identity.get("product_name"),
            identity.get("serial"),
            identity.get("product_name"),
        )

    def _load_bytes(self) -> None:
        art = self._art()
        if art.key == self._cached_key and self._cached_bytes is not None:
            return
        path = STATIC_IMAGES / art.hero
        self._cached_key = art.key
        self._cached_bytes = path.read_bytes() if path.is_file() else None
        self._attr_image_last_updated = dt_util.utcnow()

    async def async_image(self) -> bytes | None:
        self._load_bytes()
        return self._cached_bytes

    @property
    def entity_picture(self) -> str | None:
        """Static URL so dashboards can use the art without image-proxy tokens."""
        return static_image_url(self._art().hero)

    def _handle_coordinator_update(self) -> None:
        self._load_bytes()
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        # Static product art — always show even when the charger is offline.
        return True
