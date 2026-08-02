# Anker BLE

Unofficial reverse-engineering of Anker / Solix Bluetooth (FF09 ZX protocol), plus clients:

| Piece | Path | Purpose |
|-------|------|---------|
| Protocol docs | [`docs/`](docs/) | Frames, GATT, ECDH/AES, TLV |
| Python PoC | [`poc/`](poc/) | Scan, connect, confer, telemetry CLI |
| Web Bluetooth | [`web/`](web/) | Browser-only Chrome/Edge client |
| Home Assistant | [`custom_components/anker_ble/`](custom_components/anker_ble/) | HACS custom integration |

Derived from Anker app `com.anker.charging` **3.22.0**. Not affiliated with Anker Innovations.

## Protocol (short)

- Discovery UUID: `0000ff09-0000-1000-8000-00805f9b34fb`
- Wire format: header `FF09`, LE length, 3-byte pattern, 2-byte cmd, payload, XOR checksum
- Default GATT family **8C85**: service `…0001`, write `…0002`, notify `…0003`
- Session: ECDH P-256 → AES-128-CBC (key = secret\[0:16\], IV = secret\[16:32\])

Full write-up: [docs/bluetooth-protocol.md](docs/bluetooth-protocol.md)

Verified live against MagGo-style “Charging” hardware (serial `ASHDJVV1F52301602`, family `8C85`).

---

## Home Assistant (HACS)

Local Bluetooth polling: discover FF09 devices, negotiate an encrypted session, expose power / identity sensors.

### Install with HACS

1. **HACS → Integrations → ⋮ → Custom repositories**
2. Add this repo URL as category **Integration**
3. Install **Anker BLE**, restart Home Assistant
4. **Settings → Devices & services → Add integration → Anker BLE**

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=T-REX-XP&repository=Anker-BLE&category=integration)

### Manual install

```bash
cp -a custom_components/anker_ble /config/custom_components/
```

Restart Home Assistant, then add **Anker BLE**.

### Requirements

- Home Assistant **2024.1+** with Bluetooth (local adapter or BLE proxy)
- Device advertising `0000ff09-…`

### Entities

| Entity | Notes |
|--------|--------|
| Product / Firmware / Serial | From confer identity |
| Power out, Pad 1–3 power | MagGo-style TLV when present |
| Battery % | Power stations (`bb`) |
| Online / Charging | Binary sensors |

Details: [custom_components/anker_ble/README.md](custom_components/anker_ble/README.md)

### Dashboard widget

After install, add the **Anker BLE Device** card (product art from the official app):

```yaml
type: custom:anker-ble-card
entity: sensor.YOUR_DEVICE_power_out
```

More: [custom_components/anker_ble/lovelace.md](custom_components/anker_ble/lovelace.md)

---

## Python PoC

```bash
cd poc
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Discover
python find_and_connect.py scan --timeout 10

# Connect + confer + listen
python find_and_connect.py connect --first --confer --listen 15 -v
```

Bring the adapter up first (`rfkill unblock bluetooth`, `hciconfig hciX up`).  
More: [poc/README.md](poc/README.md)

---

## Web Bluetooth client

Chrome / Edge only. Prefer the hosted GitHub Pages build (HTTPS + Web Bluetooth):

**[https://t-rex-xp.github.io/Anker-BLE/](https://t-rex-xp.github.io/Anker-BLE/)**

Locally:

```bash
cd web
./serve.sh          # Windows: serve.bat
# → http://127.0.0.1:8765/
```

**Do not open `index.html` via `file://`** — Chrome blocks scripts and Web Bluetooth.

Scan & connect → automatic confer → telemetry subscribe.  
More: [web/README.md](web/README.md)

---

## Releases & GitHub Pages

### One-time repo setup

1. **Settings → Pages → Build and deployment → Source: GitHub Actions**  
   (Already enabled for this repo; URL: https://t-rex-xp.github.io/Anker-BLE/)
2. Ensure Actions are allowed to write (default fine for public repos)

### Cut a release

1. Bump `version` in [`custom_components/anker_ble/manifest.json`](custom_components/anker_ble/manifest.json) (must match the tag)
2. Commit, then tag and push:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The [Release](.github/workflows/release.yml) workflow will:

- Run hassfest + HACS validation
- Attach `anker_ble-<ver>.zip` and `anker-ble-web-<ver>.zip` to a GitHub Release
- Deploy [`web/index.html`](web/index.html) to GitHub Pages

Manual Pages-only deploy: **Actions → Release → Run workflow** (leave tag empty), or push to `main`/`master` changing `web/` ([Pages](.github/workflows/pages.yml)).

---

## Documentation index

| Doc | Contents |
|-----|----------|
| [docs/bluetooth-protocol.md](docs/bluetooth-protocol.md) | Frame format, confer, crypto, TLV |
| [docs/bluetooth-gatt-uuids.md](docs/bluetooth-gatt-uuids.md) | Discovery & GATT UUIDs |
| [docs/bluetooth-devices.md](docs/bluetooth-devices.md) | SKU → BLE modules |
| [docs/bluetooth-source-map.md](docs/bluetooth-source-map.md) | Where symbols live in the APKS |
| [docs/README.md](docs/README.md) | Docs overview |

## Disclaimer

Unofficial research and tooling. Use at your own risk; keep the official Anker app disconnected while testing BLE on the same host.
