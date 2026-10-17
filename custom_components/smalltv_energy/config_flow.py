"""Config- und Options-Flow fuer SmallTV Energie."""
from __future__ import annotations

import secrets
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN, FIELDS


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    fields: dict[Any, Any] = {}
    for key, (label, default_entity) in FIELDS.items():
        fields[vol.Optional(key, default=defaults.get(key, default_entity))] = (
            selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
        )
    fields[vol.Optional("key", default=defaults.get("key", ""))] = (
        selector.TextSelector(selector.TextSelectorConfig(type="password"))
    )
    return vol.Schema(fields)


class SmallTVEnergyFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            data = {k: v for k, v in user_input.items() if v}
            data["key"] = data.get("key") or secrets.token_urlsafe(12)
            return self.async_create_entry(title="SmallTV Energie", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(),
            description_placeholders={"hint": "key = Passwort im Feed-Link (leer = automatisch)"},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SmallTVOptionsFlow()


class SmallTVOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        entry = self.config_entry
        if user_input is not None:
            data = dict(entry.data)
            data.update({k: v for k, v in user_input.items() if v})
            if not data.get("key"):
                data["key"] = entry.data.get("key") or secrets.token_urlsafe(12)
            self.hass.config_entries.async_update_entry(entry, data=data)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="init", data_schema=_schema(dict(entry.data)))
