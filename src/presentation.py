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


@dataclass(frozen=True)
class PresentationNotification:
    kind: str
    mode_id: str
    square: tuple[int, int] | None = None
    piece_id: str | None = None
