# Spec — Mod Package

**Status:** current mod-package contract.
**Depends on:** [ADR-001](../adr/001-data-format.md) (YAML 1.2), [ADR-002](../adr/002-conflict-semantics.md).

## Folder layout

A mod is a directory under `mods/`. Everything except `manifest.yaml` is optional.

```
mods/
  base-chess/
    manifest.yaml
    pieces/        queen.yaml, pawn.yaml, …
    board/         standard.yaml
    statuses/
  base-fusion/
    manifest.yaml
    pieces/        warden.yaml, inquisitor.yaml, …
    fusion/        rules.yaml
  base-events/
    manifest.yaml
    events/        tai_xiu.yaml, …
  mymod/
    manifest.yaml
    pieces/
    code/          __init__.py   ← code mods only; registers verbs
```

Content type is determined by the **declaration inside the file**, not by the directory. Folders are
for humans. A modder who puts a piece in `stuff/things.yaml` gets a working mod and a tidiness
problem, not a load error — the loader must not enforce taste.

## Manifest

`manifest.yaml`, required, one per mod:

```yaml
id: mymod:dragons             # required — the mod's own namespaced ID
name: My Cool Mod             # required — human-facing
version: 1.2.0                # required — semver
authors: [Someone]
description: Adds a dragon.

engine: "^1.0"                # compatibility range; enforced against the running engine

dependencies:
  required:
    base:chess: "^1.0"        # missing → this mod is disabled, loudly
  optional:
    other:mod: "^2.0"         # absent → fine; present → load after it

code: false                   # true → ships Python. See Trust.
```

## ID grammar (D4)

**`namespace:name`** — e.g. `base:queen`, `mymod:dragon`.

- **Charset:** `[a-z0-9_]+` for both parts. Lowercase only.
- **Separator:** a single `:`.
- A mod may only *define* IDs in its own namespace.

**A mod is identified by an ID under the same grammar** — `base:chess`, `mymod:dragons` — declared
as `id:` in its manifest. **The namespace it claims is that ID's namespace part**, so `base:chess`
claims `base` and `mymod:dragons` claims `mymod`. One field, derived rather than declared twice.

This is what dependency keys, disable chains, and every error message name. A mod's ID is content-
addressable like its content, which is not an accident: `base:chess` is a legal ID in the namespace
`base:chess` claims, so the model closes over itself instead of needing a second identity concept.

## Namespace sharing — the originator rule

**A namespace may be claimed by more than one mod, but only when they demonstrably know about each
other.** Formally: among the mods claiming a namespace, **exactly one must be a dependency —
direct or transitive — of every other claimant.** That mod is the namespace's **originator**. If no
such mod exists, it is a **hard load error naming every claimant and the namespace**, never a merge.

The base game is why this rule exists, and it is also its proof. `base:chess`, `base:fusion`, and
`base:events` all define `base:*` IDs — `base:queen`, `base:warden`, `base:poison`. Under
one-namespace-per-mod they could not coexist, and D2's split (required by UC11) would be illegal.
`base:chess` is a dependency of both siblings, so it originates `base` and all three load.

The property the strict rule protected survives intact. Two strangers who both call their mod
`dragonmod` have no dependency between them, no common claimant, and therefore no originator — still
a hard error, still naming both. What the originator rule permits is precisely the case where an
author *chose* to write into a namespace whose owner is in their dependency chain, which means the
owner loaded first and any duplicate ID is a deterministic, attributable error rather than a race.

The alternative was to give each base mod its own namespace (`base_chess:queen`,
`base_events:poison`). Rejected: it bakes **our packaging decision into every ID a third-party mod
references**, so moving `shield` from `base:chess` to `base:events` — an internal reorganisation —
would rename an ID and break every dependent. The partition is our business; the namespace is the
ecosystem's.

**Duplicate IDs are an error regardless**, and sharing a namespace is what makes them possible
across mods rather than only within one file set. The loader catches it by ID, not by namespace.

