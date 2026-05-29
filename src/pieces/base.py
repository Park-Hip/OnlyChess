"""Base piece abstraction and shared movement helpers."""

from ..constants import BOARD_ROWS
from ..game.move import Move


class Piece:
    """Base class for all chess pieces."""

    piece_code = ""
    material_value = 0

    def __init__(self, color, name, pos):
        """
        Initialize a chess piece.
        color: 'w' for White or 'b' for Black
        name: short piece code such as 'p', 'N', 'B', 'R', 'Q', 'K'
        pos: (row, col)
        """
        self.color = color
        self.name = name
        self.pos = pos
        self.id = f"{color}{self.get_piece_code()}"
        self.has_moved = False
        self.is_active = True
        self.has_fused = False
        self.fusion_components = [self.get_piece_code()]
        self.primary_component_code = self.get_piece_code()

    def set_position(self, pos):
        """Update the piece position."""
        self.pos = pos

    def get_possible_moves(self, gs):
        """Return pseudo-legal moves for this piece."""
        if not self.is_active:
            return []
        return self._calculate_moves(gs)

    def _calculate_moves(self, gs):
        """Return piece-specific moves."""
        return []

    def _get_sliding_moves(self, gs, directions):
        """Generate moves for pieces that slide across the board."""
        moves = []
        r, c = self.pos
        for dr, dc in directions:
            for i in range(1, BOARD_ROWS):
                end_row = r + dr * i
                end_col = c + dc * i
                if not gs.board.is_inside_board(end_row, end_col):
                    break
                target = gs.board.get_piece_at(end_row, end_col)
                if target is None:
                    moves.append(Move((r, c), (end_row, end_col), gs.board.grid))
                elif self.can_capture_target(target):
                    moves.append(Move((r, c), (end_row, end_col), gs.board.grid))
                    break
                else:
                    break
        return moves

    def _get_one_step_moves(self, gs, directions):
        """Generate one-square moves for temporary movement limits."""
        moves = []
        r, c = self.pos
        for dr, dc in directions:
            end_row = r + dr
            end_col = c + dc
            if not gs.board.is_inside_board(end_row, end_col):
                continue
            target = gs.board.get_piece_at(end_row, end_col)
            if target is None or self.can_capture_target(target):
                moves.append(Move((r, c), (end_row, end_col), gs.board.grid))
        return moves

    def can_capture_target(self, target):
        """Return whether this piece can capture a target piece."""
        if target is None:
            return False
        if target.color == self.color:
            return False
        return not getattr(target, "is_shielded", False)

    def get_piece_code(self):
        """Return the stable piece code for registry and rules."""
        return self.piece_code or self.name

    def get_display_id(self):
        """Return the color-prefixed code used by the current UI."""
        return f"{self.color}{self.get_piece_code()}"

    def get_sprite_key(self):
        """Return the asset key used for piece rendering."""
        return self.get_display_id()

    def get_material_value(self):
        """Return the material value used by score summaries."""
        return self.material_value

    def can_fuse(self):
        """Return whether the piece is eligible for future fusion rules."""
        return not self.has_fused

    def is_minor_piece(self):
        """Return whether the piece counts as a minor piece."""
        return False

    def get_fusion_tags(self):
        """Return tags future fusion logic can use for matching."""
        return [self.get_piece_code()]

    def get_move_profile_name(self):
        """Return a readable movement profile name."""
        return self.__class__.__name__

    def __repr__(self):
        return f"{self.id}({self.pos[0]},{self.pos[1]})"
