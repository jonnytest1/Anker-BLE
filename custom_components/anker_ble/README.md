# Home Assistant — Anker BLE custom integration

Local-polling integration for Anker BLE devices (Prime chargers, MagGo / banks, Solix)
using the FF09 ZX protocol: confer → AES-CBC session → telemetry subscribe.

**Verified:** Anker Prime Charger **160W / 3 ports / smart display (A2687)**.

## Install with HACS

1. **HACS → Integrations → Custom repositories**
2. Add `https://github.com/T-REX-XP/Anker-BLE`, category **Integration**
3. Download **Anker BLE**, restart Home Assistant
4. **Settings → Devices & services → Add integration → Anker BLE**

See the [root README](../../README.md) for the My Home Assistant badge.

## Manual install

```bash
cp -a custom_components/anker_ble /config/custom_components/anker_ble
```

Restart Home Assistant. Requirements (`bleak-retry-connector`, `pycryptodome`, `cryptography`) are declared in `manifest.json`. Bluetooth must be enabled.

## Setup

1. **Settings → Devices & services → Add integration → Anker BLE**
2. Pick a discovered FF09 device, or enter its MAC address
3. Entities appear under the device (port power, serial, firmware, online, …)

Bluetooth discovery also prompts automatically when an FF09 advert is seen.

Close the official Anker phone app while HA is polling — it holds the BLE link.

## Behaviour

Every poll interval (default **120 s**):

1. Resolve device via HA’s Bluetooth scanner (wait for advertisement if needed)
2. Connect with `bleak-retry-connector`
3. ECDH confer
4. Telemetry subscribe (`0x4200`)
5. Listen briefly for encrypted session frames
6. Disconnect

Options (integration → Configure): poll interval and listen window.

## Entities

| Entity | Source |
|--------|--------|
| Serial / Firmware / Product | Confer identity (stage `0829`) |
| Power out / Port 1–3 power | Parsed TLV (USB-C ports on A2687) |
| Battery % | TLV `bb` when present (banks / stations) |
| Online | Last poll succeeded |
| Charging | Derived from status TLV when available |
| Device image | Product photo from synced app assets |

## Dashboard card (widget)

```yaml
type: custom:anker-ble-card
entity: sensor.YOUR_DEVICE_power_out
```

See [lovelace.md](lovelace.md). Product art is synced from [`assets/images/`](../../assets/images/).

## Images / brand

Do not edit `static/images/` or `brand/` by hand. Update [`assets/images/`](../../assets/images/) then:

```bash
python3 scripts/sync_images.py
```

## Notes

- Charger-first: sensors are **port power** (USB-C1–C3); battery is optional
- Power-station AC/DC switches are not exposed yet
- Device catalog: [docs/bluetooth-devices.md](../../docs/bluetooth-devices.md)

## Troubleshooting

**“never seen by any scanner” / connection slot errors**

1. Keep the device powered and within range of HA’s Bluetooth adapter or an ESPHome BLE proxy
2. Close the official Anker app
3. Wait for HA to see a fresh advertisement, then **Retry** the config entry
4. v0.2.1+ uses HA’s scanner + `bleak-retry-connector` (not a raw MAC-only connect)

**HACS “icon not available”**

Known [HACS frontend bug](https://github.com/hacs/integration/issues/5223) on HA 2026.3+. Icons still show under **Settings → Devices & services**.
