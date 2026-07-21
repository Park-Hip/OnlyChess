# OnlyChess

**A moddable chess engine.** Pieces, boards, abilities, events, fusion rules, themes, and HUD
layouts are all defined as data under `mods/` — the engine in `src/` holds no chess knowledge of its
own. Standard chess is the starting point, not the product.

## How it works

The core is an engine; all content is a mod. Core may never import a concrete piece, branch on a
piece id, or hardcode the roster. When a change would require core to know about a specific piece,
that is a missing capability in the engine, not a task for the modder.

**The base game is a mod.** Standard chess, fusion, and events load from `mods/base-*` through
exactly the path a third-party mod uses — no privileges, no private API. `base:chess` registers
`castle` and `enpassant` through the same public verb call any code mod would use. This is the
project's forcing function: if the mod API cannot express the base game, the API is incomplete, and
the game visibly breaks.

Two consequences worth knowing, because they explain most of the design:

- **Every state change is an action, and every action has an inverse.** Nothing mutates game state
  directly; the engine records what happened. Undo therefore *reverses the log* rather than replaying
  effects — so it never asks what an effect meant, only what it did, and it works for a mod's effect
  the engine has never heard of, including a random one.
- **Code mods grow the vocabulary; they do not bypass it.** A modder who needs shogi drops registers
  a `drop` move type, and from then on *every* data mod can write `type: drop` without touching
  Python. Content stays data.

## Play

**The easiest way to play** is to download the latest release:
Download `OnlyChess.exe` from the [v2.0.0 Release](https://github.com/Park-Hip/OnlyChess/releases) page.

### Running from source (Developers / Mac / Linux)

Requires Python 3.12. Set up a virtual environment with the standard library:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

or, on Windows, `.venv\Scripts\python main.py`. [`uv`](https://github.com/astral-sh/uv) works too
(`uv run python main.py`) but is a convenience, not a requirement — the dependencies are `pygame` and
`ruamel.yaml`. The game needs a display; over SSH, connect with `ssh -X` so `DISPLAY` is set.

The menu offers every linked mode discovered under `mods/`:

- **Standard Chess** — standard chess from `base:chess` only.
- **Advanced** — chess plus `base:fusion` and `base:events`.

**Mods** lists installed metadata, flags code-bearing mods, and reports attributed load errors.
**Options** sets a time limit and cycles curated board and piece colours. Games save to one slot per
mode and appear under **Continue** on the menu.

Adding a mod means placing its folder under `mods/` and restarting. There is no hot reload, load-order
editor, or mod manager.

### Controls

Click a piece then a highlighted square, or drag it. Right-click a piece for its abilities.

| Key | Action |
|---|---|
| **Ctrl-Z** | Undo the last move or ability |
| **R** | Restart this mode |
| **Backspace** | Return to the menu |
| **Esc** | Pause, or cancel what is open |
| **H** | Controls help |

The **Reference** screen, reachable from the pause menu, is generated from the loaded registries
rather than written by hand — hardcoded help text would have to name content.

## Mechanics

- **Fusion:** a displacing capture — one where the capturer ends up standing on the captured square —
  absorbs the captured piece's components, and the capturer's moves are rebuilt from everything it
  now contains. Any pair fuses, and capture order does not change the result. Identity follows the
  capturer, so a fused rook keeps its own sprite and abilities. Royalty is never absorbed, expressed
  as a property check rather than a piece id.
- **Abilities:** pieces spend Action Points on content-defined effects such as swapping, sniping,
  shielding, or sprinting.
- **Events:** Advanced mode selects a scheduled event, warns before it executes, and records its
  outcome as reversible actions.

Fusion moved from a hand-authored table to composition on 2026-07-19. The table named a result for six
ordered pairs, so only those six could fuse. Composition costs one thing worth stating: Warden's
diagonal was deliberately capped at three squares, and no derived rule can express a cap, so a
rook-bishop now moves as a full rook *and* a full bishop. That is a chosen balance change. The four
authored fused pieces remain placeable content; nothing produces them any more.

## Making a mod

A mod is a folder with a `manifest.yaml` and content files. Folders are cosmetic — the loader reads
the `type:` declaration inside each file, never the path.

```
mymod/
  manifest.yaml
  pieces/dragon.yaml
  code/__init__.py     # optional, only if you need a new verb
```

A piece is data. Offsets are `[forward, right]` in the piece's own frame, never raw board
coordinates:

```yaml
type: piece
id: mymod:dragon
name: Dragon
material: 3
presentation: { glyph: D }
moves:
  - type: leap
    offsets: [[1, 2], [2, 1], [2, -1], [1, -2], [-1, -2], [-2, -1], [-2, 1], [-1, 2]]
```

IDs are namespaced (`mymod:dragon`) because two authors will both invent a Dragon and unnamespaced
IDs make that a silent collision.

A code mod never imports from `src`. It is handed an api object, and that object is the entire
surface:

```python
# mymod/code/__init__.py
def register(api):
    api.move_type("drop", drop_fn, threatens=False)
```

The vocabulary freezes when the last `register()` returns — a verb added after validation would mean
content was checked against an incomplete vocabulary.

Errors name the mod, file, position, field, problem, and what was expected, because the person
reading them does not write Python:

```
ERROR  mymod  pieces/dragon.yaml:7:3
  field:     moves[0].type
  problem:   unknown move type 'slid'
  expected:  one of base:castle, base:enpassant, leap, slide
  did you mean 'slide'?
```

Every content error in a load is reported in one pass, not one per run. Start with the
[modder guide](docs/modding/modder-guide.md); read a [specification](docs/modding/spec/) only when
you need the exact contract.

### What you can and cannot extend today

Data mods compose the existing vocabulary across thirteen content types. Code mods register
`move_type` verbs. **Not yet extensible:** effects, conditions, selectors, event triggers beyond
scheduled pools, custom HUD widget types, arbitrary per-piece overlays, and presentation effects.
These are documented limits rather than hidden bugs — see [status.md](docs/refactor/status.md).

### Trust

There is deliberately **no sandbox**. Python cannot be meaningfully sandboxed, so rather than pretend
otherwise, a manifest declares whether a mod ships code (`code: true`) and the UI surfaces it. A
pure-data mod is genuinely safe to install, and most mods are pure data.

## Repository map

| Path | Holds |
|---|---|
| `src/engine/` | Board, move generation, the action log, statuses, the move pipeline |
| `src/modding/` | Loader, registries, validation, the code-mod api, the error contract |
| `src/ui/` | Screens, presentation runtime, board layout |
| `mods/` | The base game as three mods: `base-chess`, `base-fusion`, `base-events` |
| `docs/modding/` | Modder guide, normative specs, ADRs |

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

Use `unittest`, not `pytest`: the tests import each other package-relatively, which only resolves
under `unittest` discovery, and pytest is not a declared dependency. Do not use `uv run` for a single
module — it drops the repository root from `sys.path` and every test fails with
`ModuleNotFoundError: No module named 'src'`.

## Documentation

- [Modding guide](docs/modding/README.md)
- [New contributor onboarding](docs/onboarding/README.md)
- [Contributor start here](docs/refactor/start-here.md)
- [Current runtime status](docs/refactor/status.md)
- [What changed in refactor 2](docs/refactor/refactor2-changes.md)
- [Product completion specification](docs/refactor/product-completion-spec.md)
- [Delivery milestones](docs/refactor/milestones.md)

## Tech stack

Python 3.12, Pygame, and `ruamel.yaml`.
