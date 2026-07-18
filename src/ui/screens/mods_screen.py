"""Read-only installed-mod and loader-error report."""

from __future__ import annotations

import pygame as p

from ...constants import HEIGHT, WIDTH
from ..ui_constants import ACCENT_GOLD, CARD_BG, PANEL_BG, TEXT_PRIMARY, TEXT_SECONDARY
from .base import Screen


class ModsScreen(Screen):
    """Show trust metadata and attributed load errors without managing mods."""

    def __init__(self, shared):
        super().__init__()
        self.shared = shared
        self.back_rect = p.Rect(WIDTH // 2 - 100, HEIGHT - 80, 200, 48)

    @property
    def context(self):
        return self.shared.app_context

    def _palette(self):
        return self.context.modes[0].palette if self.context.modes else {}

    def _color(self, palette, token, fallback):
        return p.Color(palette[token]) if palette else fallback

    def handle_event(self, event):
        if event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
            self._back()
        elif event.type == p.MOUSEBUTTONDOWN and event.button == 1 and self.back_rect.collidepoint(p.mouse.get_pos()):
            self._back()

    def _back(self):
        from .menu_screen import MenuScreen
        self.next_screen = MenuScreen(self.shared)

    def draw(self, surface):
        palette = self._palette()
        surface.fill(self._color(palette, "background", PANEL_BG))
        title = self.shared.fonts["title"].render("Mods", True, self._color(palette, "accent", ACCENT_GOLD))
        surface.blit(title, title.get_rect(center=(WIDTH // 2, 70)))
        y = 120
        for info in self.context.installed:
            row = p.Rect(80, y, WIDTH - 160, 42)
            p.draw.rect(surface, self._color(palette, "panel", CARD_BG), row, border_radius=6)
            label = self.shared.fonts["normal"].render(f"{info.name}  ({info.mod_id})", True, self._color(palette, "text", TEXT_PRIMARY))
            surface.blit(label, (row.x + 12, row.y + 12))
            if info.ships_code:
                warning = self.shared.fonts["small"].render("TRUST: SHIPS CODE", True, self._color(palette, "warning", ACCENT_GOLD))
                surface.blit(warning, (row.right - warning.get_width() - 12, row.y + 14))
            y += 50
        for error in self.context.errors:
            for line in error.format().splitlines():
                if y >= self.back_rect.top - 8:
                    break
                text = self.shared.fonts["small"].render(line, True, self._color(palette, "warning", TEXT_SECONDARY))
                surface.blit(text, (80, y))
                y += 18
        p.draw.rect(surface, self._color(palette, "panel", CARD_BG), self.back_rect, border_radius=8)
        p.draw.rect(surface, self._color(palette, "selection", ACCENT_GOLD), self.back_rect, width=2, border_radius=8)
        back = self.shared.fonts["normal"].render("Back", True, self._color(palette, "text", TEXT_PRIMARY))
        surface.blit(back, back.get_rect(center=self.back_rect.center))
