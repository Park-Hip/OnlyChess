"""Tests for the position description.

The oracle is only as trustworthy as its FEN adapter. A silent bug here — a
dropped castling right, a flipped rank — would be invisible to an old-vs-old
comparison, because both sides would read the same wrong position. So the FEN
layer is tested directly rather than through the oracle.
"""

import unittest

from src.constants import BLACK, KING_CODE, PAWN_CODE, QUEEN_CODE, WHITE

from .position import (
    STARTING_FEN,
    fen_from_game_state,
    game_state_from_fen,
    rc_to_square,
    square_to_rc,
)


class SquareMappingTests(unittest.TestCase):
    """Rank/file <-> grid indices. Off-by-one here silently rotates the board."""

    def test_a8_is_the_grid_origin(self):
        self.assertEqual(square_to_rc("a8"), (0, 0))

    def test_h1_is_the_far_corner(self):
        self.assertEqual(square_to_rc("h1"), (7, 7))

    def test_e4_matches_the_engines_own_mapping(self):
        # Move.ranks_to_rows says "4" -> 4 and files_to_cols says "e" -> 4.
        self.assertEqual(square_to_rc("e4"), (4, 4))

    def test_round_trips(self):
        for square in ("a1", "e4", "h8", "d7", "b2"):
            self.assertEqual(rc_to_square(*square_to_rc(square)), square)


class FenParsingTests(unittest.TestCase):

    def test_starting_position_places_kings_where_the_engine_expects(self):
        state = game_state_from_fen(STARTING_FEN)
        self.assertEqual(state.white_king_pos, (7, 4))
        self.assertEqual(state.black_king_pos, (0, 4))

    def test_pawn_case_means_colour_not_a_different_code(self):
        # The trap: FEN uses case for colour, the engine's pawn code is "p" for
        # both. Conflating them would make every black pawn an unknown piece.
        state = game_state_from_fen(STARTING_FEN)
        white_pawn = state.board.grid[6][0]
        black_pawn = state.board.grid[1][0]
        self.assertEqual(white_pawn.get_piece_code(), PAWN_CODE)
        self.assertEqual(black_pawn.get_piece_code(), PAWN_CODE)
        self.assertEqual(white_pawn.color, WHITE)
        self.assertEqual(black_pawn.color, BLACK)

    def test_side_to_move(self):
        self.assertTrue(game_state_from_fen(STARTING_FEN).white_to_move)
        black = STARTING_FEN.replace(" w ", " b ")
        self.assertFalse(game_state_from_fen(black).white_to_move)

    def test_castling_rights_are_read_per_flag(self):
        state = game_state_from_fen(
            "r3k2r/8/8/8/8/8/8/R3K2R w Kq - 0 1"
        )
        rights = state.current_castle_rights
        self.assertTrue(rights.wks)
        self.assertFalse(rights.wqs)
        self.assertFalse(rights.bks)
        self.assertTrue(rights.bqs)

    def test_no_castling_rights(self):
        state = game_state_from_fen("r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1")
        rights = state.current_castle_rights
        self.assertFalse(any((rights.wks, rights.wqs, rights.bks, rights.bqs)))

    def test_enpassant_target_is_a_square_not_a_string(self):
        state = game_state_from_fen(
            "rnbqkbnr/pppp1ppp/8/4p3/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1"
        )
        self.assertEqual(state.enpassant_possible, (2, 4))

    def test_absent_enpassant_is_the_empty_tuple(self):
        # The engine tests `enpassant_possible` for truthiness and compares it to
        # a (row, col) tuple; None would work by luck, () is what it uses.
        self.assertEqual(game_state_from_fen(STARTING_FEN).enpassant_possible, ())

    def test_empty_square_runs(self):
        state = game_state_from_fen("8/8/8/4Q3/8/8/8/K6k w - - 0 1")
        self.assertEqual(state.board.grid[3][4].get_piece_code(), QUEEN_CODE)
        self.assertIsNone(state.board.grid[3][3])
        self.assertEqual(state.board.grid[7][0].get_piece_code(), KING_CODE)


class KinglessFenTests(unittest.TestCase):
    """A FEN without a king must fail loudly, not default.

    GameState.__init__ pre-seeds white_king_pos = (7, 4) for the classic setup.
    A kingless FEN would keep it, in_check() would probe an empty square, and the
    move set would be silently wrong — with no exception and nothing in the
    output looking off. That is worst precisely when someone hand-writes a
    fragment position to debug a divergence, which is the oracle's whole job.
    """

    def test_no_kings_at_all_raises(self):
        with self.assertRaises(ValueError) as caught:
            game_state_from_fen("8/8/8/4Q3/8/8/8/8 w - - 0 1")
        self.assertIn("white", str(caught.exception))
        self.assertIn("black", str(caught.exception))

    def test_missing_white_king_raises_and_names_the_side(self):
        with self.assertRaises(ValueError) as caught:
            game_state_from_fen("7k/8/8/4Q3/8/8/8/8 w - - 0 1")
        message = str(caught.exception)
        self.assertIn("white", message)
        self.assertNotIn("black", message)

    def test_missing_black_king_raises_and_names_the_side(self):
        with self.assertRaises(ValueError) as caught:
            game_state_from_fen("8/8/8/4Q3/8/8/8/K7 w - - 0 1")
        self.assertIn("black", str(caught.exception))

    def test_the_error_quotes_the_offending_fen(self):
        fen = "8/8/8/4Q3/8/8/8/8 w - - 0 1"
        with self.assertRaises(ValueError) as caught:
            game_state_from_fen(fen)
        self.assertIn(fen, str(caught.exception))


class FenSerialisationTests(unittest.TestCase):

    def test_starting_position_round_trips_exactly(self):
        self.assertEqual(fen_from_game_state(game_state_from_fen(STARTING_FEN)), STARTING_FEN)

    def test_round_trips_the_published_perft_positions(self):
        # If any of these lose a field, the perft suite is measuring the wrong
        # position and its ground truth means nothing.
        from .perft import POSITIONS

        for name, (fen, _) in POSITIONS.items():
            with self.subTest(position=name):
                # Normalise the counters this engine does not track.
                expected = " ".join(fen.split()[:4]) + " 0 1"
                self.assertEqual(fen_from_game_state(game_state_from_fen(fen)), expected)

    def test_fused_pieces_survive_a_round_trip(self):
        # The FEN extension: A/C/W/I are not standard, and nothing outside this
        # project will validate them for us.
        fen = "w6i/8/8/8/8/8/8/K5Ak w - - 0 1"
        self.assertEqual(fen_from_game_state(game_state_from_fen(fen)), fen)
