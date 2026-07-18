"""Turn a recorded action log into readable move history.

Standard algebraic notation cannot be used as written, and the reason is the whole project in
miniature: SAN's `Nf3` depends on knowing that knights are called N and that pawns are called
nothing. Both facts are chess's, not this engine's, and a mod whose pieces are `◆` and `▲` has no
letters to borrow.

So notation is derived from what content declares. A piece's own glyph names it, squares are
lettered and numbered from the board's own size, and the two conventions that survive are the ones
that describe shape rather than chess: `x` for a capture, `=` for a promotion.

The result is long algebraic — origin and destination both written out. Short algebraic omits the
origin and disambiguates only when two pieces could reach the same square, which needs the position
before the move; the log is read after. Long form is unambiguous without remembering anything.
"""

from __future__ import annotations

from .engine.actions import Relocate, RecordAbility, RecordMove, Replace


def square_name(square, rows: int) -> str:
    """`(row, col)` as file letter and rank number, counted from the board's own dimensions."""
    row, col = square
    return f"{chr(ord('a') + col)}{rows - row}"


def describe_record(record, state, glyph) -> str | None:
    """One line for one completed action list, or None when it changed nothing worth reading.

    `glyph` resolves a piece id to the character content chose for it, so this function never
    learns a piece's name.
    """
    for action in record:
        if isinstance(action, RecordAbility):
            return _ability(action, state, glyph)
    for action in record:
        if isinstance(action, RecordMove):
            return _move(action.move, record, state, glyph)
    return None


def _move(move, record, state, glyph) -> str:
    rows = state.board.rows
    text = f"{glyph(move.piece.definition.id)}{square_name(move.start, rows)}"
    text += "x" if move.captured is not None else "-"
    text += square_name(move.end, rows)

    # Two pieces relocating in one move is castling, in every game that has such a thing. Detected
    # by shape rather than by name, so a mod's own two-piece move reads correctly without core
    # knowing it exists.
    if sum(isinstance(action, Relocate) for action in move.actions) > 1:
        text += " (castle)"

    promotion = next((action for action in move.actions if isinstance(action, Replace)), None)
    if promotion is not None:
        text += f"={glyph(promotion.new.definition.id)}"
    return text


def _ability(action, state, glyph) -> str:
    used = f"~{glyph(action.piece_id)}{square_name(action.square, state.board.rows)} {action.name}"
    return f"{used} [{action.cost}]" if action.cost else used


def history(state, glyph) -> tuple[str, ...]:
    """Every completed action list, most recent last. Derived, so undo shortens it for free."""
    lines = []
    for record in state.action_log:
        described = describe_record(record, state, glyph)
        if described is not None:
            lines.append(described)
    return tuple(lines)
