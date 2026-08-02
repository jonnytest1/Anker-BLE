# Anker Bluetooth docs

Protocol notes reverse-engineered from **Anker** app `com.anker.charging` **3.22.0**.

| Document | Description |
|----------|-------------|
| [bluetooth-protocol.md](./bluetooth-protocol.md) | Frame format, confer/crypto, TLV, lifecycle |
| [bluetooth-gatt-uuids.md](./bluetooth-gatt-uuids.md) | GATT / discovery UUIDs found in the binary |
| [bluetooth-devices.md](./bluetooth-devices.md) | Product SKU → Flutter BLE modules |
| [bluetooth-source-map.md](./bluetooth-source-map.md) | Where code lives in the APKS |
| [requirements.md](./requirements.md) | Original extraction task |

## PoC

Scan / connect / ECDH confer: [`../poc/`](../poc/)

## Web Bluetooth

Browser client (Chrome/Edge): [`../web/`](../web/)

```bash
cd /opt/anker/web && python3 -m http.server 8765 --bind 127.0.0.1
# open http://127.0.0.1:8765/
```

## Home Assistant

Custom integration (HACS-ready): [`../custom_components/anker_ble/`](../custom_components/anker_ble/)

```text
HACS → Custom repositories → <github-repo-url> → Integration
```

Or:

```bash
cp -a /opt/anker/custom_components/anker_ble /config/custom_components/
# restart HA → Add integration → Anker BLE
```
