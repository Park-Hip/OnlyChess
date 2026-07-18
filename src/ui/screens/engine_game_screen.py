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
        # Shell navigation: reachable any time during play, not only from the outcome screen.
        if event.type == p.KEYDOWN and event.key == p.K_r:
            self._restart(); return
        if event.type == p.KEYDOWN and event.key == p.K_BACKSPACE:
            self._go_to_menu(); return
        if self.session.outcome and event.type == p.MOUSEBUTTONDOWN and event.button == 1:
            restart_rect, menu_rect = self._outcome_button_rects(self._layout(p.display.get_surface()))
            position = p.mouse.get_pos()
            if restart_rect.collidepoint(position):
                self._restart(); return
            if menu_rect.collidepoint(position):
                self._go_to_menu(); return
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

    def _restart(self):
        """A fresh game of the same mode: a brand-new EngineSession with an empty action
        log, never a replay or reversal of the current one's log."""
        self.next_screen = EngineGameScreen(self.shared, session=EngineSession(self.session.load_result, self.session.mode_id))

    def _go_to_menu(self):
        from .menu_screen import MenuScreen  # deferred: menu_screen imports this module at top level
        self.next_screen = MenuScreen(self.shared)

    def _outcome_button_rects(self, layout):
        center = layout.board.center
        restart = p.Rect(0, 0, 140, 40).move(center[0] - 150, center[1] + 40)
        menu = p.Rect(0, 0, 140, 40).move(center[0] + 10, center[1] + 40)
        return restart, menu

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
        self._draw_board(surface, layout)
        self._draw_hud(surface, layout, palette)
        if self.session.outcome:
            # Dim the finished game toward the theme's own void, then draw the overlay on top.
            veil = p.Color(palette["background"]) if palette else PANEL_BG
            scrim = p.Surface(surface.get_size(), p.SRCALPHA)
            scrim.fill((veil.r, veil.g, veil.b, 180))
            surface.blit(scrim, (0, 0))
            text = self.shared.fonts["title"].render(self.session.outcome, True, ACCENT_GOLD)
            surface.blit(text, text.get_rect(center=layout.board.center))
            self._draw_outcome_buttons(surface, layout, palette)
        if self.ability_choices:
            self._draw_ability_modal(surface)

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
                    self._draw_status_markers(surface, piece, rect, accent, layout.square_size)

    def _draw_status_markers(self, surface, piece, rect, accent, square_size):
        """Stack every visible status on the piece, not just the first: icon sprite when the
        status declares one, else its glyph. The mod owns which statuses are visible and how."""
        icon_size = max(10, square_size // 3)
        x, y = rect.right - icon_size - 2, rect.y + 2
        for status_id in piece.statuses:
            presentation = self.presentation.status_presentation(status_id)
            if not presentation.get("visible"):
                continue
            icon = self.presentation.status_icon(status_id, icon_size)
            if icon:
                surface.blit(icon, (x, y))
            else:
                surface.blit(self.shared.fonts["small"].render(presentation.get("glyph", "*"), True, accent), (x, y))
            y += icon_size + 1

    def _prompt_text(self):
        """The transient prompt line. This is UI state, not game state, so it enters the
        read-only snapshot through the dedicated ``prompt=`` parameter rather than a game field."""
        if self.pending_move is not None:
            return "Promote: " + "/".join(choice.rsplit(":", 1)[-1][0].upper() for choice in self.pending_move.choices)
        if self.pending_ability is not None:
            return "Choose an ability target (Esc cancels)"
        if self.error_message:
            return self.error_message
        return None

    def _draw_hud(self, surface, layout, palette):
        """Render exactly the widgets the active mode's hud_layout declares, into their slots.

        Core owns the loop; the mod owns which widgets exist and their order. Nothing here names a
        widget type, colour, or label except as a dispatch key tied to the four validated widget types.
        """
        snapshot = self.session.presentation_snapshot(prompt=self._prompt_text())
        slots = {"top": layout.top, "side": layout.side, "bottom": layout.bottom}
        grouped = {"top": [], "side": [], "bottom": []}
        for widget in self.presentation.hud_widgets():
            grouped[widget["slot"]].append(widget)
        if grouped["side"]:  # draw the side background only when a side widget is declared
            p.draw.rect(surface, p.Color(palette["panel"]) if palette else CARD_BG, layout.side, border_radius=8)
        for slot_name, widgets in grouped.items():
            rect = slots[slot_name]
            cursor = rect.y + 12
            for widget in widgets:
                cursor = self._DRAW[widget["type"]](self, surface, widget, rect, cursor, snapshot, palette)

    def _color(self, palette, token, fallback):
        return p.Color(palette[token]) if palette else fallback

    def _widget_turn(self, surface, widget, rect, y, snapshot, palette):
        label = f"{snapshot.current_side_name} to move | Ctrl-Z: undo | click a selected piece again for abilities"
        surface.blit(self.shared.fonts["normal"].render(label, True, self._color(palette, "text", TEXT_PRIMARY)), (rect.x + 12, y))
        return y + 24

    def _widget_resources(self, surface, widget, rect, y, snapshot, palette):
        color = self._color(palette, "text", TEXT_PRIMARY)
        for index, (key, value) in enumerate(snapshot.resources):
            parts = key.split(":")
            label = f"{parts[1]} {parts[-1]}: {value}"  # side tail + resource tail, e.g. "white ap: 0"
            surface.blit(self.shared.fonts["small"].render(label, True, color), (rect.x + 12, y + index * 20))
        return y + max(1, len(snapshot.resources)) * 20 + 12

    def _widget_log(self, surface, widget, rect, y, snapshot, palette):
        color = self._color(palette, "text", TEXT_PRIMARY)
        max_lines = widget.get("max_lines", 8)
        for index, message in enumerate(snapshot.messages[-max_lines:]):
            surface.blit(self.shared.fonts["small"].render(message, True, color), (rect.x + 12, y + index * 22))
        return y + min(len(snapshot.messages), max_lines) * 22 + 12

    def _widget_prompt(self, surface, widget, rect, y, snapshot, palette):
        if snapshot.prompt:
            surface.blit(self.shared.fonts["small"].render(snapshot.prompt, True, self._color(palette, "warning", ACCENT_GOLD)), (rect.x + 12, y))
        return y + 22

    _DRAW = {"turn": _widget_turn, "resources": _widget_resources, "log": _widget_log, "prompt": _widget_prompt}

    def _draw_outcome_buttons(self, surface, layout, palette):
        panel = self._color(palette, "panel", CARD_BG)
        border = self._color(palette, "selection", ACCENT_GOLD)
        text_color = self._color(palette, "text", TEXT_PRIMARY)
        for rect, label in zip(self._outcome_button_rects(layout), ("Restart (R)", "Menu (Backspace)")):
            p.draw.rect(surface, panel, rect, border_radius=8)
            p.draw.rect(surface, border, rect, width=2, border_radius=8)
            text = self.shared.fonts["small"].render(label, True, text_color)
            surface.blit(text, text.get_rect(center=rect.center))

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
