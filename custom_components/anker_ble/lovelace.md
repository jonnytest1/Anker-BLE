# Lovelace — Anker BLE device card

After installing the integration and restarting Home Assistant, the **Anker BLE Device** card is registered automatically.

## Add the card

1. Edit a dashboard → **Add card** → **Custom: Anker BLE Device**
2. Or YAML:

```yaml
type: custom:anker-ble-card
entity: sensor.YOUR_DEVICE_power_out
name: Prime Charger 160W
show_pads: true
show_battery: true
show_status: true
```

`entity` must be the **Power out** sensor from an Anker BLE device. The card auto-discovers port power, online, charging, battery, and product image entities on the same device.

`show_pads` still controls the **Port 1–3** row (legacy option name).

## Manual resource (only if the card is missing)

**Settings → Dashboards → ⋮ → Resources → Add resource**

- URL: `/anker_ble_static/anker-ble-card.js`
- Type: **JavaScript module**

## Product artwork

Photos are synced from [`assets/images/product/`](../../assets/images/product/) into the integration (`static/images/`) and served from:

`/anker_ble_static/images/<sku>.png`

Examples: `a2687.png` (Prime Charger 160W), `a110a.png`, `a1770.png`, …

The **Device image** entity (`image.*_device_image`) and the **Power out** sensor expose `entity_picture` for built-in picture cards:

```yaml
type: picture-entity
entity: sensor.YOUR_DEVICE_power_out
```
