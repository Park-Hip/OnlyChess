"""Help overlay rendering for controls and advanced-mode rules."""

import pygame as p

from ..constants import HEIGHT, WIDTH


HELP_SECTIONS = [
    ("Controls", ["Left-click/drag: move pieces", "Right-click own piece: abilities", "H: toggle this help"]),
    ("Fusion", ["Knight captures Bishop -> Archbishop", "Rook captures Knight -> Chancellor", "Rook captures Bishop -> Tempo Burst"]),
    ("Abilities", ["Knight Swap: 2 AP", "Bishop Snipe: 3 AP", "Rook Shield: 3 AP", "Pawn Sprint: 1 AP"]),
    ("Events", ["Warning appears on displayed turn 9", "Event resolves on displayed turn 10", "Then the cycle repeats every 10 turns"]),
]


def get_help_lines():
    """Return help overlay text as a flat list of drawable lines."""
    lines = []
    for title, items in HELP_SECTIONS:
        lines.append(title)
        lines.extend(f"- {item}" for item in items)
        lines.append("")
    return lines[:-1]


def draw_help_overlay(screen, font, width=WIDTH, height=HEIGHT):
    """Draw an in-game help overlay with controls and advanced-mode rules."""
    overlay = p.Surface((width, height))
    overlay.set_alpha(220)
    overlay.fill(p.Color("black"))
    screen.blit(overlay, (0, 0))

    title_font = p.font.SysFont("Helvetica", 28, True, False)
    title = title_font.render("Chess Fusion Help", True, p.Color("white"))
    screen.blit(title, (40, 35))

    y = 85
    for line in get_help_lines():
        color = p.Color("cyan") if line and not line.startswith("-") else p.Color("white")
        rendered_line = font.render(line, True, color)
        screen.blit(rendered_line, (45, y))
        y += 22

