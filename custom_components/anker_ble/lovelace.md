# Lovelace — Anker BLE device card

After installing the integration and restarting Home Assistant, the **Anker BLE Device** card is registered automatically.

## Add the card

1. Edit a dashboard → **Add card** → **Custom: Anker BLE Device**
2. In the editor, pick the device’s **Power out** sensor (`sensor.*_power_out`)
3. Optionally set a name and toggle Port / battery / status chips

YAML:

```yaml
type: custom:anker-ble-card
entity: sensor.YOUR_DEVICE_power_out
name: Prime Charger 160W
show_ports: true
show_battery: true
show_status: true
```

The entity picker is filtered to Anker BLE **power** sensors (Power out and Port 1–3). Port sensors also work; the card still resolves Power out and siblings automatically.

Empty entity while editing shows a placeholder — it no longer throws a configuration error.

## Manual resource (only if the card is missing)

**Settings → Dashboards → ⋮ → Resources → Add resource**

- URL: `/anker_ble_static/anker-ble-card.js?v=0.2.11`
- Type: **JavaScript module**

Hard-refresh the browser (Ctrl+Shift+R) after updating the integration so the new card JS loads.

## Product artwork

Photos are synced from [`assets/images/product/`](../../assets/images/product/) into the integration (`static/images/`) and served from:

`/anker_ble_static/images/<sku>.png`

Examples: `a2687.png` (Prime Charger 160W), `a110a.png`, `a1770.png`, …
