"""Choosing a face that can actually draw what content declares."""

from __future__ import annotations

import pygame as p

#: Preferred UI faces, best first. A mod's piece and status glyphs are arbitrary characters —
#: `proof:prism` declares `◆` — so the face has to carry more than Latin text, and a mod cannot
#: fix a bad choice here because the font belongs to core.
FONT_PREFERENCES = ("Segoe UI", "DejaVu Sans", "Noto Sans", "Liberation Sans", "FreeSans")


def font_family():
    """Return the first genuinely installed preferred face, or None for pygame's default.

    Availability is checked against `get_fonts()` rather than by passing the whole list to
    `SysFont`, because `match_font` resolves an *absent* name to its nearest neighbour: on a
    Linux box with no Segoe UI it happily returns Ubuntu, so a comma-separated preference list
    never reaches its own fallbacks. The failure is silent in the worst way — `Font.metrics()`
    reports a glyph the resolved face actually draws as `.notdef`, so unrenderable content
    looks like empty boxes rather than raising.
    """
    installed = set(p.font.get_fonts())
    for family in FONT_PREFERENCES:
        if family.lower().replace(" ", "") in installed:
            return family
    return None


