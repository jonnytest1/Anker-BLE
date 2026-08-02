# Bluetooth Source Map (Anker 3.22.0)

Where protocol pieces live inside `Anker_3.22.0_apkcube.apks`.

## Artifact layout

| Path | Contents |
|------|----------|
| `artifacts/Anker_3.22.0_apkcube.apks` | Play Asset Delivery / APK set (zip) |
| `base.apk` | App stub + assets; packed Java (`s.h.e.l.l.S`); Flutter assets; RN zip |
| `split_config.arm64_v8a.apk` | Native libs including `libapp.so`, `libecc-encryption.so` |
| `split_flutter_assets_pack.apk` | Large Flutter asset pack |

Unpacked working copy used for analysis: `artifacts/unpacked/`, `artifacts/arm64_extracted/`.

## Flutter packages (from `libapp.so` path strings)

### Core BLE

| Package path | Purpose |
|--------------|---------|
| `charging/ble/ble_manager.dart` | Central BLE manager |
| `charging/ble/ble_scanner.dart` | Scan |
| `charging/ble/ble_device_connector.dart` | Connect |
| `charging/ble/ble_operation.dart` | GATT ops |
| `charging/ble/ble_handler*.dart` | Response handlers (incl. legacy) |
| `charging/ble/reactive_ble_manager.dart` | flutter_reactive_ble wrapper |
| `charging/ble/sdk_handler/sdk_ble_*.dart` | Alternate SDK connector/scanner |
| `charging/communication/command_controller/ble_command_controller.dart` | Command controller |

### ZX protocol

| Package path | Purpose |
|--------------|---------|
| `charging/ble_zx/base/assemble_command_util.dart` | Build FF09 / TLV commands |
| `charging/ble_zx/helper/ble_write_payload_helper.dart` | Write payload assembly |
| `charging/ble_zx/helper/aes_helper.dart` | AES helpers |
| `charging/ble_zx/helper/ble_info_helper.dart` | Device info parse |
| `charging/ble_zx/helper/zx_ble_confer.dart` | Confer orchestration |
| `charging/ble_zx/ble_confer/ble_confer.dart` | Base confer |
| `charging/ble_zx/ble_confer/aes_confer_v1.dart` | AES confer v1 |
| `charging/ble_zx/ble_confer/ecdh_confer.dart` | ECDH confer |
| `charging/ble_zx/ble_confer/secure_ecdh_confer.dart` | Secure ECDH confer |
| `charging/ble_zx/constant/ble_index.dart` | GATT index / UUID selection |
| `charging/ble_zx/constant/ble_status_code.dart` | Status codes |

### Utilities / legacy

| Package path | Purpose |
|--------------|---------|
| `charging/util/ak_cmd_util.dart` | Command utilities |
| `charging/util/cmd_util.dart` | Command utilities |
| `charging/util/crc32_util.dart` | CRC32 |
| `charging/impl/old_anker_cmd_serviceImpl.dart` | Legacy Anker cmds |
| `base_service/service/old_anker_cmd_service.dart` | Legacy interface |
| `base_service/services/i_ble_manager.dart` | BLE manager interface |
| `base_service/services/ble_types.dart` | Shared types |
| `base_service/util/simple_ble_connector.dart` | Simple connector |
| `base_service/bean/model/ble_transfer_data.dart` | Transfer model |

### Per-device

See [bluetooth-devices.md](./bluetooth-devices.md). Pattern:

`charging/ble/device/<SKU>/…_commands.dart`

## Native libraries

| Library | Role |
|---------|------|
| `libapp.so` | Flutter AOT — majority of BLE protocol |
| `libecc-encryption.so` | JNI ECC + AES-CBC (`EccEncryption`) |
| `libflutter.so` | Flutter engine |
| `libreactnative.so` / `libhermes.so` | RN runtime for charging accessory UI |

## Android permissions

From decoded manifest:

- `BLUETOOTH` / `BLUETOOTH_ADMIN` (maxSdk 30)
- `BLUETOOTH_SCAN` (neverForLocation flag)
- `BLUETOOTH_CONNECT`

## Analysis notes

- `classes.dex` in `base.apk` is a tiny shell stub; real DEX is runtime-decrypted (`application` = `s.h.e.l.l.S`).
- `bledata.proto` in the APK is **flutter_reactive_ble** platform IPC, not Anker device TLV.
- Opcode numeric tables are largely compiled into AOT without readable enum source; names recovered from log/format strings and community traces. Deeper opcode dumps need Blutter/reFlutter or live GATT capture.
