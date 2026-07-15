"""Options screen for configuration."""

import pygame as p

from ...constants import HEIGHT, WIDTH
from ...config import game_config
from ..ui_constants import ACCENT_GOLD, CARD_BG, TEXT_PRIMARY, ACCENT_RED
from .base import Screen

TITLE_CENTER_Y = HEIGHT // 6
BUTTON_WIDTH = 250
BUTTON_HEIGHT = 40
BUTTON_SPACING = 15
BUTTON_BORDER_RADIUS = 8
BUTTON_BORDER_WIDTH = 2

# Preset colors for cycling
PIECE_COLORS = ["#FFFFFF", "#333333", "#FF5555", "#5555FF", "#55FF55", "#FFFF55", "#FF55FF", "#55FFFF"]
BOARD_LIGHT_COLORS = ["#E8D5B5", "#FFFFFF", "#FFDDDD", "#DDFFDD", "#DDDDFF", "#EEEEEE"]
BOARD_DARK_COLORS = ["#8B6F47", "#555555", "#AA5555", "#55AA55", "#5555AA", "#888888"]

class OptionsScreen(Screen):
    """Configuration menu."""

    def __init__(self, shared):
        super().__init__()
        self.shared = shared
        self.error_msg = None
        
        start_y = HEIGHT // 3
        
        self.time_btn = self._button_rect(start_y)
        self.wp_btn = self._button_rect(start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 1)
        self.bp_btn = self._button_rect(start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 2)
        self.ls_btn = self._button_rect(start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 3)
        self.ds_btn = self._button_rect(start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 4)
        
        self.save_btn = self._button_rect(start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 6)
        self.back_btn = self._button_rect(start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 7)

    @staticmethod
    def _button_rect(center_y):
        rect = p.Rect(0, 0, BUTTON_WIDTH + 100, BUTTON_HEIGHT)
        rect.center = (WIDTH // 2, center_y)
        return rect

    def handle_event(self, event):
        if event.type != p.MOUSEBUTTONDOWN:
            return
        mouse_pos = p.mouse.get_pos()
        
        if self.back_btn.collidepoint(mouse_pos):
            # Discard changes
            game_config.load()
            from .menu_screen import MenuScreen
            self.next_screen = MenuScreen(self.shared)
            
        elif self.save_btn.collidepoint(mouse_pos):
            error = game_config.get_color_validation_error()
            if error:
                self.error_msg = error
            else:
                game_config.save()
                from .menu_screen import MenuScreen
                self.next_screen = MenuScreen(self.shared)
                
        elif self.time_btn.collidepoint(mouse_pos):
            game_config.clock_minutes = 5 if game_config.clock_minutes == 15 else (15 if game_config.clock_minutes == 10 else 10)
        elif self.wp_btn.collidepoint(mouse_pos):
            self._cycle_color(PIECE_COLORS, "color_white_piece")
        elif self.bp_btn.collidepoint(mouse_pos):
            self._cycle_color(PIECE_COLORS, "color_black_piece")
        elif self.ls_btn.collidepoint(mouse_pos):
            self._cycle_color(BOARD_LIGHT_COLORS, "color_light_square")
        elif self.ds_btn.collidepoint(mouse_pos):
            self._cycle_color(BOARD_DARK_COLORS, "color_dark_square")

    def _cycle_color(self, color_list, config_attr):
        current = getattr(game_config, config_attr)
        if current in color_list:
            idx = (color_list.index(current) + 1) % len(color_list)
        else:
            idx = 0
        setattr(game_config, config_attr, color_list[idx])
        self.error_msg = None # Clear error on change

    def draw(self, surface):
        surface.blit(self.shared.menu_background, (0, 0))

        title_font = self.shared.fonts["title"]
        title_surface = title_font.render("Options", True, ACCENT_GOLD)
        title_rect = title_surface.get_rect(center=(WIDTH // 2, TITLE_CENTER_Y))
        surface.blit(title_surface, title_rect)

        button_font = self.shared.fonts["normal"]
        
        self._draw_button(surface, button_font, self.time_btn, f"Clock: {game_config.clock_minutes} mins")
        self._draw_button(surface, button_font, self.wp_btn, f"White Piece: {game_config.color_white_piece}", game_config.color_white_piece)
        self._draw_button(surface, button_font, self.bp_btn, f"Black Piece: {game_config.color_black_piece}", game_config.color_black_piece)
        self._draw_button(surface, button_font, self.ls_btn, f"Light Sq: {game_config.color_light_square}", game_config.color_light_square)
        self._draw_button(surface, button_font, self.ds_btn, f"Dark Sq: {game_config.color_dark_square}", game_config.color_dark_square)
        
        self._draw_button(surface, button_font, self.save_btn, "Save & Return")
        self._draw_button(surface, button_font, self.back_btn, "Cancel")
        
        if self.error_msg:
            err_surface = button_font.render(self.error_msg, True, ACCENT_RED)
            err_rect = err_surface.get_rect(center=(WIDTH // 2, self.save_btn.top - 20))
            surface.blit(err_surface, err_rect)

    @staticmethod
    def _draw_button(surface, font, rect, label, color_hex=None):
        p.draw.rect(surface, CARD_BG, rect, border_radius=BUTTON_BORDER_RADIUS)
        p.draw.rect(surface, ACCENT_GOLD, rect, width=BUTTON_BORDER_WIDTH, border_radius=BUTTON_BORDER_RADIUS)
        text_surface = font.render(label, True, TEXT_PRIMARY)
        text_rect = text_surface.get_rect(center=rect.center)
        
        if color_hex:
            # Shift text slightly to right to make room for swatch
            text_rect.x += 15
            swatch_rect = p.Rect(0, 0, 24, 24)
            swatch_rect.centery = rect.centery
            swatch_rect.right = text_rect.left - 10
            p.draw.rect(surface, p.Color(color_hex), swatch_rect, border_radius=4)
            p.draw.rect(surface, TEXT_PRIMARY, swatch_rect, width=1, border_radius=4)
            
        surface.blit(text_surface, text_rect)
