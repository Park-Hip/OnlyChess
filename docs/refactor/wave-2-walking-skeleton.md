# Wave 2: Walking Skeleton

**Status:** complete, 2026-07-17. The first target-engine vertical slice now loads content through
the mod loader and renders it without constructing the legacy `GameState`.

## What proves the path

`mods/skeleton/` contains one pure-data mod:

```text
manifest.yaml
pieces/beacon.yaml
board/preview.yaml
modes/preview.yaml
assets/sprites/beacon/skeleton/blue.png
```

The preview invokes:

```powershell
uv run python -m src.ui.mod_preview
```

It explicitly selects `skeleton:demo`, then validates and links:

```text
skeleton:preview -> skeleton:preview_board -> skeleton:beacon -> sprite PNG
```

The preview path is intentionally separate from `src/main.py`. The old game remains the runnable
legacy oracle until cutover.

## Narrow Stage 5 and Stage 8 support

`load(..., validate=True, link=True)` adds the active-engine slice:

- validation for `piece`, `board`, and `game_mode`;
- linking game modes to boards and board placements to pieces;
- a small immutable render layout, not a general board/piece/game-state model;
- selected-mod loading, so incomplete future base content does not stop this proof.

The default loader remains registry-only for Wave 1 contracts and unsupported content types. That is
an explicit temporary boundary, not a claim that events, abilities, statuses, or fusion are valid.

## Asset contract

Side IDs remain namespaced data, but a colon cannot occur in a Windows filename. A sprite therefore
uses this portable path:

```text
<mod>/assets/sprites/<sprite-name>/<side-namespace>/<side-name>.png
```

A missing sprite raises an attributed `ModLoadError`; there is no Queen fallback in the new path.

## Verification

The focused walking-skeleton tests cover selection, validation/linking, safe asset paths, successful
asset loading, and missing-asset failure. The full suite passed: **370 tests, 3 skipped**.

## Deferred to Wave 3

- generic `Piece` / `Board` models;
- movement, turns, actions, simulation, undo, and statuses;
- standard-chess oracle comparison against the new engine.
