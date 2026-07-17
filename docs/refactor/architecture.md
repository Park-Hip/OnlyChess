# Target Architecture at a Glance

This page is an orientation map. The normative contracts under `docs/modding/spec/` define the
supported modding surface.

## Ownership

| Area | Core engine owns | Mods own |
|---|---|---|
| Game state | board geometry, turn lifecycle, action application/undo | board layouts and starting positions |
| Rules | move/capture pipeline, registries, validation, event bus | piece moves, effects, conditions, selectors, fusion rules |
| Presentation | render loop, input dispatch, glyph rendering | Future content-defined sprites, sounds, themes, and HUD elements |
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

The loader validates and links the content types consumed by the active engine; unsupported content
must fail loudly rather than being treated as playable.

## Boundaries worth protecting

- Core never imports or names a concrete piece, event, ability, fusion rule, or base mod.
- Registries are populated by the loader at runtime, not by import side effects.
- Conditions are pure predicates; computation belongs in effects or code-mod verbs.
- Error messages identify the mod, file, field, and expected correction.
- `simulate` calculates legality without permanent effects; `apply` records actions and can undo.
- `main.py` creates an engine-backed session through the public loader; it does not import content
  rules or a compatibility runtime. The current screen intentionally renders glyphs while the
  presentation extension surface remains future work.

## Which document answers which question?

| Question | Document |
|---|---|
| What is active now? | [status.md](status.md) |
| What does a content file mean? | `docs/modding/spec/content-schemas.md` |
| What is the loader's complete contract? | `docs/modding/spec/loader-lifecycle.md` |
