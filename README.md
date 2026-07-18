# OnlyChess

OnlyChess is a Python/Pygame chess variant. Standard chess is the base mode; optional mods add
capture fusion, Action Point abilities, and scheduled global events.

The application is mod-driven: the engine in `src/` loads pieces, rules, boards, abilities, events,
and tuning from `mods/`. The base game uses the same public path as any third-party mod.

## Play

Requires Python 3.12. Either set up a virtual environment with the standard library:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

or, on Windows, `.venv\Scripts\python main.py`. [`uv`](https://github.com/astral-sh/uv) works too if
you have it:

```powershell
uv run python main.py
```

`uv` is a convenience, not a requirement — the dependencies are `pygame` and `ruamel.yaml`, and
nothing in the project needs more than a plain venv. The game needs a display; over SSH, connect
with `ssh -X` so `DISPLAY` is set.

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

```bash
MODS=$(find tests -name 'test_*.py' | sed 's|/|.|g; s|\.py$||' | sort)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m unittest $MODS -q
```

The dummy SDL drivers let the Pygame suites run with no display or audio device. The PowerShell
equivalent:

```powershell
$test_modules = rg --files tests -g 'test_*.py' | ForEach-Object { $_.Replace('\\', '.').Replace('/', '.').Replace('.py', '') }
uv run python -m unittest @test_modules -q
```

Do not use `uv run` for a single module: it drops the repository root from `sys.path` and every test
fails with `ModuleNotFoundError: No module named 'src'`.

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
