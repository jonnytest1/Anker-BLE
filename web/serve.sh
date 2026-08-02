#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "Serving Anker BLE web client at http://127.0.0.1:8765/"
echo "Press Ctrl+C to stop."
exec python3 -m http.server 8765 --bind 127.0.0.1
