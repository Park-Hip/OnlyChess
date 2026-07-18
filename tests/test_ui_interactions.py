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
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame as p

from src.engine.actions import AdjustResource
from src.engine.piece import Piece
from src.runtime import ApplicationContext, EngineSession
from src.ui.screens.engine_game_screen import EngineGameScreen


class ClickPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p.init()
        # convert_alpha() and the layout both want a real video surface, as in the running app.
        cls.surface = p.display.set_mode((800, 600))
        cls.context = ApplicationContext.load()

    def screen(self, mode_id="base:vanilla"):
        session = EngineSession(self.context.load_result, mode_id)
        shared = type("Shared", (), {"fonts": self._fonts(), "app_context": self.context})()
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

    def test_clicking_a_selected_piece_opens_its_abilities_and_targeting_spends_ap(self):
        screen = self.screen()
        AdjustResource("base:white", "base:ap", 3).apply(screen.session.state)

        self.click(screen, (7, 1))
        self.click(screen, (7, 1))

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

        self.click(screen, (7, 1))
        self.click(screen, (7, 1))
        self.assertTrue(screen.ability_choices)

        self.press(screen, p.K_ESCAPE)

        self.assertEqual((), screen.ability_choices)
        self.assertIsNone(screen.pending_ability)
        self.assertEqual(3, screen.session.state.resources["base:white"]["base:ap"])

    def test_a_capture_clicked_on_the_board_fuses_and_undo_splits_it(self):
        screen = self.screen("base:advanced")
        self.clear_to(
            screen,
            ("base:rook", "base:white", (4, 0)), ("base:bishop", "base:black", (3, 0)),
            ("base:king", "base:white", (7, 4)), ("base:king", "base:black", (0, 4)),
        )

        self.click(screen, (4, 0))
        self.click(screen, (3, 0))

        self.assertEqual("base:warden", self.occupant(screen, (3, 0)))

        self.undo(screen)

        self.assertEqual("base:rook", self.occupant(screen, (4, 0)))
        self.assertEqual("base:bishop", self.occupant(screen, (3, 0)))


if __name__ == "__main__":
    unittest.main()
