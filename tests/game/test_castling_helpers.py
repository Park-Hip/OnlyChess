"""Regression tests for extracted castling helpers and king-only control."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, ROOK_CODE, WHITE
from src.game.board import Board, GameState
from src.game.castling import (
    copy_castle_rights,
    create_initial_castle_rights,
    get_piece_moves,
    restore_castle_rights_from_log,
    update_castle_rights_for_move,
)
from src.game.move import Move
from src.pieces import King, Rook


class CastlingHelperTests(unittest.TestCase):
    """Verify castling helpers keep rights logic out of GameState."""

    def test_king_move_disables_both_castling_rights_for_that_side(self):
        castle_rights = create_initial_castle_rights()
        board = Board()
        move = Move((7, 4), (6, 4), board.grid)

        update_castle_rights_for_move(castle_rights, move)

        self.assertFalse(castle_rights.wks)
        self.assertFalse(castle_rights.wqs)
        self.assertTrue(castle_rights.bks)
        self.assertTrue(castle_rights.bqs)

    def test_rook_move_disables_only_the_matching_side(self):
        castle_rights = create_initial_castle_rights()
        board = Board()
        move = Move((7, 7), (6, 7), board.grid)

        update_castle_rights_for_move(castle_rights, move)

        self.assertFalse(castle_rights.wks)
        self.assertTrue(castle_rights.wqs)

    def test_rook_capture_disables_the_matching_enemy_right(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.grid[4][0] = Rook(WHITE, (4, 0))
        game_state.board.grid[0][0] = Rook(BLACK, (0, 0))
        move = Move((4, 0), (0, 0), game_state.board.grid)
        castle_rights = create_initial_castle_rights()

        update_castle_rights_for_move(castle_rights, move)

        self.assertFalse(castle_rights.bqs)
        self.assertTrue(castle_rights.bks)

    def test_restore_castle_rights_from_log_returns_last_snapshot(self):
        first = create_initial_castle_rights()
        second = copy_castle_rights(first)
        second.wks = False

        restored = restore_castle_rights_from_log([first, second])

        self.assertFalse(restored.wks)
        self.assertTrue(restored.wqs)

    def test_game_state_undo_restores_castling_rights(self):
        game_state = GameState()
        move = Move((7, 7), (6, 7), game_state.board.grid)

        game_state.make_move(move)
        game_state.undo_move()

        self.assertTrue(game_state.current_castle_rights.wks)
        self.assertTrue(game_state.current_castle_rights.wqs)

    def test_attack_map_excludes_castling_pseudo_move_targets(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.grid[7][4] = King(WHITE, (7, 4))
        game_state.board.grid[0][4] = King(BLACK, (0, 4))
        game_state.white_king_pos = (7, 4)
        game_state.black_king_pos = (0, 4)
        game_state.white_to_move = True

        self.assertFalse(game_state.square_under_attack(0, 6))

    def test_get_piece_moves_keeps_include_castle_local_to_king(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        king = King(WHITE, (7, 4))
        rook = Rook(WHITE, (7, 7))
        game_state.board.grid[7][4] = king
        game_state.board.grid[7][7] = rook
        game_state.white_king_pos = (7, 4)

        king_moves = get_piece_moves(king, game_state, include_castle=False)
        rook_moves = get_piece_moves(rook, game_state, include_castle=False)

        self.assertTrue(all(not move.is_castle_move for move in king_moves))
        self.assertTrue(all(not move.is_castle_move for move in rook_moves))
        self.assertEqual(rook.get_piece_code(), ROOK_CODE)
        self.assertEqual(king.get_piece_code(), KING_CODE)


if __name__ == "__main__":
    unittest.main()
