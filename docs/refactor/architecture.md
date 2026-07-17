# Target Architecture at a Glance

This page is an orientation map. The detailed design and rationale live in the
[migration plan](../modding/migration-plan.md); do not duplicate decisions here.

## Ownership

| Area | Core engine owns | Mods own |
|---|---|---|
| Game state | board geometry, turn lifecycle, action application/undo | board layouts and starting positions |
| Rules | move/capture pipeline, registries, validation, event bus | piece moves, effects, conditions, selectors, fusion rules |
| Presentation | render loop, input dispatch, audio playback | sprites, sounds, text, themes, HUD elements |
| Loading | discovery, dependency order, attribution, link/activation | manifests, content files, optional trusted code |

The dividing question is simple: if a third-party modder would need to edit `src/` to add it, the
engine is missing a capability.

## Runtime flow

```text
1. Discover mod manifests
2. Resolve dependencies and load trusted code mods
3. Validate, patch, register, and link content
4. Activate one game mode
5. Engine interprets registered movement/effect vocabulary
6. Effects emit reversible actions
7. UI renders registered content; it does not decide rules
```

The loader stages are deliberately incremental. Wave 1 implements only the stages required for its
seam; later stages must not be silently faked. See [wave-1-loader.md](wave-1-loader.md).

## Boundaries worth protecting

- Core never imports or names a concrete piece, event, ability, fusion rule, or base mod.
- Registries are populated by the loader at runtime, not by import side effects.
- Conditions are pure predicates; computation belongs in effects or code-mod verbs.
- Error messages identify the mod, file, field, and expected correction.
- `simulate` calculates legality without permanent effects; `apply` records actions and can undo.
- `main.py` creates an engine-backed session through the public loader; it does not import content
  rules or a compatibility runtime.

## Which document answers which question?

| Question | Document |
|---|---|
| What is active now? | [status.md](status.md) |
| Why is the refactor a rebuild and what lands in each wave? | [migration-plan.md](../modding/migration-plan.md) |
| What does a content file mean? | `docs/modding/spec/content-schemas.md` |
| What is the loader's complete contract? | `docs/modding/spec/loader-lifecycle.md` |
| Why did the old engine need replacement? | `docs/modding/engine-gap-analysis.md` |
| What does old code currently do? | `docs/system-overview.md` and `tests/oracle/` |
