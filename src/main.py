"""Pygame entry point for the chess application.

main() is a thin orchestrator: it initializes pygame, loads shared
resources once, and forwards events/update/draw to whichever Screen is
currently active, swapping screens or exiting when a screen requests it.
"""

import pygame as p

from pathlib import Path

from .constants import HEIGHT, MAX_FPS, WIDTH
from .runtime import ApplicationContext
from .settings import Settings
from .ui.screens.menu_screen import MenuScreen
from .ui.screens.shared_resources import SharedResources
from .ui.ui_constants import PANEL_BG

REPO_ROOT = Path(__file__).resolve().parents[1]


#: Preferred UI faces, best first. A mod's piece and status glyphs are arbitrary characters —
#: `proof:prism` declares `◆` — so the face has to carry more than Latin text, and a mod cannot
#: fix a bad choice here because the font belongs to core.
_FONT_PREFERENCES = ("Segoe UI", "DejaVu Sans", "Noto Sans", "Liberation Sans", "FreeSans")


def _font_family():
    """Return the first genuinely installed preferred face, or None for pygame's default.

    Availability is checked against `get_fonts()` rather than by passing the whole list to
    `SysFont`, because `match_font` resolves an *absent* name to its nearest neighbour: on a
    Linux box with no Segoe UI it happily returns Ubuntu, so a comma-separated preference list
    never reaches its own fallbacks. The failure is silent in the worst way — `Font.metrics()`
    reports a glyph the resolved face actually draws as `.notdef`, so unrenderable content
    looks like empty boxes rather than raising.
    """
    installed = set(p.font.get_fonts())
    for family in _FONT_PREFERENCES:
        if family.lower().replace(" ", "") in installed:
            return family
    return None


def _load_fonts():
    """Load fonts once, from a face that can draw mod-supplied glyphs on this platform."""
    family = _font_family()
    return {
        "title": p.font.SysFont(family, 24, bold=True),
        "normal": p.font.SysFont(family, 16, bold=True),
        "small": p.font.SysFont(family, 13),
    }


def main():
    """Run the main Pygame application loop, swapping between screens."""
    p.init()
    # Audio playback is core's job, but it must never take the game down: a machine
    # with no output device should still run silently. The presentation runtime guards
    # every play() call with mixer.get_init(), so a failure here degrades to no sound.
    try:
        p.mixer.init()
    except p.error:
        pass
    screen = p.display.set_mode((WIDTH, HEIGHT))
    p.display.set_caption("OnlyChess")
    clock = p.time.Clock()
    screen.fill(PANEL_BG)

    menu_background = p.Surface((WIDTH, HEIGHT))
    menu_background.fill(PANEL_BG)
    shared = SharedResources(
        images={},
        fonts=_load_fonts(),
        menu_background=menu_background,
        app_context=ApplicationContext.load(),
        settings=Settings.load(REPO_ROOT),
        settings_root=REPO_ROOT,
    )

    current_screen = MenuScreen(shared)
    running = True

    while running:
        for event in p.event.get():
            if event.type == p.QUIT:
                running = False
                continue
            current_screen.handle_event(event)

        if not running or current_screen.should_quit:
            break

        if current_screen.next_screen is not None:
            current_screen = current_screen.next_screen

        current_screen.update()
        current_screen.draw(screen)

        clock.tick(MAX_FPS)
        p.display.flip()


if __name__ == "__main__":
    main()
