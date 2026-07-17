"""Minimal pygame presentation for a game owned by :class:`EngineSession`."""

from __future__ import annotations

import pygame as p

from ...constants import BOARD_HEIGHT, BOARD_WIDTH, INFO_PANEL_HEIGHT, SQ_SIZE
from ...runtime import EngineSession
from ..ui_constants import ACCENT_GOLD, COLOR_DARK, COLOR_LIGHT, PANEL_BG, TEXT_PRIMARY
from .base import Screen


_PIECE_GLYPHS = {
    "pawn": "P", "knight": "N", "bishop": "B", "rook": "R", "queen": "Q", "king": "K",
    "archbishop": "A", "chancellor": "C", "warden": "W", "inquisitor": "I",
}


class EngineGameScreen(Screen):
    """Render and select engine moves without importing legacy game code."""

    def __init__(self, shared, *, session=None):
        super().__init__()
        self.shared = shared
        self.session = session or EngineSession()
        self.selected_square = None
        self.pending_move = None
        self.pending_ability = None
        self.error_message = None

    def handle_event(self, event):
        if event.type == p.KEYDOWN and event.key == p.K_z and (event.mod & p.KMOD_CTRL):
            self.session.undo()
            self.selected_square = None
            return
        if event.type == p.KEYDOWN and self.pending_move is not None:
            choices = {choice.rsplit(":", 1)[-1][0].lower(): choice for choice in self.pending_move.choices}
            choice = choices.get(event.unicode.lower())
            if choice:
                self.session.move(self.pending_move.start, self.pending_move.end, choice=choice)
                self.pending_move = None
            return
        if event.type == p.KEYDOWN and event.key == p.K_a and self.selected_square is not None:
            abilities = self.session.abilities_for(self.selected_square)
            if abilities:
                ability_id = abilities[0]
                if self.session.state.ability_defs[ability_id].target == "self":
                    try:
                        self.session.use_ability(self.selected_square, ability_id)
                    except ValueError as error:
                        self.error_message = str(error)
                        return
                    self.selected_square = None
                else:
                    self.pending_ability = ability_id
            return
        if event.type != p.MOUSEBUTTONDOWN or event.button != 1 or self.pending_move is not None:
            return
        square = self._square_at(p.mouse.get_pos())
        if square is None:
            return
        if self.pending_ability is not None:
            try:
                self.session.use_ability(self.selected_square, self.pending_ability, target=square)
            except ValueError as error:
                self.error_message = str(error)
                return
            self.pending_ability = None
            self.selected_square = None
            return
        if self.selected_square is None:
            if self.session.state.board.at(square) is not None:
                self.selected_square = square
            return
        candidates = [move for move in self.session.moves_from(self.selected_square) if move.end == square]
        if candidates:
            move = candidates[0]
            if move.choices:
                self.pending_move = move
            else:
                self.session.move(move.start, move.end)
            self.selected_square = None
        else:
            self.selected_square = square if self.session.state.board.at(square) is not None else None

    def update(self):
        return None

    def draw(self, surface):
        surface.fill(PANEL_BG)
        self._draw_header(surface)
        self._draw_board(surface)
        self._draw_messages(surface)
        if self.session.outcome:
            text = self.shared.fonts["title"].render(self.session.outcome, True, ACCENT_GOLD)
            surface.blit(text, text.get_rect(center=(BOARD_WIDTH // 2, INFO_PANEL_HEIGHT + BOARD_HEIGHT // 2)))

    def _square_at(self, position):
        x, y = position
        row, col = (y - INFO_PANEL_HEIGHT) // SQ_SIZE, x // SQ_SIZE
        if 0 <= row < self.session.state.board.rows and 0 <= col < self.session.state.board.columns:
            return row, col
        return None

    def _draw_header(self, surface):
        label = f"{self.session.state.current_side.rsplit(':', 1)[-1].title()} to move  |  Ctrl-Z: undo | A: ability"
        text = self.shared.fonts["normal"].render(label, True, TEXT_PRIMARY)
        surface.blit(text, (12, 12))

    def _draw_board(self, surface):
        board = self.session.state.board
        targets = {move.end for move in self.session.moves_from(self.selected_square)} if self.selected_square else set()
        for row in range(board.rows):
            for col in range(board.columns):
                rect = p.Rect(col * SQ_SIZE, INFO_PANEL_HEIGHT + row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
                p.draw.rect(surface, (COLOR_LIGHT, COLOR_DARK)[(row + col) % 2], rect)
                if (row, col) == self.selected_square:
                    p.draw.rect(surface, ACCENT_GOLD, rect, 4)
                elif (row, col) in targets:
                    p.draw.circle(surface, ACCENT_GOLD, rect.center, SQ_SIZE // 7)
                piece = board.at((row, col))
                if piece:
                    name = piece.definition.id.rsplit(":", 1)[-1]
                    glyph = _PIECE_GLYPHS.get(name, name[:1].upper())
                    color = p.Color("white") if piece.side.endswith(":white") else p.Color("black")
                    text = self.shared.fonts["title"].render(glyph, True, color)
                    surface.blit(text, text.get_rect(center=rect.center))

    def _draw_messages(self, surface):
        x = BOARD_WIDTH + 16
        title = self.shared.fonts["normal"].render("Game log", True, TEXT_PRIMARY)
        surface.blit(title, (x, INFO_PANEL_HEIGHT + 12))
        for index, message in enumerate(self.session.state.event_messages[-12:]):
            text = self.shared.fonts["small"].render(message, True, TEXT_PRIMARY)
            surface.blit(text, (x, INFO_PANEL_HEIGHT + 42 + index * 22))
        if self.pending_move is not None:
            choices = "/".join(choice.rsplit(":", 1)[-1][0].upper() for choice in self.pending_move.choices)
            prompt = self.shared.fonts["normal"].render(f"Promote: press {choices}", True, ACCENT_GOLD)
            surface.blit(prompt, (x, INFO_PANEL_HEIGHT + 320))
        elif self.pending_ability is not None:
            prompt = self.shared.fonts["normal"].render("Choose an ability target", True, ACCENT_GOLD)
            surface.blit(prompt, (x, INFO_PANEL_HEIGHT + 320))
        elif self.error_message:
            prompt = self.shared.fonts["small"].render(self.error_message, True, ACCENT_GOLD)
            surface.blit(prompt, (x, INFO_PANEL_HEIGHT + 320))
