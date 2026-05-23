"""Move object for representing chess actions."""

from ..constants import LAST_BOARD_INDEX, PAWN_CODE


class Move:
    """Represent one chess move together with undo snapshot data."""

    # Bản đồ chuyển đổi tọa độ cờ vua sang chỉ số mảng
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board_grid, is_enpassant_move=False, is_castle_move=False):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        
        self.piece_moved = board_grid[self.start_row][self.start_col]
        self.piece_captured = board_grid[self.end_row][self.end_col]
        
        # Đánh dấu nước đi đặc biệt
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            # Quân bị ăn trong En Passant nằm ở hàng của quân đi, nhưng ở cột đích
            self.piece_captured = board_grid[self.start_row][self.end_col]
            
        self.is_castle_move = is_castle_move
        
        # Phong cấp
        self.is_pawn_promotion = False
        if self.piece_moved is not None:
            self.is_pawn_promotion = (
                self.piece_moved.name == PAWN_CODE and (self.end_row == 0 or self.end_row == LAST_BOARD_INDEX)
            )
        
        # Move ID để so sánh dễ dàng
        self.move_id = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col
        
        # Lưu lại trạng thái trước đó để Undo
        self.enpassant_possible_prev = ()
        self.moved_piece_prev_pos = None
        self.moved_piece_prev_has_moved = None
        self.captured_piece_prev_pos = None
        self.captured_piece_prev_has_moved = None
        self.promoted_to_piece = None
        self.rook_moved = None
        self.rook_start_pos = None
        self.rook_end_pos = None
        self.rook_prev_has_moved = None
        self.is_real_move = False

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False

    def get_chess_notation(self):
        # Ví dụ: "e2e4"
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, r, c):
        return self.cols_to_files[c] + self.rows_to_ranks[r]

    def __repr__(self):
        return f"Move({self.get_chess_notation()})"
