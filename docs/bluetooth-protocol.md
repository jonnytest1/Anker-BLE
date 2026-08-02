# Anker App Bluetooth Protocol

Reverse-engineered from **Anker** Android app `com.anker.charging` **v3.22.0** (`Anker_3.22.0_apkcube.apks`).

Primary implementation lives in Flutter AOT (`libapp.so`), packages:

- `charging/ble/` — connection, scan, per-device commands
- `charging/ble_zx/` — ZX session framing, confer (handshake), AES helpers
- `base_service/` — shared BLE types / bind models
- Native crypto: `libecc-encryption.so` (`com.anker.esiotkit.support.crypto.EccEncryption`)

Transport library: [`flutter_reactive_ble`](https://pub.dev/packages/flutter_reactive_ble) (platform protobuf in APK as `bledata.proto`).

> This documents the wire protocol as implemented by the app. It is unofficial and not affiliated with Anker.

---

## Architecture overview

```
┌─────────────────────────────────────────────────────────────┐
│  Flutter UI / device controllers (A17xx, A51xx, …)          │
├─────────────────────────────────────────────────────────────┤
│  charging/ble  (BleManager, scanner, handlers, commands)    │
├─────────────────────────────────────────────────────────────┤
│  charging/ble_zx  (AssembleCmdUtil, confer, payload helper) │
├─────────────────────────────────────────────────────────────┤
│  reactive_ble → Android GATT                                │
└─────────────────────────────────────────────────────────────┘
```

Two related stacks coexist:

| Stack | Role in app | Notes |
|-------|-------------|--------|
| **ZX / FF09** | Solix / PPS / Solarbank-style power products | Magic `0xFF09`, ECDH + AES-CBC session, TLV payloads |
| **Legacy / “Old Anker”** | Older chargers / accessory paths | `OldAnkerCmdService`, `PPSDeviceCommands`, AES key exchange APIs |
| **HES / A5101 opcodes** | Home energy system | Dedicated `ZXOpcode` / `zx_opcode_0gmex01`, `0x0f`, `0x12` |
| **React Native bridge** | Some MagGo / small-charging UI | `akiot.device.*` / `akiot.pairing.*` — BLE bind via native, not full wire codec in JS |

---

## Discovery

Devices advertise (among others) the 16-bit UUID:

| UUID | Role |
|------|------|
| `0000ff09-0000-1000-8000-00805f9b34fb` | Identifier / filter UUID (`FF09`) |

Related advertised / service 16-bit IDs also present in the binary:

| UUID | Likely use |
|------|------------|
| `0000ef0a-…` / `0000ef0b-…` | Alternate / secondary service chars |
| `00001770` / `00001780` / `000017A0`–`000017A2` | Product-family service IDs |
| `00002540-…` | Product-family service ID |
| `014BF5DA` / `0156F5DA`–`0159F5DA` / `016DF5DA` | Custom 32-bit-style IDs in Bluetooth base UUID |

---

## GATT layout (ZX / Solix family)

Default Solix-style triplet (confirmed in app strings and matching community RE):

| Role | UUID |
|------|------|
| **Service** | `8c850001-0302-41c5-b46e-cf057c562025` |
| **Write / command** | `8c850002-0302-41c5-b46e-cf057c562025` |
| **Notify / telemetry** | `8c850003-0302-41c5-b46e-cf057c562025` |

### Product-prefixed UUID families

The app embeds the same `…-4002-81c5-b46e-cf057c562025` (or `0302-41c5-…`) pattern with different 4-byte prefixes. Convention observed:

| Prefix | `…0001` | `…0002` | `…0003` |
|--------|---------|---------|---------|
| `8C85` | service | write | notify |
| `2215` | service | write | notify |
| `2540` | service | write | notify |
| `4158` | service | write | notify |

App code selects `serviceUUID` / `writeCharacteristicUUID` / `notifyCharacteristicUUID` per device class (`BleIndex`, device feature mixins).

Typical flow:

1. Scan for `FF09` (and/or device name / manufacturer data).
2. Connect + discover services.
3. Subscribe to notify characteristic.
4. Run **confer** (handshake) on write characteristic.
5. Exchange encrypted command / telemetry frames.

MTU negotiation is explicit (`setMtu` / `putMtu`); OTA and large payloads use raised MTU (community traces cite ~200–400).

---

## Wire frame format (`0xFF09`)

All ZX-style packets:

```
┌──────────┬──────────┬───────────┬─────────┬──────────┬──────────┐
│  Header  │  Length  │  Pattern  │   Cmd   │ Payload  │ Checksum │
│  2 bytes │  2 bytes │  3 bytes  │ 2 bytes │  N bytes │  1 byte  │
│  FF 09   │  LE u16  │           │         │          │  XOR     │
└──────────┴──────────┴───────────┴─────────┴──────────┴──────────┘
```

| Field | Size | Description |
|-------|------|-------------|
| Header | 2 | Always `0xFF09` |
| Length | 2 | Little-endian total packet length (including header + checksum) |
| Pattern | 3 | Message class (negotiation vs session) |
| Cmd | 2 | Opcode / command code |
| Payload | N | Plain or AES-CBC ciphertext; often TLV |
| Checksum | 1 | XOR of all preceding bytes |

App builders: `AssembleCmdUtil`, `BleWritePayloadHelper`, `CmdUtil` / `ZXCmdUtil`, `ak_cmd_util.dart`.

### Pattern values (session / negotiation)

| Pattern (hex) | Meaning |
|---------------|---------|
| `030001` | Negotiation / confer messages |
| `03010f` / `030111` | Session messages (encrypted telemetry / commands) |
| Outbound encrypt | App/community use `03000f` when building encrypted writes |

### Negotiation command stages (`pattern = 030001`)

| Stage cmd | Direction | Role |
|-----------|-----------|------|
| `0001` | App → device | Start confer |
| `0801` | Device → app | Stage 1 |
| `0803` | Device → app | Stage 2 |
| `0829` | Device → app | Stage 3 (timestamp base established) |
| `0805` | Device → app | Stage 4 |
| `0821` | Device → app | Stage 5 — device ECDH public key in TLV `a1` |
| (final app write) | App → device | Complete session |

App types: `BleConfer`, `AesConferV1`, `EcdhConfer`, `SecureEcdhConfer`, `ZXBleConfer`, `startZXBleConfer`, `isBleConferDone`.

---

## Session crypto

### ECDH + AES-128-CBC (ZX)

1. App and device perform ECDH on **secp256r1** (P-256).
2. Shared secret is 32 bytes:
   - bytes `[0..15]` → AES-128 key  
   - bytes `[16..31]` → CBC IV  
3. Payloads use **AES-CBC** with **PKCS7** padding.
4. Native path also exposes `libecc-encryption.so`:
   - `generateEccKey` / `eccEncrypt` / `eccDecrypt`
   - `aes128_cbc_enc` / `aes128_cbc_dec`
   - `HMAC_SHA_256`, `uECC_*`

App helpers: `AesHelper`, `getAesKeyReq` / `getAesKeyRes`, `getExchangedAesKey`, `aesEncrypt` / `aesDecrypt`, `OpcodeTypeExtension.isEncrypted`.

### Replay protection

Negotiated base timestamp is carried in TLV parameters; subsequent commands include a rolling time field so old frames are rejected.

### Fragmentation

Encrypted telemetry may span multiple GATT notifications:

- First payload byte: high nibble = fragment index, low nibble = fragment total.
- Reassemble in order, then decrypt, then parse TLV.

App: `_parseBlePackData`, `parseBleResponseData`, fragment/MTU helpers around OTA (`putMtu`, `subPackageNumber`).

---

## TLV payload encoding

After decrypt (or plaintext for some negotiation msgs), payload is a sequence of parameters:

```
<id:1B> <len:1–2B> <type:1B> <data:nB> …
```

- Parameter IDs commonly rendered as hex `a1`, `a2`, … (and higher tags such as CRC tag `0x1FA` / 506 in schedule flows).
- Optional leading `0x00` may appear and is stripped before parse.
- Assembly log string in binary: `"Assembled protocol command data from tlv: "`.
- Helpers: `parseTlvData`, `tlvPayload`, `getSupportAbilityTlv`, `getMinSocTlv`, etc.

### Example high-level commands (community + app naming)

These illustrate the command-layer style used by Solarbank / plug controllers (hex cmd IDs in the 2-byte cmd field or mapped opcode tables):

| Area | Example | Notes |
|------|---------|--------|
| Schedule | `0x005E` | Many TLV tags + CRC32 tag |
| SOC reserve | `0x0067` | e.g. `a2`/`a4`/`a6` SOC fields |
| Plug toggle | `0x007A` | Dual BLE + MQTT on some SKUs |
| Plug schedule | `0x007C` | Weekday bitmask, max slots |
| Power limit | `0x0080` | Solarbank |
| Temp unit | `0x0050` | BLE-only setting |

App maps opcodes via `commonOpcodeMap`, `chargingOpcodeMap`, `ZXOpcodeType`, `getOpcodeFromCmd`, `FEATURE_OPCODE_KEY` / `OPCODE_KEY`.

Known `ZXOpcodeType` names from logs:

- `getMultiDevicesReq` / `getMultiDevicesRes`
- `getAllDeviceInfo` / `getAllDeviceInfoRes`
- HES-specific: `ZXHesOpcode`, `zx_opcode_0x01`, `zx_opcode_0x0f`, `zx_opcode_0x12`

---

## Integrity

| Mechanism | Where |
|-----------|--------|
| Frame XOR checksum | Last byte of every `FF09` packet |
| CRC32 | OTA (`crc32_util.dart`, `CRC32Helper`), schedule/large TLV (tag-based), screen-image transfers |

---

## Connection lifecycle (app)

Approximate sequence encoded in `BleManager` / `BleDeviceConnector` / confer helpers:

1. Permission + adapter check (`BLUETOOTH_SCAN` / `BLUETOOTH_CONNECT`).
2. Scan (`BleScanner` / `SdkBleScanner` / `reactive_ble_manager`).
3. Connect + set notify/write characteristics.
4. `startConfer` / `startZXBleConfer` until `isBleConferDone`.
5. Business commands (`sendBleCmd`, device `*_commands.dart`).
6. Optional Wi-Fi provisioning over BLE (`parseConnectWifiData`, `parseActivateWifiData`, `parseBindUserIdData` — often encrypted).
7. OTA over BLE (`startBleOTA`, `sendBleOtaData`, Wi-Fi+BLE parallel OTA for some SKUs).

Status tracking: `BleCmdStatus`, `BleStatusCode`, `BLE_CMD_STATUS_KEY`.

---

## Related documentation

- [GATT UUID reference](./bluetooth-gatt-uuids.md)
- [Device SKUs & code map](./bluetooth-devices.md)
- [Source map (packages / natives)](./bluetooth-source-map.md)

### External corroboration

Frame layout, `FF09` GATT UUIDs, and ECDH/AES session semantics align with community projects such as [flip-dots/SolixBLE](https://github.com/flip-dots/SolixBLE) and [v0l/anker-rs](https://github.com/v0l/anker-rs). Opcode examples for Solarbank flows appear in [anker-solix-api-exploration](https://github.com/moag1000/anker-solix-api-exploration).
