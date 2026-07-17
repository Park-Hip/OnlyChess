"""A move is an ordered action list, never a bundle of content-specific flags."""

from dataclasses import dataclass


@dataclass
class Move:
    piece: object
    start: tuple[int, int]
    end: tuple[int, int]
    actions: list[object]
    captured: object | None = None
    choices: tuple[str, ...] = ()
    selected_choice: str | None = None
