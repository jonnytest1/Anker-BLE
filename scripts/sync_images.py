#!/usr/bin/env python3
"""Sync centralized assets/images into web + Home Assistant consumers.

Source of truth:
  assets/images/product/  → product heroes / thumbs
  assets/images/brand/    → HACS / HA brand icons

Destinations:
  web/images/
  custom_components/anker_ble/static/images/
  custom_components/anker_ble/brand/
  brand/   (repo-root mirror some HACS validators check)

Usage:
  python3 scripts/sync_images.py          # copy
  python3 scripts/sync_images.py --check  # exit 1 if destinations drift
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PRODUCT = ROOT / "assets" / "images" / "product"
SRC_BRAND = ROOT / "assets" / "images" / "brand"

DEST_WEB = ROOT / "web" / "images"
DEST_HA_STATIC = ROOT / "custom_components" / "anker_ble" / "static" / "images"
DEST_HA_BRAND = ROOT / "custom_components" / "anker_ble" / "brand"
DEST_ROOT_BRAND = ROOT / "brand"

BRAND_README = """# Brand assets

Synced from `assets/images/brand/` via `scripts/sync_images.py`.

Used by Home Assistant 2026.3+ via `/api/brands/integration/anker_ble/…`.

HACS Downloads may still show “icon not available” until HACS uses the local
brands proxy — see https://github.com/hacs/integration/issues/5223
"""


def _files(directory: Path, patterns: tuple[str, ...] = ("*.png", "*.svg", "*.md")) -> list[Path]:
    out: list[Path] = []
    if not directory.is_dir():
        return out
    for pattern in patterns:
        out.extend(sorted(directory.glob(pattern)))
    return out


def sync_dir(src: Path, dest: Path, *, wipe: bool = True) -> list[str]:
    if not src.is_dir():
        raise SystemExit(f"missing source directory: {src}")
    dest.mkdir(parents=True, exist_ok=True)
    if wipe:
        for existing in dest.iterdir():
            if existing.is_file() and existing.suffix.lower() in {".png", ".svg", ".md"}:
                if existing.name == "README.md":
                    continue
                existing.unlink()
    copied: list[str] = []
    for path in _files(src):
        target = dest / path.name
        shutil.copy2(path, target)
        copied.append(str(target.relative_to(ROOT)))
    return copied


def check_dir(src: Path, dest: Path) -> list[str]:
    errors: list[str] = []
    if not dest.is_dir():
        return [f"missing destination: {dest}"]
    src_files = {p.name: p for p in _files(src)}
    dest_files = {
        p.name: p
        for p in dest.iterdir()
        if p.is_file() and p.suffix.lower() in {".png", ".svg", ".md"} and p.name != "README.md"
    }
    for name, sp in src_files.items():
        dp = dest_files.get(name)
        if dp is None:
            errors.append(f"missing {dest.relative_to(ROOT)}/{name}")
            continue
        if not filecmp.cmp(sp, dp, shallow=False):
            errors.append(f"drift {dest.relative_to(ROOT)}/{name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify destinations match assets/ (no writes)",
    )
    args = parser.parse_args()

    targets = [
        (SRC_PRODUCT, DEST_WEB),
        (SRC_PRODUCT, DEST_HA_STATIC),
        (SRC_BRAND, DEST_HA_BRAND),
        (SRC_BRAND, DEST_ROOT_BRAND),
    ]

    if args.check:
        errors: list[str] = []
        for src, dest in targets:
            errors.extend(check_dir(src, dest))
        if errors:
            print("Image sync check FAILED:")
            for err in errors:
                print(f"  - {err}")
            print("\nRun: python3 scripts/sync_images.py")
            return 1
        print("Image sync check OK")
        return 0

    copied_all: list[str] = []
    for src, dest in targets:
        copied_all.extend(sync_dir(src, dest))

    DEST_HA_BRAND.mkdir(parents=True, exist_ok=True)
    (DEST_HA_BRAND / "README.md").write_text(BRAND_README)

    print(f"Synced {len(copied_all)} files from assets/images/")
    for path in copied_all:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
