"""Board-aware pygame presentation for a selected engine session."""

from __future__ import annotations

from dataclasses import dataclass

import pygame as p

from ... import savegame
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


#: Pause entries, in the order they are drawn. Shell chrome, not content: these act on the session
#: and the screen stack, and none of them names a piece, mode, or mod.
PAUSE_ENTRIES = ("Resume", "Save Game", "Restart", "Help", "Main Menu")

#: Help describes the controls core itself implements. It deliberately says nothing about pieces,
#: abilities, or fusion — that text would have to name content, and content is a mod's to describe.
HELP_LINES = (
    "Click a piece, then a highlighted square, to move it.",
    "Click a selected piece again to see its abilities.",
    "When promoting, press the letter shown in the prompt.",
    "",
    "Ctrl-Z    undo the last move or ability",
    "R         restart this mode",
    "Backspace return to the menu",
    "Esc       pause, or cancel what is open",
    "H         this screen",
)


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
        self.overlay = None
        #: The square a drag started from, and where the cursor has reached. Drag is an addition to
        #: click-then-click, never a replacement: both reach the same move through the same path.
        self.dragging = None
        self.drag_pos = None
        #: How far back through the history the player has scrolled, in lines.
        self.history_scroll = 0
        self._last_tick = p.time.get_ticks()
        self.presentation = PresentationRuntime(session.load_result, session.mode_id)

    def _palette(self):
        """The active mode's palette with the player's colour preferences laid over it.

        Settings are the one layer allowed to overrule a mod, and the override is narrow: it
        replaces named tokens the theme already has and leaves everything else as authored.
        """
        return self.shared.settings.apply(self.presentation.palette())

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
        # An open overlay swallows input. Pausing that still let the board be clicked would be a
        # pause menu in appearance only.
        if self.overlay is not None:
            self._handle_overlay_event(event)
            return
        if event.type == p.KEYDOWN and event.key == p.K_z and (event.mod & p.KMOD_CTRL):
            self.session.undo(); self.selected_square = None; return
        if event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
            # Esc means "back out of the innermost thing". Only once nothing is open does it pause,
            # so it never strands a half-made choice behind a menu.
            if self.ability_choices or self.pending_ability is not None:
                self.ability_choices = (); self.pending_ability = None; return
            self.overlay = "pause"; return
        if event.type == p.KEYDOWN and event.key == p.K_h and self.pending_move is None:
            self.overlay = "help"; return
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
            restart_rect, menu_rect, quit_rect = self._outcome_button_rects(self._layout(p.display.get_surface()))
            position = p.mouse.get_pos()
            if restart_rect.collidepoint(position):
                self._restart(); return
            if menu_rect.collidepoint(position):
                self._go_to_menu(); return
            if quit_rect.collidepoint(position):
                self.should_quit = True; return
        if event.type == p.MOUSEWHEEL:
            # Clamped on read rather than here: the history grows between wheel events, and a value
            # clamped now would be wrong by the next move.
            self.history_scroll = max(0, self.history_scroll + event.y)
            return
        if event.type == p.MOUSEMOTION and self.dragging is not None:
            self.drag_pos = p.mouse.get_pos()
            return
        if event.type == p.MOUSEBUTTONUP and event.button == 1:
            self._finish_drag()
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
            if self.session.state.board.at(square) is not None:
                self.selected_square = square
                self.dragging, self.drag_pos = square, position
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

    def _finish_drag(self):
        """Release: play the move if the cursor left the square it started on.

        Releasing where the drag began is a click, not a drag, so the selection simply stays and the
        click-then-click path continues from there.
        """
        origin, self.dragging, self.drag_pos = self.dragging, None, None
        if origin is None or self.pending_move is not None:
            return
        square = self._layout(p.display.get_surface()).square_at(p.mouse.get_pos())
        if square is None or square == origin:
            return
        candidates = [move for move in self.session.moves_from(origin) if move.end == square]
        if not candidates:
            return
        move = candidates[0]
        self.pending_move = move if move.choices else None
        if not move.choices:
            self.session.move(move.start, move.end)
        self.selected_square = None

    def _restart(self):
        """A fresh game of the same mode: a brand-new EngineSession with an empty action
        log, never a replay or reversal of the current one's log."""
        self.next_screen = EngineGameScreen(self.shared, session=EngineSession(self.session.load_result, self.session.mode_id, time_limit=self.shared.settings.time_limit))

    def _go_to_menu(self):
        from .menu_screen import MenuScreen  # deferred: menu_screen imports this module at top level
        self.next_screen = MenuScreen(self.shared)

    #: Game-over choices, in drawn order. Quit is here because a finished game is the one moment a
    #: player is most likely to be done, and making them walk back through the menu to leave is a
    #: small rudeness the shell can simply not commit.
    OUTCOME_ENTRIES = ("Restart (R)", "Menu (Backspace)", "Quit")

    def _outcome_button_rects(self, layout):
        center = layout.board.center
        width, gap = 140, 10
        span = len(self.OUTCOME_ENTRIES) * width + (len(self.OUTCOME_ENTRIES) - 1) * gap
        left = center[0] - span // 2
        return tuple(p.Rect(left + index * (width + gap), center[1] + 40, width, 40) for index in range(len(self.OUTCOME_ENTRIES)))

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
        self._update_cursor(self._layout(p.display.get_surface()))
        self._charge_elapsed_time()
        self.presentation.play(self.session.drain_notifications())
        return None

    def _update_cursor(self, layout):
        """A hand over anything that responds to a click, an arrow everywhere else."""
        position = p.mouse.get_pos()
        if self.overlay is not None:
            interactive = any(rect.collidepoint(position) for rect in self._overlay_entry_rects())
        elif self.session.outcome:
            interactive = any(rect.collidepoint(position) for rect in self._outcome_button_rects(layout))
        else:
            square = layout.square_at(position)
            targets = {move.end for move in self.session.moves_from(self.selected_square)} if self.selected_square else set()
            interactive = square is not None and (square in targets or self.session.state.board.at(square) is not None)
        try:
            p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND if interactive else p.SYSTEM_CURSOR_ARROW)
        except p.error:
            # Same reasoning as main()'s guard around mixer.init(): a machine that cannot supply a
            # system cursor — a headless driver, an unusual platform — should still play the game.
            # The cursor is feedback about what is clickable, not a way of clicking it.
            pass

    def _charge_elapsed_time(self):
        """Bill real time to the side on move.

        `_last_tick` is advanced on every frame, including paused ones, so time spent behind an
        overlay is discarded rather than charged in a lump when play resumes. The session does the
        arithmetic; this only measures.
        """
        now = p.time.get_ticks()
        elapsed, self._last_tick = (now - self._last_tick) / 1000.0, now
        if self.overlay is None:
            self.session.tick(elapsed)

    def draw(self, surface):
        palette = self._palette()
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
        if self.dragging is not None and self.drag_pos is not None:
            piece = self.session.state.board.at(self.dragging)
            if piece is not None:
                size = layout.square_size
                held = p.Rect(0, 0, size, size)
                held.center = self.drag_pos
                self._draw_piece(surface, piece, held, p.Color(palette["text"]) if palette else TEXT_PRIMARY, size)
        if self.ability_choices:
            self._draw_ability_modal(surface)
        if self.overlay is not None:
            self._draw_overlay(surface, palette)

    def _draw_board(self, surface, layout):
        board = self.session.state.board
        palette = self._palette()
        light, dark = (p.Color(palette["board_light"]), p.Color(palette["board_dark"])) if palette else (COLOR_LIGHT, COLOR_DARK)
        text_color = p.Color(palette["text"]) if palette else TEXT_PRIMARY
        accent = p.Color(palette["selection"]) if palette else ACCENT_GOLD
        target = p.Color(palette["target"]) if palette else ACCENT_GOLD
        targets = {move.end for move in self.session.moves_from(self.selected_square)} if self.selected_square else set()
        last = self.session.state.last_move
        last_squares = {last.start, last.end} if last is not None else set()
        warning = self.session.presentation_snapshot().warning
        warned = set(warning.squares) if warning else set()
        warning_color = p.Color(palette["warning"]) if palette else ACCENT_GOLD
        for row in range(board.rows):
            for col in range(board.columns):
                rect = layout.square_rect((row, col))
                p.draw.rect(surface, (light, dark)[(row + col) % 2], rect)
                if (row, col) in last_squares:
                    # Where the previous move ran. A translucent wash rather than an outline, so it
                    # reads as "this happened" and never competes with the selection ring.
                    tint = p.Surface((layout.square_size, layout.square_size), p.SRCALPHA)
                    tint.fill((accent.r, accent.g, accent.b, 60))
                    surface.blit(tint, rect.topleft)
                if (row, col) in warned:
                    # An announced event that has already bound its zone has committed to these
                    # squares. Shown so a player can move out of the way, which is the only reason
                    # a warning phase exists at all.
                    tint = p.Surface((layout.square_size, layout.square_size), p.SRCALPHA)
                    tint.fill((warning_color.r, warning_color.g, warning_color.b, 80))
                    surface.blit(tint, rect.topleft)
                if (row, col) == self.selected_square: p.draw.rect(surface, accent, rect, max(2, layout.square_size // 14))
                elif (row, col) in targets: p.draw.circle(surface, target, rect.center, max(3, layout.square_size // 7))
                piece = board.at((row, col))
                if piece and (row, col) != self.dragging:
                    self._draw_piece(surface, piece, rect, text_color, layout.square_size)
                    self._draw_components(surface, piece, rect, text_color)
                    self._draw_status_markers(surface, piece, rect, accent, layout.square_size)
                self._draw_coordinates(surface, layout, board, row, col, rect, light, dark)

    def _draw_piece(self, surface, piece, rect, text_color, square_size):
        image = self.presentation.image(piece.definition.id, square_size, piece.side)
        if image:
            surface.blit(image, rect)
        else:
            text = self.shared.fonts["title"].render(self.presentation.glyph(piece.definition.id), True, text_color)
            surface.blit(text, text.get_rect(center=rect.center))

    def _draw_components(self, surface, piece, rect, text_color):
        """Mark what a fused piece has absorbed, beyond the one it is still named after.

        Without this a composed rook and a plain rook are the same picture, and the only way to
        learn a piece moves diagonally now is to click it. Uses each absorbed piece's own glyph, so
        core never learns a name here either.
        """
        extra = piece.definition.components[1:]
        if not extra:
            return
        text = self.shared.fonts["small"].render("+" + "+".join(self.presentation.glyph(component) for component in extra), True, text_color)
        surface.blit(text, (rect.right - text.get_width() - 2, rect.bottom - text.get_height() - 1))

    def _draw_coordinates(self, surface, layout, board, row, col, rect, light, dark):
        """Rank down the left edge, file along the bottom, tinted into the square itself.

        Boards here are any size, so the labels count from the board's own dimensions rather than
        assuming eight of anything. Files run past 'z' on a wide enough board, which is a real
        limit, but a 27-column board is not a thing any content has asked for.
        """
        if layout.square_size < 28:
            return  # below this the label is unreadable and only adds noise
        label_color = (dark if (row + col) % 2 == 0 else light)
        font = self.shared.fonts["small"]
        if col == 0:
            rank = font.render(str(board.rows - row), True, label_color)
            surface.blit(rank, (rect.x + 3, rect.y + 2))
        if row == board.rows - 1:
            file_label = font.render(chr(ord("a") + col), True, label_color)
            surface.blit(file_label, (rect.right - file_label.get_width() - 3, rect.bottom - file_label.get_height() - 1))

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
        snapshot = self.session.presentation_snapshot(prompt=self._prompt_text(), glyph=self.presentation.glyph)
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
        if snapshot.prompt and not any(widget["type"] == "prompt" for widget in self.presentation.hud_widgets()):
            self._draw_fallback_prompt(surface, layout, snapshot, palette)

    def _draw_fallback_prompt(self, surface, layout, snapshot, palette):
        """Draw the prompt line for a mode whose hud_layout does not carry a prompt widget.

        A prompt is not decoration. While one is showing, `handle_event` refuses clicks until the
        awaited key arrives, so a mode that declares no `presentation:` — or a layout that simply
        omits the widget — leaves the board looking frozen with nothing on screen explaining why.
        The modder who hits that is the one writing their first minimal mod.

        Core drawing this is not a boundary violation: core already owns the render loop, and the
        text comes from the pending move's own choices, so nothing here names content. Requiring
        `presentation:` instead would have made the smallest possible mod harder to write, which is
        the wrong trade for a project whose audience includes people who do not write code.
        """
        text = self.shared.fonts["small"].render(snapshot.prompt, True, self._color(palette, "warning", ACCENT_GOLD))
        surface.blit(text, (layout.bottom.x + 12, layout.bottom.y + 12))

    def _color(self, palette, token, fallback):
        return p.Color(palette[token]) if palette else fallback

    def _widget_turn(self, surface, widget, rect, y, snapshot, palette):
        label = f"Turn {snapshot.turn_number + 1} | {snapshot.current_side_name} to move | Esc: menu | H: help"
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

    def _widget_clock(self, surface, widget, rect, y, snapshot, palette):
        """One line per side. Draws nothing at all when the mode declares no time limit, so a
        layout can name the widget unconditionally and a clockless mode simply has no clock."""
        text_color = self._color(palette, "text", TEXT_PRIMARY)
        warning = self._color(palette, "warning", ACCENT_GOLD)
        for name, remaining in snapshot.clocks:
            minutes, seconds = divmod(int(remaining), 60)
            # Under a minute is when the number stops being information and starts being pressure.
            color = warning if remaining < 60 else text_color
            label = self.shared.fonts["normal"].render(f"{name}  {minutes}:{seconds:02d}", True, color)
            surface.blit(label, (rect.x + 12, y))
            y += 24
        return y + (12 if snapshot.clocks else 0)

    def _widget_material(self, surface, widget, rect, y, snapshot, palette):
        """Who is ahead, and by how much. Silent at parity: `+0` is noise, not information."""
        totals = dict(snapshot.material)
        if len(totals) != 2:
            return y
        (first, first_total), (second, second_total) = snapshot.material
        if first_total != second_total:
            leader, margin = (first, first_total - second_total) if first_total > second_total else (second, second_total - first_total)
            text = self.shared.fonts["small"].render(f"{leader} +{margin}", True, self._color(palette, "text", TEXT_PRIMARY))
            surface.blit(text, (rect.x + 12, y))
            return y + 22
        return y

    def _widget_countdown(self, surface, widget, rect, y, snapshot, palette):
        """Draws nothing when no pool is scheduled, so a layout can declare it unconditionally."""
        if snapshot.event_countdown is None:
            return y
        # The last move before an event lands is the one worth flagging.
        color = self._color(palette, "warning", ACCENT_GOLD) if snapshot.event_countdown <= 1 else self._color(palette, "text", TEXT_PRIMARY)
        text = self.shared.fonts["small"].render(f"Next event in {snapshot.event_countdown}", True, color)
        surface.blit(text, (rect.x + 12, y))
        return y + 22

    def _widget_captures(self, surface, widget, rect, y, snapshot, palette):
        """A row of glyphs per side, in capture order. Uses each piece's own declared glyph, so a
        mod's pieces appear here without core knowing any of their names."""
        color = self._color(palette, "text", TEXT_PRIMARY)
        for name, taken in snapshot.captures:
            if not taken:
                continue
            glyphs = " ".join(self.presentation.glyph(piece_id) for piece_id in taken)
            surface.blit(self.shared.fonts["small"].render(f"{name}: {glyphs}", True, color), (rect.x + 12, y))
            y += 20
        return y + (8 if any(taken for _, taken in snapshot.captures) else 0)

    def _widget_history(self, surface, widget, rect, y, snapshot, palette):
        """The move list, newest at the bottom, showing the tail that fits."""
        color = self._color(palette, "text", TEXT_PRIMARY)
        max_lines = widget.get("max_lines", 10)
        # Scrolling past the top simply stops there, and a new move pulls the view back to the
        # bottom, which is where a move log is worth reading.
        back = min(self.history_scroll, max(0, len(snapshot.history) - max_lines))
        end = len(snapshot.history) - back
        shown = snapshot.history[max(0, end - max_lines):end]
        offset = end - len(shown)
        for index, line in enumerate(shown):
            numbered = f"{offset + index + 1}. {line}"
            surface.blit(self.shared.fonts["small"].render(numbered, True, color), (rect.x + 12, y + index * 20))
        return y + len(shown) * 20 + (10 if shown else 0)

    def _widget_warning(self, surface, widget, rect, y, snapshot, palette):
        """The announced event: what is coming and how long there is to react."""
        if snapshot.warning is None:
            return y
        color = self._color(palette, "warning", ACCENT_GOLD)
        card = p.Rect(rect.x + 8, y - 4, rect.width - 16, 46)
        p.draw.rect(surface, color, card, width=1, border_radius=6)
        surface.blit(self.shared.fonts["small"].render(snapshot.warning.name, True, color), (card.x + 8, card.y + 6))
        remaining = snapshot.event_countdown
        detail = "now" if not remaining else f"in {remaining}"
        surface.blit(self.shared.fonts["small"].render(f"incoming {detail}", True, color), (card.x + 8, card.y + 24))
        return card.bottom + 10

    _DRAW = {"turn": _widget_turn, "warning": _widget_warning, "history": _widget_history, "material": _widget_material, "captures": _widget_captures, "countdown": _widget_countdown, "resources": _widget_resources, "log": _widget_log, "prompt": _widget_prompt, "clock": _widget_clock}

    def _draw_outcome_buttons(self, surface, layout, palette):
        panel = self._color(palette, "panel", CARD_BG)
        border = self._color(palette, "selection", ACCENT_GOLD)
        text_color = self._color(palette, "text", TEXT_PRIMARY)
        for rect, label in zip(self._outcome_button_rects(layout), self.OUTCOME_ENTRIES):
            p.draw.rect(surface, panel, rect, border_radius=8)
            p.draw.rect(surface, border, rect, width=2, border_radius=8)
            text = self.shared.fonts["small"].render(label, True, text_color)
            surface.blit(text, text.get_rect(center=rect.center))

    def _modal_rect(self):
        height = 74 + len(self.ability_choices) * 42
        return p.Rect(0, 0, 360, height).move(220, 150)

    def _overlay_rect(self):
        height = 96 + (len(PAUSE_ENTRIES) * 44 if self.overlay == "pause" else len(HELP_LINES) * 26)
        return p.Rect(0, 0, 460, height).move(170, 110)

    def _overlay_entry_rects(self):
        """Clickable rows for the pause overlay. Help has none — it closes and nothing else."""
        if self.overlay != "pause":
            return ()
        panel = self._overlay_rect()
        return tuple(p.Rect(panel.x + 24, panel.y + 66 + index * 44, panel.width - 48, 36) for index in range(len(PAUSE_ENTRIES)))

    def _handle_overlay_event(self, event):
        if event.type == p.KEYDOWN and event.key in (p.K_ESCAPE, p.K_h):
            self.overlay = None
            return
        if event.type != p.MOUSEBUTTONDOWN or event.button != 1:
            return
        position = p.mouse.get_pos()
        for rect, entry in zip(self._overlay_entry_rects(), PAUSE_ENTRIES):
            if rect.collidepoint(position):
                self._choose_pause_entry(entry)
                return
        if self.overlay == "help" and not self._overlay_rect().collidepoint(position):
            self.overlay = None

    def _choose_pause_entry(self, entry):
        if entry == "Resume":
            self.overlay = None
        elif entry == "Save Game":
            savegame.write(self.session, self.shared.settings_root)
            self.error_message = "Game saved"
            self.overlay = None
        elif entry == "Restart":
            self._restart()
        elif entry == "Help":
            self.overlay = "help"
        elif entry == "Main Menu":
            self._go_to_menu()

    def _draw_overlay(self, surface, palette):
        panel = self._overlay_rect()
        veil = p.Color(palette["background"]) if palette else PANEL_BG
        scrim = p.Surface(surface.get_size(), p.SRCALPHA)
        scrim.fill((veil.r, veil.g, veil.b, 200))
        surface.blit(scrim, (0, 0))

        border = self._color(palette, "selection", ACCENT_GOLD)
        text_color = self._color(palette, "text", TEXT_PRIMARY)
        p.draw.rect(surface, self._color(palette, "panel", CARD_BG), panel, border_radius=10)
        p.draw.rect(surface, border, panel, width=2, border_radius=10)
        title = self.shared.fonts["title"].render("Paused" if self.overlay == "pause" else "Controls", True, border)
        surface.blit(title, (panel.x + 24, panel.y + 20))

        if self.overlay == "pause":
            for rect, entry in zip(self._overlay_entry_rects(), PAUSE_ENTRIES):
                p.draw.rect(surface, border, rect, width=1, border_radius=6)
                label = self.shared.fonts["normal"].render(entry, True, text_color)
                surface.blit(label, label.get_rect(center=rect.center))
            return
        for index, line in enumerate(HELP_LINES):
            surface.blit(self.shared.fonts["small"].render(line, True, text_color), (panel.x + 24, panel.y + 66 + index * 26))

    def _draw_ability_modal(self, surface):
        modal = self._modal_rect()
        p.draw.rect(surface, CARD_BG, modal, border_radius=8); p.draw.rect(surface, ACCENT_GOLD, modal, width=2, border_radius=8)
        surface.blit(self.shared.fonts["normal"].render("Choose ability (Esc cancels)", True, TEXT_PRIMARY), (modal.x + 16, modal.y + 16))
        for index, choice in enumerate(self.ability_choices):
            row = p.Rect(modal.x + 16, modal.y + 50 + index * 42, modal.width - 32, 34)
            p.draw.rect(surface, PANEL_BG, row, border_radius=4)
            label = f"{choice.name} — {choice.cost}"
            surface.blit(self.shared.fonts["small"].render(label, True, TEXT_PRIMARY), (row.x + 8, row.y + 8))
