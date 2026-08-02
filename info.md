# Anker BLE (HACS)

Local Bluetooth integration for Anker / Solix devices using the FF09 encrypted session protocol.

## Features

- Bluetooth discovery of FF09 devices
- ECDH confer + AES-CBC session
- Sensors: power / pads, serial, firmware, product
- Binary sensors: online, charging
- Device image entity + MagGo-style Lovelace card (`anker-ble-card`)

## Setup after install

**Settings → Devices & services → Add integration → Anker BLE**

Dashboard: **Add card → Custom: Anker BLE Device** (uses product artwork from the Anker app).

Requires Home Assistant 2024.1+ with a Bluetooth adapter or BLE proxy.
