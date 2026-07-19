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
from .ui.fonts import font_family
from .ui.screens.menu_screen import MenuScreen
from .ui.screens.shared_resources import SharedResources
from .ui.ui_constants import PANEL_BG

REPO_ROOT = Path(__file__).resolve().parents[1]


def _menu_background():
    """The title screen's backdrop: the shipped image when it is there, a flat fill when it is not.

    Application chrome rather than mod content — no mode is selected yet, so there is no theme to
    ask. A missing or unreadable file degrades to the fill rather than stopping startup, on the same
    reasoning as the audio and cursor guards.
    """
    background = p.Surface((WIDTH, HEIGHT))
    background.fill(PANEL_BG)
    image_path = REPO_ROOT / "images" / "6h50_2.png"
    if image_path.is_file():
        try:
            return p.transform.smoothscale(p.image.load(str(image_path)).convert(), (WIDTH, HEIGHT))
        except p.error:
            pass
    return background


def _load_fonts():
    """Load fonts once, from a face that can draw mod-supplied glyphs on this platform."""
    family = font_family()
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

    menu_background = _menu_background()
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
