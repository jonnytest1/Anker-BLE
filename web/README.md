# Anker BLE — Web Bluetooth client

Browser client with the same device widget as the Home Assistant card: product art,
total power, **Port 1–3**, online / charging / battery chips, identity.

Aimed at chargers such as the **Anker Prime Charger 160W (A2687)** as well as MagGo / Solix FF09 devices.

## Hosted (GitHub Pages)

**[https://t-rex-xp.github.io/Anker-BLE/](https://t-rex-xp.github.io/Anker-BLE/)**

HTTPS is required for Web Bluetooth on non-localhost origins.

## Do not open `index.html` as a file

Chrome blocks scripts and **Web Bluetooth** under `file://`.  
Serve over HTTP instead (or use the Pages URL above).

## Run (Windows)

1. Copy this `web` folder wherever you like
2. Double-click **`serve.bat`** (or in that folder: `python -m http.server 8765`)
3. Open **[http://127.0.0.1:8765/](http://127.0.0.1:8765/)** in Chrome or Edge

## Run (macOS / Linux)

```bash
cd web
./serve.sh
# or: python3 -m http.server 8765 --bind 127.0.0.1
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/)

## Features (parity with HA card)

| Feature | Notes |
|---------|--------|
| Product hero image | Synced from `assets/images/product/` (A2687, A110x, Solix, …) |
| Power out | Large watt readout |
| Port 1–3 | USB-C / output power from TLV |
| Status chips | Online, charging, battery %, session |
| Identity | Product, firmware, serial, MAC |
| Refresh telemetry | Re-sends subscribe `0x4200` |

## Requirements

- Chrome or Edge (desktop or Android)
- `http://localhost…` or HTTPS
- Device nearby and advertising

## Files

| File | Role |
|------|------|
| `index.html` | UI + protocol |
| `images/` | **Synced** from `assets/images/product/` — do not edit by hand |
| `serve.bat` / `serve.sh` | Local static server |

After changing artwork in the repo root:

```bash
python3 scripts/sync_images.py
```
