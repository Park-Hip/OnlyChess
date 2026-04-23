import pygame as p
from .board import GameState
from .move import Move
from .constants import *

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = GameState()
    valid_moves = gs.get_valid_moves()
    move_made = False # Flag cho khi có nước đi được thực hiện
    
    images = load_images()
    running = True
    sq_selected = () # (row, col) cuối cùng được chọn
    player_clicks = [] # [(row, col), (row, col)] 2 điểm chọn (điểm đầu và điểm cuối)
    
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # Xử lý chuột
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos() # (x, y)
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                
                if sq_selected == (row, col): # Click lại ô cũ -> Hủy chọn
                    sq_selected = ()
                    player_clicks = []
                else:
                    if len(player_clicks) == 0: # Lần click đầu tiên
                        piece = gs.board.grid[row][col]
                        if piece is not None and piece.color == ('w' if gs.white_to_move else 'b'):
                            sq_selected = (row, col)
                            player_clicks.append(sq_selected)
                    else: # Lần click thứ hai
                        sq_selected = (row, col)
                        player_clicks.append(sq_selected)
                
                if len(player_clicks) == 2: # Đã chọn đủ 2 điểm
                    move = Move(player_clicks[0], player_clicks[1], gs.board.grid)
                    for i in range(len(valid_moves)):
                        if move == valid_moves[i]:
                            gs.make_move(valid_moves[i])
                            move_made = True
                            sq_selected = () # Reset chọn
                            player_clicks = []
                    if not move_made:
                        # Nếu nước đi không hợp lệ, giữ lại ô vừa click làm ô chọn mới nếu nó là quân của mình
                        piece = gs.board.grid[row][col]
                        if piece is not None and piece.color == ('w' if gs.white_to_move else 'b'):
                            player_clicks = [(row, col)]
                            sq_selected = (row, col)
                        else:
                            player_clicks = []
                            sq_selected = ()
            
            # Xử lý phím (Undo)
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undo_move()
                    move_made = True

        if move_made:
            valid_moves = gs.get_valid_moves()
            move_made = False

        draw_game_state(screen, gs, valid_moves, sq_selected, images)
        clock.tick(MAX_FPS)
        p.display.flip()

def load_images():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    images = {}
    for piece in pieces:
        # Lưu ý: Bạn cần đảm bảo đường dẫn đúng tới thư mục images
        images[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
    return images

def draw_game_state(screen, gs, valid_moves, sq_selected, images):
    draw_board(screqen)
    highlight_squares(screen, gs, valid_moves, sq_selected)
    draw_pieces(screen, gs.board.grid, images)

def draw_board(screen):
    colors = [COLOR_LIGHT, COLOR_DARK]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def highlight_squares(screen, gs, valid_moves, sq_selected):
    if sq_selected != ():
        r, c = sq_selected
        if gs.board.grid[r][c] and gs.board.grid[r][c].color == ('w' if gs.white_to_move else 'b'):
            # Highlight ô được chọn
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color("blue"))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
            # Highlight các nước đi hợp lệ
            s.fill(p.Color("yellow"))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    screen.blit(s, (move.end_col * SQ_SIZE, move.end_row * SQ_SIZE))

def draw_pieces(screen, board_grid, images):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board_grid[r][c]
            if piece:
                screen.blit(images[piece.id], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

if __name__ == "__main__":
    main()
