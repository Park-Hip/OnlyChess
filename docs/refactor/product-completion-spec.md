# Product Completion Specification

**Status:** approved product definition and delivery constraints.
**Date:** 2026-07-17.
**Authority:** this document records the decisions made after the completion research pass. It
complements the normative modding contracts; where the current source disagrees with those
contracts, source must be brought into conformance rather than weakening the contract to match it.

## Product statement

OnlyChess is a local, turn-based, moddable tactical chess game. Standard chess is the starting
ruleset, not the product boundary: installed mods can provide pieces, boards, abilities, statuses,
resources, fusion rules, scheduled events, presentation, and complete game modes.

The player-facing base game includes standard chess, optional capture fusion, Action Point
abilities, and scheduled global events. The engine must make those mechanics available as ordinary
mod content rather than treating them as special cases.

The defining promise is:

> A third-party mod can provide playable content without editing `src/`, and the shipped base game
> reaches the runtime through exactly that same public path.

## Approved decisions

### The written contract is authoritative

`AGENTS.md`, the modding specifications, and the accepted ADRs define the target product. Current
implementation gaps are work to complete, not reasons to reduce the contract. In particular, the
loader must eventually provide every documented lifecycle stage, strict validation, attributed
errors, dependency handling, patching, linking, and runtime registration.

Current-status documents must describe the executable state accurately. They must not call a
contract complete merely because the shipped base content happens to load.

### Initial mod activation is automatic

For v1, the application discovers and resolves every compatible mod under `mods/` at startup. It
then displays the loaded `game_mode` content in the normal menu. A player chooses a mode, not a
hardcoded base-game branch.

This is deliberately not a mod manager: there is no install service, marketplace, manual load-order
editor, or hot reload. A mod is installed by placing its folder under `mods/`; compatibility,
dependencies, conflicts, and disable chains are the loader's responsibility.

### The release proof is an independent data mod

V1 is not finished when only the two shipped base modes play. It is finished when an independent
data mod proves the public surface end to end:

- it is discovered automatically;
- it supplies a selectable game mode and a board whose dimensions differ from standard chess;
- it supplies pieces and rules using registered vocabulary;
- it supplies its own presentation data, status visibility, and HUD content;
- it plays through the normal UI without editing `src/`;
- moves, abilities, events, fusion where enabled, promotion, terminal outcomes, and undo remain
  correct and reversible.

The proof mod is an acceptance test and a regression fixture. It is not privileged demo content.

## Product boundaries

### Core owns the stable machinery

- Board geometry, state, move legality, turn lifecycle, actions, inverses, and undo.
- Mod discovery, dependency resolution, validation, patches, registries, linking, and activation.
- The Pygame loop, responsive layout, input dispatch, generic rendering primitives, and audio
  playback.
- A read-only presentation snapshot and lifecycle notifications that presentation can consume.

### Mods own game and presentation content

- Pieces, move declarations, abilities, statuses, resources, fusion tables, events, pools, boards,
  and game modes.
- Piece glyphs/sprites, status markers, themes, HUD layouts, text, and sound-cue mappings.
- New reusable vocabulary through trusted code mods. A code mod grows the data language; it does
  not define content directly or mutate game state outside actions.

### Non-goals for this release

- Hot reload, a mod marketplace, distribution service, sandboxing, or manual load-order editor.
- Multiplayer, AI, localization, achievements, replay sharing, or cloud saves.
- Speculative gameplay vocabulary such as arbitrary event triggers, hit points, arithmetic, or
  general scripting. Add vocabulary only when real content requires it.
- Arbitrary Python drawing callbacks or mods receiving Pygame objects.

## Definition of done

OnlyChess is complete at this product scope when all four gates below pass.

| Gate | Required result |
|---|---|
| Contract-complete engine | The documented loader lifecycle and all active content contracts are implemented, validated, linked, and tested. |
| Mod-complete runtime | Any loaded game mode can be selected and played on its declared board without core naming base content or assuming an 8x8 white/black game. |
| Presentation-complete application | Registered mod content supplies piece visuals, themes, status markers, HUD content, and sound cues; core only renders and dispatches. |
| Release-complete product | A player can launch, choose a mode, play, undo, reach an outcome, restart, and receive actionable errors; automated and manual release checks pass. |

## Required capabilities

### 1. Loader and content-contract parity

The implementation must fulfil the documented nine-stage lifecycle:

1. Discover manifests without reading disabled content.
2. Resolve required/optional dependencies, semver compatibility, namespace originators, cycles, and
   deterministic order.
