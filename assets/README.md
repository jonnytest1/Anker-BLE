# Central media assets

Source of truth for product photos and brand icons used by the Web client and Home Assistant integration.

```bash
python3 scripts/sync_images.py          # copy into consumers
python3 scripts/sync_images.py --check  # fail CI if destinations drift
```

| Path | Contents |
|------|----------|
| [`images/product/`](images/product/) | Device heroes / thumbs (A2687, A110x, A134x, Solix, …) |
| [`images/brand/`](images/brand/) | HACS / HA `icon.png`, `logo.png`, `@2x`, `dark_*` |

## Copied to

| Destination | Used by |
|-------------|---------|
| `web/images/` | Web Bluetooth client / GitHub Pages |
| `custom_components/anker_ble/static/images/` | Lovelace card + `entity_picture` |
| `custom_components/anker_ble/brand/` | HA Devices & services brand API |
| `brand/` | Repo-root mirror for some HACS checks |

Do **not** edit the destination folders by hand — change files here, then sync.

Product SKU → filename mapping is documented in [`docs/bluetooth-devices.md`](../docs/bluetooth-devices.md) and implemented in `custom_components/anker_ble/product_art.py`.
