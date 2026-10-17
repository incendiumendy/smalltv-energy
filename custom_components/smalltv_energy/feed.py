"""Payload-Bau fuer den SmallTV-Feed (Format der ESP8266-Firmware)."""
from __future__ import annotations

import datetime as dt
import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import HIST_TTL, POINTS, SCALE_STEPS, STATE_TTL

_LOGGER = logging.getLogger(__name__)

_cache: dict[str, tuple[float, dict]] = {}
_debug: dict[str, dict] = {}


def _ck(hours: int) -> str:
    return f"h{hours}"


def _num(state, default=None):
    if state is None:
        return default
    try:
        return float(state.state)
    except (TypeError, ValueError):
        return default


def read_states(hass: HomeAssistant, cfg: dict) -> dict:
    key = "states:" + ",".join(f"{k}={v}" for k, v in sorted(cfg.items()))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < STATE_TTL:
        return hit[1]

    out = {}
    for fld, eid in cfg.items():
        st = hass.states.get(eid) if eid else None
        out[fld] = {
            "v": _num(st),
            "t": st.last_updated.isoformat() if (st and st.last_updated) else "",
        }
    _cache[key] = (time.time(), out)
    return out


def _ts(value) -> float:
    """Zeitstempel aus datetime oder Unix-Float."""
    if isinstance(value, (int, float)):
        return float(value)
    return value.timestamp()


def _stats_sync(hass, start, end, ids):
    """5-Minuten-Mittelwerte aus der Langzeit-Statistik."""
    from homeassistant.components.recorder.statistics import statistics_during_period

    return statistics_during_period(hass, start, end, set(ids), "5minute", None, {"mean"})


def _states_sync(hass, start, end, ids):
    """Rohzustände aus dem Recorder (Fallback)."""
    from homeassistant.components.recorder.history import get_significant_states

    return get_significant_states(hass, start, end, ids, minimal_response=False, no_attributes=True)


async def read_history(hass: HomeAssistant, cfg: dict, hours: int) -> dict:
    """48 Bins ueber das Fenster: PV (DC) und Hausverbrauch (AC + Netz)."""
    key = f"hist:{hours}:" + ",".join(f"{k}={v}" for k, v in sorted(cfg.items()))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < HIST_TTL:
        return hit[1]

    now = dt_util.utcnow()
    start = now - dt.timedelta(hours=hours)
    ids = [i for i in (cfg.get("pv"), cfg.get("pv_ac"), cfg.get("grid")) if i]

    series: dict[str, list[tuple[float, float]]] = {}
    src = "leer"
    try:
        from homeassistant.components.recorder import get_instance

        rec = get_instance(hass)
        raw = await rec.async_add_executor_job(_stats_sync, hass, start, now, ids)
        for eid, rows in (raw or {}).items():
            pts = []
            for row in rows or []:
                mean = row.get("mean")
                if mean is None:
                    continue
                try:
                    pts.append((_ts(row.get("start")), float(mean)))
                except (TypeError, ValueError):
                    continue
            if pts:
                series[eid] = pts
        src = "statistik"
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("SmallTV: Statistik nicht lesbar: %s", err)

    if not any(series.values()):
        try:
            from homeassistant.components.recorder import get_instance

            rec = get_instance(hass)
            raw = await rec.async_add_executor_job(_states_sync, hass, start, now, ids)
            for eid, rows in (raw or {}).items():
                pts = []
                for row in rows or []:
                    try:
                        val = row["state"] if isinstance(row, dict) else row.state
                        lc = row["last_changed"] if isinstance(row, dict) else row.last_changed
                        pts.append((_ts(lc), float(val)))
                    except (TypeError, ValueError, KeyError, AttributeError):
                        continue
                if pts:
                    series[eid] = pts
            src = "recorder"
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("SmallTV: Recorder-Historie nicht lesbar: %s", err)

    pv_s = series.get(cfg.get("pv") or "", [])
    ac_s = series.get(cfg.get("pv_ac") or "", [])
    gr_s = series.get(cfg.get("grid") or "", [])

    def sample(pts, t):
        last = None
        for ts, val in pts:
            if ts <= t:
                last = val
            else:
                break
        return last

    step = hours * 3600 / POINTS
    t0 = now.timestamp() - hours * 3600
    pv_out, house_out = [], []
    for i in range(POINTS):
        probes = [t0 + i * step + step * k / 4 for k in range(5)]
        sp = [v for v in (sample(pv_s, t) for t in probes) if v is not None]
        sh = []
        for t in probes:
            a, g = sample(ac_s, t), sample(gr_s, t)
            if a is not None:
                sh.append(max(0.0, a + (g or 0.0)))
        pv_out.append(round(sum(sp) / len(sp)) if sp else 0)
        house_out.append(round(sum(sh) / len(sh)) if sh else 0)

    peak = max(pv_out + house_out + [1000])
    scale = 40000
    for limit in SCALE_STEPS:
        if peak <= limit * 0.92:
            scale = limit
            break

    label_step = 6 if hours >= 12 else (3 if hours >= 6 else 1)
    labels = [dt_util.as_local(start + dt.timedelta(hours=h)).strftime("%H")
              for h in range(0, hours + 1, label_step)]
    if len(labels) > 9:
        labels = labels[::2]

    _debug[key] = {
        "quelle": src,
        "punkte": {k: len(v) for k, v in series.items()},
        "erster": {k: (dt_util.as_local(dt.datetime.fromtimestamp(v[0][0], dt.timezone.utc)).isoformat()
                       if v else None) for k, v in series.items()},
        "letzter": {k: (dt_util.as_local(dt.datetime.fromtimestamp(v[-1][0], dt.timezone.utc)).isoformat()
                        if v else None) for k, v in series.items()},
        "distinct_pv": len(set(pv_out)),
    }

    result = {"pv": pv_out, "house": house_out, "scale": scale, "labels": labels}
    _cache[key] = (time.time(), result)
    return result


async def build_payload(hass: HomeAssistant, cfg: dict, hours: int = 24, debug: bool = False) -> dict:
    st = read_states(hass, cfg)
    hist = await read_history(hass, cfg, hours)

    def val(k, default=0.0):
        v = st.get(k, {}).get("v")
        return default if v is None else v

    i3_age = ""
    i3_t = st.get("i3", {}).get("t", "")
    if i3_t:
        try:
            ts = dt.datetime.fromisoformat(i3_t)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.timezone.utc)
            age = (dt_util.utcnow() - ts).total_seconds()
            i3_age = f"{age/3600:.0f}h" if age >= 3600 else f"{age/60:.0f}m"
        except Exception:
            i3_age = ""

    payload = {
        "now": dt_util.as_local(dt_util.utcnow()).strftime("%H:%M"),
        "pv": round(val("pv")),
        "house": round(val("pv_ac") + val("grid")),
        "grid": round(val("grid")),
        "soc": round(val("soc")),
        "batt": round(val("batt")),
        "today": round(val("today") * 10) / 10.0,
        "pool": round(val("pool") * 10) / 10.0,
        "out": round(val("out") * 10) / 10.0,
        "hum": round(val("hum")),
        "i3": round(val("i3")),
        "i3age": i3_age,
        "w": int(hours),
        "hist": hist,
        "stale": [k for k, v in st.items() if v.get("v") is None],
    }
    if debug:
        payload["debug"] = _debug.get(f"hist:{hours}:" + ",".join(f"{k}={v}" for k, v in sorted(cfg.items())), {})
    return payload
