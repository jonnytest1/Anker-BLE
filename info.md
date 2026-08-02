# Anker BLE (HACS)

Local Bluetooth integration for Anker BLE devices (Prime chargers, MagGo / banks, Solix)
using the FF09 encrypted session protocol.

## Features

- Bluetooth discovery of FF09 devices
- ECDH confer + AES-CBC session
- Sensors: power out, **port 1–3**, serial, firmware, product
- Binary sensors: online, charging
- Device image entity + Lovelace card (`anker-ble-card`)
- Brand icons from `assets/images/brand/` (synced into the integration)

## Setup after install

**Settings → Devices & services → Add integration → Anker BLE**

Dashboard: **Add card → Custom: Anker BLE Device**

> **HACS icon:** the HACS list may show “icon not available” even though brand assets ship with the integration. That is a [known HACS bug](https://github.com/hacs/integration/issues/5223) on HA 2026.3+. The icon still appears under **Settings → Devices & services** after install.

Requires Home Assistant 2024.1+ with a Bluetooth adapter or BLE proxy. Close the Anker phone app while polling.
