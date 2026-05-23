"""Special event definitions and event manager."""

import copy

import pygame as p

from .constants import BOARD_COLS, BOARD_ROWS, ROOK_CODE
from .pieces.piece import Knight

class EventStateSnapshot:
    # Lưu trữ trạng thái bàn cờ trước khi sự kiện xảy ra để hỗ trợ tính năng Undo
    def __init__(self, move_log_len, grid_copy):
        self.move_log_len = move_log_len
        self.grid_copy = grid_copy

class ChessEvent:
    # Lớp cơ sở cho tất cả các sự kiện đặc biệt
    def __init__(self, game_state):
        self.gs = game_state
        self.name = "Base Event"
        self.duration = 0
        
    def trigger_warning(self):
        pass
        
    def execute(self):
        pass
        
    def cleanup(self):
        pass
        
    def draw(self, screen, font, WIDTH, HEIGHT, INFO_PANEL_HEIGHT):
        pass

class GiaXangTang(ChessEvent):
    # Sự kiện "Giá Xăng Tăng": Biến tất cả Xe (Rook) thành Mã (Knight)
    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Gia Xang Tang"
        self.warning_active = False

    def trigger_warning(self):
        self.warning_active = True

    def execute(self):
        self.warning_active = False
        # Transform all Rooks into Knights
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                piece = self.gs.board.grid[r][c]
                if piece and piece.id[1] == ROOK_CODE:
                    new_knight = Knight(piece.color, (r, c))
                    new_knight.has_moved = piece.has_moved
                    self.gs.board.grid[r][c] = new_knight
        print("Event executed: Gia Xang Tang (All Rooks became Knights)")

    def draw(self, screen, font, WIDTH, HEIGHT, INFO_PANEL_HEIGHT):
        if self.warning_active:
            text = "WARNING: GIA XANG TANG INCOMING! ALL ROOKS BECOME KNIGHTS."
            text_object = font.render(text, True, p.Color("red"))
            screen.blit(text_object, (10, INFO_PANEL_HEIGHT + 10))

class EventManager:
    # Quản lý hệ thống sự kiện: đếm turn, kích hoạt sự kiện, và xử lý Undo
    def __init__(self, game_state):
        self.gs = game_state
        self.turn_counter = 0
        self.active_events = []
        self.queued_event = None
        self.snapshots = []
        
        self.event_pool = [GiaXangTang]
        self._queue_next_event()

    def _queue_next_event(self):
        import random
        event_class = random.choice(self.event_pool)
        self.queued_event = event_class(self.gs)

    def _create_snapshot(self):
        grid_copy = copy.deepcopy(self.gs.board.grid)
        return EventStateSnapshot(len(self.gs.move_log), grid_copy)

    def update(self):
        self.turn_counter = len(self.gs.move_log) // 2
        
        # Check for event warning (Turn 9, 19, etc.)
        if self.turn_counter > 0 and self.turn_counter % 10 == 9:
            if self.queued_event and self.queued_event not in self.active_events:
                self.queued_event.trigger_warning()
                self.active_events.append(self.queued_event)

        # Check for event execution (Turn 10, 20, etc.)
        if self.turn_counter > 0 and self.turn_counter % 10 == 0:
            # We must only execute once per Turn 10, Turn 20, etc.
            # We can verify this by checking if queued_event is still the one for this cycle
            if self.queued_event and self.queued_event in self.active_events:
                self.snapshots.append(self._create_snapshot())
                
                self.queued_event.execute()
                if self.queued_event.duration == 0:
                    self.queued_event.cleanup()
                    self.active_events.remove(self.queued_event)
                
                self.queued_event = None
                self._queue_next_event()

    def handle_undo(self):
        """Checks if we need to revert an event snapshot. Must be called BEFORE gs.undo_move()."""
        if not self.snapshots:
            return False
            
        latest_snapshot = self.snapshots[-1]
        
        # If the current move_log length matches the snapshot, an event happened right after this move.
        if len(self.gs.move_log) == latest_snapshot.move_log_len:
            self.gs.board.grid = copy.deepcopy(latest_snapshot.grid_copy)
            self.snapshots.pop()
            return True
            
        return False

    def sync_state(self):
        """Called AFTER gs.undo_move() to recalculate turn counters and warnings."""
        self.turn_counter = len(self.gs.move_log) // 2
        self.active_events.clear()
        
        # If we are back at Turn 9, reinstate the warning
        if self.turn_counter > 0 and self.turn_counter % 10 == 9:
            self.queued_event = GiaXangTang(self.gs)
            self.queued_event.trigger_warning()
            self.active_events.append(self.queued_event)
        elif self.turn_counter % 10 != 0:
            # If not a resolution or warning turn, just queue the next event normally
            self.queued_event = GiaXangTang(self.gs)
