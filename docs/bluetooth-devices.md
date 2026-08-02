# Bluetooth Device Catalog (Anker app 3.22.0)

Unofficial map of products that speak Anker BLE (FF09 / ZX and related stacks) in
`com.anker.charging` **3.22.0**.

> **Verified live:** serial `ASHDJVV1F52301602`, advert name `Charging`, GATT **8C85**,
> Solix-style ECDH confer + MagGo subscribe `0x4200` → telemetry `0x4a00` with three
> port power TLVs. That matches the **Anker Prime Charger (160W, 3 Ports, Smart Display) — A2687**.

The Home Assistant integration is **charger-first** (per-port watts), not power-bank-only.
Battery % is optional when TLV `bb` is present (banks / stations).

---

## Accessory / Prime charging (RN + Flutter)

Native bridge PN map from `index.charging.bundle`:

| Bridge id | SKU | Product (marketing) |
|-----------|-----|---------------------|
| B401 | **A91B2** | Accessory / charger family |
| B402 | **A2345** | Feature mixin device (also Flutter PPS path) |
| B403 | **A1341** | Multi-port charger (RN assets) |
| B404 | **A110A** | Anker Prime Power Bank (26K, 300W) |
| B405 | **A2687** | **Anker Prime Charger (160W, 3 Ports, Smart Display)** |
| B406 | **A110B** | Anker Prime Power Bank (20K, 220W) |
| B407 | **A1903** | Anker Prime Charging Base (150W, 3 Ports) |
| B408 | **A25X7** | Wireless charger family (~35W class) |
| B409 | **A2692** | Prime / high-watt charger sibling |
| B40A | **A110G** | MagGo / Prime pad / bank variant |

App “device type” labels under accessory category `10`:

| Id | Label |
|----|--------|
| 1 | Power Bank 26K |
| 2 / 13 | Power Bank 20K |
| 4 | Power Bank 5K |
| 5 | Power Bank 10K |
| 6 | Charging Base 150W |
| 8 | Power Bank 27K |
| 9 | Wireless Charger 35W |
| **10** | **Charger 160W** ← A2687 |
| 11 | Charger 250W |
| 12 | Charging Station 240W |

### Flutter asset packs (chargers)

| Folder | Notes |
|--------|--------|
| `img/a2687/` | Full Prime 160W UI (device hero, C1/C2/C3 ports, display chrome) |
| `img/a2693/` | Related high-watt charger UI |
| `img/a25x7/` | Wireless charger |
| `img/a91b2/` | Accessory |
| `img/a1340/` | Charger A1340 (Flutter ZX feature pages) |

### Wire path (A2687 / “Charging”)

Same ZX stack as Solix MagGo-style accessories:

1. Discover `0000ff09-…`
2. GATT family **8C85** (`…0001` / `…0002` / `…0003`)
3. ECDH confer (patterns `030001`, cmds `0801`…`0821`)
4. Encrypted subscribe `cmd 4200` payload `a10121`
5. Telemetry `cmd 4a00` — port powers in TLV `a5`/`a6`/`a7` (or classic `a2`/`a3`/`a4`)

UI in the phone app shows **USB-C1 / C2 / C3** watts; HA/web map those to **Port 1–3**.

---

## Flutter BLE device modules (`charging/ble/device/`)

### Power stations / portable power (PPS)

| Code | Notes |
|------|--------|
| A172X | A1722–A1729 family |
| A1753–A1762 | Mid PPS family |
| A1770 / A1771 / A1772 | Solix PPS (heroes in Flutter assets) |
| A1780 / A1780P | PPS + parallel / Wi-Fi+BLE OTA |
| A1781 | Controller |
| A1790 / A1790P | Commands + controller |
| A17X7 / A17X7US / A17X8 | Regional / feature mixins |
| A17Y0 | Connect / OTA |
| A2345 | Also in RN bridge map |

### Solarbank / home backup

| Code | Notes |
|------|--------|
| A17B1 / A17B2 | Multi-device / site |
| A17C0–A17C5 | Station family + BLE OTA |

### Coolers

| Code | Notes |
|------|--------|
| A17A0–A17A5 | `ZXCoolerDeviceFeature` |

### Chargers (Flutter ZX)

| Code | Notes |
|------|--------|
| **A1340** | Charger feature + protocol UI |
| **A2687** | Prime 160W smart display (Flutter `img/a2687` + RN bridge) |
| A91B2 | Feature mixin |

### HES / energy system

| Code | Notes |
|------|--------|
| A5101 | HES connect-over-BLE |
| A5140 / A5141 / A5143 | Station / HES |
| A5150 | Controller |
| A5190 / A5191 | EV charger UI assets |

### Third party

| Code | Notes |
|------|--------|
| Shelly | `third_party_device/Shelly/…` |

---

## Shared BLE features

- `ZXBleFeature` — ZX confer + FF09 framing (chargers, banks, many stations)
- `PpsDeviceFeature` — portable power station behaviors
- `BleOtaField` — BLE OTA
- Product features (`A1340DeviceFeature`, `A17X8DeviceFeature`, …)

## Integration coverage today

| Capability | Status |
|------------|--------|
| Discover FF09 / 8C85 | Yes |
| ECDH confer + identity | Yes |
| Port 1–3 power (A2687 / MagGo-style TLV) | Yes |
| Battery % (TLV `bb`) | Yes when present |
| Product art (A2687, A110x, A134x, Solix, …) | Yes |
| AC/DC switches / PPS deep TLV | Not yet |
| Solarbank / HES / coolers | Discovery possible; telemetry maps incomplete |

## Serial / name hints

| Hint | Likely product art key |
|------|------------------------|
| `ASHD…` serial, name `Charging` | **a2687** (Prime 160W) |
| `A2687` | a2687 |
| `A110A` / `A110B` / `A110G` | Prime / MagGo banks & pads |
| `A1903` | Charging base |
| `A1340` / `A1341` | Chargers |
| `A1770`–`A1772` | Solix PPS |
