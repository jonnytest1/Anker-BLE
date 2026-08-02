# Anker BLE

Unofficial reverse-engineering of Anker / Solix Bluetooth (FF09 ZX protocol), plus clients:

| Piece | Path | Purpose |
|-------|------|---------|
| Protocol docs | [`docs/`](docs/) | Frames, GATT, ECDH/AES, TLV |
| Shared images | [`assets/images/`](assets/images/) | Product + brand art (source of truth) |
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

Verified live against **Anker Prime Charger 160W (A2687)** — serial `ASHDJVV1F52301602`, GATT `8C85`.

Full device catalog: [docs/bluetooth-devices.md](docs/bluetooth-devices.md)

## Images

Product and brand artwork live in [`assets/images/`](assets/images/). After changing files there:

```bash
python3 scripts/sync_images.py          # copy into web/ + custom_components/
python3 scripts/sync_images.py --check  # CI drift check
```

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
| Power out, Port 1–3 power | Prime charger / MagGo TLV (USB-C ports) |
| Battery % | Power banks / stations (`bb`) when present |
| Online / Charging | Binary sensors |

Details: [custom_components/anker_ble/README.md](custom_components/anker_ble/README.md)

### Dashboard widget

After install, add the **Anker BLE Device** card (product art from the official app):

```yaml
type: custom:anker-ble-card
entity: sensor.YOUR_DEVICE_power_out
```

More: [custom_components/anker_ble/lovelace.md](custom_components/anker_ble/lovelace.md)

Brand icons live in [`assets/images/brand/`](assets/images/brand/) (synced into the integration). The HACS downloads row may still show “icon not available” because of a [HACS frontend bug](https://github.com/hacs/integration/issues/5223) (CDN vs local brands proxy on HA 2026.3+).

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
git tag v0.2.2
git push origin v0.2.2
```

The [Release](.github/workflows/release.yml) workflow will:

- Sync images from `assets/` and run hassfest + HACS validation
- Attach `anker_ble-<ver>.zip` and `anker-ble-web-<ver>.zip` to a GitHub Release
- Deploy the web client (with synced images) to GitHub Pages

Manual Pages-only deploy: **Actions → Release → Run workflow** (leave tag empty), or push to `main`/`master` changing `web/` or `assets/` ([Pages](.github/workflows/pages.yml)).

---

## Documentation index

| Doc | Contents |
|-----|----------|
| [docs/bluetooth-protocol.md](docs/bluetooth-protocol.md) | Frame format, confer, crypto, TLV |
| [docs/bluetooth-gatt-uuids.md](docs/bluetooth-gatt-uuids.md) | Discovery & GATT UUIDs |
| [docs/bluetooth-devices.md](docs/bluetooth-devices.md) | Device catalog (A2687, banks, Solix, …) |
| [docs/bluetooth-source-map.md](docs/bluetooth-source-map.md) | Where symbols live in the APKS |
| [docs/README.md](docs/README.md) | Docs overview |
| [assets/README.md](assets/README.md) | Central images + sync |

## Disclaimer

Unofficial research and tooling. Use at your own risk; keep the official Anker app disconnected while testing BLE on the same host.
