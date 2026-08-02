# Anker Bluetooth docs

Protocol notes reverse-engineered from **Anker** app `com.anker.charging` **3.22.0**.

| Document | Description |
|----------|-------------|
| [bluetooth-protocol.md](./bluetooth-protocol.md) | Frame format, confer/crypto, TLV, lifecycle |
| [bluetooth-gatt-uuids.md](./bluetooth-gatt-uuids.md) | GATT / discovery UUIDs found in the binary |
| [bluetooth-devices.md](./bluetooth-devices.md) | Device catalog (A2687 Prime charger, banks, Solix, …) |
| [bluetooth-source-map.md](./bluetooth-source-map.md) | Where code lives in the APKS |
| [requirements.md](./requirements.md) | Original extraction task |

## Clients

| Client | Path | Notes |
|--------|------|--------|
| Python PoC | [`../poc/`](../poc/) | Scan / connect / confer / telemetry CLI |
| Web Bluetooth | [`../web/`](../web/) | Chrome/Edge; https://t-rex-xp.github.io/Anker-BLE/ |
| Home Assistant | [`../custom_components/anker_ble/`](../custom_components/anker_ble/) | HACS integration + Lovelace card |

## Images

Central artwork: [`../assets/images/`](../assets/images/) — sync with `python3 scripts/sync_images.py`.

## Quick links

```bash
# Web (local)
cd web && ./serve.sh   # http://127.0.0.1:8765/

# HA (manual)
cp -a custom_components/anker_ble /config/custom_components/
# restart → Add integration → Anker BLE
```

HACS: **Integrations → Custom repositories** → this GitHub repo → category **Integration**.
