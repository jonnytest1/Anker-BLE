"""Config flow for Anker BLE."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.device_registry import format_mac

from .const import (
    CONF_ADDRESS,
    CONF_LISTEN_SECONDS,
    CONF_NAME,
    CONF_POLL_INTERVAL,
    DEFAULT_LISTEN_SECONDS,
    DEFAULT_NAME,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)
from .protocol.uuids import EXTRA_IDENTIFIER_UUIDS, UUID_FAMILIES, normalize_uuid

_DISCOVERY_INFO: dict[str, BluetoothServiceInfoBleak] = {}


def _is_supported(discovery_info: BluetoothServiceInfoBleak) -> bool:
    uuids = {normalize_uuid(u) for u in discovery_info.service_uuids}
    id_set = {normalize_uuid(u) for u in EXTRA_IDENTIFIER_UUIDS}
    if uuids & id_set:
        return True
    for family in UUID_FAMILIES.values():
        if normalize_uuid(family["service"]) in uuids:
            return True
    name = (discovery_info.name or "").lower()
    return any(h in name for h in ("anker", "solix", "ashd", "a17", "a25"))


class AnkerBleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle Anker BLE config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovery: BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        if not _is_supported(discovery_info):
            return self.async_abort(reason="not_supported")

        address = format_mac(discovery_info.address)
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        _DISCOVERY_INFO[address] = discovery_info
        self._discovery = discovery_info
        self.context["title_placeholders"] = {
            "name": discovery_info.name or address,
            "address": address,
        }
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._discovery is not None
        address = format_mac(self._discovery.address)
        title = self._discovery.name or address

        if user_input is not None:
            return self.async_create_entry(
                title=title,
                data={
                    CONF_ADDRESS: address,
                    CONF_NAME: title,
                    CONF_POLL_INTERVAL: DEFAULT_POLL_INTERVAL,
                    CONF_LISTEN_SECONDS: DEFAULT_LISTEN_SECONDS,
                },
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": title, "address": address},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        current = {
            format_mac(entry.unique_id)
            for entry in self._async_current_entries()
            if entry.unique_id
        }

        discovered: dict[str, BluetoothServiceInfoBleak] = {
            format_mac(info.address): info
            for info in bluetooth.async_discovered_service_info(
                self.hass, connectable=True
            )
            if _is_supported(info) and format_mac(info.address) not in current
        }
        for addr, info in _DISCOVERY_INFO.items():
            if addr not in current:
                discovered.setdefault(addr, info)

        if user_input is not None:
            address = format_mac(user_input[CONF_ADDRESS])
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            info = discovered.get(address)
            title = (info.name if info else None) or user_input.get(CONF_NAME) or address
            return self.async_create_entry(
                title=title,
                data={
                    CONF_ADDRESS: address,
                    CONF_NAME: title,
                    CONF_POLL_INTERVAL: user_input.get(
                        CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
                    ),
                    CONF_LISTEN_SECONDS: user_input.get(
                        CONF_LISTEN_SECONDS, DEFAULT_LISTEN_SECONDS
                    ),
                },
            )

        if not discovered:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_ADDRESS): str,
                        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                        vol.Optional(
                            CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL
                        ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                        vol.Optional(
                            CONF_LISTEN_SECONDS, default=DEFAULT_LISTEN_SECONDS
                        ): vol.All(vol.Coerce(float), vol.Range(min=2, max=60)),
                    }
                ),
                errors=errors,
            )

        addresses = {
            addr: f"{info.name or 'Anker'} ({addr})"
            for addr, info in sorted(
                discovered.items(),
                key=lambda item: item[1].rssi if item[1].rssi is not None else -999,
                reverse=True,
            )
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(addresses),
                    vol.Optional(
                        CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                    vol.Optional(
                        CONF_LISTEN_SECONDS, default=DEFAULT_LISTEN_SECONDS
                    ): vol.All(vol.Coerce(float), vol.Range(min=2, max=60)),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Any) -> AnkerBleOptionsFlow:
        return AnkerBleOptionsFlow()


class AnkerBleOptionsFlow(OptionsFlow):
    """Options for poll interval / listen window."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_POLL_INTERVAL,
                        default=data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                    vol.Optional(
                        CONF_LISTEN_SECONDS,
                        default=data.get(CONF_LISTEN_SECONDS, DEFAULT_LISTEN_SECONDS),
                    ): vol.All(vol.Coerce(float), vol.Range(min=2, max=60)),
                }
            ),
        )
