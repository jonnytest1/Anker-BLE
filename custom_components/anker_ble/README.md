# Home Assistant — Anker BLE custom integration

Local-polling integration for Anker / Solix BLE devices using the FF09 ZX protocol
(confer → AES-CBC session → telemetry subscribe).

## Install with HACS

1. **HACS → Integrations → Custom repositories**
2. Add your GitHub repo URL, category **Integration**
3. Download **Anker BLE**, restart Home Assistant
4. **Settings → Devices & services → Add integration → Anker BLE**

See the [root README](../../README.md) for the My Home Assistant badge template.

## Manual install

```bash
cp -a custom_components/anker_ble /config/custom_components/anker_ble
```

Restart Home Assistant. Requirements (`pycryptodome`, `cryptography`) are declared in `manifest.json` and installed by HA on first load. Bluetooth must be enabled.

## Setup

1. **Settings → Devices & services → Add integration → Anker BLE**
2. Pick a discovered FF09 device, or enter its MAC address
3. Entities appear under the device (power pads, serial, firmware, online, …)

Bluetooth discovery also prompts automatically when an FF09 advert is seen.

## Behaviour

Every poll interval (default **120 s**):

1. BLE connect  
2. ECDH confer  
3. Telemetry subscribe (`0x4200`)  
4. Listen briefly for encrypted session frames  
5. Disconnect  

Options (integration → Configure): poll interval and listen window.

## Entities

| Entity | Source |
|--------|--------|
| Serial / Firmware / Product | Confer identity (stage `0829`) |
| Power out / Pad 1–3 power | Parsed TLV (when present) |
| Battery % | TLV `bb` (power stations) |
| Online | Last poll succeeded |
| Charging | Derived from status TLV when available |

## Notes

- Verified against MagGo-style `Charging` devices (`8C85` GATT, Solix CBC confer).
- Power-station AC/DC switches are not exposed yet (sensors-first).
- Keep the host Bluetooth adapter free; overlapping connections from the phone app will contend.
