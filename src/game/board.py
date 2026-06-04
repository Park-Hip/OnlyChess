"""Board and game-state models for the chess domain."""

from ..constants import BISHOP_CODE, BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, KNIGHT_CODE, PAWN_CODE, QUEEN_CODE, ROOK_CODE, STANDARD_PIECE_ORDER, WHITE
from ..events.manager import EventManager
from ..fusion.manager import FusionManager
from ..pieces import Pawn, create_piece
from .action_points import ActionPointTracker
from .capture_tracker import CaptureTracker
from .castling import (
    copy_castle_rights,
    create_initial_castle_rights,
    get_piece_moves,
    restore_castle_rights_from_log,
    update_castle_rights_for_move,
)
from .rules import run_post_move_systems
from .scoring import calculate_material_advantage
from .state_helpers import is_inside_board, safe_get_piece, set_piece

class Board:
    """Mutable board grid and starting-piece placement."""

    def __init__(self):
        self.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        self.setup_classic()
        
    def setup_classic(self):
        """Place the standard starting arrangement on the board."""
        for c in range(BOARD_COLS):
            self.grid[0][c] = self.create_piece(BLACK, STANDARD_PIECE_ORDER[c], (0, c))
            self.grid[1][c] = Pawn(BLACK, (1, c))
            self.grid[BOARD_ROWS - 2][c] = Pawn(WHITE, (BOARD_ROWS - 2, c))
            self.grid[BOARD_ROWS - 1][c] = self.create_piece(WHITE, STANDARD_PIECE_ORDER[c], (BOARD_ROWS - 1, c))
            
    def create_piece(self, color, name, pos):
        """Create a board piece through the shared piece registry."""
        return create_piece(name, color, pos)

    def is_inside_board(self, row, col):
        """Return True when the square is on the board."""
        return is_inside_board(row, col)

    def get_piece_at(self, row, col):
        """Return the piece on a square or None for invalid coordinates."""
        return safe_get_piece(self.grid, row, col)

    def set_piece_at(self, row, col, piece):
        """Set a piece on a valid board square."""
        set_piece(self.grid, row, col, piece)

    def remove_piece_at(self, row, col):
        """Remove and return the piece from a square if one exists."""
        piece = self.get_piece_at(row, col)
        self.set_piece_at(row, col, None)
        return piece

    def replace_piece_at(self, row, col, piece):
        """Replace the piece on a square and sync the new piece position."""
        self.set_piece_at(row, col, piece)
        if piece is not None:
            piece.set_position((row, col))

