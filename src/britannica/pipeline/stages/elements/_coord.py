"""Coordinate producer — `{{11co|DEG|[MIN|]DIR}}`, a single EB1911 lat/long value.

`{{11co|11|N}}` → 11° N; `{{11co|10|40|N}}` → 10° 40′ N (degrees, an optional
minutes value, then the N/S/E/W direction).  It had been a `{}` "column wrapper"
entry in the strip registry — mislabeled — so the strip leaked its arguments as
`11|N` text.  Carry it: render the degree / minute / direction glyphs.
"""
from __future__ import annotations

_DIRS = ("N", "S", "E", "W")


def process_coord(raw: str) -> str:
    """Render `{{11co|DEG|[MIN|]DIR}}` as `DEG° [MIN′ ]DIR`."""
    parts = [p.strip() for p in raw.strip().strip("{}").split("|")][1:]  # drop the name
    direction = parts.pop().upper() if parts and parts[-1].upper() in _DIRS else ""
    deg = parts[0] if parts else ""
    out = f"{deg}°"                       # degree sign
    if len(parts) >= 2 and parts[1]:
        out += f" {parts[1]}′"            # minutes (prime)
    if direction:
        out += f" {direction}"            # nbsp keeps the value with its direction
    return out
