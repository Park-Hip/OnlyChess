"""Catalog-driven title screen."""

import pygame as p

from ...constants import HEIGHT, WIDTH
from ...runtime import EngineSession
from ..ui_constants import ACCENT_GOLD, CARD_BG, TEXT_PRIMARY
from .base import Screen
from .engine_game_screen import EngineGameScreen


class MenuScreen(Screen):
    """Offer every linked game mode loaded at application startup."""

    row_height = 54
    top = 190

    def __init__(self, shared):
        super().__init__()
        self.shared = shared
        self.scroll = 0
        self.quit_rect = p.Rect(WIDTH // 2 - 100, HEIGHT - 80, 200, 48)

    @property
    def modes(self):
        return self.shared.app_context.modes

    def _visible_rows(self):
        return max(1, (self.quit_rect.top - self.top - 12) // self.row_height)

    def _row_rect(self, index):
        return p.Rect(WIDTH // 2 - 220, self.top + (index - self.scroll) * self.row_height, 440, self.row_height - 8)

    def handle_event(self, event):
        if event.type == p.MOUSEWHEEL:
            self.scroll = max(0, min(max(0, len(self.modes) - self._visible_rows()), self.scroll - event.y))
            return
        if event.type != p.MOUSEBUTTONDOWN or event.button != 1:
            return
        position = p.mouse.get_pos()
        if self.quit_rect.collidepoint(position):
            self.should_quit = True
            return
        for index, mode in enumerate(self.modes):
            if self._row_rect(index).collidepoint(position):
                self.next_screen = EngineGameScreen(self.shared, session=EngineSession(self.shared.app_context.load_result, mode.id))
                return

    def draw(self, surface):
        surface.blit(self.shared.menu_background, (0, 0))
        title = self.shared.fonts["title"].render("OnlyChess", True, ACCENT_GOLD)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, 90)))
        subtitle = self.shared.fonts["normal"].render("Choose a game mode", True, TEXT_PRIMARY)
        surface.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 132)))
        for index, mode in enumerate(self.modes):
            rect = self._row_rect(index)
            if rect.bottom < self.top or rect.top >= self.quit_rect.top:
                continue
            p.draw.rect(surface, CARD_BG, rect, border_radius=8)
            p.draw.rect(surface, ACCENT_GOLD, rect, width=2, border_radius=8)
            label = f"{mode.name}  ({mode.rows} x {mode.columns})"
            text = self.shared.fonts["normal"].render(label, True, TEXT_PRIMARY)
            surface.blit(text, text.get_rect(center=rect.center))
        p.draw.rect(surface, CARD_BG, self.quit_rect, border_radius=8)
        p.draw.rect(surface, ACCENT_GOLD, self.quit_rect, width=2, border_radius=8)
        quit_text = self.shared.fonts["normal"].render("Quit", True, TEXT_PRIMARY)
        surface.blit(quit_text, quit_text.get_rect(center=self.quit_rect.center))
