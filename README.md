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

The menu offers every linked mode discovered under `mods/`. The shipped install currently includes:

- **Standard Chess** — standard chess from `base:chess` only.
- **Advanced** — chess plus `base:fusion` and `base:events`.
- **Prism Arena** — the independent 6x6 proof mod.

The **Mods** button shows installed-mod metadata, flags code-bearing mods, and reports attributed
load errors. It is informational; installing or disabling mods still happens by changing the
folders under `mods/` and restarting the application.

### Controls

- Click a piece, then a highlighted destination to move.
- Select a piece and click it again to choose one of its available abilities; click a target when prompted.
- On promotion, press **Q**, **R**, **B**, or **N**.
- Press **Ctrl-Z** to undo; **R** restarts the current mode and **Backspace** returns to the menu.

The current screen renders mod-provided glyphs or sprites, themes, sounds, status markers, and the
declared built-in HUD widgets. It does not yet support custom HUD widget types, a chess clock, or
arbitrary per-piece text/colour overlays.

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

- [New contributor onboarding](docs/onboarding/README.md)
- [Continuation roadmap](docs/onboarding/continuation-roadmap.md)
- [Contributor start here](docs/refactor/start-here.md)
- [Current runtime status](docs/refactor/status.md)
- [Product completion specification](docs/refactor/product-completion-spec.md)
- [Delivery milestones](docs/refactor/milestones.md)
- [Modding guide](docs/modding/README.md)
- [Presentation contract](docs/modding/spec/presentation.md)

## Tech stack

Python, Pygame, and `uv`.
