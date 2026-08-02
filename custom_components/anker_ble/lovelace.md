# Lovelace — Anker BLE device card

After installing the integration and restarting Home Assistant, the **Anker BLE Device** card is registered automatically.

## Add the card

1. Edit a dashboard → **Add card** → **Custom: Anker BLE Device**
2. Or YAML:

```yaml
type: custom:anker-ble-card
entity: sensor.YOUR_DEVICE_power_out
name: MagGo Pad
show_pads: true
show_battery: true
show_status: true
```

`entity` must be the **Power out** sensor from an Anker BLE device. The card auto-discovers pad power, online, charging, battery, and product image entities on the same device.

## Manual resource (only if the card is missing)

**Settings → Dashboards → ⋮ → Resources → Add resource**

- URL: `/anker_ble_static/anker-ble-card.js`
- Type: **JavaScript module**

## Product artwork

Device photos are taken from the official Anker app asset pack (MagGo A110A/B/G, A1340/A1341, A1903, Solix A1770–A1772) and served from:

`/anker_ble_static/images/<sku>.png`

The **Device image** entity (`image.*_device_image`) and the **Power out** sensor both expose `entity_picture` for use with built-in picture cards:

```yaml
type: picture-entity
entity: sensor.YOUR_DEVICE_power_out
```
