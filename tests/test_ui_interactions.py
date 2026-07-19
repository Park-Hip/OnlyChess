"""The interactions a player performs with a mouse and keyboard, driven through the screen.

The rest of the suite exercises these rules by calling `EngineSession` directly, which proves the
engine is right but not that the screen reaches it. Everything here goes through
`EngineGameScreen.handle_event` instead, so a regression in square hit-testing, selection state,
the ability modal, or the promotion prompt fails a test rather than surviving as a green suite and
a game nobody can play.

Positions are built by placing pieces, following `test_runtime_cutover.py` -- except en passant,
which is played out, because its legality depends on the previous move rather than the position.
"""

import os
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame as p

from src.engine.actions import AdjustResource
from src.engine.movegen import pseudo_moves
from src.engine.piece import Piece
from src.runtime import ApplicationContext, EngineSession
from src.ui.screens.engine_game_screen import PAUSE_ENTRIES, EngineGameScreen
from src.settings import Settings


class ClickPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._saves = tempfile.TemporaryDirectory()
        cls.saves = Path(cls._saves.name)
        p.init()
        # convert_alpha() and the layout both want a real video surface, as in the running app.
        cls.surface = p.display.set_mode((800, 600))
        cls.context = ApplicationContext.load()

    @classmethod
    def tearDownClass(cls):
        cls._saves.cleanup()

    def screen(self, mode_id="base:vanilla"):
        session = EngineSession(self.context.load_result, mode_id)
        shared = type("Shared", (), {"fonts": self._fonts(), "app_context": self.context, "settings": Settings(), "settings_root": self.saves})()
        return EngineGameScreen(shared, session=session)

    def _fonts(self):
        return {"title": p.font.Font(None, 24), "normal": p.font.Font(None, 16), "small": p.font.Font(None, 13)}

    def click_at(self, screen, position):
        # The screens read the live cursor rather than event.pos, and the dummy driver has no
        # cursor to move, so the pointer is stubbed for the duration of the click.
        p.mouse.get_pos = lambda: position
        screen.handle_event(p.event.Event(p.MOUSEBUTTONDOWN, {"pos": position, "button": 1}))

    def click(self, screen, square):
        self.click_at(screen, screen._layout(self.surface).square_rect(square).center)

    def right_click(self, screen, square):
        """How a piece's abilities are opened. The double-click route was removed because it made
        the menu something you found by accident rather than something you asked for."""
        position = screen._layout(self.surface).square_rect(square).center
        p.mouse.get_pos = lambda: position
        screen.handle_event(p.event.Event(p.MOUSEBUTTONDOWN, {"pos": position, "button": 3}))

    def press(self, screen, code, unicode_="", mod=0):
        screen.handle_event(p.event.Event(p.KEYDOWN, {"key": code, "unicode": unicode_, "mod": mod}))

    def undo(self, screen):
        self.press(screen, p.K_z, "z", p.KMOD_CTRL)

    def occupant(self, screen, square):
        piece = screen.session.state.board.at(square)
        return piece.definition.id if piece else None

    def clear_to(self, screen, *pieces):
        """Empty the board, then place `(piece_id, side, square)` triples on it."""
        state = screen.session.state
        for piece in list(state.board.pieces()):
            state.board.remove(piece.pos)
        for index, (piece_id, side, square) in enumerate(pieces, start=1):
            state.board.place(Piece(index, state.piece_defs[piece_id], side, square), square)

    def test_clicking_a_piece_then_a_target_square_plays_the_move(self):
        screen = self.screen()
        move = screen.session.legal_moves[0]

        self.click(screen, move.start)
        self.assertEqual(move.start, screen.selected_square)
        self.click(screen, move.end)

        self.assertIsNone(self.occupant(screen, move.start))
        self.assertEqual("base:pawn", self.occupant(screen, move.end))
        self.assertIsNone(screen.selected_square)

    def test_a_click_outside_the_board_selects_nothing_and_does_not_raise(self):
        screen = self.screen()

        self.click_at(screen, (self.surface.get_width() - 2, self.surface.get_height() - 2))

        self.assertIsNone(screen.selected_square)

    def test_castling_moves_the_rook_too_and_one_undo_restores_both(self):
        screen = self.screen()
        self.clear_to(
            screen,
            ("base:king", "base:white", (7, 4)), ("base:rook", "base:white", (7, 7)),
            ("base:king", "base:black", (0, 4)),
        )

        self.click(screen, (7, 4))
        self.click(screen, (7, 6))

        self.assertEqual("base:king", self.occupant(screen, (7, 6)))
        self.assertEqual("base:rook", self.occupant(screen, (7, 5)))
        self.assertIsNone(self.occupant(screen, (7, 7)))

        self.undo(screen)

        self.assertEqual("base:king", self.occupant(screen, (7, 4)))
        self.assertEqual("base:rook", self.occupant(screen, (7, 7)))
        self.assertIsNone(self.occupant(screen, (7, 5)))

    def test_en_passant_removes_a_pawn_the_capturer_never_lands_on(self):
        screen = self.screen()
        # Played rather than placed: en passant is legal because of the previous move.
        for start, end in (((6, 4), (4, 4)), ((1, 0), (2, 0)), ((4, 4), (3, 4)), ((1, 3), (3, 3))):
            screen.session.move(start, end)

        self.click(screen, (3, 4))
        self.click(screen, (2, 3))

        self.assertEqual("base:pawn", self.occupant(screen, (2, 3)))
        self.assertIsNone(self.occupant(screen, (3, 3)))

        self.undo(screen)

        self.assertEqual("base:pawn", self.occupant(screen, (3, 3)))

    def test_a_promotion_waits_for_a_keypress_and_the_board_ignores_clicks_meanwhile(self):
        screen = self.screen()
        self.clear_to(
            screen,
            ("base:pawn", "base:white", (1, 0)),
            ("base:king", "base:white", (7, 4)), ("base:king", "base:black", (0, 4)),
        )

        self.click(screen, (1, 0))
        self.click(screen, (0, 0))

        self.assertIsNotNone(screen.pending_move)
        self.assertIn("base:queen", screen.pending_move.choices)
        self.assertIsNone(self.occupant(screen, (0, 0)))

        self.click(screen, (7, 4))
        self.assertIsNotNone(screen.pending_move)

        self.press(screen, p.K_q, "q")

        self.assertEqual("base:queen", self.occupant(screen, (0, 0)))
        self.assertIsNone(screen.pending_move)

        self.undo(screen)

        self.assertEqual("base:pawn", self.occupant(screen, (1, 0)))

    def test_right_clicking_a_piece_opens_its_abilities_and_targeting_spends_ap(self):
        screen = self.screen()
        AdjustResource("base:white", "base:ap", 3).apply(screen.session.state)

        self.right_click(screen, (7, 1))

        choices = [choice.id for choice in screen.ability_choices]
        self.assertIn("base:knight_swap", choices)

        index = choices.index("base:knight_swap")
        modal = screen._modal_rect()
        self.click_at(screen, p.Rect(modal.x + 16, modal.y + 50 + index * 42, modal.width - 32, 34).center)
        self.assertEqual("base:knight_swap", screen.pending_ability)

        self.click(screen, (7, 0))

        self.assertEqual("base:rook", self.occupant(screen, (7, 1)))
        self.assertEqual("base:knight", self.occupant(screen, (7, 0)))
        self.assertEqual(1, screen.session.state.resources["base:white"]["base:ap"])

        self.undo(screen)

        self.assertEqual("base:knight", self.occupant(screen, (7, 1)))
        self.assertEqual(3, screen.session.state.resources["base:white"]["base:ap"])

    def test_escape_closes_the_ability_menu_without_spending_anything(self):
        screen = self.screen()
        AdjustResource("base:white", "base:ap", 3).apply(screen.session.state)

        self.right_click(screen, (7, 1))
        self.assertTrue(screen.ability_choices)

        self.press(screen, p.K_ESCAPE)

        self.assertEqual((), screen.ability_choices)
        self.assertIsNone(screen.pending_ability)
        self.assertEqual(3, screen.session.state.resources["base:white"]["base:ap"])

    def test_a_pending_prompt_is_drawn_even_when_no_prompt_widget_is_declared(self):
        """A prompt blocks input, so a mode that never draws one looks broken rather than busy.

        Asserts on pixels because the bug was invisible at every other layer: `_prompt_text()`
        already returned the right string, the snapshot already carried it, and only the draw call
        was missing.
        """
        screen = self.screen()
        self.clear_to(
            screen,
            ("base:pawn", "base:white", (1, 0)),
            ("base:king", "base:white", (7, 4)), ("base:king", "base:black", (0, 4)),
        )
        self.click(screen, (1, 0))
        self.click(screen, (0, 0))
        self.assertIsNotNone(screen.pending_move)

        declared = screen.presentation.hud_widgets()
        screen.presentation.hud_widgets = lambda: [w for w in declared if w["type"] != "prompt"]

        def frame():
            surface = p.Surface(self.surface.get_size())
            surface.fill((0, 0, 0))
            screen.draw(surface)
            bottom = screen._layout(surface).bottom
            return surface.subsurface(p.Rect(bottom.x, bottom.y, bottom.width, min(40, bottom.height))).copy()

        # Compared against the same screen with the prompt cleared, not against a blank surface:
        # other widgets colour this strip too, so a blank comparison passes whether or not the
        # prompt is drawn.
        with_prompt = frame()
        screen.pending_move = None
        without_prompt = frame()

        self.assertNotEqual(
            p.image.tostring(without_prompt, "RGB"),
            p.image.tostring(with_prompt, "RGB"),
            "the pending prompt left no pixels behind",
        )

    def test_escape_pauses_only_once_nothing_else_is_open(self):
        """Esc backs out of the innermost thing, so it never strands a half-made choice."""
        screen = self.screen()
        AdjustResource("base:white", "base:ap", 3).apply(screen.session.state)
        self.right_click(screen, (7, 1))
        self.assertTrue(screen.ability_choices)

        self.press(screen, p.K_ESCAPE)
        self.assertEqual((), screen.ability_choices)
        self.assertIsNone(screen.overlay)

        self.press(screen, p.K_ESCAPE)
        self.assertEqual("pause", screen.overlay)

        self.press(screen, p.K_ESCAPE)
        self.assertIsNone(screen.overlay)

    def test_a_paused_game_ignores_board_clicks(self):
        """A pause that still let the board be clicked would be a pause menu in appearance only."""
        screen = self.screen()
        move = screen.session.legal_moves[0]
        self.press(screen, p.K_ESCAPE)

        self.click(screen, move.start)
        self.click(screen, move.end)

        self.assertIsNone(screen.selected_square)
        self.assertEqual("base:pawn", self.occupant(screen, move.start))
        self.assertEqual([], screen.session.state.action_log)

    def test_pause_entries_resume_restart_and_leave(self):
        screen = self.screen()
        move = screen.session.legal_moves[0]
        screen.session.move(move.start, move.end)

        self.press(screen, p.K_ESCAPE)
        self.click_at(screen, screen._overlay_entry_rects()[PAUSE_ENTRIES.index("Resume")].center)
        self.assertIsNone(screen.overlay)

        self.press(screen, p.K_ESCAPE)
        self.click_at(screen, screen._overlay_entry_rects()[PAUSE_ENTRIES.index("Help")].center)
        self.assertEqual("help", screen.overlay)
        self.press(screen, p.K_ESCAPE)

        self.press(screen, p.K_ESCAPE)
        self.click_at(screen, screen._overlay_entry_rects()[PAUSE_ENTRIES.index("Restart")].center)
        self.assertIsInstance(screen.next_screen, EngineGameScreen)
        self.assertEqual([], screen.next_screen.session.state.action_log)

    def test_pause_offers_a_route_to_the_main_menu(self):
        screen = self.screen()
        self.press(screen, p.K_ESCAPE)

        self.click_at(screen, screen._overlay_entry_rects()[PAUSE_ENTRIES.index("Main Menu")].center)

        self.assertIsNotNone(screen.next_screen)
        self.assertNotIsInstance(screen.next_screen, EngineGameScreen)

    def test_h_opens_help_during_play_and_closes_again(self):
        screen = self.screen()

        self.press(screen, p.K_h, "h")
        self.assertEqual("help", screen.overlay)

        self.press(screen, p.K_h, "h")
        self.assertIsNone(screen.overlay)

    def release(self, screen, square):
        p.mouse.get_pos = lambda: screen._layout(self.surface).square_rect(square).center
        screen.handle_event(p.event.Event(p.MOUSEBUTTONUP, {"button": 1}))

    def test_dragging_a_piece_to_a_square_plays_the_move(self):
        screen = self.screen()
        move = screen.session.legal_moves[0]

        self.click(screen, move.start)
        self.assertEqual(move.start, screen.dragging)
        self.release(screen, move.end)

        self.assertEqual("base:pawn", self.occupant(screen, move.end))
        self.assertIsNone(screen.dragging)
        self.assertIsNone(screen.selected_square)

    def test_releasing_where_the_drag_began_selects_instead_of_moving(self):
        """A press and release on one square is a click, so the click-then-click path continues."""
        screen = self.screen()
        move = screen.session.legal_moves[0]

        self.click(screen, move.start)
        self.release(screen, move.start)

        self.assertIsNone(screen.dragging)
        self.assertEqual(move.start, screen.selected_square)
        self.assertEqual([], screen.session.state.action_log)

        self.click(screen, move.end)
        self.assertEqual("base:pawn", self.occupant(screen, move.end))

    def test_dropping_on_an_illegal_square_changes_nothing(self):
        screen = self.screen()

        self.click(screen, (7, 0))
        self.release(screen, (3, 3))

        self.assertEqual("base:rook", self.occupant(screen, (7, 0)))
        self.assertEqual([], screen.session.state.action_log)

    def test_a_second_piece_can_be_dragged_while_another_is_selected(self):
        """Drag used to begin only when nothing was selected, so the second piece you touched could
        never be dragged. That is what made dragging work only some of the time."""
        screen = self.screen()

        self.click(screen, (7, 0))          # select a rook, which has nowhere to go
        self.release(screen, (7, 0))
        self.assertEqual((7, 0), screen.selected_square)

        self.click(screen, (6, 4))          # now press a different piece
        self.assertEqual((6, 4), screen.dragging)

        self.release(screen, (4, 4))

        self.assertEqual("base:pawn", self.occupant(screen, (4, 4)))

    def test_an_armed_ability_highlights_what_it_can_reach(self):
        """Pawn sprint has exactly one destination, and nothing on screen used to say which."""
        screen = self.screen()
        AdjustResource("base:white", "base:ap", 3).apply(screen.session.state)

        self.right_click(screen, (6, 0))
        index = [choice.id for choice in screen.ability_choices].index("base:pawn_sprint")
        modal = screen._modal_rect()
        self.click_at(screen, p.Rect(modal.x + 16, modal.y + 50 + index * 42, modal.width - 32, 34).center)

        highlighted = screen._highlight_targets()

        self.assertEqual("base:pawn_sprint", screen.pending_ability)
        # Three squares forward, and only that square.
        self.assertEqual({(3, 0)}, highlighted)

    def test_the_highlight_returns_to_ordinary_moves_when_the_ability_is_cancelled(self):
        screen = self.screen()
        AdjustResource("base:white", "base:ap", 3).apply(screen.session.state)
        self.right_click(screen, (6, 0))
        modal = screen._modal_rect()
        index = [choice.id for choice in screen.ability_choices].index("base:pawn_sprint")
        self.click_at(screen, p.Rect(modal.x + 16, modal.y + 50 + index * 42, modal.width - 32, 34).center)

        self.press(screen, p.K_ESCAPE)
        screen.selected_square = (6, 0)

        self.assertIsNone(screen.pending_ability)
        self.assertEqual({(5, 0), (4, 0)}, screen._highlight_targets())

    def test_a_long_event_message_is_wrapped_into_the_panel(self):
        """Messages are written by mods and can be any length; drawn unwrapped they ran off the
        side of the window."""
        screen = self.screen("base:advanced")
        screen.session.state.event_messages.append("A" * 200)

        wrapped = screen._wrap("A very long event message that certainly does not fit inside a narrow side panel", 120)

        self.assertGreater(len(wrapped), 1)
        for line in wrapped:
            self.assertLessEqual(screen.shared.fonts["small"].size(line)[0], 120)

    def test_a_fused_piece_shows_what_it_absorbed(self):
        screen = self.screen("base:advanced")
        self.clear_to(
            screen,
            ("base:rook", "base:white", (4, 0)), ("base:bishop", "base:black", (3, 0)),
            ("base:king", "base:white", (7, 4)), ("base:king", "base:black", (0, 4)),
        )
        self.click(screen, (4, 0))
        self.click(screen, (3, 0))

        blank = p.Surface(self.surface.get_size())
        blank.fill((0, 0, 0))
        drawn = blank.copy()
        screen.draw(drawn)
        rect = screen._layout(drawn).square_rect((3, 0))
        corner = p.Rect(rect.centerx, rect.centery, rect.width // 2, rect.height // 2)

        # The absorbed component's glyph is drawn into the square's bottom-right corner; a plain
        # rook leaves that corner as bare board.
        plain = blank.copy()
        self.clear_to(screen, ("base:rook", "base:white", (3, 0)), ("base:king", "base:white", (7, 4)), ("base:king", "base:black", (0, 4)))
        screen.draw(plain)
        self.assertNotEqual(
            p.image.tostring(plain.subsurface(corner), "RGB"),
            p.image.tostring(drawn.subsurface(corner), "RGB"),
        )

    def test_a_capture_clicked_on_the_board_fuses_and_undo_splits_it(self):
        screen = self.screen("base:advanced")
        self.clear_to(
            screen,
            ("base:rook", "base:white", (4, 0)), ("base:bishop", "base:black", (3, 0)),
            ("base:king", "base:white", (7, 4)), ("base:king", "base:black", (0, 4)),
        )

        self.click(screen, (4, 0))
        self.click(screen, (3, 0))

        fused = screen.session.state.board.at((3, 0))
        self.assertEqual(("base:rook", "base:bishop"), fused.definition.components)
        # It moves as both now: a diagonal destination no plain rook could reach. Generated rather
        # than read from legal_moves, which is current-side only and it is Black's turn.
        self.assertIn((2, 1), [move.end for move in pseudo_moves(screen.session.state, fused)])

        self.undo(screen)

        self.assertEqual("base:rook", self.occupant(screen, (4, 0)))
        self.assertEqual("base:bishop", self.occupant(screen, (3, 0)))


if __name__ == "__main__":
    unittest.main()
