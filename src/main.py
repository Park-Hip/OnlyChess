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
    dragging = False
    mouse_pos = (0, 0)
    move_attempt_type = 'click'
    click_type = 'first_click'
    font_panel = p.font.SysFont("Helvetica", 16, True, False)
    
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
                    start_x = BOARD_WIDTH // 2 - menu_width // 2
                    start_y = INFO_PANEL_HEIGHT + BOARD_HEIGHT // 2 - menu_height // 2
                    
                    if start_x <= location[0] < start_x + menu_width and start_y <= location[1] < start_y + menu_height:
                        index = (location[0] - start_x) // SQ_SIZE
                        pieces = ['Q', 'R', 'B', 'N']
                        choice = pieces[index]
                        gs.make_move(promotion_move_pending, choice, is_real_move=True) # is_real_move=True báo hiệu nước đi thật để kích hoạt sự kiện
                        move_made = True
                    promotion_move_pending = None
                    sq_selected = ()
                    player_clicks = []
                    continue

                location = p.mouse.get_pos() # (x, y)
                if location[1] < INFO_PANEL_HEIGHT or location[1] >= INFO_PANEL_HEIGHT + BOARD_HEIGHT:
                    continue # Clicked outside the board
                
                col = location[0] // SQ_SIZE
                row = (location[1] - INFO_PANEL_HEIGHT) // SQ_SIZE
                
                if sq_selected == (row, col):
                    dragging = True
                    mouse_pos = location
                    click_type = 'second_click'
                else:
                    piece = gs.board.grid[row][col]
                    if len(player_clicks) == 0:
                        if piece is not None and piece.color == ('w' if gs.white_to_move else 'b'):
                            sq_selected = (row, col)
                            player_clicks.append(sq_selected)
                            dragging = True
                            mouse_pos = location
                            click_type = 'first_click'
                    else:
                        if piece is not None and piece.color == ('w' if gs.white_to_move else 'b'):
                            sq_selected = (row, col)
                            player_clicks = [sq_selected]
                            dragging = True
                            mouse_pos = location
                            click_type = 'first_click'
                        else:
                            sq_selected = (row, col)
                            player_clicks.append(sq_selected)
                            move_attempt_type = 'click'
            
            elif e.type == p.MOUSEMOTION:
                mouse_pos = p.mouse.get_pos()
                
            elif e.type == p.MOUSEBUTTONUP:
                if promotion_move_pending:
                    continue
                if dragging:
                    dragging = False
                    location = p.mouse.get_pos()
                    end_col = max(0, min(7, location[0] // SQ_SIZE))
                    end_row = max(0, min(7, (location[1] - INFO_PANEL_HEIGHT) // SQ_SIZE))
                    
                    if (end_row, end_col) != player_clicks[0]:
                        player_clicks.append((end_row, end_col))
                        move_attempt_type = 'drag'
                    else:
                        if click_type == 'second_click':
                            sq_selected = ()
                            player_clicks = []

            # Process Move Attempt
            if len(player_clicks) == 2:
                move = Move(player_clicks[0], player_clicks[1], gs.board.grid)
                move_found = False
                for i in range(len(valid_moves)):
                    if move == valid_moves[i]:
                        move_found = True
                        if valid_moves[i].is_pawn_promotion:
                            promotion_move_pending = valid_moves[i]
                        else:
                            gs.make_move(valid_moves[i], is_real_move=True) # Truyền cờ is_real_move để phân biệt với lúc get_valid_moves giả lập
                            move_made = True
                            sq_selected = ()
                            player_clicks = []
                        break
                if not move_found and not promotion_move_pending:
                    if move_attempt_type == 'drag':
                        sq_selected = player_clicks[0]
                        player_clicks = [player_clicks[0]]
                    else:
                        r, c = player_clicks[1]
                        piece = gs.board.grid[r][c]
                        if piece is not None and piece.color == ('w' if gs.white_to_move else 'b'):
                            player_clicks = [(r, c)]
                            sq_selected = (r, c)
                        else:
                            player_clicks = []
                            sq_selected = ()
            
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.event_manager.handle_undo() # Khôi phục trạng thái bàn cờ nếu nước đi vừa Undo có liên quan đến sự kiện
                    gs.undo_move()
                    gs.event_manager.sync_state() # Đồng bộ lại bộ đếm turn và UI cảnh báo sau khi Undo
                    move_made = True

        if move_made:
            valid_moves = gs.get_valid_moves()
            move_made = False

        draw_game_state(screen, gs, valid_moves, sq_selected, images, dragging, mouse_pos)
        draw_info_panels(screen, gs, images, font_panel)
        if promotion_move_pending:
            color = 'w' if gs.white_to_move else 'b'
            draw_promotion_menu(screen, color, images)
            
        # Vẽ các hiệu ứng UI của sự kiện (ví dụ: dòng cảnh báo đỏ của Gia Xang Tang)
        for event in gs.event_manager.active_events:
            event.draw(screen, font_panel, WIDTH, HEIGHT, INFO_PANEL_HEIGHT)

        if gs.checkmate:
            draw_text(screen, "CHECKMATE! " + ("Black" if gs.white_to_move else "White") + " wins")
        elif gs.stalemate:
            draw_text(screen, "STALEMATE!")

        clock.tick(MAX_FPS)
        p.display.flip()

def draw_promotion_menu(screen, color, images):
    menu_width = 4 * SQ_SIZE
    menu_height = SQ_SIZE
    start_x = BOARD_WIDTH // 2 - menu_width // 2
    start_y = INFO_PANEL_HEIGHT + BOARD_HEIGHT // 2 - menu_height // 2
    
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
    text_location = p.Rect(0, INFO_PANEL_HEIGHT, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH/2 - text_object.get_width()/2, BOARD_HEIGHT/2 - text_object.get_height()/2)
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

def draw_game_state(screen, gs, valid_moves, sq_selected, images, dragging, mouse_pos):
    draw_board(screen)
    highlight_squares(screen, gs, valid_moves, sq_selected)
    draw_pieces(screen, gs.board.grid, images, sq_selected if dragging else ())
    
    if dragging and sq_selected:
        r, c = sq_selected
        piece = gs.board.grid[r][c]
        if piece:
            image = images[piece.id]
            screen.blit(image, p.Rect(mouse_pos[0] - SQ_SIZE//2, mouse_pos[1] - SQ_SIZE//2, SQ_SIZE, SQ_SIZE))

def draw_board(screen):
    colors = [COLOR_LIGHT, COLOR_DARK]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE + INFO_PANEL_HEIGHT, SQ_SIZE, SQ_SIZE))

def highlight_squares(screen, gs, valid_moves, sq_selected):
    if len(gs.move_log) > 0:
        last_move = gs.move_log[-1]
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(100)
        s.fill(p.Color("yellow"))
        screen.blit(s, (last_move.start_col * SQ_SIZE, last_move.start_row * SQ_SIZE + INFO_PANEL_HEIGHT))
        screen.blit(s, (last_move.end_col * SQ_SIZE, last_move.end_row * SQ_SIZE + INFO_PANEL_HEIGHT))

    if sq_selected != ():
        r, c = sq_selected
        if gs.board.grid[r][c] and gs.board.grid[r][c].color == ('w' if gs.white_to_move else 'b'):
            # Highlight ô được chọn
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color("blue"))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE + INFO_PANEL_HEIGHT))
            # Highlight các nước đi hợp lệ
            s.fill(p.Color("yellow"))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    screen.blit(s, (move.end_col * SQ_SIZE, move.end_row * SQ_SIZE + INFO_PANEL_HEIGHT))

def draw_pieces(screen, board_grid, images, dragged_sq):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            if (r, c) == dragged_sq:
                continue
            piece = board_grid[r][c]
            if piece:
                screen.blit(images[piece.id], p.Rect(c * SQ_SIZE, r * SQ_SIZE + INFO_PANEL_HEIGHT, SQ_SIZE, SQ_SIZE))

def draw_info_panels(screen, gs, images, font):
    # Top Panel (Black info)
    p.draw.rect(screen, p.Color("#2f2f2f"), p.Rect(0, 0, WIDTH, INFO_PANEL_HEIGHT))
    # Bottom Panel (White info)
    p.draw.rect(screen, p.Color("#2f2f2f"), p.Rect(0, HEIGHT - INFO_PANEL_HEIGHT, WIDTH, INFO_PANEL_HEIGHT))
    
    score = gs.get_material_advantage()
    white_captured, black_captured = gs.get_captured_pieces()
    
    mini_size = 24
    
    # Draw Top Panel (Player 2 / Black)
    name_text_b = font.render("Player 2", True, p.Color("white"))
    screen.blit(name_text_b, (10, 10))
    
    cx = 10
    cy = 32
    for piece in black_captured:
        img = p.transform.scale(images[piece], (mini_size, mini_size))
        screen.blit(img, (cx, cy))
        cx += mini_size // 2
    if score < 0:
        score_text = font.render(f"+{-score}", True, p.Color("white"))
        screen.blit(score_text, (cx + 10, cy + 2))
        
    # Draw Bottom Panel (Player 1 / White)
    name_text_w = font.render("Player 1", True, p.Color("white"))
    screen.blit(name_text_w, (10, HEIGHT - INFO_PANEL_HEIGHT + 10))
    
    cx = 10
    cy = HEIGHT - INFO_PANEL_HEIGHT + 32
    for piece in white_captured:
        img = p.transform.scale(images[piece], (mini_size, mini_size))
        screen.blit(img, (cx, cy))
        cx += mini_size // 2
    if score > 0:
        score_text = font.render(f"+{score}", True, p.Color("white"))
        screen.blit(score_text, (cx + 10, cy + 2))
        
    # Event UI: Tính toán và hiển thị thời gian diễn ra sự kiện tiếp theo
    turn_text = font.render(f"Turn: {gs.event_manager.turn_counter + 1}", True, p.Color("white"))
    turns_to_event = 10 - (gs.event_manager.turn_counter % 10)
    event_text = font.render(f"Next Event in: {turns_to_event}", True, p.Color("yellow"))
    screen.blit(turn_text, (WIDTH - 150, HEIGHT - INFO_PANEL_HEIGHT + 10))
    screen.blit(event_text, (WIDTH - 150, HEIGHT - INFO_PANEL_HEIGHT + 30))

if __name__ == "__main__":
    main()
