# OnlyChess

OnlyChess is a Python/Pygame chess variant. Standard chess is the base mode; optional mods add
capture fusion, Action Point abilities, and scheduled global events.

The application is mod-driven: the engine in `src/` loads pieces, rules, boards, abilities, events,
and tuning from `mods/`. The base game uses the same public path as any third-party mod.

## Play

Requires Python and [`uv`](https://github.com/astral-sh/uv).

```powershell
uv run python main.py
```

The menu offers two shipped modes:

- **Start** — standard chess from `base:chess` only.
- **Advanced** — chess plus `base:fusion` and `base:events`.

### Controls

- Click a piece, then a highlighted destination to move.
- Press **Ctrl-Z** to undo the complete previous turn, including any event outcome.
- Select a piece and press **A** to use its available ability; click a target when prompted.
- On promotion, press **Q**, **R**, **B**, or **N**.

The current screen renders letter glyphs for pieces. Mod-provided sprites, sounds, themes, and HUD
elements are not yet part of the playable runtime.

## Mechanics

- **Fusion:** eligible captures can replace the capturer with a fused piece. Direction matters:
  Rook + Bishop becomes a Warden, while Bishop + Rook becomes an Inquisitor.
- **Abilities:** pieces may spend Action Points on content-defined effects such as swapping,
  sniping, shielding, or sprinting.
- **Events:** Advanced mode selects a scheduled event, warns before it executes, and records its
  outcome as reversible actions.

## Verify

```powershell
$test_modules = rg --files tests -g 'test_*.py' | ForEach-Object { $_.Replace('\\', '.').Replace('/', '.').Replace('.py', '') }
uv run python -m unittest @test_modules -q
```

## Documentation

- [Contributor start here](docs/refactor/start-here.md)
- [Current runtime status](docs/refactor/status.md)
- [Product completion specification](docs/refactor/product-completion-spec.md)
- [Delivery milestones](docs/refactor/milestones.md)
- [Modding guide](docs/modding/README.md)

## Tech stack

Python, Pygame, and `uv`.
