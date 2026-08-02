"""Product artwork catalog extracted from the Anker app."""

from __future__ import annotations

from dataclasses import dataclass

STATIC_URL_PREFIX = "/anker_ble_static"
IMAGES_SUBDIR = "images"


@dataclass(frozen=True)
class ProductArt:
    """Mapped product artwork filenames."""

    key: str
    hero: str
    thumb: str
    label: str


# Keys match SKU fragments / serial prefixes / product name hints from the app.
PRODUCT_ART: dict[str, ProductArt] = {
    "a110a": ProductArt("a110a", "a110a.png", "thumb_a110a.png", "MagGo Pad A110A"),
    "a110b": ProductArt("a110b", "a110b.png", "thumb_a110b.png", "MagGo Pad A110B"),
    "a110g": ProductArt("a110g", "a110g.png", "thumb_a110g.png", "MagGo Pad A110G"),
    "a1340": ProductArt("a1340", "a1340.png", "a1340.png", "Anker Charger A1340"),
    "a1341": ProductArt("a1341", "a1341.png", "thumb_a1341.png", "Anker Charger A1341"),
    "a1903": ProductArt("a1903", "a1903.png", "thumb_a1903.png", "MagGo Battery A1903"),
    "a1770": ProductArt("a1770", "a1770.png", "a1770.png", "Solix A1770"),
    "a1771": ProductArt("a1771", "a1771.png", "a1771.png", "Solix A1771"),
    "a1772": ProductArt("a1772", "a1772.png", "a1772.png", "Solix A1772"),
    "default": ProductArt("default", "default.png", "thumb_a110a.png", "Anker Device"),
}

# Serial / marketing-name heuristics used by MagGo-style chargers.
_SERIAL_HINTS: tuple[tuple[str, str], ...] = (
    ("ashd", "a110a"),  # observed MagGo-style Charging serials
    ("a110a", "a110a"),
    ("a110b", "a110b"),
    ("a110g", "a110g"),
    ("a1340", "a1340"),
    ("a1341", "a1341"),
    ("a1903", "a1903"),
    ("a1770", "a1770"),
    ("a1771", "a1771"),
    ("a1772", "a1772"),
)


def resolve_product_key(
    product_name: str | None = None,
    serial: str | None = None,
    model: str | None = None,
) -> str:
    """Pick a catalog key from identity fields."""
    blob = " ".join(x for x in (product_name, serial, model) if x).lower()
    if not blob:
        return "default"
    for hint, key in _SERIAL_HINTS:
        if hint in blob.replace(" ", "").replace("-", ""):
            return key
    # Product name "Charging" → MagGo pad default art
    if "charging" in blob or "maggo" in blob:
        return "a110a"
    if "solix" in blob:
        return "a1770"
    return "default"


def art_for_identity(
    product_name: str | None = None,
    serial: str | None = None,
    model: str | None = None,
) -> ProductArt:
    key = resolve_product_key(product_name, serial, model)
    return PRODUCT_ART.get(key, PRODUCT_ART["default"])


def static_image_url(filename: str) -> str:
    return f"{STATIC_URL_PREFIX}/{IMAGES_SUBDIR}/{filename}"


def hero_url(
    product_name: str | None = None,
    serial: str | None = None,
    model: str | None = None,
) -> str:
    return static_image_url(art_for_identity(product_name, serial, model).hero)


def thumb_url(
    product_name: str | None = None,
    serial: str | None = None,
    model: str | None = None,
) -> str:
    return static_image_url(art_for_identity(product_name, serial, model).thumb)
