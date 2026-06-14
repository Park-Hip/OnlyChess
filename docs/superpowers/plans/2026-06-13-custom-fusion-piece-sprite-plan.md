# Custom Fusion Piece Sprite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give a fusion piece its own custom image so it renders with dedicated art instead of reusing a base-piece sprite.

**Architecture:** Keep the change basic and local. The piece class should return a stable custom sprite key, the UI asset loader should include that key in its default sprite list, and rendering should continue to rely on `piece.get_sprite_key()` so no drawing code needs special cases.

**Tech Stack:** Python, Pygame, unittest

---

### Task 1: Give Archbishop a dedicated sprite key

**Files:**
- Modify: `src/constants.py`
- Modify: `src/pieces/fused.py`
- Test: `tests/pieces/test_fused_pieces.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from src.constants import WHITE
from src.pieces import Archbishop


class FusedPieceTests(unittest.TestCase):
    def test_archbishop_uses_custom_sprite_key(self):
        piece = Archbishop(WHITE, (4, 4))
        self.assertEqual(piece.get_sprite_key(), "wA")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run python -m unittest tests.pieces.test_fused_pieces -v`
Expected: the test fails because `Archbishop.get_sprite_key()` still falls back to the primary component sprite.

- [ ] **Step 3: Write the minimal implementation**

```python
# src/constants.py
ARCHBISHOP_SPRITE_KEY = "A"

# src/pieces/fused.py
from ..constants import ARCHBISHOP_CODE, ARCHBISHOP_SPRITE_KEY, BISHOP_CODE, KNIGHT_CODE
from .standard import Bishop, Knight


class Archbishop(FusedPiece, Bishop):
    """Fused Knight + Bishop piece."""

    piece_code = ARCHBISHOP_CODE
    material_value = 6
    component_codes = (KNIGHT_CODE, BISHOP_CODE)

    def __init__(self, color, pos):
        super().__init__(color, ARCHBISHOP_CODE, pos)

    def get_sprite_key(self):
        return f"{self.color}{ARCHBISHOP_SPRITE_KEY}"
```

- [ ] **Step 4: Run the test again**

Run: `uv run python -m unittest tests.pieces.test_fused_pieces -v`
Expected: PASS.

- [ ] **Step 5: Commit the change**

```bash
git add src/constants.py src/pieces/fused.py tests/pieces/test_fused_pieces.py
git commit -m "feat: add custom archbishop sprite key"
```

### Task 2: Load the custom sprite by default

**Files:**
- Modify: `src/ui/assets.py`
- Test: `tests/ui/test_assets.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from src.ui.assets import load_images


class AssetHelperTests(unittest.TestCase):
    def test_default_load_includes_archbishop_sprite(self):
        loaded_paths = []

        def fake_loader(path):
            loaded_paths.append(path)
            return path

        def fake_scaler(image, size):
            return (image, size)

        load_images(image_loader=fake_loader, scaler=fake_scaler, square_size=64)

        self.assertIn("images/wA.png", loaded_paths)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run python -m unittest tests.ui.test_assets -v`
Expected: the test fails because `load_images()` currently only loads the standard 12 sprites.

- [ ] **Step 3: Write the minimal implementation**

```python
# src/ui/assets.py
from ..constants import (
    ARCHBISHOP_SPRITE_KEY,
    BISHOP_CODE,
    BLACK,
    KING_CODE,
    KNIGHT_CODE,
    PAWN_CODE,
    QUEEN_CODE,
    ROOK_CODE,
    WHITE,
)


STANDARD_SPRITE_KEYS = [
    WHITE + PAWN_CODE,
    WHITE + ROOK_CODE,
    WHITE + KNIGHT_CODE,
    WHITE + BISHOP_CODE,
    WHITE + KING_CODE,
    WHITE + QUEEN_CODE,
    WHITE + ARCHBISHOP_SPRITE_KEY,
    BLACK + PAWN_CODE,
    BLACK + ROOK_CODE,
    BLACK + KNIGHT_CODE,
    BLACK + BISHOP_CODE,
    BLACK + KING_CODE,
    BLACK + QUEEN_CODE,
]


def get_standard_sprite_keys():
    return list(STANDARD_SPRITE_KEYS)
```

- [ ] **Step 4: Run the test again**

Run: `uv run python -m unittest tests.ui.test_assets -v`
Expected: PASS.

- [ ] **Step 5: Commit the change**

```bash
git add src/ui/assets.py tests/ui/test_assets.py
git commit -m "feat: load custom fusion sprite by default"
```

### Task 3: Add the image file and verify the game boots

**Files:**
- Create: `images/wA.png`
- Optional: `docs/fusion-system.md`
- Optional: `docs/ui-and-input.md`

- [ ] **Step 1: Add the new image**

Create a transparent PNG named `images/wA.png`. Keep the visual style consistent with the existing chess piece artwork.

- [ ] **Step 2: Run the focused regression tests**

Run: `uv run python -m unittest discover -s tests/pieces -p "test_*.py" -v`
Run: `uv run python -m unittest discover -s tests/ui -p "test_*.py" -v`
Expected: PASS.

- [ ] **Step 3: Smoke test the app**

Run: `uv run python -c "import os; os.environ['SDL_VIDEODRIVER']='dummy'; import pygame as p; p.init(); p.event.post(p.event.Event(p.QUIT)); import run; run.main(); print('smoke-ok')"`
Expected: prints `smoke-ok` and exits cleanly.

- [ ] **Step 4: Update the docs**

Add a short note to `docs/fusion-system.md` or `docs/ui-and-input.md` that says:

```md
Custom fusion art should live in `images/` and use the sprite key returned by the fused piece, for example `wA.png` for a white Archbishop.
The UI scales sprites to the board-square size at runtime, so the source file can be any reasonable size, but a transparent PNG is recommended so the piece blends cleanly with the board.
```

- [ ] **Step 5: Commit the final change**

```bash
git add images/wA.png docs/fusion-system.md docs/ui-and-input.md
git commit -m "feat: add custom fusion piece art"
```

## Notes For The Implementer

- Keep `src/ui/render_board.py` unchanged so the rendering flow stays simple and still uses `piece.get_sprite_key()`.
- If you want a different fusion piece to get custom art first, repeat the same pattern with a new constant, a new filename, and a matching test.
- The board displays every sprite at `64x64` pixels because `SQ_SIZE` is `512 / 8`.
- Transparent backgrounds are recommended, not strictly required by the code, but they look much better on alternating board squares.

## Self-Review Checklist

- [ ] The fused piece returns a stable custom sprite key.
- [ ] The asset loader includes the custom sprite without special render code.
- [ ] The PNG file name matches the sprite key exactly.
- [ ] The tests cover both the piece-level key and the loader path.
- [ ] The plan stays basic and explainable for an OOP course project.
