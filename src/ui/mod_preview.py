"""A deliberately small Pygame preview for the Wave 2 loaded-content slice.

This is a loader/rendering probe. The playable application uses ``EngineGameScreen``; the preview
remains useful for isolated mod-content diagnostics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pygame as p

from ..modding.errors import ContentError, ModLoadError
from ..modding.loader import LoadResult, activate, load

_LIGHT = p.Color("#f0d9b5")
_DARK = p.Color("#b58863")


def sprite_path(piece_sprite: str, side_id: str, mod_root: Path) -> Path:
    """Return the Windows-safe path for a piece sprite and a namespaced side id.

    IDs remain `namespace:name` in content.  Namespaces become directories, never filename
    characters, so `skeleton:blue` resolves to `.../beacon/skeleton/blue.png` on every
    supported filesystem.
    """
    sprite_name = piece_sprite.rsplit("/", 1)[-1].split(":", 1)[-1]
    side_namespace, side_name = side_id.split(":", 1)
    return mod_root / "assets" / "sprites" / sprite_name / side_namespace / f"{side_name}.png"


def load_preview_images(
    result: LoadResult,
    mode_id: str,
    *,
    image_loader: Callable[[str], object] | None = None,
    scaler: Callable[[object, tuple[int, int]], object] | None = None,
    square_size: int = 128,
) -> dict[tuple[str, str], object]:
    """Load every image required by a linked preview mode; missing assets are load errors."""
    if result.linked is None or mode_id not in result.linked.modes:
        raise ModLoadError([ContentError(mod_id="<engine>", file="<preview>", problem=f"game mode '{mode_id}' is not linked")])
    if image_loader is None:
        image_loader = p.image.load
    if scaler is None:
        scaler = p.transform.smoothscale

    images: dict[tuple[str, str], object] = {}
    mode = result.linked.modes[mode_id]
    for placement in mode.board.placements:
        key = (placement.piece_id, placement.side_id)
        if key in images:
            continue
        entry = result.registries.content["piece"].get(placement.piece_id)
        assert entry is not None  # Link stage proves this; keeping the failure local if it regresses.
        root = result.mod_roots[entry.mod_id]
        path = sprite_path(entry.value.tree["sprite"], placement.side_id, root)
        if not path.is_file():
            raise ModLoadError([
                ContentError(
                    mod_id=entry.mod_id,
                    file=entry.value.display,
                    problem=f"sprite file is missing: {path.relative_to(root)}",
                    field="sprite",
                    expected="a PNG at the mod-owned sprite path",
                )
            ])
        try:
            images[key] = scaler(image_loader(str(path)), (square_size, square_size))
        except Exception as error:
            raise ModLoadError([
                ContentError(
                    mod_id=entry.mod_id,
                    file=entry.value.display,
                    problem=f"could not load sprite: {error}",
                    field="sprite",
                )
            ]) from error
    return images


def draw_preview(screen: p.Surface, result: LoadResult, mode_id: str, images: dict[tuple[str, str], object], *, square_size: int = 128) -> None:
    """Draw one linked board and its placed sprites without legacy board or piece objects."""
    assert result.linked is not None
    board = result.linked.modes[mode_id].board
    for row in range(board.rows):
        for col in range(board.columns):
            color = _LIGHT if (row + col) % 2 == 0 else _DARK
            p.draw.rect(screen, color, p.Rect(col * square_size, row * square_size, square_size, square_size))
    for placement in board.placements:
        screen.blit(images[(placement.piece_id, placement.side_id)], (placement.col * square_size, placement.row * square_size))


def run_skeleton_preview(mods_dir: Path = Path("mods")) -> None:
    """Open the manual Wave 2 proof: the selected skeleton mod rendered by Pygame."""
    result = load(mods_dir, enabled_mod_ids=("skeleton:demo",), validate=True, link=True)
    activate(result)
    mode_id = "skeleton:preview"
    square_size = 256
    images = load_preview_images(result, mode_id, square_size=square_size)
    p.init()
    screen = p.display.set_mode((square_size, square_size))
    p.display.set_caption("OnlyChess — Wave 2 walking skeleton")
    running = True
    while running:
        for event in p.event.get():
            if event.type == p.QUIT:
                running = False
        draw_preview(screen, result, mode_id, images, square_size=square_size)
        p.display.flip()
    p.quit()


if __name__ == "__main__":
    run_skeleton_preview()
