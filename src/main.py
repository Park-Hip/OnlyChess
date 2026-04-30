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
    promotion_move_pending = None
    
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # Xử lý chuột
            elif e.type == p.MOUSEBUTTONDOWN:
                if promotion_move_pending:
                    location = p.mouse.get_pos()
                    menu_width = 4 * SQ_SIZE
                    menu_height = SQ_SIZE
                    start_x = WIDTH // 2 - menu_width // 2
                    start_y = HEIGHT // 2 - menu_height // 2
                    
                    if start_x <= location[0] < start_x + menu_width and start_y <= location[1] < start_y + menu_height:
                        index = (location[0] - start_x) // SQ_SIZE
                        pieces = ['Q', 'R', 'B', 'N']
                        choice = pieces[index]
                        gs.make_move(promotion_move_pending, choice)
                        move_made = True
                    promotion_move_pending = None
                    sq_selected = ()
                    player_clicks = []
                    continue

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
                    move_found = False
                    for i in range(len(valid_moves)):
                        if move == valid_moves[i]:
                            move_found = True
                            if valid_moves[i].is_pawn_promotion:
                                promotion_move_pending = valid_moves[i]
                            else:
                                gs.make_move(valid_moves[i])
                                move_made = True
                                sq_selected = () # Reset chọn
                                player_clicks = []
                            break
                    if not move_found and not promotion_move_pending:
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
        if promotion_move_pending:
            color = 'w' if gs.white_to_move else 'b'
            draw_promotion_menu(screen, color, images)

        if gs.checkmate:
            draw_text(screen, "CHECKMATE! " + ("Black" if gs.white_to_move else "White") + " wins")
        elif gs.stalemate:
            draw_text(screen, "STALEMATE!")

        clock.tick(MAX_FPS)
        p.display.flip()

def draw_promotion_menu(screen, color, images):
    menu_width = 4 * SQ_SIZE
    menu_height = SQ_SIZE
    start_x = WIDTH // 2 - menu_width // 2
    start_y = HEIGHT // 2 - menu_height // 2
    
    # Vẽ nền
    p.draw.rect(screen, p.Color("gray"), p.Rect(start_x, start_y, menu_width, menu_height))
    p.draw.rect(screen, p.Color("black"), p.Rect(start_x, start_y, menu_width, menu_height), 2)
    
    # Vẽ các quân cờ
    pieces = ['Q', 'R', 'B', 'N']
    for i, piece in enumerate(pieces):
        image = images[color + piece]
        screen.blit(image, p.Rect(start_x + i * SQ_SIZE, start_y, SQ_SIZE, SQ_SIZE))

def draw_text(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, 0, p.Color("Gray"))
    text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - text_object.get_width()/2, HEIGHT/2 - text_object.get_height()/2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, p.Color("Black"))
    screen.blit(text_object, text_location.move(2, 2))

def load_images():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    images = {}
    for piece in pieces:
        # Lưu ý: Bạn cần đảm bảo đường dẫn đúng tới thư mục images
        images[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
    return images

def draw_game_state(screen, gs, valid_moves, sq_selected, images):
    draw_board(screen)
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
