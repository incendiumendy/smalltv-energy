"""SmallTV Energie - Feed fuer den GeekMagic SmallTV-Ultra."""
from __future__ import annotations

import logging
import secrets

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, VERSION
from .http import SmallTVFeedView

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[str] = []


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    data = dict(entry.data)
    data.setdefault("key", secrets.token_urlsafe(12))
    hass.data[DOMAIN][entry.entry_id] = data
    hass.data[DOMAIN]["_view"] = True

    if not hass.data[DOMAIN].get("_registered"):
        hass.http.register_view(SmallTVFeedView())
        hass.data[DOMAIN]["_registered"] = True

    entry.async_on_unload(entry.add_update_listener(_reload))
    _LOGGER.info(
        "SmallTV Energie %s bereit: http://<ha>:8123/api/smalltv_energy/feed?key=%s",
        VERSION, data["key"],
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
