# SmallTV Energie

Home-Assistant-Custom-Integration, die die Daten fuer das **GeekMagic SmallTV-Ultra**
Energiedisplay (ESP8266, 240x240) bereitstellt — konfigurierbar ueber die HA-Oberflaeche.

Ersetzt einen eigenstaendigen Feed-Container: die Integration liest die Entities direkt
aus Home Assistant, holt die 24-h-Historie aus der Recorder-Statistik und liefert alles
unter einem eigenen HTTP-Endpunkt im Format der Firmware.

## Installation (HACS)

1. HACS -> Integrationen -> drei Punkte -> **Benutzerdefinierte Repositories**
2. `incendiumendy/smalltv-energy` als Kategorie **Integration** hinzufuegen
3. Installieren, Home Assistant neu starten
4. Einstellungen -> Geraete & Dienste -> **Integration hinzufuegen** -> "SmallTV Energie"
5. Entities auswaehlen (PV, Wechselrichter AC, Netz, Batterie-SoC/-Leistung, Tagesertrag,
   Pool, Aussentemperatur, Aussenfeuchte, i3-Ladestand) und optional ein **Feed-Passwort** setzen

## Feed-URL

```
http://<home-assistant>:8123/api/smalltv_energy/feed?key=<passwort>&w=24
```

- `w` = 3, 6, 12 oder 24 (Stunden) — die Firmware haengt es selbst an.
- Ohne passenden `key` antwortet der Endpunkt mit HTTP 403.
- `&debug=1` liefert zusaetzlich Diagnose (Datenquelle, Punktzahl, Zeitstempel).

## Payload

`now, pv, house, grid, soc, batt, today, pool, out, hum, i3, i3age, w, stale` und
`hist: {pv[48], house[48], scale, labels[]}` — Leistungen in Watt, Temperaturen in °C.

- `pv` = DC-Eingangsleistung, `house` = Wechselrichter-AC + Netzleistung
- `grid` positiv = Bezug, negativ = Einspeisung
- `hist` = 48 Stuetzpunkte aus 5-Minuten-Mittelwerten (Fallback: Recorder-Rohzustaende)

## Voraussetzungen

- Home Assistant 2024.6 oder neuer, Recorder aktiv
- Die gewaehlten Sensoren sollten `state_class: measurement` haben (fuer die Statistik-Historie)

## Lizenz

MIT
