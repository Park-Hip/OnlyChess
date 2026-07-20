"""Player preferences, edited by cycling through curated choices.

Cycling rather than a colour picker: a curated list cannot produce a combination that fails the
contrast check by accident, and it needs no widget core does not already have. The check still runs
on save, because a mod's theme can supply a colour the presets were never compared against.
"""

from __future__ import annotations

import pygame as p

from ...constants import HEIGHT, WIDTH
from ...settings import CLOCK_CHOICES, COLOR_CHOICES, Settings
from ..ui_constants import ACCENT_GOLD, CARD_BG, PANEL_BG, TEXT_PRIMARY
from .base import Screen

#: Rows, in display order: the setting key, its label, and the choices it cycles through.
ROWS = (
    ("clock_minutes", "Time limit", CLOCK_CHOICES),
    ("light_square", "Light squares", COLOR_CHOICES["light_square"]),
    ("dark_square", "Dark squares", COLOR_CHOICES["dark_square"]),
    ("piece_first", "Piece colour (first)", COLOR_CHOICES["piece_first"]),
    ("piece_second", "Piece colour (second)", COLOR_CHOICES["piece_second"]),
)


class OptionsScreen(Screen):
    """Edit a copy of the settings; nothing reaches disk or the game until Save."""

    def __init__(self, shared):
        super().__init__()
        self.shared = shared
        # A working copy, so Cancel is genuinely a cancel rather than an undo of live changes.
        self.draft = Settings(clock_minutes=shared.settings.clock_minutes, colors=dict(shared.settings.colors))
        self.problems: list[str] = []
        self.save_rect = p.Rect(WIDTH // 2 - 210, HEIGHT - 80, 200, 48)
        self.cancel_rect = p.Rect(WIDTH // 2 + 10, HEIGHT - 80, 200, 48)

    def _row_rect(self, index):
        return p.Rect(120, 150 + index * 56, WIDTH - 240, 44)

    def _value(self, key):
        return self.draft.clock_minutes if key == "clock_minutes" else self.draft.colors.get(key)

    def _label(self, key, value):
        if key == "clock_minutes":
            return "No clock" if value is None else f"{value} minutes"
        return value or "Mod default"

    def _cycle(self, key, choices):
        """Step to the next choice. An unset colour starts the cycle rather than being skipped, so
        a player who has never chosen one still reaches every option."""
        current = self._value(key)
        options = list(choices) if key == "clock_minutes" else [None, *choices]
        index = options.index(current) if current in options else 0
        nxt = options[(index + 1) % len(options)]
        if key == "clock_minutes":
            self.draft.clock_minutes = nxt
        elif nxt is None:
            self.draft.colors.pop(key, None)
        else:
            self.draft.colors[key] = nxt
        self.problems = []

    def handle_event(self, event):
        if event.type == p.KEYDOWN and event.key in (p.K_ESCAPE, p.K_BACKSPACE):
            self._leave(); return
        if event.type != p.MOUSEBUTTONDOWN or event.button != 1:
            return
        position = p.mouse.get_pos()
        for index, (key, _, choices) in enumerate(ROWS):
            if self._row_rect(index).collidepoint(position):
                self._cycle(key, choices)
                return
        if self.save_rect.collidepoint(position):
            self._save()
        elif self.cancel_rect.collidepoint(position):
            self._leave()

    def _save(self):
        # Refuse rather than warn: a saved combination nobody can see is not a preference, and the
        # player is one click from a readable one.
        self.problems = self.draft.conflicts()
        if self.problems:
            return
        self.shared.settings.clock_minutes = self.draft.clock_minutes
        self.shared.settings.colors = dict(self.draft.colors)
        self.shared.settings.save(self.shared.settings_root)
        self._leave()

    def _leave(self):
        from .menu_screen import MenuScreen  # deferred: menu_screen imports this module at top level
        self.next_screen = MenuScreen(self.shared)

    def draw(self, surface):
        surface.fill(PANEL_BG)
        title = self.shared.fonts["title"].render("Options", True, ACCENT_GOLD)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, 90)))

        for index, (key, label, _) in enumerate(ROWS):
            rect = self._row_rect(index)
            p.draw.rect(surface, CARD_BG, rect, border_radius=8)
            p.draw.rect(surface, ACCENT_GOLD, rect, width=1, border_radius=8)
            surface.blit(self.shared.fonts["normal"].render(label, True, TEXT_PRIMARY), (rect.x + 16, rect.y + 12))
            value = self._value(key)
            text = self.shared.fonts["normal"].render(self._label(key, value), True, TEXT_PRIMARY)
            surface.blit(text, (rect.right - text.get_width() - 56, rect.y + 12))
            if key != "clock_minutes" and value:
                # Show the colour itself; a hex string is not a preview.
                swatch = p.Rect(rect.right - 40, rect.y + 10, 24, 24)
                p.draw.rect(surface, p.Color(value), swatch, border_radius=4)
                p.draw.rect(surface, ACCENT_GOLD, swatch, width=1, border_radius=4)

        for index, problem in enumerate(self.problems):
            warning = self.shared.fonts["small"].render(problem, True, p.Color("#C86B5E"))
            surface.blit(warning, (120, HEIGHT - 130 + index * 20))

        for rect, label in ((self.save_rect, "Save"), (self.cancel_rect, "Cancel")):
            p.draw.rect(surface, CARD_BG, rect, border_radius=8)
            p.draw.rect(surface, ACCENT_GOLD, rect, width=2, border_radius=8)
            text = self.shared.fonts["normal"].render(label, True, TEXT_PRIMARY)
            surface.blit(text, text.get_rect(center=rect.center))
