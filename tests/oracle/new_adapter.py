"""Wave 3 engine adapter, deliberately backed by the test-only standard fixture."""

from pathlib import Path

from src.engine.factory import build_state
from src.engine.piece import Piece
from src.engine.pipeline import Pipeline
from src.modding.loader import load

from .adapters import EngineAdapter

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "wave3_mods"
FEN_IDS = {"P": "fixture:pawn", "N": "fixture:knight", "B": "fixture:bishop", "R": "fixture:rook", "Q": "fixture:queen", "K": "fixture:king"}


def _square(row, col): return chr(ord("a") + col) + str(8 - row)


class NewEngine(EngineAdapter):
    name = "wave3"

    def _state(self, fen):
        registries = load(FIXTURE_ROOT, enabled_mod_ids=("fixture:standard",)).registries
        state = build_state(registries, "fixture:standard")
        for piece in list(state.board.pieces()): state.board.remove(piece.pos)
        placement, active, _, _ = fen.split()[:4]
        uid = 0
        definitions = {entry.id: entry.value.tree for entry in registries.content["piece"]}
        from src.engine.piece import PieceDef
        for row, rank in enumerate(placement.split("/")):
            col = 0
            for char in rank:
                if char.isdigit(): col += int(char); continue
                uid += 1
                piece_id = FEN_IDS[char.upper()]
                data = definitions[piece_id]
                definition = PieceDef(piece_id, tuple(data["moves"]), tuple(data.get("components", [piece_id])), dict(data.get("properties", {})))
                side = "fixture:white" if char.isupper() else "fixture:black"
                # FEN does not preserve per-piece move history.  For legal chess
                # positions a pawn away from its home rank has necessarily moved,
                # which is the only Wave 3 rule that needs that history.
                has_moved = piece_id == "fixture:pawn" and row not in (1, 6)
                state.board.place(Piece(uid, definition, side, (row, col), has_moved), (row, col))
                col += 1
        state.current_side = "fixture:white" if active == "w" else "fixture:black"
        return state

    def legal_moves(self, fen):
        state = self._state(fen)
        return {_square(move.start[0], move.start[1]) + _square(move.end[0], move.end[1]) for move in Pipeline(state).legal_moves()}

    def apply(self, fen, uci):
        state = self._state(fen); pipeline = Pipeline(state)
        for move in pipeline.legal_moves():
            if _square(*move.start) + _square(*move.end) == uci:
                pipeline.apply(move); break
        else: raise ValueError(f"{uci} is not legal")
        ranks = []
        letters = {value: key for key, value in FEN_IDS.items()}
        for row in state.board.grid:
            empty = 0; rank = ""
            for piece in row:
                if piece is None: empty += 1; continue
                if empty: rank += str(empty); empty = 0
                letter = letters[piece.definition.id]
                rank += letter if piece.side == "fixture:white" else letter.lower()
            ranks.append(rank + (str(empty) if empty else ""))
        return f"{'/'.join(ranks)} {'w' if state.current_side == 'fixture:white' else 'b'} - - 0 1"
