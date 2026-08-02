# Bluetooth GATT UUID Reference

Extracted from Anker app `com.anker.charging` **3.22.0** (`libapp.so` string table).

## Identifier / scan filter

| UUID | Notes |
|------|--------|
| `0000ff09-0000-1000-8000-00805f9b34fb` | Primary Solix/Prime discovery UUID (`FF09`) |

## Standard Bluetooth base UUID form (`xxxxxxxx-0000-1000-8000-00805f9b34fb`)

| UUID | Notes |
|------|--------|
| `0000ef0a-0000-1000-8000-00805f9b34fb` | Secondary service/char family |
| `0000ef0b-0000-1000-8000-00805f9b34fb` | Used near multi-device parse paths |
| `00001770-0000-1000-8000-00805F9B34FB` | Product-family |
| `00001780-0000-1000-8000-00805F9B34FB` | Product-family |
| `000017A0-0000-1000-8000-00805F9B34FB` | Product-family |
| `000017A1-0000-1000-8000-00805F9B34FB` | Product-family |
| `000017A2-0000-1000-8000-00805F9B34FB` | Product-family |
| `00002540-0000-1000-8000-00805f9b34fb` | Product-family (`2540`) |
| `014BF5DA-0000-1000-8000-00805F9B34FB` | Custom F5DA series |
| `0156F5DA-0000-1000-8000-00805F9B34FB` | Custom F5DA series |
| `0157F5DA-0000-1000-8000-00805F9B34FB` | Custom F5DA series |
| `0158F5DA-0000-1000-8000-00805F9B34FB` | Custom F5DA series |
| `0159F5DA-0000-1000-8000-00805F9B34FB` | Custom F5DA series |
| `016DF5DA-0000-1000-8000-00805F9B34FB` | Custom F5DA series |

## Custom Anker UUID families

Pattern: `{PREFIX}000{n}-…-b46e-cf057c562025`

| Family prefix | Service (`…0001`) | Write (`…0002`) | Notify (`…0003`) |
|---------------|-------------------|-----------------|------------------|
| `8C85` | `8c850001-0302-41c5-b46e-cf057c562025` | `8c850002-0302-41c5-b46e-cf057c562025` | `8c850003-0302-41c5-b46e-cf057c562025` |
| `2215` | `22150001-4002-81c5-b46e-cf057c562025` | `22150002-4002-81c5-b46e-cf057c562025` | `22150003-4002-81c5-b46e-cf057c562025` |
| `2540` | `25400001-4002-81c5-b46e-cf057c562025` | `25400002-4002-81c5-b46e-cf057c562025` | `25400003-4002-81c5-b46e-cf057c562025` |
| `4158` | `41580001-4002-81c5-b46e-cf057c562025` | `41580002-4002-81c5-b46e-cf057c562025` | `41580003-4002-81c5-b46e-cf057c562025` |

> Exact product ↔ family mapping is selected at runtime by device feature classes (`ZXBleFeature`, per-SKU `*_anker_device.dart`). `8C85` is the widely documented Solix/PPS default.

## App field names

Flutter code exposes:

- `serviceUUID`
- `writeCharacteristicUUID`
- `notifyCharacteristicUUID`
- `mtu` / `setMtu` / `putMtu`

See [bluetooth-protocol.md](./bluetooth-protocol.md) for how these are used after connect.
