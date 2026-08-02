# Anker BLE — Web Bluetooth client

Browser-only page to scan, connect, run FF09 ECDH confer, and read telemetry.

## Hosted (GitHub Pages)

After the first successful Pages deploy:

`https://<owner>.github.io/<repo>/`

HTTPS is required for Web Bluetooth on non-localhost origins.

## Do not open `index.html` as a file

Chrome blocks scripts and **Web Bluetooth** under `file://`.  
Serve over HTTP instead (or use the Pages URL above).

## Run (Windows)

1. Copy this `web` folder wherever you like
2. Double-click **`serve.bat`** (or in that folder: `python -m http.server 8765`)
3. Open **[http://127.0.0.1:8765/](http://127.0.0.1:8765/)** in Chrome or Edge

## Run (macOS / Linux)

```bash
cd web
./serve.sh
# or: python3 -m http.server 8765 --bind 127.0.0.1
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/)

## Requirements

- Chrome or Edge (desktop or Android)
- `http://localhost…` or HTTPS
- Device nearby and advertising

Safari / Firefox desktop do not support Web Bluetooth.

## Use

1. **Scan & connect** (FF09 filter) or **Pick any device**
2. Confer runs automatically, then telemetry subscribe
3. Identity + power fields appear when session frames decrypt

## Files

| File | Role |
|------|------|
| `index.html` | Self-contained UI + protocol (no external JS) |
| `serve.bat` / `serve.sh` | Local static server |
