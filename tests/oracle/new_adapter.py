"""New-engine oracle adapter backed by the ordinary ``base:chess`` mod."""

from pathlib import Path

from src.engine.factory import build_state
from src.engine.move import Move
from src.engine.piece import Piece
from src.engine.pipeline import Pipeline
from src.modding.loader import load

ROOT = Path(__file__).resolve().parents[2]
FEN_IDS = {"P": "base:pawn", "N": "base:knight", "B": "base:bishop", "R": "base:rook", "Q": "base:queen", "K": "base:king"}
PROMOTION_IDS = {"q": "base:queen", "r": "base:rook", "b": "base:bishop", "n": "base:knight"}


def _square(row, col):
    return chr(ord("a") + col) + str(8 - row)


class NewEngine:
    """Minimal adapter contract used by the retained new-engine perft oracle."""

    name = "wave4"

    def _state(self, fen):
        placement, active, rights, enpassant = fen.split()[:4]
        result = load(ROOT / "mods", enabled_mod_ids=("base:chess",))
        result.raise_if_failed()
        state = build_state(result.registries, "base:vanilla")
        definitions = state.piece_defs
        for piece in list(state.board.pieces()):
            state.board.remove(piece.pos)

        uid = 0
        for row, rank in enumerate(placement.split("/")):
            col = 0
            for char in rank:
                if char.isdigit():
                    col += int(char)
                    continue
                uid += 1
                piece_id = FEN_IDS[char.upper()]
                side = "base:white" if char.isupper() else "base:black"
                piece = Piece(uid, definitions[piece_id], side, (row, col), self._has_moved(char, row, col, rights))
                state.board.place(piece, piece.pos)
                col += 1
        state.current_side = "base:white" if active == "w" else "base:black"
        self._restore_enpassant_history(state, enpassant)
        return state

    @staticmethod
    def _has_moved(char, row, col, rights):
        if char.upper() == "P":
            return row not in (1, 6)
        if char == "K":
            return not ("K" in rights or "Q" in rights)
        if char == "k":
            return not ("k" in rights or "q" in rights)
        if char == "R" and (row, col) == (7, 7):
            return "K" not in rights
        if char == "R" and (row, col) == (7, 0):
            return "Q" not in rights
        if char == "r" and (row, col) == (0, 7):
            return "k" not in rights
        if char == "r" and (row, col) == (0, 0):
            return "q" not in rights
        return True

    @staticmethod
    def _restore_enpassant_history(state, target):
        if target == "-":
            return
        row, col = 8 - int(target[1]), ord(target[0]) - ord("a")
        previous_side = "base:black" if state.current_side == "base:white" else "base:white"
        direction = state.board.sides[previous_side].forward
        end = (row + direction, col)
        pawn = state.board.at(end)
        if pawn is None:
            raise ValueError(f"en-passant target {target!r} has no preceding pawn")
        start = (row - direction, col)
        state.last_move = Move(pawn, start, end, [])

    def legal_moves(self, fen):
        state = self._state(fen)
        moves = set()
        for move in Pipeline(state).legal_moves():
            basic = _square(*move.start) + _square(*move.end)
            if move.choices:
                suffixes = {key for key, value in PROMOTION_IDS.items() if value in move.choices}
                moves.update(basic + suffix for suffix in suffixes)
            else:
                moves.add(basic)
        return moves

    def apply(self, fen, uci):
        state = self._state(fen)
        pipeline = Pipeline(state)
        squares, suffix = uci[:4], uci[4:]
        for move in pipeline.legal_moves():
            if _square(*move.start) + _square(*move.end) != squares:
                continue
            choice = PROMOTION_IDS.get(suffix)
            pipeline.apply(move, choice=choice)
            return self._fen(state)
        raise ValueError(f"{uci} is not legal")

    @staticmethod
    def _fen(state):
        letters = {value: key for key, value in FEN_IDS.items()}
        ranks = []
        for row in state.board.grid:
            empty, rank = 0, ""
            for piece in row:
                if piece is None:
                    empty += 1
                    continue
                if empty:
                    rank += str(empty)
                    empty = 0
                letter = letters[piece.definition.id]
                rank += letter if piece.side == "base:white" else letter.lower()
            ranks.append(rank + (str(empty) if empty else ""))
        rights = NewEngine._castle_rights(state)
        enpassant = NewEngine._enpassant_target(state)
        return (
            f"{'/'.join(ranks)} {'w' if state.current_side == 'base:white' else 'b'} "
            f"{rights or '-'} {enpassant} 0 1"
        )

    @staticmethod
    def _castle_rights(state):
        flags = []
        for side, row, letters in (("base:white", 7, ((7, "K"), (0, "Q"))), ("base:black", 0, ((7, "k"), (0, "q")))):
            king = state.board.at((row, 4))
            if king is None or king.side != side or king.definition.id != "base:king" or king.has_moved:
                continue
            for col, letter in letters:
                partner = state.board.at((row, col))
                if partner is not None and partner.side == side and partner.definition.id == "base:rook" and not partner.has_moved:
                    flags.append(letter)
        return "".join(flags)

    @staticmethod
    def _enpassant_target(state):
        previous = state.last_move
        if (
            previous is None
            or abs(previous.start[0] - previous.end[0]) != 2
            or not any(part.get("type") == "enpassant" for part in previous.piece.definition.moves)
        ):
            return "-"
        row = (previous.start[0] + previous.end[0]) // 2
        return _square(row, previous.end[1])
