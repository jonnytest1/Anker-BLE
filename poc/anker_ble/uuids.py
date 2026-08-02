"""GATT / discovery UUIDs from Anker app 3.22.0."""

from __future__ import annotations

IDENTIFIER_UUID = "0000ff09-0000-1000-8000-00805f9b34fb"

# 16-bit / base-UUID identifiers seen in advertising or GATT
EXTRA_IDENTIFIER_UUIDS = (
    IDENTIFIER_UUID,
    "0000ef0a-0000-1000-8000-00805f9b34fb",
    "0000ef0b-0000-1000-8000-00805f9b34fb",
    "00001770-0000-1000-8000-00805f9b34fb",
    "00001780-0000-1000-8000-00805f9b34fb",
    "000017a0-0000-1000-8000-00805f9b34fb",
    "000017a1-0000-1000-8000-00805f9b34fb",
    "000017a2-0000-1000-8000-00805f9b34fb",
    "00002540-0000-1000-8000-00805f9b34fb",
)

# Custom families: service / write / notify
UUID_FAMILIES: dict[str, dict[str, str]] = {
    "8C85": {
        "service": "8c850001-0302-41c5-b46e-cf057c562025",
        "write": "8c850002-0302-41c5-b46e-cf057c562025",
        "notify": "8c850003-0302-41c5-b46e-cf057c562025",
    },
    "2215": {
        "service": "22150001-4002-81c5-b46e-cf057c562025",
        "write": "22150002-4002-81c5-b46e-cf057c562025",
        "notify": "22150003-4002-81c5-b46e-cf057c562025",
    },
    "2540": {
        "service": "25400001-4002-81c5-b46e-cf057c562025",
        "write": "25400002-4002-81c5-b46e-cf057c562025",
        "notify": "25400003-4002-81c5-b46e-cf057c562025",
    },
    "4158": {
        "service": "41580001-4002-81c5-b46e-cf057c562025",
        "write": "41580002-4002-81c5-b46e-cf057c562025",
        "notify": "41580003-4002-81c5-b46e-cf057c562025",
    },
}

# Name prefixes commonly used by Anker power / Solix products
NAME_HINTS = (
    "anker",
    "solix",
    "a17",
    "a51",
    "a17c",
    "a17x",
    "a178",
    "a179",
    "a176",
    "a175",
    "pps",
    "c300",
    "c800",
    "c1000",
    "f2000",
    "f3800",
    "solarbank",
)


def normalize_uuid(value: str) -> str:
    return value.lower()


def match_uuid_family(service_uuids: list[str]) -> str | None:
    """Return family key if a known Anker service UUID is present."""
    lowered = {normalize_uuid(u) for u in service_uuids}
    for family, uuids in UUID_FAMILIES.items():
        if normalize_uuid(uuids["service"]) in lowered:
            return family
    return None
