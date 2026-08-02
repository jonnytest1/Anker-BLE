"""Sensor platform for Anker BLE."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ADDRESS, CONF_NAME, DOMAIN, MANUFACTURER
from .coordinator import AnkerBleCoordinator

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="power_out_w",
        translation_key="power_out",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="pad_1_power_w",
        translation_key="pad_1_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="pad_2_power_w",
        translation_key="pad_2_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="pad_3_power_w",
        translation_key="pad_3_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_percent",
        translation_key="battery",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AnkerBleCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        AnkerBleParsedSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    entities.extend(
        [
            AnkerBleIdentitySensor(coordinator, entry, "serial", "serial"),
            AnkerBleIdentitySensor(coordinator, entry, "firmware", "firmware"),
            AnkerBleIdentitySensor(coordinator, entry, "product_name", "product_name"),
            AnkerBleInfoSensor(coordinator, entry, "telemetry_cmd", "telemetry_cmd"),
        ]
    )
    async_add_entities(entities)


class AnkerBleEntity(CoordinatorEntity[AnkerBleCoordinator]):
    """Shared device info."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AnkerBleCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        address = entry.data[CONF_ADDRESS]
        name = entry.data.get(CONF_NAME) or address
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer=MANUFACTURER,
            model=None,
            connections={("mac", address)},
        )

    @property
    def device_info(self) -> DeviceInfo:
        identity = self._identity()
        return DeviceInfo(
            identifiers={(DOMAIN, self._address)},
            name=self._entry.data.get(CONF_NAME) or self._address,
            manufacturer=MANUFACTURER,
            model=identity.get("product_name"),
            sw_version=identity.get("firmware"),
            serial_number=identity.get("serial"),
            connections={("mac", self._address)},
        )

    def _identity(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return data.get("identity") or {}


class AnkerBleParsedSensor(AnkerBleEntity, SensorEntity):
    """Sensor backed by parsed telemetry dict."""

    def __init__(
        self,
        coordinator: AnkerBleCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.data[CONF_ADDRESS]}_{description.key}"

    @property
    def native_value(self) -> float | int | None:
        parsed = (self.coordinator.data or {}).get("parsed") or {}
        return parsed.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None


class AnkerBleIdentitySensor(AnkerBleEntity, SensorEntity):
    def __init__(
        self,
        coordinator: AnkerBleCoordinator,
        entry: ConfigEntry,
        key: str,
        translation_key: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.data[CONF_ADDRESS]}_{key}"

    @property
    def native_value(self) -> str | None:
        return self._identity().get(self._key)

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None


class AnkerBleInfoSensor(AnkerBleEntity, SensorEntity):
    def __init__(
        self,
        coordinator: AnkerBleCoordinator,
        entry: ConfigEntry,
        key: str,
        translation_key: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.data[CONF_ADDRESS]}_{key}"
        self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> Any:
        return (self.coordinator.data or {}).get(self._key)
