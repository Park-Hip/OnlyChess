"""Catalog-driven title screen."""

import pygame as p

from ... import savegame
from ...constants import HEIGHT, WIDTH
from ...runtime import EngineSession
from ..ui_constants import ACCENT_GOLD, CARD_BG, PANEL_BG, TEXT_PRIMARY
from .base import Screen
from .engine_game_screen import EngineGameScreen
from .mods_screen import ModsScreen


class MenuScreen(Screen):
    """Offer every linked game mode loaded at application startup."""

    row_height = 54
    top = 190

    def __init__(self, shared):
        super().__init__()
        self.shared = shared
        self.scroll = 0
        self.quit_rect = p.Rect(WIDTH // 2 - 100, HEIGHT - 80, 200, 48)
        self.mods_rect = p.Rect(WIDTH // 2 - 320, HEIGHT - 80, 200, 48)
        self.options_rect = p.Rect(WIDTH // 2 + 120, HEIGHT - 80, 200, 48)
        self.load_rect = p.Rect(WIDTH // 2 - 100, HEIGHT - 140, 200, 44)
        self.load_error = None

    @property
    def modes(self):
        return self.shared.app_context.modes

    def _visible_rows(self):
        return max(1, (self.quit_rect.top - self.top - 12) // self.row_height)

    def _row_rect(self, index):
        return p.Rect(WIDTH // 2 - 220, self.top + (index - self.scroll) * self.row_height, 440, self.row_height - 8)

    def _color(self, palette, token, fallback):
        return p.Color(palette[token]) if palette else fallback

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
        if self.mods_rect.collidepoint(position):
            self.next_screen = ModsScreen(self.shared)
            return
        if self.load_rect.collidepoint(position) and savegame.exists(self.shared.settings_root):
            self._load_saved_game()
            return
        if self.options_rect.collidepoint(position):
            from .options_screen import OptionsScreen  # deferred: options_screen imports this module
            self.next_screen = OptionsScreen(self.shared)
            return
        for index, mode in enumerate(self.modes):
            if self._row_rect(index).collidepoint(position):
                self.next_screen = EngineGameScreen(self.shared, session=EngineSession(self.shared.app_context.load_result, mode.id, time_limit=self.shared.settings.time_limit))
                return

    def _draw_backdrop(self, surface, chrome):
        """The shipped backdrop under a veil in the catalog's own colour.

        Layered rather than swapped: the menu deliberately takes its chrome from the first mode's
        palette, and dropping a photograph in place of that would throw the theme away. The veil is
        what keeps the title and the rows legible over an image core cannot predict.
        """
        veil = self._color(chrome, "background", PANEL_BG)
        background = getattr(self.shared, "menu_background", None)
        if background is None:
            surface.fill(veil)
            return
        surface.blit(p.transform.smoothscale(background, surface.get_size()), (0, 0))
        scrim = p.Surface(surface.get_size(), p.SRCALPHA)
        scrim.fill((veil.r, veil.g, veil.b, 190))
        surface.blit(scrim, (0, 0))

    def _load_saved_game(self):
        """Resume a saved game, or say why it cannot be resumed.

        A refusal is shown on the menu rather than raised: a save that no longer matches the
        installed mods is the player's problem to understand, not a crash to survive.
        """
        try:
            session = savegame.restore(self.shared.app_context.load_result, savegame.read(self.shared.settings_root))
        except savegame.SaveError as error:
            self.load_error = str(error)
            return
        self.next_screen = EngineGameScreen(self.shared, session=session)

    def draw(self, surface):
        chrome = self.modes[0].palette if self.modes else {}
        self._draw_backdrop(surface, chrome)
        title = self.shared.fonts["title"].render("OnlyChess", True, self._color(chrome, "accent", ACCENT_GOLD))
        surface.blit(title, title.get_rect(center=(WIDTH // 2, 90)))
        subtitle = self.shared.fonts["normal"].render("Choose a game mode", True, self._color(chrome, "text", TEXT_PRIMARY))
        surface.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 132)))
        for index, mode in enumerate(self.modes):
            rect = self._row_rect(index)
            if rect.bottom < self.top or rect.top >= self.quit_rect.top:
                continue
            p.draw.rect(surface, self._color(mode.palette, "panel", CARD_BG), rect, border_radius=8)
            p.draw.rect(surface, self._color(mode.palette, "selection", ACCENT_GOLD), rect, width=2, border_radius=8)
            label = f"{mode.name}  ({mode.rows} x {mode.columns})"
            text = self.shared.fonts["normal"].render(label, True, self._color(mode.palette, "text", TEXT_PRIMARY))
            surface.blit(text, text.get_rect(center=rect.center))
        if savegame.exists(self.shared.settings_root):
            p.draw.rect(surface, self._color(chrome, "panel", CARD_BG), self.load_rect, border_radius=8)
            p.draw.rect(surface, self._color(chrome, "selection", ACCENT_GOLD), self.load_rect, width=2, border_radius=8)
            resume = self.shared.fonts["normal"].render("Continue Saved Game", True, self._color(chrome, "text", TEXT_PRIMARY))
            surface.blit(resume, resume.get_rect(center=self.load_rect.center))
        if self.load_error:
            for index, line in enumerate(self.load_error.splitlines()):
                surface.blit(self.shared.fonts["small"].render(line, True, p.Color("#C86B5E")), (60, HEIGHT - 190 + index * 18))
        p.draw.rect(surface, self._color(chrome, "panel", CARD_BG), self.quit_rect, border_radius=8)
        p.draw.rect(surface, self._color(chrome, "selection", ACCENT_GOLD), self.quit_rect, width=2, border_radius=8)
        quit_text = self.shared.fonts["normal"].render("Quit", True, self._color(chrome, "text", TEXT_PRIMARY))
        surface.blit(quit_text, quit_text.get_rect(center=self.quit_rect.center))
        p.draw.rect(surface, self._color(chrome, "panel", CARD_BG), self.mods_rect, border_radius=8)
        p.draw.rect(surface, self._color(chrome, "selection", ACCENT_GOLD), self.mods_rect, width=2, border_radius=8)
        p.draw.rect(surface, self._color(chrome, "panel", CARD_BG), self.options_rect, border_radius=8)
        p.draw.rect(surface, self._color(chrome, "selection", ACCENT_GOLD), self.options_rect, width=2, border_radius=8)
        options_text = self.shared.fonts["normal"].render("Options", True, self._color(chrome, "text", TEXT_PRIMARY))
        surface.blit(options_text, options_text.get_rect(center=self.options_rect.center))
        mods_text = self.shared.fonts["normal"].render("Mods", True, self._color(chrome, "text", TEXT_PRIMARY))
        surface.blit(mods_text, mods_text.get_rect(center=self.mods_rect.center))