class GameState:
    """Coordinate board state, legal move generation, and turn flow."""

    def __init__(self):
        self.board = Board()
        self.white_to_move = True
        self.move_log = []
        self.white_king_pos = (BOARD_ROWS - 1, 4)
        self.black_king_pos = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.enpassant_possible = ()  # Target square where en passant is legal next turn.
        self.current_castle_rights = create_initial_castle_rights()
        self.castle_rights_log = [copy_castle_rights(self.current_castle_rights)]
        self.capture_tracker = CaptureTracker()
        self.action_points = ActionPointTracker()
        self.event_manager = EventManager(self)
        self.fusion_manager = FusionManager(self)
        self.tempo_burst_pending = False
        self.tempo_burst_piece = None
        self.tempo_burst_owner = None
        self.ability_used_this_turn = False
        self.active_shields = []

    def make_move(self, move, promotion_choice='Q', is_real_move=False):
        """Apply a move and update all related game-state fields."""
        self._record_move_state(move)
        move.is_tempo_burst_move = self._is_tempo_burst_move(move)
        self._apply_base_piece_movement(move)
        self._resolve_en_passant_capture(move)
        self._resolve_pawn_promotion(move, promotion_choice)
        self._update_en_passant_square(move)
        self._resolve_castle_rook_movement(move)
        self._update_castle_state(move)
        self._finalize_move(move, is_real_move)

    def _record_move_state(self, move):
        """Store the state needed to roll back a simulated move exactly."""
        move.enpassant_possible_prev = self.enpassant_possible
        move.moved_piece_prev_pos = move.piece_moved.pos
        move.moved_piece_prev_has_moved = move.piece_moved.has_moved
        if move.piece_captured is not None:
            move.captured_piece_prev_pos = move.piece_captured.pos
            move.captured_piece_prev_has_moved = move.piece_captured.has_moved

    def _apply_base_piece_movement(self, move):
        """Move the piece to its destination square."""
        self.board.set_piece_at(move.start_row, move.start_col, None)
        self.board.set_piece_at(move.end_row, move.end_col, move.piece_moved)
        move.piece_moved.set_position((move.end_row, move.end_col))
        move.piece_moved.has_moved = True

    def _resolve_en_passant_capture(self, move):
        """Remove the captured pawn for en passant moves."""
        if move.is_enpassant_move:
            self.board.set_piece_at(move.start_row, move.end_col, None)

    def _resolve_pawn_promotion(self, move, promotion_choice):
        """Replace a promoted pawn with the selected piece type."""
        if move.is_pawn_promotion:
            promoted_piece_code = promotion_choice
            if promoted_piece_code not in (QUEEN_CODE, ROOK_CODE, BISHOP_CODE, KNIGHT_CODE):
                promoted_piece_code = QUEEN_CODE

            promoted_piece = create_piece(promoted_piece_code, move.piece_moved.color, (move.end_row, move.end_col))

            promoted_piece.has_moved = True
            move.promoted_to_piece = promoted_piece
            self.board.set_piece_at(move.end_row, move.end_col, promoted_piece)

    def _update_en_passant_square(self, move):
        """Update the en passant target square for the next turn."""
        if move.piece_moved.name == PAWN_CODE and abs(move.start_row - move.end_row) == 2:
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

    def _resolve_castle_rook_movement(self, move):
        """Move the rook when the king castles."""
        if move.is_castle_move:
            if move.end_col - move.start_col == 2: # King side
                rook = self.board.get_piece_at(move.end_row, move.end_col + 1)
                rook_start_col = move.end_col + 1
                rook_end_col = move.end_col - 1
            else: # Queen side
                rook = self.board.get_piece_at(move.end_row, move.end_col - 2)
                rook_start_col = move.end_col - 2
                rook_end_col = move.end_col + 1

            if rook:
                move.rook_moved = rook
                move.rook_start_pos = (move.end_row, rook_start_col)
                move.rook_end_pos = (move.end_row, rook_end_col)
                move.rook_prev_has_moved = rook.has_moved
                self.board.set_piece_at(move.end_row, rook_end_col, rook)
                self.board.set_piece_at(move.end_row, rook_start_col, None)
                rook.set_position((move.end_row, rook_end_col))
                rook.has_moved = True

    def _update_castle_state(self, move):
        """Update castling rights and persist them to the rights log."""
        update_castle_rights_for_move(self.current_castle_rights, move)
        self.castle_rights_log.append(copy_castle_rights(self.current_castle_rights))

    def _finalize_move(self, move, is_real_move):
        """Log the move, switch turns, and update king/event state."""
        self.move_log.append(move)
        if not move.is_tempo_burst_move:
            self.white_to_move = not self.white_to_move
        self.ability_used_this_turn = False
        self._update_king_position(move)
        move.is_real_move = is_real_move
        if is_real_move:
            run_post_move_systems(self, move)
        if is_real_move and move.is_tempo_burst_move:
            self.clear_tempo_burst()

    def _update_king_position(self, move):
        """Update the cached king location after a king move."""
        if move.piece_moved.name == KING_CODE:
            if move.piece_moved.color == WHITE:
                self.white_king_pos = (move.end_row, move.end_col)
            else:
                self.black_king_pos = (move.end_row, move.end_col)

    def _update_king_position_after_piece_relocation(self, piece):
        """Update cached king position after non-move relocation effects."""
        if piece is not None and piece.name == KING_CODE:
            if piece.color == WHITE:
                self.white_king_pos = piece.pos
            else:
                self.black_king_pos = piece.pos

    def _rollback_last_move(self):
        """Roll back the most recent simulated move."""
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            self._restore_base_piece_positions(move)
            self._restore_en_passant_capture(move)
            self._restore_turn_state(move)
            self._restore_castling_state()
            self._restore_castle_rook_position(move)
            self.white_to_move = not self.white_to_move
            self._restore_king_position(move)
            self.checkmate = False
            self.stalemate = False

    def _restore_base_piece_positions(self, move):
        """Restore the moved piece and destination square."""
        self.board.set_piece_at(move.start_row, move.start_col, move.piece_moved)
        self.board.set_piece_at(move.end_row, move.end_col, move.piece_captured)
        move.piece_moved.set_position(move.moved_piece_prev_pos)
        move.piece_moved.has_moved = move.moved_piece_prev_has_moved

    def _restore_en_passant_capture(self, move):
        """Restore the captured pawn for en passant moves."""
        if move.is_enpassant_move:
            self.board.set_piece_at(move.end_row, move.end_col, None)
            self.board.set_piece_at(move.start_row, move.end_col, move.piece_captured)

        if move.piece_captured is not None and move.captured_piece_prev_pos is not None:
            move.piece_captured.set_position(move.captured_piece_prev_pos)
            if move.captured_piece_prev_has_moved is not None:
                move.piece_captured.has_moved = move.captured_piece_prev_has_moved

    def _restore_turn_state(self, move):
        """Restore turn-local state fields."""
        self.enpassant_possible = move.enpassant_possible_prev

    def _restore_castling_state(self):
        """Restore castling rights from the rights log."""
        self.castle_rights_log.pop()
        self.current_castle_rights = restore_castle_rights_from_log(self.castle_rights_log)

    def _restore_castle_rook_position(self, move):
        """Move a rook back if the undone move was castling."""
        if move.rook_moved and move.rook_start_pos and move.rook_end_pos:
            self.board.set_piece_at(move.rook_start_pos[0], move.rook_start_pos[1], move.rook_moved)
            self.board.set_piece_at(move.rook_end_pos[0], move.rook_end_pos[1], None)
            move.rook_moved.set_position(move.rook_start_pos)
            move.rook_moved.has_moved = move.rook_prev_has_moved

    def _restore_king_position(self, move):
        """Restore the cached king location after rollback."""
        if move.piece_moved.name == KING_CODE:
            if move.piece_moved.color == WHITE:
                self.white_king_pos = (move.start_row, move.start_col)
            else:
                self.black_king_pos = (move.start_row, move.start_col)

    def get_valid_moves(self):
        # Generate pseudo-legal moves first.
        moves = self.get_all_possible_moves()
        
        # Temporarily apply each move and remove those that expose own king.
        for i in range(len(moves) - 1, -1, -1):
            move = moves[i]
            self.make_move(move)
            
            # Flip turn so in_check() evaluates the side that moved.
            self.white_to_move = not self.white_to_move
            if self.in_check():
                moves.remove(move)
            self.white_to_move = not self.white_to_move
            self._rollback_last_move()
            
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
        # Flip turn to generate opponent pseudo-legal moves.
        self.white_to_move = not self.white_to_move
        opp_moves = self.get_all_possible_moves(include_castle=False)
        self.white_to_move = not self.white_to_move
        for move in opp_moves:
            if move.end_row == r and move.end_col == c:
                return True
        return False

    def get_all_possible_moves(self, include_castle=True):
        moves = []
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                piece = self.board.grid[r][c]
                if self.tempo_burst_pending:
                    if piece is self.tempo_burst_piece:
                        moves.extend(get_piece_moves(piece, self, include_castle=include_castle))
                    continue
                if piece and ((piece.color == WHITE and self.white_to_move) or \
                             (piece.color == BLACK and not self.white_to_move)):
                    moves.extend(get_piece_moves(piece, self, include_castle=include_castle))
        return moves

    def _is_tempo_burst_move(self, move):
        """Return whether this move spends the pending Tempo Burst extra move."""
        return self.tempo_burst_pending and move.piece_moved is self.tempo_burst_piece

    def clear_tempo_burst(self):
        """Clear pending Tempo Burst extra-move state."""
        self.tempo_burst_pending = False
        self.tempo_burst_piece = None
        self.tempo_burst_owner = None

    def finish_ability_turn(self, color):
        """Consume the current turn after a successful ability use."""
        if self.tempo_burst_pending:
            self.move_log.append({"ability_turn": color, "tempo_burst": True})
            self.clear_tempo_burst()
            return

        self.ability_used_this_turn = True
        self.action_points.gain_for_move(color)
        self.move_log.append({"ability_turn": color})
        self.white_to_move = color != WHITE
        self.expire_shields_after_turn(color)
        if self.just_finished_full_turn():
            self.event_manager.update()
        self.ability_used_this_turn = False

    def add_shielded_piece(self, piece, owner_color):
        """Track a shielded piece until the opponent completes a turn."""
        piece.is_shielded = True
        piece.shield_owner = owner_color
        piece.shield_turns = 1
        if piece not in self.active_shields:
            self.active_shields.append(piece)

    def expire_shields_after_turn(self, completed_turn_color):
        """Remove shields after the protected side's opponent completes a turn."""
        for piece in list(self.active_shields):
            if getattr(piece, "shield_owner", None) == completed_turn_color:
                continue
            piece.is_shielded = False
            piece.shield_turns = 0
            piece.shield_owner = None
            self.active_shields.remove(piece)

    def get_captured_pieces(self):
        """Return captured-piece summaries for both players."""
        return self.capture_tracker.get_captured_pieces()

    def get_half_turn_count(self):
        """Return the number of half-turns recorded in the move log."""
        return len(self.move_log)

    def get_full_turn_count(self):
        """Return the number of completed full turns."""
        return self.get_half_turn_count() // 2

    def just_finished_full_turn(self):
        """Return whether the latest real move completed a full turn."""
        return self.white_to_move

    def get_material_advantage(self):
        """Return white material minus black material."""
        return calculate_material_advantage(self.board.grid)

    def get_turn_number(self):
        """Return the human-readable turn number shown in the UI."""
        return self.event_manager.turn_counter + 1

    def get_turns_to_next_event(self):
        """Return the number of turns remaining before the next event."""
        current_turn_number = self.get_turn_number()
        turns_until_event = 10 - (current_turn_number % 10)
        return 10 if turns_until_event == 0 else turns_until_event

