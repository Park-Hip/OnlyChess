# OnlyChess

OnlyChess is a Python/Pygame chess variant. Standard chess is the base mode; optional mods add
capture fusion, Action Point abilities, and scheduled global events.

The application is mod-driven: the engine in `src/` loads pieces, rules, boards, abilities, events,
presentation, and tuning from `mods/`. The base game uses the same public path as any third-party
mod.

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

The menu offers every linked mode discovered under `mods/`. The shipped install includes:

- **Standard Chess** — standard chess from `base:chess` only.
- **Advanced** — chess plus `base:fusion` and `base:events`.

If a saved game exists, the menu leads with **Continue** above the mode list.

The **Mods** button shows installed-mod metadata, flags code-bearing mods, and reports attributed
load errors. It is informational; installing or disabling mods still happens by changing the
folders under `mods/` and restarting the application.

The **Options** button sets a time limit and cycles curated colours for the light squares, dark
squares, and each side's pieces. Preferences are the one layer allowed to overrule a mod, and the
override is deliberately narrow: they may replace palette tokens a theme already has, but cannot
invent tokens it lacks. Nothing reaches disk or the running game until **Save**.

The `proof:arena_mode` fixture — an independent 6x6 mod that proves core holds no chess assumption —
deliberately lives under `tests/fixtures/proof-mod/` rather than `mods/`, so it is not offered to
players. Core cannot filter a fixture out at discovery without naming a mod, which the prime
directive forbids, so the directory is where that distinction has to live.

### Controls

- Click a piece, then a highlighted square, to move it.
- Drag a piece to its destination if you prefer.
- Right-click a piece to see its abilities; click a target when prompted.
- When promoting, press the letter shown in the prompt.

| Key | Action |
|---|---|
| **Ctrl-Z** | Undo the last move or ability |
| **R** | Restart this mode |
| **Backspace** | Return to the menu |
| **Esc** | Pause, or cancel what is open |
| **H** | Controls help |

Pausing offers Resume, Save Game, Restart, Help, Reference, and Main Menu. The **Reference** screen
is generated from the loaded registries rather than written by hand — hardcoded help text would have
to name content, and content is a mod's to describe.

## Mechanics

- **Fusion:** a displacing capture — one where the capturer ends up standing on the captured
  square — absorbs the captured piece's components, and the capturer's moves are rebuilt from
  everything it now contains. Any pair fuses, and capture order does not change the result. Identity
  follows the capturer, so a fused rook is still primarily a rook and keeps its own sprite and
  abilities. Royalty is never absorbed.
- **Abilities:** pieces may spend Action Points on content-defined effects such as swapping,
  sniping, shielding, or sprinting.
- **Events:** Advanced mode selects a scheduled event, warns before it executes, and records its
  outcome as reversible actions.

Fusion moved from a hand-authored table to composition on 2026-07-19. The table named a result for
six specific ordered pairs, so only those six could fuse. Composition is more general but costs one
thing worth stating: Warden's diagonal was deliberately capped at three squares, and no derived rule
can express a cap like that, so a rook-bishop now moves as a full rook *and* a full bishop. That is a
chosen balance change, not an oversight. The four authored fused pieces (Archbishop, Chancellor,
Warden, Inquisitor) remain valid, placeable content; nothing produces them any more. A mod that wants
authored pairs can still use `rules`.

## Saving

Saving writes `saves/<mode>.json` — one slot per mode, so saving one game cannot destroy another's.
A save is a state snapshot, not a replay: replaying would force every random effect through an RNG
core owns, and a save that reconstructs a game that never happened fails hours later instead of
immediately. A save records the mod set and manifest versions it was played against and refuses to
load against a different one, naming both sides of the mismatch.

The action log is **not** saved, so a loaded game cannot be undone past the load point. That is a
deliberate trade, recorded in `src/savegame.py`.

## Presentation

The screen renders mod-declared themes, piece sprites or glyphs, status markers, HUD widgets, and
sound cues. Base chess ships artwork for all twelve piece/side combinations and base fusion ships
four more; move and capture play real recordings, and the remaining cues are placeholders.

The board sits between two per-player panels showing clock, resources, material lead, and captures.
Which player a panel describes comes from the seating order in the snapshot, not from a side name in
the layout — a layout naming `base:white` would only work for mods that happen to have a white.

The move log uses long algebraic notation derived from the board's own dimensions and each piece's
declared glyph, because `Nf3` depends on knowing knights are called N, which is a fact about chess
rather than about this engine. Castling is recognised by shape — two pieces relocating in one move —
so a mod's own two-piece move reads correctly. History derives from the action log, so undo shortens
it for free.

Still out of scope, and documented as limits rather than bugs: custom HUD widget *types*, arbitrary
per-piece text overlays, new event triggers beyond scheduled pools, and presentation effects. Data
mods compose the existing vocabulary; code mods register `move_type` verbs. See
[status.md](docs/refactor/status.md) for the full boundary.

## Verify

```bash
MODS=$(find tests -name 'test_*.py' | sed 's|/|.|g; s|\.py$||' | sort)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m unittest $MODS -q
```

The dummy SDL drivers let the Pygame suites run with no display or audio device. The PowerShell
equivalent:

```powershell
$test_modules = rg --files tests -g 'test_*.py' | ForEach-Object { $_.Replace('\\', '.').Replace('/', '.').Replace('.py', '') }
python -m unittest @test_modules -q
```

295 tests, all passing as of 2026-07-21. Keep both forms working — only the PowerShell form was
documented until 2026-07-18, which is why the suite had never run on another platform and a
Windows-only path assertion survived in it.

**Use `unittest`, not `pytest`.** The suite is not pytest-collectable: the tests import each other
package-relatively (`from .modding.builders import ...`), which only resolves under `unittest`'s
package discovery. `pytest` fails at collection with `ImportError: attempted relative import with no
known parent package`, and pytest is not a declared dependency. Note that `CLAUDE.md` currently
instructs `python -m pytest`; that instruction does not work and needs reconciling.

Do not use `uv run` for a single module: it drops the repository root from `sys.path` and every test
fails with `ModuleNotFoundError: No module named 'src'`.

## Documentation

- [New contributor onboarding](docs/onboarding/README.md)
- [Continuation roadmap](docs/onboarding/continuation-roadmap.md)
- [Contributor start here](docs/refactor/start-here.md)
- [Current runtime status](docs/refactor/status.md)
- [What changed in refactor 2](docs/refactor/refactor2-changes.md)
- [Product completion specification](docs/refactor/product-completion-spec.md)
- [Delivery milestones](docs/refactor/milestones.md)
- [Modding guide](docs/modding/README.md)
- [Presentation contract](docs/modding/spec/presentation.md)

## Tech stack

Python 3.12, Pygame, and `ruamel.yaml`.
