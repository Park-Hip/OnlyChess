"""Pygame entry point for the chess application.

main() is a thin orchestrator: it initializes pygame, loads shared
resources once, and forwards events/update/draw to whichever Screen is
currently active, swapping screens or exiting when a screen requests it.
"""

import pygame as p

from .constants import HEIGHT, MAX_FPS, WIDTH, get_resource_path
from .ui.assets import load_images
from .ui.audio import SoundPlayer, load_sounds
from .ui.screens.menu_screen import MenuScreen
from .ui.screens.shared_resources import SharedResources
from .ui.ui_constants import PANEL_BG

MENU_BACKGROUND_PATH = "images/6h50_2.png"


def _load_fonts():
    """Load fonts once — Segoe UI for consistent Vietnamese character support."""
    return {
        "title": p.font.SysFont("Segoe UI", 24, bold=True),
        "normal": p.font.SysFont("Segoe UI", 16, bold=True),
        "small": p.font.SysFont("Segoe UI", 13),
    }


def _load_menu_background(image_loader=None, scaler=None):
    """Load and scale the menu screen background to fill the window."""
    if image_loader is None:
        image_loader = p.image.load
    if scaler is None:
        scaler = p.transform.smoothscale
    background = image_loader(get_resource_path(MENU_BACKGROUND_PATH)).convert()
    return scaler(background, (WIDTH, HEIGHT))


def _load_sound_player():
    """Initialize the audio mixer and load sound effects, if audio is available."""
    try:
        p.mixer.init()
    except p.error as e:
        print(f"Warning: audio disabled ({e}).")
        return SoundPlayer()
    return SoundPlayer(load_sounds())


def main():
    """Run the main Pygame application loop, swapping between screens."""
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    p.display.set_caption("OnlyChess")
    clock = p.time.Clock()
    screen.fill(PANEL_BG)

    images = load_images(image_loader=p.image.load, scaler=p.transform.scale)
    menu_background = _load_menu_background()
    sound_player = _load_sound_player()
    shared = SharedResources(
        images=images,
        fonts=_load_fonts(),
        menu_background=menu_background,
        sound_player=sound_player,
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
