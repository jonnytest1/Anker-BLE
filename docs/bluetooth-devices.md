# Bluetooth Device SKUs (App Implementation Map)

Product folders under Flutter package `charging/ble/device/` in Anker app **3.22.0**. Each SKU typically has:

- `*_anker_device.dart` — device model / feature mixins  
- `*_device_commands.dart` or `*_commands.dart` — BLE command builders  
- `*_device_controller.dart` — UI/business orchestration  

## Power stations / portable power (PPS)

| Code | Classes / notes |
|------|-----------------|
| A172X | A1722–A1729 family (`172X/a172x_*`) |
| A1753 | A1753 / A1754 / A1755 / A1761 / A1762 |
| A1770 | Commands + controller |
| A1771 | Commands + controller |
| A1772 | Device class |
| A1780 | Commands + controller |
| A1780P | Parallel / Pro variant, Wi-Fi+BLE OTA |
| A1781 | Controller |
| A1790 | Commands + controller; A1790P subfolder |
| A17X7 / A17X7US | Regional variants |
| A17X8 | Feature mixin `A17X8DeviceFeature` |
| A17Y0 | Connect / OTA flows |
| A2345 | Feature mixin |

## Solarbank / home backup / station

| Code | Notes |
|------|--------|
| A17B1 | Multi-device list assemble; MQTT order model |
| A17B2 | Group / site device |
| A17C0 | Station commands + BLE OTA |
| A17C1 | Station commands + BLE OTA |
| A17C2 / A17C3 / A17C5 | Station family |

## Coolers / specialty

| Code | Notes |
|------|--------|
| A17A0–A17A5 | Cooler feature `ZXCoolerDeviceFeature`, double-box temps |

## Chargers / MagGo / small charging

| Code | Notes |
|------|--------|
| A1340 | Feature + protocol UI pages |
| A91B2 | Feature mixin |

## HES / energy system

| Code | Notes |
|------|--------|
| A5101 | HES connect-over-BLE; opcodes `0x01`, `0x0f`, `0x12` |
| A5140 / A5141 / A5143 | Related HES/station modules (A5140 reuses some A1780 cmds) |
| A5150 | Controller |

## Third party

| Code | Notes |
|------|--------|
| Shelly | `third_party_device/Shelly/shelly_device_commands.dart` |

## Shared BLE feature mixins

Observed on many SKUs:

- `ZXBleFeature` — ZX confer + FF09 framing  
- `PpsDeviceFeature` — portable power station behaviors  
- `BleOtaField` — BLE OTA capability  
- Product-specific features (`A1340DeviceFeature`, `A17X8DeviceFeature`, …)

## RN accessory path

`assets/rn_bundle_android_charging.zip` → `index.charging.bundle` talks to native via:

- `akiot.device.accessory.scan` / `.bind`
- `akiot.device.get_bound_bluetooth_device_list`
- `akiot.pairing.ble_bind_device` / `pro_ble_bind_device`
- `parseCustomBluetoothFormat` for bound-device list payloads  

Used for MagGo / A110x / A1903 style accessory UX; wire codec remains in Flutter/native.
