# Anker BLE (HACS)

Local Bluetooth integration for Anker / Solix devices using the FF09 encrypted session protocol.

## Features

- Bluetooth discovery of FF09 devices
- ECDH confer + AES-CBC session
- Sensors: power / pads, serial, firmware, product
- Binary sensors: online, charging
- Device image entity + MagGo-style Lovelace card (`anker-ble-card`)
- Brand icons in `custom_components/anker_ble/brand/` (HA Devices & services)

## Setup after install

**Settings → Devices & services → Add integration → Anker BLE**

Dashboard: **Add card → Custom: Anker BLE Device** (uses product artwork from the Anker app).

> **HACS icon:** the HACS list may show “icon not available” even though brand assets ship with the integration. That is a [known HACS bug](https://github.com/hacs/integration/issues/5223) on HA 2026.3+. The icon still appears under **Settings → Devices & services** after install.

Requires Home Assistant 2024.1+ with a Bluetooth adapter or BLE proxy.
