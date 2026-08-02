# Anker BLE find & connect PoC

Scan for Anker / Solix-style BLE devices (FF09 and related UUIDs) and connect.

## Setup

```bash
cd /opt/anker/poc
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ensure a BlueZ adapter is up (`hci1` on this host):

```bash
rfkill unblock bluetooth
sudo hciconfig hci1 up
```

## Usage

```bash
# Discover supported devices
./.venv/bin/python find_and_connect.py scan --timeout 10

# Connect to the strongest match and list GATT
./.venv/bin/python find_and_connect.py connect --first

# Connect + ECDH confer + listen for telemetry
./.venv/bin/python find_and_connect.py connect --first --confer --listen 15 -v

# Specific adapter / address
./.venv/bin/python find_and_connect.py connect --adapter hci1 \
  --address AA:BB:CC:DD:EE:FF --confer
```

## What “supported” means

A device is listed if advertising matches any of:

- Service UUID `0000ff09-…` (primary Solix/Prime filter)
- Other Anker identifier UUIDs (`ef0a`/`ef0b`, `1770`/`1780`/`17A0`–`17A2`, `2540`)
- Known GATT family service UUIDs (`8C85`, `2215`, `2540`, `4158`)
- Name hints (`Anker`, `Solix`, `A17…`, `C1000`, …)

## Verified on this host

Against a nearby `FF09` device (`ASHDJVV1F52301602` / family `8C85`):

- Scan detects via `0000ff09-…`
- GATT resolves to `8c850001/0002/0003`
- Full ECDH confer completes (`Confer: SUCCESS`)

Telemetry listen may be quiet until encrypted command subscriptions are sent (out of scope for this PoC).

## Notes

- Confer uses the fixed client ECDH key material documented for the FF09 ZX path (same as community SolixBLE).
- Not every Anker product uses this confer; MagGo / legacy stacks may connect but fail negotiation.
- Requires Bluetooth permissions and proximity to a powered, advertising device.
