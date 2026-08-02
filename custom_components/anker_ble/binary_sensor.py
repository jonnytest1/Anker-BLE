"""Binary sensors for Anker BLE."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ADDRESS, DOMAIN
from .coordinator import AnkerBleCoordinator
from .sensor import AnkerBleEntity

BINARY_SENSORS = (
    BinarySensorEntityDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AnkerBleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AnkerBleBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class AnkerBleBinarySensor(AnkerBleEntity, BinarySensorEntity):
    def __init__(
        self,
        coordinator: AnkerBleCoordinator,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.data[CONF_ADDRESS]}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        key = self.entity_description.key
        if key == "online":
            return bool(data.get("online"))
        parsed = data.get("parsed") or {}
        value = parsed.get(key)
        if value is None:
            return None
        return bool(value)
