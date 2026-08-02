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
    kind: str = "charger"  # charger | bank | station | accessory


# Keys match SKU fragments / serial prefixes / product name hints from the app.
PRODUCT_ART: dict[str, ProductArt] = {
    # Anker Prime Charger (160W, 3 Ports, Smart Display)
    "a2687": ProductArt(
        "a2687",
        "a2687.png",
        "thumb_a2687.png",
        "Anker Prime Charger 160W",
        "charger",
    ),
    "a110a": ProductArt(
        "a110a", "a110a.png", "thumb_a110a.png", "Prime Power Bank A110A", "bank"
    ),
    "a110b": ProductArt(
        "a110b", "a110b.png", "thumb_a110b.png", "Prime Power Bank A110B", "bank"
    ),
    "a110g": ProductArt(
        "a110g", "a110g.png", "thumb_a110g.png", "MagGo / Prime A110G", "bank"
    ),
    "a1340": ProductArt(
        "a1340", "a1340.png", "a1340.png", "Anker Charger A1340", "charger"
    ),
    "a1341": ProductArt(
        "a1341", "a1341.png", "thumb_a1341.png", "Anker Charger A1341", "charger"
    ),
    "a1903": ProductArt(
        "a1903", "a1903.png", "thumb_a1903.png", "Prime Charging Base A1903", "charger"
    ),
    "a1770": ProductArt("a1770", "a1770.png", "a1770.png", "Solix A1770", "station"),
    "a1771": ProductArt("a1771", "a1771.png", "a1771.png", "Solix A1771", "station"),
    "a1772": ProductArt("a1772", "a1772.png", "a1772.png", "Solix A1772", "station"),
    "default": ProductArt(
        "default", "a2687.png", "thumb_a2687.png", "Anker Charger", "charger"
    ),
}

# Order matters: more specific hints first.
_SERIAL_HINTS: tuple[tuple[str, str], ...] = (
    ("a2687", "a2687"),
    ("ashd", "a2687"),  # observed Prime Charger 160W serials (ASHDJVV…)
    ("a110a", "a110a"),
    ("a110b", "a110b"),
    ("a110g", "a110g"),
    ("a1340", "a1340"),
    ("a1341", "a1341"),
    ("a1903", "a1903"),
    ("a1770", "a1770"),
    ("a1771", "a1771"),
    ("a1772", "a1772"),
    ("a2692", "a2687"),  # sibling high-watt charger → shared charger art for now
)


def resolve_product_key(
    product_name: str | None = None,
    serial: str | None = None,
    model: str | None = None,
) -> str:
    """Pick a catalog key from identity fields."""
    blob = " ".join(x for x in (product_name, serial, model) if x).lower()
    compact = blob.replace(" ", "").replace("-", "")
    if not compact:
        return "default"
    for hint, key in _SERIAL_HINTS:
        if hint in compact:
            return key
    # Confer often reports product_name "Charging" for Prime wall chargers
    if "charging" in blob and "base" not in blob and "bank" not in blob:
        return "a2687"
    if "prime charger" in blob or "160w" in compact or "charger 160" in blob:
        return "a2687"
    if "maggo" in blob:
        return "a110a"
    if "solix" in blob or "power house" in blob:
        return "a1770"
    if "power bank" in blob:
        return "a110a"
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