3. Parse all enabled content through the YAML 1.2 chokepoint with source positions.
4. Load trusted code-mod vocabulary in resolved order, then freeze it.
5. Validate every active content type and nested vocabulary strictly, including unknown keys,
   required fields, types, values, and registered verbs.
6. Apply replacements and field patches with provenance, conflict reporting, and revalidation.
7. Normalize author-facing data only after patches land.
8. Link every cross-reference before a session starts.
9. Activate only when at least one fully linked game mode is available.

All thirteen content types must have an engine consumer or be rejected as unsupported; they must never be
silently accepted as registry-only data. Error reports must name the mod, file, position, field, the
problem, and the expected correction.

### 2. Generic mode and board runtime

- Startup loads the compatible mod set once and produces a catalog of linked game modes.
- The menu renders that catalog and passes the selected mode to the session.
- `EngineSession` receives its load result/mode selection from the application boundary; it has no
  hardcoded `base:*` default content.
- Board rectangle, square dimensions, hit testing, selection overlays, outcome placement, and panel
  layout derive from the active board and available viewport.
- The UI treats sides as data. It does not infer identity or colour from `:white` / `:black` suffixes.
- The UI presents all available abilities with their content-defined names, costs, and target flow;
  it never silently chooses the first ability.
- The engine exposes display metadata needed by the UI without leaking mutable state or content
  implementation details.

### 3. Presentation contract

The initial presentation vocabulary stays declarative and small:

| Content | Responsibility |
|---|---|
| `theme` | Palette tokens, board treatment, typography choices, selection and warning colours. |
| Piece/status presentation fields | Display name, glyph fallback, optional sprite/icon references, and public-status visibility. |
| `hud_layout` | A list of supported, declarative HUD widgets and their placement tokens. |
| `sound` | Reusable audio assets and mappings from engine-owned lifecycle notifications to cues. |
| Game-mode presentation selection | References the theme and HUD layout active for that mode. |

The schema is defined by [spec/presentation.md](../modding/spec/presentation.md) and is consumed by
the playable runtime. It is intentionally small: separate reusable `theme`, `hud_layout`, and
`sound` definitions, with piece- and status-specific visuals on the content they describe. The
current public code API registers movement verbs only; custom presentation widgets remain future
work.

Core exposes generic layout/rendering primitives and read-only state. Future presentation verbs may
be registered through `ModApi` as declarative values, but code mods must never receive surfaces,
fonts, audio devices, or mutable game state. In the current implementation, `ModApi` registers
movement verbs only.

### 4. Presentation notifications

Presentation needs stable, engine-owned lifecycle notifications rather than inspecting action
implementation details. The initial vocabulary is earned by the shipped game:

- move completed;
- capture completed;
- ability used;
- promotion chosen;
- event warning;
- event executed;
- status applied or expired;
- game outcome reached;
- undo completed.

These notifications are observation only. They must not offer a path to mutate state outside the
action log. Sound and HUD systems subscribe to them; rules do not call audio or Pygame directly.

### 5. Release and proof requirements

The release test matrix includes:

- standard chess mode, including castling, en passant, promotion, checkmate/stalemate, and undo;
- advanced mode, including resources, abilities, fusion, warnings, event execution, status expiry,
  and complete-turn undo;
- a deliberately independent data mod with a non-8x8 board, a custom piece, a selectable mode, and
  presentation content;
- loader failures for malformed data, missing assets, dependency/version errors, patches, conflicts,
  and disabled-mod references;
- headless Pygame smoke tests for menu navigation, mode selection, dynamic board input, presentation
  rendering, restart, and outcome handling;
- a manual release checklist using a clean environment and the canonical verification command.

## Delivery order

```text
Contract parity
  -> mode catalog and board-aware runtime
    -> presentation specification
      -> presentation vertical slice
        -> release proof and quality gate
```

The loader work comes first because presentation is itself mod content. A presentation system built
before strict validation, dependencies, patching, and linking would create a second unverified path
and contradict the product promise.

The detailed work sequence and acceptance criteria live in
[milestones.md](milestones.md).

## Decisions deliberately deferred

- Whether v1 supports more than two sides. Board data remains generic, but the release proof only
  requires two-side modes until real content earns multiplayer-side rules and UI treatment.
- Presentation depth beyond the current static vocabulary: custom widgets, clock state, arbitrary
  per-piece text/colour fields, and effect-driven animation primitives. The current asset formats,
  scaling policy, fallback behavior, and four-widget HUD set are defined in the presentation spec.
- New code-mod verb kinds beyond the requirements needed to implement the approved presentation
  contract. Each addition needs a content consumer and action-safe API design.
