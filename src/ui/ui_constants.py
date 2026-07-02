"""UI-only constants for board and panel rendering — Classic Warmth palette."""

import pygame as p


# Board square colors
COLOR_LIGHT = p.Color("#E8D5B5")  # Cream
COLOR_DARK = p.Color("#8B6F47")   # Warm brown

# Panel backgrounds
PANEL_BG = p.Color("#2B1B17")       # Mahogany (main panels)
SIDEBAR_BG = p.Color("#3B2921")     # Walnut (sidebar / elevated)
CARD_BG = p.Color("#4A3728")        # Dark oak (cards, menus, modals)

# Text colors
TEXT_PRIMARY = p.Color("#D4C5A9")    # Parchment
TEXT_SECONDARY = p.Color("#8B7D6B")  # Dim / muted

# Accent colors
ACCENT_GOLD = p.Color("#C9A84C")     # Highlights, borders, headings
ACCENT_GREEN = p.Color("#6B8E6B")    # AP display
ACCENT_RED = p.Color("#B85450")      # Warnings

# Separator
SEPARATOR = p.Color("#5A4A3A")

# Deprecated aliases kept for backward compatibility with tests
PANEL_BACKGROUND = "#2B1B17"
