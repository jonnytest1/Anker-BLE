# Anker BLE find & connect PoC

Scan for Anker BLE devices (FF09 / related UUIDs), connect, run ECDH confer, and optionally subscribe for telemetry.

Works with chargers such as the **Anker Prime Charger 160W (A2687)** as well as MagGo / Solix-style products.

## Setup

```bash
cd poc
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Ensure a BlueZ adapter is up:

```bash
rfkill unblock bluetooth
sudo hciconfig hciX up
```

## Usage

```bash
# Discover supported devices
./.venv/bin/python find_and_connect.py scan --timeout 10

# Connect to the strongest match and list GATT
./.venv/bin/python find_and_connect.py connect --first

# Connect + ECDH confer + subscribe + listen for telemetry
./.venv/bin/python find_and_connect.py connect --first --confer --listen 15 -v

# Specific adapter / address
./.venv/bin/python find_and_connect.py connect --adapter hci1 \
  --address AA:BB:CC:DD:EE:FF --confer --listen 10
```

## What “supported” means

A device is listed if advertising matches any of:

- Service UUID `0000ff09-…` (primary Solix / Prime filter)
- Other Anker identifier UUIDs (`ef0a`/`ef0b`, `1770`/`1780`/`17A0`–`17A2`, `2540`)
- Known GATT family service UUIDs (`8C85`, `2215`, `2540`, `4158`)
- Name hints (`Anker`, `Solix`, `Charging`, `A17…`, …)

## Verified

Against **Anker Prime Charger 160W (A2687)** — serial `ASHDJVV1F52301602`, advert name `Charging`, family `8C85`:

- Scan detects via `0000ff09-…`
- GATT resolves to `8c850001` / `0002` / `0003`
- Full ECDH confer completes
- Subscribe `0x4200` yields encrypted telemetry (`0x4a00`) with per-port power TLVs

Device catalog: [docs/bluetooth-devices.md](../docs/bluetooth-devices.md)

## Notes

- Confer uses the fixed client ECDH key material documented for the FF09 ZX path.
- Close other BLE clients (Anker app, HA) while testing on the same adapter.
- Not every Anker product uses this confer path; some legacy stacks may connect but fail negotiation.
