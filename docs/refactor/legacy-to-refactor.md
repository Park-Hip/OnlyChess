# Retired Legacy Code Map

This historical page records where the removed hardcoded implementation went. The mod-driven engine
is now the only runtime; do not recreate any listed legacy path.

## The refactor vision

The refactor turns OnlyChess from a hardcoded chess variant into a reusable game engine. The
engine owns the generic machinery - loading content, validating it, generating moves, applying and
undoing actions, running the turn pipeline, and drawing registered presentation elements - while
mods own the game itself. Standard chess, fusion, abilities, events, statuses, board layouts,
tuning, sprites, and HUD elements are all content supplied through the same public mod API that a
third-party mod receives. If adding a feature requires naming it or editing `src/`, that is evidence
that the engine is missing a reusable capability, not a reason to add another special case.

## What runs today

`main.py` opens the engine-backed menu. **Start** loads `base:chess` and `base:vanilla`; **Advanced**
loads `base:chess`, `base:fusion`, and `base:events` with `base:advanced`. `EngineSession` is the
application boundary between the UI and the loader/engine.

## Legacy-to-refactor map

| Legacy location or concept | Refactor destination | What changes |
|---|---|---|
| `src/game/GameState` | `src/engine/state.py` and `src/engine/pipeline.py` | State and lifecycle are split into generic state, move processing, and reversible actions. |
| `src/game/board.py` | `src/engine/board.py` | Board geometry and occupancy become content-independent. |
| `src/game/move.py` and `src/game/rules.py` | `src/engine/move.py` and `src/engine/movegen.py` | Generic movement verbs interpret mod-defined slide and leap parts. |
| `src/pieces/` and `src/pieces/registry.py` | `src/engine/piece.py` plus piece files under `mods/` | Piece identity and movement are namespaced data, not core constants or import registration. |
| `src/events/` | `mods/base-events/` plus `src/engine/events.py` | Events are data using generic, reversible effects. |
| `src/abilities/` | `mods/base-chess/abilities/` plus `src/engine/abilities.py` | Ability definitions are content interpreted by engine vocabulary. |
| `src/fusion/` | `mods/base-fusion/` plus `src/engine/fusion.py` | Fusion is a mod rule table on the capture bus. |
| `src/game/action_points.py` | `mods/base-chess/resources/ap.yaml` | Resources are namespaced mod data. |
| `poisoned_turns`, shield flags, and similar fields | `src/engine/status.py` plus status content under `mods/` | Statuses become first-class instances with central expiry and generic modifiers. |
| `src/ui/` renderers and panels | Target render loop plus mod-registered sprites, themes, text, and HUD elements | Core owns drawing and input dispatch; mods own what is drawn. |
| Legacy tests in `tests/game/`, `tests/pieces/`, `tests/events/`, and so on | `tests/engine/`, `tests/modding/`, `tests/test_runtime_cutover.py`, and new-engine perft | Tests assert public behavior, not retired implementation details. |

## Safe first session

From the repository root:

```powershell
python main.py
python -m pytest
uv run python -m src.ui.mod_preview
```

The first command opens the mod-driven game. The second runs the project test suite. The third opens
the isolated walking-skeleton preview and proves that a selected mod can load a piece, board,
game mode, and mod-owned sprite.

Before changing code:

1. Read [status.md](status.md) and identify the active wave.
2. Read the matching wave document and its tests.
3. Use the content schemas and engine tests to learn behaviour; deleted paths have no compatibility contract.
4. Keep new content in `mods/` whenever an existing verb can express it.
5. Add an engine capability only when the content cannot be expressed; make that capability
   available through the same public path to base and third-party mods.

## What the historical map is useful for

It explains why rule identity and mutations belong in mods and actions. It is not a template for
new architecture: do not restore concrete piece/event imports, direct state mutations, or special
cases into `src/engine/`.

For the design rationale, see [architecture.md](architecture.md), the focused wave document, and
the normative specifications under `docs/modding/spec/`.
