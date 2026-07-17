# Start Here: Contributing to the Mod-Driven Refactor

Use this page before opening source files. The repository runs the mod-driven engine; the hardcoded
runtime was removed at Wave 6.

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

1. [status.md](status.md) — current wave, completed evidence, and deliberate gaps.
2. [architecture.md](architecture.md) — component responsibilities and boundaries.
3. [wave-1-loader.md](wave-1-loader.md) — current source code you can safely change today.
4. The focused section of [the migration plan](../modding/migration-plan.md) for the wave you are
   implementing.
5. The relevant normative spec under `docs/modding/spec/`, only when changing its contract.

Read the legacy overview, `docs/system-overview.md`, when you need to understand behaviour the new
engine must reproduce. Do not use it as a guide for adding new target-engine content.

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

For expanded definitions, see [glossary.md](glossary.md).

## First-change checklist

- Identify the engine/mod boundary your change belongs to.
- Name the wave and contract it advances; do not pull later-wave work forward casually.
- Read the matching tests before changing the implementation.
- Keep base content on the same public API a third-party mod uses.
- Update `status.md` if the live boundary or verified state changed.

The project rules in `AGENTS.md` are authoritative when this guide is less specific.
