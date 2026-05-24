"""Standard chess piece implementations."""

from ..constants import (
    BISHOP_CODE,
    BLACK,
    BOARD_COLS,
    BOARD_ROWS,
    KING_CODE,
    KNIGHT_CODE,
    PAWN_CODE,
    QUEEN_CODE,
    ROOK_CODE,
    WHITE,
)
from ..game.state_helpers import is_inside_board
from ..game.move import Move
from .base import Piece

class Pawn(Piece):
    """Standard pawn movement rules."""

    piece_code = PAWN_CODE
    material_value = 1

    def __init__(self, color, pos):
        super().__init__(color, PAWN_CODE, pos)
        self.direction = -1 if color == WHITE else 1

    def is_minor_piece(self):
        """Pawns are not minor pieces."""
        return False

    def _calculate_moves(self, gs):
        moves = []
        r, c = self.pos
        one_step_row = r + self.direction

        # Single-step forward move.
        if is_inside_board(one_step_row, c) and gs.board.get_piece_at(one_step_row, c) is None:
            moves.append(Move((r, c), (one_step_row, c), gs.board.grid))
            # Two-step forward move from the starting rank.
            if (self.color == WHITE and r == BOARD_ROWS - 2) or (self.color == BLACK and r == 1):
                two_step_row = r + 2 * self.direction
                if is_inside_board(two_step_row, c) and gs.board.get_piece_at(two_step_row, c) is None:
                    moves.append(Move((r, c), (two_step_row, c), gs.board.grid))
        
        # Diagonal capture and en passant checks.
        for dc in [-1, 1]:
            nc = c + dc
            nr = r + self.direction
            if is_inside_board(nr, nc):
                target = gs.board.get_piece_at(nr, nc)
                if target is not None and target.color != self.color:
                    moves.append(Move((r, c), (nr, nc), gs.board.grid))
                elif (nr, nc) == gs.enpassant_possible:
                    moves.append(Move((r, c), (nr, nc), gs.board.grid, is_enpassant_move=True))
        return moves

class Knight(Piece):
    """Standard knight movement rules."""

    piece_code = KNIGHT_CODE
    material_value = 3

    def __init__(self, color, pos):
        super().__init__(color, KNIGHT_CODE, pos)

    def is_minor_piece(self):
        """Knights count as minor pieces."""
        return True

    def _calculate_moves(self, gs):
        moves = []
        r, c = self.pos
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for dr, dc in knight_moves:
            nr, nc = r + dr, c + dc
            if is_inside_board(nr, nc):
                target = gs.board.get_piece_at(nr, nc)
                if target is None or target.color != self.color:
                    moves.append(Move((r, c), (nr, nc), gs.board.grid))
        return moves

class Bishop(Piece):
    """Standard bishop movement rules."""

    piece_code = BISHOP_CODE
    material_value = 3

    def __init__(self, color, pos):
        super().__init__(color, BISHOP_CODE, pos)

    def is_minor_piece(self):
        """Bishops count as minor pieces."""
        return True

    def _calculate_moves(self, gs):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self._get_sliding_moves(gs, directions)

class Rook(Piece):
    """Standard rook movement rules."""

    piece_code = ROOK_CODE
    material_value = 5

    def __init__(self, color, pos):
        super().__init__(color, ROOK_CODE, pos)

    def is_minor_piece(self):
        """Rooks are not minor pieces."""
        return False

    def _calculate_moves(self, gs):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self._get_sliding_moves(gs, directions)

class Queen(Piece):
    """Standard queen movement rules."""

    piece_code = QUEEN_CODE
    material_value = 9

    def __init__(self, color, pos):
        super().__init__(color, QUEEN_CODE, pos)

    def is_minor_piece(self):
        """Queens are not minor pieces."""
        return False

    def _calculate_moves(self, gs):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
        return self._get_sliding_moves(gs, directions)

class King(Piece):
    """Standard king movement rules including castling."""

    piece_code = KING_CODE
    material_value = 0

    def __init__(self, color, pos):
        super().__init__(color, KING_CODE, pos)

    def can_fuse(self):
        """Kings are never eligible for fusion."""
        return False

    def is_minor_piece(self):
        """Kings are not minor pieces."""
        return False

    def get_possible_moves(self, gs, include_castle=True):
        """Return king moves while optionally including castling."""
        if not self.is_active:
            return []
        return self._calculate_moves(gs, include_castle=include_castle)

    def _calculate_moves(self, gs, include_castle=True):
        moves = []
        r, c = self.pos
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_inside_board(nr, nc):
                target = gs.board.get_piece_at(nr, nc)
                if target is None or target.color != self.color:
                    moves.append(Move((r, c), (nr, nc), gs.board.grid))
        
        # Add castling moves when castling generation is enabled.
        if include_castle:
            moves.extend(self.get_castle_moves(gs))
        return moves

    def get_castle_moves(self, gs):
        moves = []
        if gs.in_check():
            return moves  # Castling is illegal while the king is in check.
        
        r, c = self.pos
        if (self.color == WHITE and gs.current_castle_rights.wks) or (self.color == BLACK and gs.current_castle_rights.bks):
            # King side castle
            corner_piece = gs.board.get_piece_at(r, BOARD_COLS - 1)
            if (
                corner_piece is not None
                and corner_piece.color == self.color
                and corner_piece.get_piece_code() == ROOK_CODE
                and gs.board.get_piece_at(r, c + 1) is None
                and gs.board.get_piece_at(r, c + 2) is None
            ):
                if not gs.square_under_attack(r, c+1) and not gs.square_under_attack(r, c+2):
                    moves.append(Move((r, c), (r, c+2), gs.board.grid, is_castle_move=True))
        
        if (self.color == WHITE and gs.current_castle_rights.wqs) or (self.color == BLACK and gs.current_castle_rights.bqs):
            # Queen side castle
            corner_piece = gs.board.get_piece_at(r, 0)
            if (
                corner_piece is not None
                and corner_piece.color == self.color
                and corner_piece.get_piece_code() == ROOK_CODE
                and gs.board.get_piece_at(r, c - 1) is None
                and gs.board.get_piece_at(r, c - 2) is None
                and gs.board.get_piece_at(r, c - 3) is None
            ):
                if not gs.square_under_attack(r, c-1) and not gs.square_under_attack(r, c-2):
                    moves.append(Move((r, c), (r, c-2), gs.board.grid, is_castle_move=True))
        return moves

