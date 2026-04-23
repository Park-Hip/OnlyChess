# src/board.py
from .piece import Pawn, Knight, Bishop, Rook, Queen, King

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.setup_classic()
        
    def setup_classic(self):
        # Đặt quân cờ theo luật Classic
        placement = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        for c in range(8):
            self.grid[0][c] = self.create_piece('b', placement[c], (0, c))
            self.grid[1][c] = Pawn('b', (1, c))
            self.grid[6][c] = Pawn('w', (6, c))
            self.grid[7][c] = self.create_piece('w', placement[c], (7, c))
            
    def create_piece(self, color, name, pos):
        if name == 'R': return Rook(color, pos)
        if name == 'N': return Knight(color, pos)
        if name == 'B': return Bishop(color, pos)
        if name == 'Q': return Queen(color, pos)
        if name == 'K': return King(color, pos)
        return None

class GameState:
    def __init__(self):
        self.board = Board()
        self.white_to_move = True
        self.move_log = []
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self.checkmate = False
        self.stalemate = False

    def make_move(self, move):
        # Di chuyển quân cờ trên lưới
        self.board.grid[move.start_row][move.start_col] = None
        self.board.grid[move.end_row][move.end_col] = move.piece_moved
        
        # Cập nhật tọa độ trong Piece object
        move.piece_moved.set_position((move.end_row, move.end_col))
        move.piece_moved.has_moved = True
        
        # Ghi log
        self.move_log.append(move)
        
        # Đổi lượt
        self.white_to_move = not self.white_to_move
        
        # Cập nhật vị trí Vua nếu cần
        if move.piece_moved.name == 'K':
            if move.piece_moved.color == 'w':
                self.white_king_pos = (move.end_row, move.end_col)
            else:
                self.black_king_pos = (move.end_row, move.end_col)

    def undo_move(self):
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            
            # Khôi phục vị trí cũ
            self.board.grid[move.start_row][move.start_col] = move.piece_moved
            self.board.grid[move.end_row][move.end_col] = move.piece_captured
            
            # Khôi phục tọa độ trong Piece object
            move.piece_moved.set_position((move.start_row, move.start_col))
            # Lưu ý: has_moved có thể cần logic phức tạp hơn nếu muốn undo chính xác tuyệt đối
            
            # Đổi lại lượt
            self.white_to_move = not self.white_to_move
            
            # Cập nhật lại vị trí Vua nếu cần
            if move.piece_moved.name == 'K':
                if move.piece_moved.color == 'w':
                    self.white_king_pos = (move.start_row, move.start_col)
                else:
                    self.black_king_pos = (move.start_row, move.start_col)

    def get_valid_moves(self):
        # 1. Lấy tất cả các nước đi pseudo-legal
        moves = self.get_all_possible_moves()
        
        # 2. Với mỗi nước đi, giả định thực hiện nó
        for i in range(len(moves) - 1, -1, -1):
            move = moves[i]
            self.make_move(move)
            
            # 3. Sau khi di chuyển, kiểm tra xem Vua của mình có bị chiếu không
            self.white_to_move = not self.white_to_move # Đổi lại lượt tạm thời để kiểm tra Vua của mình
            if self.in_check():
                moves.remove(move)
            self.white_to_move = not self.white_to_move # Đổi lại lượt
            self.undo_move()
            
        if len(moves) == 0:
            if self.in_check():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False
            
        return moves

    def in_check(self):
        if self.white_to_move:
            return self.square_under_attack(self.white_king_pos[0], self.white_king_pos[1])
        else:
            return self.square_under_attack(self.black_king_pos[0], self.black_king_pos[1])

    def square_under_attack(self, r, c):
        # Đổi lượt để xem các nước đi của đối phương
        self.white_to_move = not self.white_to_move
        opp_moves = self.get_all_possible_moves()
        self.white_to_move = not self.white_to_move
        for move in opp_moves:
            if move.end_row == r and move.end_col == c:
                return True
        return False

    def get_all_possible_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board.grid[r][c]
                if piece and ((piece.color == 'w' and self.white_to_move) or \
                             (piece.color == 'b' and not self.white_to_move)):
                    moves.extend(piece.get_possible_moves(self.board))
        return moves
