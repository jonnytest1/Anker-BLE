#!/usr/bin/env python3
"""Find supported Anker BLE devices and optionally connect / confer.

Examples:
  ./find_and_connect.py scan
  ./find_and_connect.py scan --timeout 12
  ./find_and_connect.py connect --address AA:BB:CC:DD:EE:FF
  ./find_and_connect.py connect --first --confer
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from anker_ble.client import AnkerBleClient
from anker_ble.scan import scan_devices


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _print_devices(devices) -> None:
    if not devices:
        print("No supported devices found.")
        print("Hints: power on the product, enable Bluetooth advertising, stay nearby.")
        return
    print(f"Found {len(devices)} supported device(s):\n")
    for i, d in enumerate(devices):
        print(f"[{i}] {d.address}")
        print(f"    name     : {d.name or '(none)'}")
        print(f"    rssi     : {d.rssi} dBm")
        print(f"    reasons  : {', '.join(d.reasons)}")
        print(f"    family   : {d.family or '(detect on connect)'}")
        if d.service_uuids:
            print(f"    uuids    : {', '.join(d.service_uuids[:6])}")
        print()


async def cmd_scan(args: argparse.Namespace) -> int:
    devices = await scan_devices(timeout=args.timeout, adapter=args.adapter)
    _print_devices(devices)
    return 0 if devices else 1


async def cmd_connect(args: argparse.Namespace) -> int:
    devices = await scan_devices(timeout=args.timeout, adapter=args.adapter)
    _print_devices(devices)

    target = None
    if args.address:
        wanted = args.address.lower()
        for d in devices:
            if d.address.lower() == wanted:
                target = d
                break
        if target is None:
            # Connect by address even if not seen in this scan window
            logging.getLogger(__name__).warning(
                "address %s not in scan results — connecting directly", args.address
            )
            client = AnkerBleClient(args.address, family=args.family, adapter=args.adapter)
            return await _run_session(client, args)
    elif args.first:
        if not devices:
            return 1
        target = devices[0]
    elif args.index is not None:
        if args.index < 0 or args.index >= len(devices):
            print(f"index out of range (0..{len(devices)-1})")
            return 1
        target = devices[args.index]
    else:
        print("Specify --address, --first, or --index N")
        return 2

    assert target is not None
    client = AnkerBleClient(target, family=args.family or target.family, adapter=args.adapter)
    return await _run_session(client, args)


async def _run_session(client: AnkerBleClient, args: argparse.Namespace) -> int:
    try:
        await client.connect(timeout=args.connect_timeout)
    except Exception as exc:
        logging.getLogger(__name__).error("connect failed: %s", exc)
        return 1

    print("\nGATT services:")
    for line in client.list_gatt():
        print(f"  {line}")

    ok = True
    try:
        if args.confer:
            print("\nRunning ECDH confer…")
            ok = await client.start_confer(timeout=args.confer_timeout)
            print("Confer:", "SUCCESS" if ok else "FAILED")
            if ok and args.listen > 0:
                print(f"Listening {args.listen:.0f}s for telemetry…")
                packets = await client.listen(args.listen)
                print(f"Received {len(packets)} notification(s)")
                for pkt in packets[:20]:
                    print(f"  {pkt.hex()}")
        elif args.listen > 0:
            print(f"\nSubscribing and listening {args.listen:.0f}s…")
            packets = await client.listen(args.listen)
            print(f"Received {len(packets)} notification(s)")
            for pkt in packets[:20]:
                print(f"  {pkt.hex()}")
        else:
            # Brief hold so connection is observable
            await asyncio.sleep(args.hold)
    finally:
        await client.disconnect()

    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Anker BLE find & connect PoC")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument(
        "--adapter",
        default=None,
        help="BlueZ adapter name (e.g. hci1). Default: system default.",
    )

    sub = p.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Discover supported devices")
    scan.add_argument("--timeout", type=float, default=8.0)
    scan.set_defaults(func=cmd_scan)

    conn = sub.add_parser("connect", help="Scan, then connect to a device")
    conn.add_argument("--timeout", type=float, default=8.0, help="Scan duration")
    conn.add_argument("--connect-timeout", type=float, default=20.0)
    conn.add_argument("--address", help="Device MAC address")
    conn.add_argument("--first", action="store_true", help="Connect to strongest match")
    conn.add_argument("--index", type=int, help="Connect to Nth scan result")
    conn.add_argument("--family", choices=["8C85", "2215", "2540", "4158"])
    conn.add_argument(
        "--confer",
        action="store_true",
        help="Run FF09 ECDH session negotiation after connect",
    )
    conn.add_argument("--confer-timeout", type=float, default=60.0)
    conn.add_argument(
        "--listen",
        type=float,
        default=0.0,
        help="Seconds to listen for notifications after connect/confer",
    )
    conn.add_argument(
        "--hold",
        type=float,
        default=2.0,
        help="Seconds to stay connected when not listening/conferring",
    )
    conn.set_defaults(func=cmd_connect)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    return asyncio.run(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
