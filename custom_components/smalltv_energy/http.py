"""Oeffentlicher HTTP-Endpunkt fuer das SmallTV (LAN, ohne Token)."""
from __future__ import annotations

import json
import logging

from aiohttp import web
from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN
from .feed import build_payload

_LOGGER = logging.getLogger(__name__)


class SmallTVFeedView(HomeAssistantView):
    url = "/api/smalltv_energy/feed"
    name = "api:smalltv_energy:feed"
    requires_auth = False
    cors_allowed = True

    async def get(self, request: web.Request) -> web.Response:
        hass = request.app["hass"]
        entries = hass.data.get(DOMAIN, {})
        wants = request.query.get("entry")

        match = None
        for eid, data in entries.items():
            if not isinstance(data, dict) or "entities" not in data:
                continue
            if wants and eid != wants:
                continue
            if request.query.get("key") == data.get("key"):
                match = data
                break

        if match is None:
            return web.Response(status=403, text="forbidden", content_type="text/plain")

        hours = 24
        try:
            hours = max(1, min(48, int(float(request.query.get("w", "24").rstrip("h")))))
        except ValueError:
            pass

        try:
            payload = await build_payload(hass, match["entities"], hours)
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("SmallTV: Payload-Fehler")
            return web.json_response({"error": str(err)[:160]}, status=500)

        return web.json_response(payload)
