# Mod-Driven Refactor Status

The snapshot below names the committed Wave 1 baseline. The current handoff also includes the
Wave 2 and Wave 3 implementation and documentation in this worktree; replace the baseline commit
with the final handoff commit after committing the branch.

**This is the live status page for the refactor.** Update it in the same change that advances a
wave, changes an invariant, or changes what a contributor can safely rely on.

**Snapshot:** 2026-07-17 · branch `refactor/mod-driven-prep` · latest refactor commit
`ada54c6` (`Wave 1: the seam — api, registries, parse, errors, loader`).

## Start here

For legacy contributors, use the [legacy-to-refactor map](legacy-to-refactor.md) alongside the
short orientation route.

The old hardcoded game has been retired. The playable application now builds an engine session from
loaded mods; every piece, event, rule, board, and resource enters through the same public path.

Read [start-here.md](start-here.md) for the short orientation route. Read the
[migration plan](../modding/migration-plan.md) only after that route when you need design detail.

## Non-negotiable rules

1. **Core is an engine; all content is a mod.** The base mods receive no private APIs or special
   cases.
2. **Every state change is an action with an inverse.** Effects emit actions; they do not mutate
   game state directly. This is what makes unknown mod effects undoable.
3. **Content identity is namespaced data.** IDs such as `base:queen` are loaded at runtime; they are
   not constants scattered through the engine.

## Wave board

| Wave | State | Evidence and next boundary |
|---|---|---|
| 0 — de-risk | Complete | YAML/source-position spike and differential oracle are complete. The legacy engine remains the oracle. |
| 1 — seam | Complete | `src/modding/` and `tests/modding/` landed in `ada54c6`. Discovery, parsing, trusted code loading, registration, and activation exist. |
| 2 — walking skeleton | Complete | `mods/skeleton/` validates, links, loads its mod-owned sprite, and renders a selected one-piece preview. Full suite: 370 tests green (3 skipped). |
| 3 — engine core | Complete | `src/engine/` interprets data-defined slide/leap pieces, records reversible move/turn/status actions, and matches the legacy oracle on supported fixture positions. See [wave-3-engine-core.md](wave-3-engine-core.md). |
| 4 — `base:chess` | Complete | `base:chess` now registers castle/en-passant, provides promotion/resources/abilities, and passes the standard-chess oracle through perft depth 2. See [wave-4-base-chess.md](wave-4-base-chess.md). |
| 5 — fusion and events | Complete | Fusion, deterministic scheduled events, stored bindings/messages, validation/linking, and extensibility probes run through reversible engine seams. See [wave-5-fusion-events.md](wave-5-fusion-events.md). |
| 6 — cutover | Complete | `main.py` starts an engine session; vanilla and advanced mod sets are selectable; legacy runtime, helpers, and implementation tests are removed. Runtime interaction tests cover promotion, abilities, fusion, and event scheduling. |

## Wave 2: what exists and what does not

The selected walking-skeleton path implements **discover, parse, load code, validate, register,
link, and activate** for `piece`, `board`, and `game_mode`. It uses `load(..., validate=True,
link=True)` so Wave 1's registry-only loader contract remains available while other content types
are still unvalidated.

The loader must not pretend the remaining stages are finished:

- dependency resolution and load graph;
- validation for abilities, events, fusion, statuses, resources, and their runtime vocabulary;
- patch operations and provenance;
- cross-content linking.

These omissions are intentional boundaries, not bugs to work around. See
[wave-2-walking-skeleton.md](wave-2-walking-skeleton.md) before extending this slice.

## Wave 3: what exists and what does not

The isolated engine in `src/engine/` now owns generic board geometry, data-defined pieces,
slide/leap movement, legality simulation, a reversible action log, turn changes, status expiry,
and a capture event bus. `tests/fixtures/wave3_mods/` is deliberately a test fixture rather than
the base game: it exercises only the standard movement that Wave 3 can honestly interpret.

The original comparison runtime was retired after Wave 6. Castling, en-passant, promotion,
resources, abilities, and base-game content are delivered through ordinary loader and code-mod
paths; retained new-engine perft tests provide the standard-chess regression gate.

## Wave 4: what exists and what does not

`mods/base-chess/` is now an executable ordinary mod. It registers its two opaque move types through
`ModApi`; the generic engine dispatches those verbs without naming chess content. The engine records
compound castling actions, history-aware en-passant capture, promotion replacement, resource spending,
ability effects, and turn transitions in the same undo log.

The new-engine adapter reads standard FEN state—including castling rights and en-passant targets—and
matches published standard-chess perft positions through depth 2. The one documented difference is
intentional: the new engine correctly rejects castling through an attacked transit square.

## Verification

Run the repository command from `AGENTS.md`:

```powershell
python -m pytest
```

If the active interpreter lacks `pytest`, fix/select the project test environment before treating
that as a product failure. Wave 3 and Wave 4 changes additionally use `tests/oracle/`; ordinary unit
tests alone are not sufficient evidence that chess behaviour was preserved.

## Documentation ownership

- This page: current state and next boundary.
- [migration-plan.md](../modding/migration-plan.md): target architecture and reasons for the waves.
- `docs/modding/spec/`: normative content and loader contracts.
- Legacy runtime docs: observed old behaviour and oracle context only.

Before merging refactor work, use [contributing.md](contributing.md)'s short documentation check.
