"""Board geometry and side data, built from a linked content layout."""

from __future__ import annotations

from dataclasses import dataclass, field

from .piece import Piece


@dataclass(frozen=True)
class Side:
    id: str
    name: str
    forward: int
    moves_first: bool = False
    promotes_at: int | None = None


@dataclass
class Board:
    rows: int
    columns: int
    sides: dict[str, Side]
    grid: list[list[Piece | None]] = field(init=False)

    def __post_init__(self) -> None:
        self.grid = [[None for _ in range(self.columns)] for _ in range(self.rows)]

    def inside(self, square: tuple[int, int]) -> bool:
        row, col = square
        return 0 <= row < self.rows and 0 <= col < self.columns

    def at(self, square: tuple[int, int]) -> Piece | None:
        row, col = square
        return self.grid[row][col] if self.inside(square) else None

    def place(self, piece: Piece, square: tuple[int, int]) -> None:
        row, col = square
        self.grid[row][col] = piece
        piece.pos = square

    def remove(self, square: tuple[int, int]) -> Piece | None:
        row, col = square
        piece = self.grid[row][col]
        self.grid[row][col] = None
        return piece

    def pieces(self):
        for row in self.grid:
            for piece in row:
                if piece is not None:
                    yield piece
