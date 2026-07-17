# ADR-002 — Conflict and override semantics

**Status:** accepted (roadmap C5 / D5)
**Date:** 2026-07-16

## Context

Two mods modify the same thing. What happens? This is where "everybody can extend" either works or
collapses into a mod-manager nightmare, and it constrains the content schemas — so it cannot be
deferred.

**The prior art gives a direct, documented answer.** RimWorld is our closest analogue: an OOP game,
content-as-data, a large non-coder modding scene, with a code escape hatch. Its history is the
evidence:

> Prior to RimWorld alpha 17, modders could only modify Defs by creating new ones that overwrote the
> original; this often resulted in compatibility issues — if more than one mod tried to overwrite
> the same Def, only the last mod in the load order would succeed, as prior ones would themselves be
> overwritten.
> — [RimWorld Wiki, PatchOperations](https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations)

RimWorld shipped whole-content last-wins override, it produced mass conflicts, and they **retrofitted
XPath-based patching in alpha 17**. Afterwards, [two mods can modify different parts of the same Def
without conflict](https://rimworldwiki.com/wiki/Modding_Tutorials/Compatibility).

This is exactly the failure mode the roadmap told us to read prior art for. We should not
independently rediscover it.

## Decision

**Content is addressable at field granularity, and mods interact with it three ways:**

| Mode | Meaning | Conflicts? |
|---|---|---|
| **define** | introduce new content under your own namespace | never — the common case |
| **patch** | modify specific fields of existing content | only if two mods touch the *same field* |
| **replace** | substitute an entire content definition by ID | coarse; last-wins; discouraged |

**Minimal patch operation set — three ops, not XPath:**

```yaml
patches:
  - target: base:queen
    op: set
    path: moves[0].limit
    value: 3
```

`set` (change a field) · `add` (append to a list) · `remove` (delete a field or list entry).

**Load order derives from the dependency graph** (ADR pending, roadmap C2), making patch application
deterministic and reproducible.

**Same-field collisions are detected and reported, never silent.** When two mods patch the same
path, the later one wins *and the loader says so*, naming both mods, the target, and the field.

## Rationale

**Why not last-wins whole-content override, the simplest thing?** Because we have direct evidence of
where it leads. RimWorld ran that experiment for us and had to retrofit. The simple option is not
cheaper — it is deferred cost plus an ecosystem-wide migration.

**Why not full XPath?** RimWorld's XPath is powerful and notoriously hard for non-coders — it is a
query language on top of a data format, which is the Phase B trap wearing a different hat. Three
ops covers "change a number," "add a move," and "remove a thing," which is what patches are actually
for. More ops can be earned later.

**Is this speculative, given the "vocabulary is earned" rule?** No, and the distinction matters.
That rule governs the **content vocabulary** — triggers, conditions, effects. Conflict semantics are
**shape**: two extensions that cannot coexist mean the project's central claim is false. Seamless
extension *is* the requirement, and it is what earns this.

**Why detection matters more than it looks.** Silent breakage is the actual pain of modding — the
game does not crash, it just quietly behaves wrong, and nobody knows which mod did it. Detection is
nearly free once patches are addressable, and it upholds the `CLAUDE.md` invariant: fail loud, with
attribution. We cannot *resolve* a genuine same-field disagreement — that needs a human — but we can
refuse to hide it.

## Consequences

- **The loader's data model must be addressable before anything is built on it.** This is the part
  that is expensive to retrofit; the ops themselves are easy. If content is only ever "a file that
  replaces a file," this ADR is unimplementable later.
- **Patch targets are part of the public contract.** Renaming a field in `base:chess` breaks every
  mod patching it. Field names are API, and versioning (D8) must account for that.
- **`replace` stays legal but discouraged**, documented as the blunt instrument. Sometimes a total
  conversion genuinely wants to replace a piece outright, and forbidding it just makes people fork.
- **Patch ordering is only as good as the dependency graph.** Cycle detection (C2) is now
  load-bearing for correctness, not just for clean errors.
- We ship three ops with **no base-game consumer** — `base:fusion` and `base:events` extend
  `base:chess` additively rather than by patching. The first real test will be a third-party mod.
  Accepted knowingly: the addressing model is what must exist early, and the ops are what prove it.

## Alternatives rejected

| Option | Why not |
|---|---|
| Last-wins whole-content override | RimWorld's documented failure; retrofit cost is ecosystem-wide |
| Full XPath patching | a query language for non-coders; the Phase B trap again |
| Tag/registry merging only (Minecraft-style) | elegant for additive lists, cannot express "change this number" |
| Manual load-order tools (Skyrim-style) | pushes conflict resolution onto players; needs a whole tool ecosystem |
| Forbid overlap entirely | mods could not tune each other; kills the Tuner persona |
