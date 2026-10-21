"""Konstanten fuer die SmallTV-Energie-Integration."""

DOMAIN = "smalltv_energy"
VERSION = "1.0.0"

# Feld -> (Label, Standard-Entity)
FIELDS = {
    "pv":     ("PV-Leistung (DC)",            "sensor.wechselrichter_eingangsleistung"),
    "pv_ac":  ("Wechselrichter AC-Leistung",  "sensor.wechselrichter_wirkleistung"),
    "grid":   ("Netzleistung (Zaehler)",      "sensor.stromzahler_wirkleistung"),
    "soc":    ("Batterie-Ladestand",          "sensor.batterien_batterieladung"),
    "batt":   ("Batterie-Leistung",           "sensor.batterien_lade_entladeleistung"),
    "today":  ("Tagesertrag",                 "sensor.wechselrichter_tagesertrag"),
    "pool":   ("Pooltemperatur",              "sensor.wetter_station_fuhlertemperatur_kanal_2"),
    "out":    ("Aussentemperatur",            "sensor.wetter_station_fuhler_temperatur"),
    "hum":    ("Aussenluftfeuchte",           "sensor.wetter_station_aussenluftfeuchtigkeit"),
    "i3":     ("i3 Ladestand",                "sensor.i3_94_battery_ev_state_of_charge"),
}

POINTS = 96          # Stuetzpunkte im Verlauf (15 min bei 24 h)
HIST_TTL = 50.0      # Sekunden Cache fuer die Historie
STATE_TTL = 15.0     # Sekunden Cache fuer die Momentanwerte
SCALE_STEPS = (4000, 6000, 8000, 10000, 13000)   # Obergrenze 13 kW
