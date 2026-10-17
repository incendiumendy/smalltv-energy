"""Oeffentlicher HTTP-Endpunkt fuer das SmallTV (LAN, ohne Token)."""
from __future__ import annotations

import logging

from aiohttp import web
from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN, FIELDS
from .feed import build_payload

_LOGGER = logging.getLogger(__name__)


class SmallTVFeedView(HomeAssistantView):
    """Liefert das JSON, das die ESP8266-Firmware erwartet."""

    url = "/api/smalltv_energy/feed"
    name = "api:smalltv_energy:feed"
    requires_auth = False
    cors_allowed = True

    async def get(self, request: web.Request) -> web.Response:
        hass = request.app["hass"]
        store = hass.data.get(DOMAIN, {})
        want_entry = request.query.get("entry")
        got_key = request.query.get("key", "")

        match = None
        for entry_id, data in store.items():
            if not isinstance(data, dict):
                continue
            if "key" not in data:
                continue
            if want_entry and entry_id != want_entry:
                continue
            if got_key and got_key == data["key"]:
                match = data
                break

        if match is None:
            return web.Response(status=403, text="forbidden", content_type="text/plain")

        entities = {k: v for k, v in match.items() if k in FIELDS and v}

        hours = 24
        try:
            hours = max(1, min(48, int(float(request.query.get("w", "24").rstrip("h")))))
        except ValueError:
            pass

        try:
            payload = await build_payload(hass, entities, hours)
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("SmallTV: Payload-Fehler")
            return web.json_response({"error": str(err)[:160]}, status=500)

        return web.json_response(payload)
