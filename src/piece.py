from .move import Move

class Piece:
    def __init__(self, color, name, pos):
        """
        Khởi tạo quân cờ.
        color: 'w' (Trắng) hoặc 'b' (Đen)
        name: 'p', 'N', 'B', 'R', 'Q', 'K'
        pos: (row, col)
        """
        self.color = color
        self.name = name
        self.pos = pos
        self.id = f"{color}{name}" # VD: "bp", "wK"
        self.has_moved = False
        self.status = "active" # Có thể là "active", "locked", "disabled", v.v.

    def set_position(self, pos):
        self.pos = pos

    def get_possible_moves(self, board):
        """
        Trả về danh sách các Move object hợp lệ (chưa xét chiếu).
        """
        if self.status != "active":
            return []
        return self._calculate_moves(board)

    def _calculate_moves(self, board):
        return []

    def _get_sliding_moves(self, board, directions):
        moves = []
        r, c = self.pos
        for dr, dc in directions:
            for i in range(1, 8):
                end_row = r + dr * i
                end_col = c + dc * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    target = board.grid[end_row][end_col]
                    if target is None:
                        moves.append(Move((r, c), (end_row, end_col), board.grid))
                    elif target.color != self.color:
                        moves.append(Move((r, c), (end_row, end_col), board.grid))
                        break
                    else:
                        break
                else:
                    break
        return moves

    def __repr__(self):
        return f"{self.id}({self.pos[0]},{self.pos[1]})"

class Pawn(Piece):
    def __init__(self, color, pos):
        super().__init__(color, 'p', pos)
        self.direction = -1 if color == 'w' else 1

    def _calculate_moves(self, board):
        moves = []
        r, c = self.pos
        # Đi thẳng
        if board.grid[r + self.direction][c] is None:
            moves.append(Move((r, c), (r + self.direction, c), board.grid))
            # Đi 2 ô nếu ở vị trí xuất phát
            if (self.color == 'w' and r == 6) or (self.color == 'b' and r == 1):
                if board.grid[r + 2 * self.direction][c] is None:
                    moves.append(Move((r, c), (r + 2 * self.direction, c), board.grid))
        
        # Ăn chéo
        for dc in [-1, 1]:
            nc = c + dc
            nr = r + self.direction
            if 0 <= nc < 8 and 0 <= nr < 8:
                target = board.grid[nr][nc]
                if target is not None and target.color != self.color:
                    moves.append(Move((r, c), (nr, nc), board.grid))
        return moves

class Knight(Piece):
    def __init__(self, color, pos):
        super().__init__(color, 'N', pos)

    def _calculate_moves(self, board):
        moves = []
        r, c = self.pos
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for dr, dc in knight_moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board.grid[nr][nc]
                if target is None or target.color != self.color:
                    moves.append(Move((r, c), (nr, nc), board.grid))
        return moves

class Bishop(Piece):
    def __init__(self, color, pos):
        super().__init__(color, 'B', pos)

    def _calculate_moves(self, board):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self._get_sliding_moves(board, directions)

class Rook(Piece):
    def __init__(self, color, pos):
        super().__init__(color, 'R', pos)

    def _calculate_moves(self, board):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self._get_sliding_moves(board, directions)

class Queen(Piece):
    def __init__(self, color, pos):
        super().__init__(color, 'Q', pos)

    def _calculate_moves(self, board):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
        return self._get_sliding_moves(board, directions)

class King(Piece):
    def __init__(self, color, pos):
        super().__init__(color, 'K', pos)

    def _calculate_moves(self, board):
        moves = []
        r, c = self.pos
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board.grid[nr][nc]
                if target is None or target.color != self.color:
                    moves.append(Move((r, c), (nr, nc), board.grid))
        return moves
