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

The old hardcoded game still runs. It is the **legacy runtime** and comparison oracle, not the
place to add new content architecture. The target is an engine in `src/` that loads every piece,
event, rule, board, resource, and HUD element from `mods/` through the same public path.

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
| 4 — `base:chess` | Planned | Code-mod castle/en-passant verbs, standard chess content, resources, abilities, promotion, and full chess oracle. |
| 5 — fusion and events | Planned | Selector/condition/effect engine, capture bus, fusion, event pool, and acceptance probes. |
| 6 — cutover | Planned | Route `main.py` to the replacement engine and delete retired legacy core. |

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

The legacy runtime remains untouched. Its `EngineAdapter` is compared with the Wave 3 adapter on
ordinary positions; that adapter reports no differences in the supported scope. Castling,
en-passant, promotion, resources, abilities, and base-game content remain Wave 4 work, because
they require mod-provided verbs or content capabilities that do not exist yet.

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
