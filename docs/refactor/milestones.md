# Product Completion Milestones

**Status:** approved delivery roadmap.
**Defines:** the implementation sequence for the product definition in
[product-completion-spec.md](product-completion-spec.md).

The refactor's intended contract is authoritative. The first remaining milestone is therefore not
presentation: it is bringing the loader and engine to the contract already documented for mods.

## Milestone 0 — Documentation and verification hygiene

**Status:** complete, subject to keeping status documents aligned with executable behaviour.

- Remove obsolete claims that the mod runtime cannot run content.
- Correct the content-type count and historical planning gaps that are now implemented.
- Document active test suites and the canonical verification command.

## Milestone 1 — Loader and content-contract parity

**Status:** complete. The runtime uses the nine-stage loader; registry-only tests may explicitly
exercise earlier stages without activation.

**Goal:** make every documented loader and content guarantee real before adding more mod-owned
content such as presentation.

### Deliverables

- Implement manifest engine/version checks, dependency resolution, deterministic topological order,
  originator checks, cycles, and disable chains.
- Implement strict registry-driven validation for all ten content types and nested vocabularies.
- Implement `replaces`, `set`, `add`, and `remove` patch semantics, conflict reporting, provenance,
  and post-patch revalidation.
- Normalize all author-facing values after patches, then link every reference before activation.
- Expand the code-mod API only where an active content requirement proves a new verb kind is needed.
- Replace registry-only acceptance of unsupported content with a complete engine consumer or a
  load-time error.

### Acceptance criteria

- A malformed field, dangling reference, dependency error, patch error, or unknown verb prevents
  the affected mod from loading and identifies the responsible mod, file, location, and field.
- Base chess, fusion, and events load in dependency order using the same resolver a third-party mod
  uses.
- A third-party fixture exercises dependencies, a patch, a replacement, and a code-provided verb.
- No current-facing status document claims a lifecycle capability that the source does not implement.

## Milestone 2 — Generic game-mode selection and board-aware play

**Status:** complete. Startup owns one loaded catalog; sessions, geometry, side labels, and ability
selection all derive from the selected mode.

**Goal:** let the player launch every compatible loaded game mode through normal UI without core code
naming `base:*` content or assuming a standard chessboard.

### Deliverables

- Discover and resolve compatible mods at application startup; build a linked game-mode catalog.
- Replace hardcoded Start/Advanced paths with catalog-driven mode selection.
- Pass the selected mode and load result into `EngineSession`; remove base-content defaults.
- Derive all board layout, hit testing, highlights, and panels from board dimensions and the viewport.
- Treat side identity and display as board data rather than `white`/`black` suffixes.
- Add a generic ability chooser and target-selection flow that presents all available abilities.

### Acceptance criteria

- A discovered third-party mode appears in the regular menu and starts without editing `src/ui/`.
- A non-8x8 two-side board is rendered, clickable, and correctly bounded.
- Disabling events still exposes standard chess through loaded mode content, not a base-specific UI
  branch.

## Milestone 3 — Presentation contract

**Status:** complete. Presentation content now has a strict, loader-backed declarative contract;
normal-game rendering and playback remain Milestone 4 work.

**Goal:** specify the smallest safe, declarative vocabulary by which mods describe what the core
render loop draws and plays.

### Deliverables

- Write normative schemas for themes, HUD layouts, sound assets/cues, piece/status visuals, and
  game-mode presentation selection.
- Define asset ownership, paths, formats, scaling, caching, failure attribution, and glyph fallback.
- Define a read-only presentation snapshot and engine lifecycle-notification vocabulary.
- Define the initial declarative HUD widget set from actual base and proof-mod needs.
- Define the action-safe public API for any presentation vocabulary code mods must add.

### Acceptance criteria

- Presentation data goes through the standard loader, validation, patch, and link path.
- Bad asset references and unknown presentation fields are attributed load errors.
- The schema can express every shipped visual requirement without an engine-side content name or a
  Python drawing callback.

## Milestone 4 — Presentation runtime vertical slice

**Status:** complete. The normal game screen resolves selected-mode presentation content, renders
themes and explicit piece glyphs/sprites, and dispatches declarative sound cues.

**Goal:** make the regular Pygame application render and play the registered presentation content.

### Deliverables

- Move mod-owned sprite/asset loading from the preview proof into the normal runtime.
- Replace hardcoded piece glyph mapping, palette, panels, and fixed messages with registered
  presentation content.
- Render generic status markers and declarative HUD widgets.
- Dispatch sound cues from read-only engine lifecycle notifications.
- Convert base content to this public presentation path.

### Acceptance criteria

- Base content and an independent data mod use identical presentation schemas and runtime paths.
- Missing assets never silently fall back to base assets; glyph-only fallback is explicit content.
- Core never imports or names a concrete piece, theme, HUD element, colour, or sound.

## Milestone 5 — Release proof and quality gate

**Status:** complete. Automated proof passed and the manual checklist was completed with no bugs
detected on 2026-07-17.

**Goal:** prove the full product loop in automated tests and a clean manual run.

### Deliverables

- Create the independent proof mod: non-8x8 board, custom piece, selectable mode, presentation,
  status marker, and HUD content.
- Add headless Pygame tests for modes, dynamic boards, presentation, outcome/restart, and errors.
- Cover standard chess and advanced-mode gameplay, including complete-turn undo.
- Write and execute a manual release checklist from a clean environment.
- Update status and modder documentation only after every supported capability is live.

### Acceptance criteria

- The proof mod is discovered automatically, selected normally, and played without a core edit.
- The full automated suite and manual checklist pass.
- The product-completion definition in `product-completion-spec.md` is satisfied.

## Dependency order

```text
M0 documentation hygiene
  -> M1 contract parity
    -> M2 generic runtime
      -> M3 presentation specification
        -> M4 presentation runtime
          -> M5 independent-mod release proof
```

Do not pull event triggers, AI, multiplayer, localization, hot reload, distribution, or a mod manager
into these milestones. They are not required by the approved v1 finish definition.
