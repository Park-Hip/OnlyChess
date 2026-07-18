"""Immutable public data contracts consumed by the presentation runtime."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PresentationPiece:
    piece_id: str
    side_id: str
    square: tuple[int, int]
    status_ids: tuple[str, ...]


@dataclass(frozen=True)
class PresentationSnapshot:
    mode_id: str
    rows: int
    columns: int
    current_side_name: str
    pieces: tuple[PresentationPiece, ...]
    resources: tuple[tuple[str, int], ...]
    messages: tuple[str, ...]
    prompt: str | None
    outcome: str | None
    #: `(side name, seconds remaining)` per side, empty when the mode declares no time limit.
    #: Not part of game state: clocks are session-level, so undo does not refund time.
    clocks: tuple[tuple[str, float], ...] = ()
    #: The squares the previous move ran between, for highlighting it. None before the first move.
    last_move: tuple[tuple[int, int], tuple[int, int]] | None = None
    #: `(side name, total)` of the material each side still has on the board.
    #:
    #: Totalled from what is present rather than from a record of captures, which keeps it honest
    #: for free: a piece removed by an event lowers its owner's total exactly like a captured one,
    #: and undo restores it without anything having to remember what happened.
    material: tuple[tuple[str, int], ...] = ()
    #: Completed turns so far.
    turn_number: int = 0
    #: Moves until the next scheduled event executes, or None when no pool is active.
    event_countdown: int | None = None


@dataclass(frozen=True)
class PresentationNotification:
    kind: str
    mode_id: str
    square: tuple[int, int] | None = None
    piece_id: str | None = None