**Lowercase is enforced, not encouraged.** Case-insensitive collisions (`MyMod:Dragon` vs
`mymod:dragon`) are a classic modding bug, made worse by Windows' case-insensitive filesystem.
Rejecting uppercase at load costs one validation rule and removes the entire class.

**Unqualified references resolve to the current mod's namespace.** Inside `base:chess`, `queen`
means `base:queen`. Inside `mymod`, `dragon` means `mymod:dragon`. Cross-mod references must always
be qualified.

> This deliberately differs from Minecraft, where unqualified names resolve to `minecraft:` from
> *anywhere* — so a modder writing `dragon` silently references vanilla content and gets a confusing
> error. Resolving to the *author's own* namespace matches what someone means when they omit it.

**`base` is a reserved namespace.** Only official mods may claim `base:*` — three of them do
(`base:chess`, `base:fusion`, `base:events`), under the originator rule above.

> Worth being precise, given the "base mod gets no privileges" rule in `CLAUDE.md`: this is a
> **naming** reservation, not a **capability** one. `base:chess` loads through the same path, uses
> the same verbs, and gets no engine special-casing. Reserving the name only stops third parties
> impersonating official content — it grants them nothing.

## Versioning (D8)

**Semver** — `MAJOR.MINOR.PATCH`. For a mod, the public surface that MAJOR protects is:

- IDs it defines (removing/renaming one is breaking)
- **field names in its content** — because ADR-002 makes them patch targets, and therefore API
- verbs it registers (code mods)

Dependencies use caret ranges: `^1.2` means `>=1.2.0, <2.0.0`.

**A dependency MAJOR bump auto-disables dependents** until they declare compatibility, rather than
letting them load and fail confusingly at runtime. This is standard across mod loaders and is what
makes MAJOR mean anything.

`engine: "^1.0"` is validated as a caret range at manifest read and compared with `ENGINE_VERSION`
at resolution. A mod whose range excludes the running engine is disabled with an attributed error,
and its dependents are disabled through the same propagation a missing dependency uses. Omitting
`engine:` declares no constraint and always loads.

## Dependencies and load order

**Load order is derived, never configured.** It is a topological sort of the dependency graph:
dependencies load before dependents, so everything a mod references exists by the time it loads.
Ties break by **mod id**, alphabetically, for reproducibility — not by namespace, which is no longer
unique per mod now that several mods may share one.

- **Required, missing** → the mod is disabled, with a message naming the mod, the missing
  dependency, and the version wanted.
- **Optional, present** → ordered after it. **Optional, absent** → no effect, no error.
- **Cycles** → hard error naming the full cycle (`a → b → c → a`). Cycle detection is load-bearing
  for correctness, not just diagnostics: ADR-002's patch ordering is only deterministic if the graph
  is acyclic.

There is no player-facing load-order editor. Skyrim-style manual ordering pushes conflict resolution
onto players and needs a whole tool ecosystem to survive; declared dependencies plus ADR-002's
collision reporting should make it unnecessary. Revisit only if real mods prove it isn't.

## Trust

`code: false` is the default and must be the honest common case.

- **Data mods** compose content from the verb vocabulary. They cannot execute anything. They are
  genuinely safe to install, and this is a real security property worth surfacing.
- **Code mods** register new verbs (`code/__init__.py`). They run with **full user privileges**.
  Python cannot be meaningfully sandboxed, and we do not pretend otherwise.

The manifest declares which it is; the loader verifies (a mod declaring `code: false` that ships a
`code/` directory is a load error, not a warning); the UI surfaces the distinction before install.

That is the whole mitigation — honesty, not machinery. Installing a code mod is equivalent to
running any downloaded program, and the docs must say so plainly.

## Disabling

Any mod may be disabled, including base mods. Disabling `base:events` yields playable standard
chess (UC11). Disabling a mod that others require disables those too, transitively, with the chain
reported.

## Known limitations

- **Installation and distribution.** Mods currently live under the application's `mods/` directory;
  there is no installer, marketplace, per-user data directory, or hot reload.
