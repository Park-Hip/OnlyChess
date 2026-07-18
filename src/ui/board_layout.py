"""Viewport-derived geometry for any rectangular board."""

from __future__ import annotations

from dataclasses import dataclass

import pygame as p


@dataclass(frozen=True)
class BoardLayout:
    board: p.Rect
    panel: p.Rect
    square_size: int
    rows: int
    columns: int

    @classmethod
    def for_viewport(cls, viewport: tuple[int, int], rows: int, columns: int, *, header: int = 56, margin: int = 16) -> "BoardLayout":
        width, height = viewport
        panel_width = max(180, width // 4)
        available_width = max(1, width - panel_width - margin * 3)
        available_height = max(1, height - header - margin * 2)
        square = max(1, min(available_width // columns, available_height // rows))
        board = p.Rect(margin, header + margin, columns * square, rows * square)
        panel = p.Rect(board.right + margin, header + margin, max(1, width - board.right - margin * 2), available_height)
        return cls(board, panel, square, rows, columns)

    def square_rect(self, square: tuple[int, int]) -> p.Rect:
        row, col = square
        return p.Rect(self.board.x + col * self.square_size, self.board.y + row * self.square_size, self.square_size, self.square_size)

    def square_at(self, position: tuple[int, int]) -> tuple[int, int] | None:
        if not self.board.collidepoint(position):
            return None
        col = (position[0] - self.board.x) // self.square_size
        row = (position[1] - self.board.y) // self.square_size
        return (row, col) if 0 <= row < self.rows and 0 <= col < self.columns else None
