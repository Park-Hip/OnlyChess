# Start Here: Contributing to the Mod-Driven Refactor

Use [the new contributor onboarding](../onboarding/README.md) first if you are joining from the
legacy implementation. This page is the contributor-level architecture and decision orientation.
The repository runs the mod-driven engine; the hardcoded runtime was removed at Wave 6.

## The ten-minute model

The target is not “make the old game configurable.” It is an engine whose rules and content are
provided by mods. The base game is only the first mod set, so the core must never name a queen,
event, fusion rule, colour, panel, or base-mod path.

```text
mods/ -> loader -> runtime registries -> engine verbs -> actions -> game state/UI
                  ^                         |
                  |---- trusted code mods --|
```

- **Data mods** use already-registered vocabulary to define pieces, events, abilities, and tuning.
- **Code mods** extend that vocabulary by registering verbs through the public `ModApi`.
- **Actions** are the only state mutations. Each action has an inverse so undo works even for a
  mod effect the core does not understand.
- The retained oracle is new-engine perft coverage, not a compatibility bridge to deleted code.

## Read in this order

1. [status.md](status.md) — executable behaviour, current evidence, and known gaps.
2. [product-completion-spec.md](product-completion-spec.md) — approved v1 finish definition and
   architecture decisions.
3. [milestones.md](milestones.md) — the dependency-ordered delivery plan.
4. [architecture.md](architecture.md) — component responsibilities and boundaries.
5. [contributing.md](contributing.md) — the checklist for a safe change.
6. The relevant normative spec under `docs/modding/spec/`, only when changing its contract.

## Vocabulary

| Term | Meaning |
|---|---|
| retired legacy runtime | The removed hardcoded implementation; its replacement map is historical context only. |
| mod | A folder with a manifest and content; it may declare trusted Python code. |
| content | Data a mod supplies: a piece, board, event, status, resource, and so on. |
| verb | An engine capability that data can invoke, such as a move type or effect. |
| registry | Runtime-owned map of validated namespaced IDs to content or verb definitions. |
| action | A recorded state change and its inverse; the basis of undo. |
| oracle | New-engine perft coverage in `tests/oracle/`. |


## First-change checklist

- Identify the engine/mod boundary your change belongs to.
- Name the wave and contract it advances; do not pull later-wave work forward casually.
- Read the matching tests before changing the implementation.
- Keep base content on the same public API a third-party mod uses.
- Update `status.md` if the live boundary or verified state changed.

The project rules in `AGENTS.md` are authoritative when this guide is less specific.
