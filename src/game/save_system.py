import json
import os
from .board import GameState
from ..pieces.registry import create_piece
from ..constants import WHITE, BLACK

def serialize_game_state(gs: GameState) -> dict:
    data = {}
    
    # 1. Board state
    board_grid = []
    for r in range(8):
        row_data = []
        for c in range(8):
            p = gs.board.grid[r][c]
            if p is None:
                row_data.append(None)
            else:
                piece_data = {
                    "code": p.get_piece_code(),
                    "color": p.color,
                    "has_moved": p.has_moved,
                    "is_shielded": getattr(p, "is_shielded", False),
                    "shield_owner": getattr(p, "shield_owner", None),
                    "shield_turns": getattr(p, "shield_turns", 0),
                    "has_fused": p.has_fused,
                    "fusion_components": p.fusion_components,
                    "primary_component_code": p.primary_component_code,
                }
                row_data.append(piece_data)
        board_grid.append(row_data)
    data["board"] = board_grid
    
    # 2. General state
    data["white_to_move"] = gs.white_to_move
    data["half_turn_count"] = len(gs.move_log)
    data["timers"] = gs.timers
    data["timeout"] = gs.timeout
    data["checkmate"] = gs.checkmate
    data["stalemate"] = gs.stalemate
    data["enpassant_possible"] = gs.enpassant_possible
    data["current_castle_rights"] = {
        "wks": gs.current_castle_rights.wks,
        "wqs": gs.current_castle_rights.wqs,
        "bks": gs.current_castle_rights.bks,
        "bqs": gs.current_castle_rights.bqs
    }
    
    # 3. Action points
    data["action_points"] = {
        WHITE: gs.action_points.get_ap(WHITE),
        BLACK: gs.action_points.get_ap(BLACK)
    }
    
    # 4. Capture tracker
    w_cap, b_cap = gs.get_captured_pieces()
    data["captured_pieces"] = {
        WHITE: w_cap,
        BLACK: b_cap
    }
    
    # 5. Event manager
    em = gs.event_manager
    data["event_manager"] = {
        "queued_event_key": em.queued_event_key,
        "active_events": [e.__class__.event_key for e in em.active_events]
    }
    
    return data

def deserialize_game_state(data: dict) -> GameState:
    gs = GameState()
    
    # 1. Restore board
    for r in range(8):
        for c in range(8):
            p_data = data["board"][r][c]
            if p_data is not None:
                is_fused = p_data.get("has_fused", False)
                components = p_data.get("fusion_components", [p_data["code"]])
                primary = p_data.get("primary_component_code", p_data["code"])
                
                if is_fused and len(components) > 1:
                    from ..pieces.dynamic_fused import DynamicFusedPiece
                    piece = DynamicFusedPiece(p_data["color"], primary, components, (r, c))
                else:
                    piece = create_piece(p_data["code"], p_data["color"], (r, c))
                    
                piece.has_moved = p_data["has_moved"]
                
                # Restore shield
                if p_data.get("is_shielded"):
                    gs.shield_tracker.add(piece, p_data["shield_owner"])
                    piece.shield_turns = p_data["shield_turns"]
                    
                gs.board.grid[r][c] = piece
                
                # Update King Pos
                if piece.name == "K":
                    if piece.color == WHITE:
                        gs.white_king_pos = (r, c)
                    else:
                        gs.black_king_pos = (r, c)
            else:
                gs.board.grid[r][c] = None

    # 2. General state
    gs.white_to_move = data["white_to_move"]
    # Reconstruct move log length
    gs.move_log = ["dummy_move"] * data["half_turn_count"]
    gs.timers = data["timers"]
    gs.timeout = data["timeout"]
    gs.checkmate = data["checkmate"]
    gs.stalemate = data["stalemate"]
    gs.enpassant_possible = tuple(data["enpassant_possible"]) if data["enpassant_possible"] else ()
    
    cr = gs.current_castle_rights
    cr_data = data["current_castle_rights"]
    cr.wks = cr_data["wks"]
    cr.wqs = cr_data["wqs"]
    cr.bks = cr_data["bks"]
    cr.bqs = cr_data["bqs"]
    gs.castle_rights_log = [cr]
    
    # 3. Action points
    gs.action_points.points[WHITE] = data["action_points"][WHITE]
    gs.action_points.points[BLACK] = data["action_points"][BLACK]
    
    # 4. Capture tracker
    for code in data["captured_pieces"][WHITE]:
        gs.capture_tracker.captured_by_white.append(code)
    for code in data["captured_pieces"][BLACK]:
        gs.capture_tracker.captured_by_black.append(code)
        
    # 5. Event manager
    em_data = data.get("event_manager", {})
    if "queued_event_key" in em_data and em_data["queued_event_key"]:
        from ..events.registry import create_event
        gs.event_manager.queued_event_key = em_data["queued_event_key"]
        gs.event_manager.queued_event = create_event(em_data["queued_event_key"], gs)
        
    # We do not fully restore active events state to keep it simple, they'll just re-trigger or expire.
    # We can reconstruct active events if we want, but it requires recreating event objects.
    for ev_key in em_data.get("active_events", []):
        from ..events.registry import create_event
        ev = create_event(ev_key, gs)
        gs.event_manager.active_events.append(ev)

    return gs

def save_game(gs: GameState, filename: str = "save_game.json"):
    data = serialize_game_state(gs)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_game(filename: str = "save_game.json") -> GameState:
    if not os.path.exists(filename):
        return None
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return deserialize_game_state(data)
