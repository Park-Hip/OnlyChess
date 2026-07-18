"""Board-aware pygame presentation for a selected engine session."""

from __future__ import annotations

from dataclasses import dataclass

import pygame as p

from ...runtime import EngineSession
from ..board_layout import BoardLayout
from ..presentation_runtime import PresentationRuntime
from ..ui_constants import ACCENT_GOLD, CARD_BG, COLOR_DARK, COLOR_LIGHT, PANEL_BG, TEXT_PRIMARY
from .base import Screen


@dataclass(frozen=True)
class AbilityChoice:
    id: str
    name: str
    cost: str


class EngineGameScreen(Screen):
    """Render an arbitrary rectangular board and explicit ability choices."""

    def __init__(self, shared, *, session: EngineSession):
        super().__init__()
        self.shared, self.session = shared, session
        self.selected_square = None
        self.pending_move = None
        self.pending_ability = None
        self.ability_choices: tuple[AbilityChoice, ...] = ()
        self.error_message = None
        self.presentation = PresentationRuntime(session.load_result, session.mode_id)

    def _layout(self, surface):
        board = self.session.state.board
        return BoardLayout.for_viewport(surface.get_size(), board.rows, board.columns)

    def _choices(self):
        choices = []
        for ability_id in self.session.abilities_for(self.selected_square):
            ability = self.session.state.ability_defs[ability_id]
            cost = ", ".join(f"{amount} {resource.rsplit(':', 1)[-1]}" for resource, amount in ability.cost.items()) or "free"
            choices.append(AbilityChoice(ability_id, ability.name, cost))
        return tuple(choices)

    def handle_event(self, event):
        if event.type == p.KEYDOWN and event.key == p.K_z and (event.mod & p.KMOD_CTRL):
            self.session.undo(); self.selected_square = None; return
        if event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
            self.ability_choices = (); self.pending_ability = None; return
        if event.type == p.KEYDOWN and self.pending_move is not None:
            choices = {choice.rsplit(":", 1)[-1][0].lower(): choice for choice in self.pending_move.choices}
            choice = choices.get(event.unicode.lower())
            if choice:
                self.session.move(self.pending_move.start, self.pending_move.end, choice=choice); self.pending_move = None
            return
        if event.type != p.MOUSEBUTTONDOWN or event.button != 1 or self.pending_move is not None:
            return
        position = p.mouse.get_pos()
        if self.ability_choices:
            self._choose_ability(position)
            return
        layout = self._layout(p.display.get_surface())
        square = layout.square_at(position)
        if square is None:
            return
        if self.pending_ability is not None:
            try:
                self.session.use_ability(self.selected_square, self.pending_ability, target=square)
            except ValueError as error:
                self.error_message = str(error); return
            self.pending_ability = None; self.selected_square = None; return
        if self.selected_square is None:
            if self.session.state.board.at(square) is not None: self.selected_square = square
            return
        if square == self.selected_square:
            self.ability_choices = self._choices()
            return
        candidates = [move for move in self.session.moves_from(self.selected_square) if move.end == square]
        if candidates:
            move = candidates[0]
            self.pending_move = move if move.choices else None
            if not move.choices: self.session.move(move.start, move.end)
            self.selected_square = None
        else:
            self.selected_square = square if self.session.state.board.at(square) is not None else None

    def _choose_ability(self, position):
        modal = self._modal_rect()
        for index, choice in enumerate(self.ability_choices):
            row = p.Rect(modal.x + 16, modal.y + 50 + index * 42, modal.width - 32, 34)
            if row.collidepoint(position):
                target = self.session.state.ability_defs[choice.id].target
                if target == "self":
                    try: self.session.use_ability(self.selected_square, choice.id)
                    except ValueError as error: self.error_message = str(error); return
                    self.selected_square = None
                else:
                    self.pending_ability = choice.id
                self.ability_choices = ()
                return

    def update(self):
        self.presentation.play(self.session.drain_notifications())
        return None

    def draw(self, surface):
        palette = self.presentation.palette()
        surface.fill(p.Color(palette["background"]) if palette else PANEL_BG)
        layout = self._layout(surface)
        self._draw_header(surface)
        self._draw_board(surface, layout)
        self._draw_messages(surface, layout)
        if self.session.outcome:
            text = self.shared.fonts["title"].render(self.session.outcome, True, ACCENT_GOLD)
            surface.blit(text, text.get_rect(center=layout.board.center))
        if self.ability_choices:
            self._draw_ability_modal(surface)

    def _draw_header(self, surface):
        side = self.session.state.board.sides[self.session.state.current_side].name
        label = f"{side} to move | Ctrl-Z: undo | click a selected piece again for abilities"
        surface.blit(self.shared.fonts["normal"].render(label, True, TEXT_PRIMARY), (12, 12))

    def _draw_board(self, surface, layout):
        board = self.session.state.board
        palette = self.presentation.palette()
        light, dark = (p.Color(palette["board_light"]), p.Color(palette["board_dark"])) if palette else (COLOR_LIGHT, COLOR_DARK)
        text_color = p.Color(palette["text"]) if palette else TEXT_PRIMARY
        accent = p.Color(palette["selection"]) if palette else ACCENT_GOLD
        target = p.Color(palette["target"]) if palette else ACCENT_GOLD
        targets = {move.end for move in self.session.moves_from(self.selected_square)} if self.selected_square else set()
        for row in range(board.rows):
            for col in range(board.columns):
                rect = layout.square_rect((row, col))
                p.draw.rect(surface, (light, dark)[(row + col) % 2], rect)
                if (row, col) == self.selected_square: p.draw.rect(surface, accent, rect, max(2, layout.square_size // 14))
                elif (row, col) in targets: p.draw.circle(surface, target, rect.center, max(3, layout.square_size // 7))
                piece = board.at((row, col))
                if piece:
                    image = self.presentation.image(piece.definition.id, layout.square_size)
                    if image: surface.blit(image, rect)
                    else:
                        text = self.shared.fonts["title"].render(self.presentation.glyph(piece.definition.id), True, text_color)
                        surface.blit(text, text.get_rect(center=rect.center))
                    visible = [status for status in piece.statuses if self.session.load_result.registries.content["status"].get(status).value.tree.get("presentation", {}).get("visible")]
                    if visible:
                        marker = self.session.load_result.registries.content["status"].get(visible[0]).value.tree["presentation"].get("glyph", "*")
                        surface.blit(self.shared.fonts["small"].render(marker, True, accent), (rect.right - 12, rect.y + 2))

    def _draw_messages(self, surface, layout):
        panel = layout.panel
        palette = self.presentation.palette()
        p.draw.rect(surface, p.Color(palette["panel"]) if palette else CARD_BG, panel, border_radius=8)
        surface.blit(self.shared.fonts["normal"].render("Game log", True, TEXT_PRIMARY), (panel.x + 12, panel.y + 12))
        for index, message in enumerate(self.session.state.event_messages[-12:]):
            surface.blit(self.shared.fonts["small"].render(message, True, TEXT_PRIMARY), (panel.x + 12, panel.y + 42 + index * 22))
        prompt = None
        if self.pending_move is not None:
            prompt = "Promote: " + "/".join(choice.rsplit(":", 1)[-1][0].upper() for choice in self.pending_move.choices)
        elif self.pending_ability is not None: prompt = "Choose an ability target (Esc cancels)"
        elif self.error_message: prompt = self.error_message
        if prompt: surface.blit(self.shared.fonts["small"].render(prompt, True, ACCENT_GOLD), (panel.x + 12, panel.bottom - 30))

    def _modal_rect(self):
        height = 74 + len(self.ability_choices) * 42
        return p.Rect(0, 0, 360, height).move(220, 150)

    def _draw_ability_modal(self, surface):
        modal = self._modal_rect()
        p.draw.rect(surface, CARD_BG, modal, border_radius=8); p.draw.rect(surface, ACCENT_GOLD, modal, width=2, border_radius=8)
        surface.blit(self.shared.fonts["normal"].render("Choose ability (Esc cancels)", True, TEXT_PRIMARY), (modal.x + 16, modal.y + 16))
        for index, choice in enumerate(self.ability_choices):
            row = p.Rect(modal.x + 16, modal.y + 50 + index * 42, modal.width - 32, 34)
            p.draw.rect(surface, PANEL_BG, row, border_radius=4)
            label = f"{choice.name} — {choice.cost}"
            surface.blit(self.shared.fonts["small"].render(label, True, TEXT_PRIMARY), (row.x + 8, row.y + 8))
