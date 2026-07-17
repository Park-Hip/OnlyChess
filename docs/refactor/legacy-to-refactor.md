# Legacy Code to Refactor Map

This page is for contributors who know the original OnlyChess implementation and need to
understand where that knowledge belongs in the mod-driven refactor.

## The refactor vision

The refactor turns OnlyChess from a hardcoded chess variant into a reusable game engine. The
engine owns the generic machinery - loading content, validating it, generating moves, applying and
undoing actions, running the turn pipeline, and drawing registered presentation elements - while
mods own the game itself. Standard chess, fusion, abilities, events, statuses, board layouts,
tuning, sprites, and HUD elements are all content supplied through the same public mod API that a
third-party mod receives. If adding a feature requires naming it or editing `src/`, that is evidence
that the engine is missing a reusable capability, not a reason to add another special case.

## What is running today

There are two paths in the repository:

| Path | Purpose | Status |
|---|---|---|
| `main.py` / `run.py` -> `src/main.py` | The playable legacy game | Still the real game and behavioural oracle |
| `src/modding/` + `src/engine/` + `mods/skeleton/` | The replacement path | Isolated loader, preview, generic movement, actions, turns, statuses, and oracle slice |

The replacement path is not yet the playable application. Do not route `main.py` to it or delete
legacy code until the later cutover wave says it is ready.

## Legacy-to-refactor map

| Legacy location or concept | Refactor destination | What changes |
|---|---|---|
| `src/game/GameState` | `src/engine/state.py` and `src/engine/pipeline.py` | State and lifecycle are split into generic state, move processing, and reversible actions. |
| `src/game/board.py` | `src/engine/board.py` | Board geometry and occupancy become content-independent. |
| `src/game/move.py` and `src/game/rules.py` | `src/engine/move.py` and `src/engine/movegen.py` | Generic movement verbs interpret mod-defined slide and leap parts. |
| `src/pieces/` and `src/pieces/registry.py` | `src/engine/piece.py` plus piece files under `mods/` | Piece identity and movement are namespaced data, not core constants or import registration. |
| `src/events/` | Future event content under `mods/base-events/` plus engine effect/condition verbs | Events become data that uses generic vocabulary; new verbs belong in code mods. |
| `src/abilities/` | Future ability content under `mods/base-chess/` plus engine effect verbs | Ability definitions move out of concrete Python classes where the vocabulary can express them. |
| `src/fusion/` | Future fusion content under `mods/base-fusion/` | Fusion becomes a mod rule table and capture-pipeline content. |
| `src/game/action_points.py` | Future resource content under `mods/base-chess/` | Resource names, limits, and tuning become mod data. |
| `poisoned_turns`, shield flags, and similar fields | `src/engine/status.py` plus status content under `mods/` | Statuses become first-class instances with central expiry and generic modifiers. |
| `src/ui/` renderers and panels | Target render loop plus mod-registered sprites, themes, text, and HUD elements | Core owns drawing and input dispatch; mods own what is drawn. |
| Legacy tests in `tests/game/`, `tests/pieces/`, `tests/events/`, and so on | Replacement tests plus `tests/oracle/` | Legacy tests protect the oracle; oracle tests prove equivalent behaviour where the new engine supports it. |

## Safe first session

From the repository root:

```powershell
python main.py
python -m pytest
uv run python -m src.ui.mod_preview
```

The first command opens the legacy game. The second runs the project test suite. The third opens
the isolated walking-skeleton preview and proves that a selected mod can load a piece, board,
game mode, and mod-owned sprite without constructing the legacy `GameState`.

Before changing code:

1. Read [status.md](status.md) and identify the active wave.
2. Read the matching wave document and its tests.
3. Use the legacy implementation to learn behaviour, not as the extension pattern.
4. Keep new content in `mods/` whenever an existing verb can express it.
5. Add an engine capability only when the content cannot be expressed; make that capability
   available through the same public path to base and third-party mods.

## Where the legacy knowledge is still useful

The old implementation remains valuable for three things: describing intended gameplay, exposing
edge cases, and serving as the comparison oracle. It is not a template for new architecture. In
particular, do not copy concrete piece/event imports, core constants, direct state mutations, or
special cases into `src/engine/`.

For the design rationale, see [architecture.md](architecture.md), the focused wave document, and
the normative specifications under `docs/modding/spec/`.
