# Central media assets

Source of truth for product photos and brand icons. Consumers are filled by:

```bash
python3 scripts/sync_images.py
```

| Path | Contents |
|------|----------|
| `images/product/` | Device heroes / thumbs (A2687, A110x, Solix, …) |
| `images/brand/` | HACS / HA `icon.png`, `logo.png`, `@2x`, `dark_*` |

## Copied to

- `web/images/` — Web Bluetooth client / GitHub Pages
- `custom_components/anker_ble/static/images/` — Lovelace card + entity pictures
- `custom_components/anker_ble/brand/` — HA Devices & services brand
- `brand/` — optional repo-root mirror for some HACS checks

Do **not** edit the destination folders by hand — change files here, then sync.
