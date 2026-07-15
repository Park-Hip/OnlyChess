"""Title screen shown before a game session starts."""

import pygame as p

from ...constants import HEIGHT, WIDTH
from ..ui_constants import ACCENT_GOLD, CARD_BG, TEXT_PRIMARY
from .base import Screen
from .game_screen import GameScreen

GAME_TITLE = "OnlyChess"
NEW_GAME_LABEL = "New Game"
LOAD_GAME_LABEL = "Load Game"
OPTIONS_LABEL = "Options"
QUIT_BUTTON_LABEL = "Quit"

BUTTON_WIDTH = 250
BUTTON_HEIGHT = 56
BUTTON_SPACING = 24
BUTTON_BORDER_RADIUS = 8
BUTTON_BORDER_WIDTH = 2

TITLE_CENTER_Y = HEIGHT // 3
BUTTONS_CENTER_Y = HEIGHT // 2


class MenuScreen(Screen):
    """Shows the game title with Start and Quit buttons.

    Clicking Start swaps to a fresh GameScreen. Clicking Quit requests
    application exit through the should_quit flag.
    """

    def __init__(self, shared):
        super().__init__()
        self.shared = shared
        
        # Calculate Y positions
        start_y = BUTTONS_CENTER_Y - (BUTTON_HEIGHT + BUTTON_SPACING) // 2
        
        self.new_game_rect = self._button_rect(center_y=start_y)
        self.load_game_rect = self._button_rect(center_y=start_y + (BUTTON_HEIGHT + BUTTON_SPACING))
        self.options_rect = self._button_rect(center_y=start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 2)
        self.quit_button_rect = self._button_rect(center_y=start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 3)

    @staticmethod
    def _button_rect(center_y):
        rect = p.Rect(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT)
        rect.center = (WIDTH // 2, center_y)
        return rect

    def handle_event(self, event):
        """Handle menu button clicks."""
        if event.type != p.MOUSEBUTTONDOWN:
            return
        mouse_pos = p.mouse.get_pos()
        if self.new_game_rect.collidepoint(mouse_pos):
            self.next_screen = GameScreen(self.shared)
        elif self.load_game_rect.collidepoint(mouse_pos):
            # TODO: Implement load game
            pass
        elif self.options_rect.collidepoint(mouse_pos):
            from .options_screen import OptionsScreen
            self.next_screen = OptionsScreen(self.shared)
        elif self.quit_button_rect.collidepoint(mouse_pos):
            self.should_quit = True

    def draw(self, surface):
        """Draw the background image, title, and the Start/Quit buttons."""
        surface.blit(self.shared.menu_background, (0, 0))

        title_font = self.shared.fonts["title"]
        title_surface = title_font.render(GAME_TITLE, True, ACCENT_GOLD)
        title_rect = title_surface.get_rect(center=(WIDTH // 2, TITLE_CENTER_Y))
        surface.blit(title_surface, title_rect)

        button_font = self.shared.fonts["normal"]
        self._draw_button(surface, button_font, self.new_game_rect, NEW_GAME_LABEL)
        self._draw_button(surface, button_font, self.load_game_rect, LOAD_GAME_LABEL)
        self._draw_button(surface, button_font, self.options_rect, OPTIONS_LABEL)
        self._draw_button(surface, button_font, self.quit_button_rect, QUIT_BUTTON_LABEL)

    @staticmethod
    def _draw_button(surface, font, rect, label):
        p.draw.rect(surface, CARD_BG, rect, border_radius=BUTTON_BORDER_RADIUS)
        p.draw.rect(surface, ACCENT_GOLD, rect, width=BUTTON_BORDER_WIDTH, border_radius=BUTTON_BORDER_RADIUS)
        text_surface = font.render(label, True, TEXT_PRIMARY)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)
