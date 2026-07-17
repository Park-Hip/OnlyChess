# Spec — Mod Package

**Status:** draft (roadmap C2). Decides D4 (ID grammar) and D8 (versioning).
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
    assets/        sprites/, sounds/
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
namespace: mymod              # required — owns the ID space
name: My Cool Mod             # required — human-facing
version: 1.2.0                # required — semver
authors: [Someone]
description: Adds a dragon.

engine: "^1.0"                # engine versions this works with

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
- Namespace is claimed by the manifest; a mod may only *define* IDs in its own namespace.
- Two mods claiming one namespace is a **hard load error naming both**, not a merge.

**Lowercase is enforced, not encouraged.** Case-insensitive collisions (`MyMod:Dragon` vs
`mymod:dragon`) are a classic modding bug, made worse by Windows' case-insensitive filesystem.
Rejecting uppercase at load costs one validation rule and removes the entire class.

**Unqualified references resolve to the current mod's namespace.** Inside `base:chess`, `queen`
means `base:queen`. Inside `mymod`, `dragon` means `mymod:dragon`. Cross-mod references must always
be qualified.

> This deliberately differs from Minecraft, where unqualified names resolve to `minecraft:` from
> *anywhere* — so a modder writing `dragon` silently references vanilla content and gets a confusing
> error. Resolving to the *author's own* namespace matches what someone means when they omit it.

**`base` is a reserved namespace.** Only official mods may claim `base:*`.

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

`engine: "^1.0"` gates against the game itself, whose surface is the verb vocabulary and the
loader contract.

## Dependencies and load order

**Load order is derived, never configured.** It is a topological sort of the dependency graph:
dependencies load before dependents, so everything a mod references exists by the time it loads.
Ties break by namespace, alphabetically, for reproducibility.

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

## Open

- **Where do mods live?** `mods/` beside the executable, or a per-user data directory? Affects
  packaging and whether a game update can clobber mods.
- **Asset ID scheme.** Sprites and sounds need addressing too (`mymod:sprites/dragon`), and
  `src/ui/assets.py` currently builds fixed paths.
- **Does `engine:` gate the verb vocabulary or the loader contract?** They will version differently
  once code mods register verbs.
