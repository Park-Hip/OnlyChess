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
- Implement strict registry-driven validation for all thirteen content types and nested vocabularies.
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

## Milestone 6 — Presentation fidelity and application shell

**Status:** complete. Closes verified gaps between the presentation contract specified in M3 and
what the runtime actually renders in M4, and adds the minimal application shell a real play session
and the trust model require. Precedes M7 — juice on a HUD that ignores its own declared layout is
polish on a gap.

**Progress:**
- *Slice 1 (done)* — the renderer draws the declared `hud_layout` widgets by slot instead of a
  hardcoded header/log; the `resources` widget now renders. Removing a side widget removes the panel
  with no `src/` edit.
- *Slice 2 (done)* — real sound cues. `base:classic_sounds` and `proof:sound` ship contract-legal WAV
  assets under `assets/sfx/`; the app shell initialises the mixer (soft-failing without an audio
  device); the runtime emits the `promotion_chosen` and `outcome_reached` kinds that nothing fired
  before. Cues emitted: move, capture, ability, promotion, undo, outcome. The remaining contract cue
  kinds (scheduled events, status apply/expire) fire from inside the pipeline and are deferred — they
  should be derived from the recorded action log, not hand-authored, so they cover mod effects the
  engine has never heard of. That derivation is its own slice.
- *Slice 3 (done)* — a finished game has somewhere to go. `EngineGameScreen` draws "Restart" and
  "Menu" buttons on the outcome overlay and accepts the `R` / `Backspace` shortcuts during normal
  play; both are core shell chrome (like the menu's existing "Quit"), not mod content, so they live in
  core without special-casing any mod. Restart constructs a brand-new `EngineSession` — a fresh, empty
  action log — never a replay or reversal of the current one's log, leaving the undo invariant
  untouched. The outcome overlay dims the finished board with a scrim tinted from the theme's own
  `background` token. Button colours reuse the existing palette-token-or-fallback pattern (`panel`,
  `selection`, `text`); no new hardcoded colour was added.
- *Slice 5 (done)* — status `icon` assets and multiple visible statuses. `PresentationRuntime` gained
  `status_icon`/`status_presentation` (sharing one cached sprite loader with piece sprites); the board
  now stacks *every* visible status on a piece — its declared `icon` sprite when present, else its
  `glyph` — instead of only the first, glyph-only. The proof mod demonstrates both: `proof:glow` ships
  an owned `assets/icons/glow.png`, and a new glyph-only `proof:warded` gives a second visible status,
  so one piece can show a sprite marker and a glyph marker at once. Core still names no status.
- *Slice 7 (done)* — the proof mod now offers a free `proof:glow_up` ability on its prism. A
  normal Prism Arena session can apply `proof:glow`, rendering its owned icon and emitting the
  existing ability cue without a `src/` edit. Owner is scoped `tag_any: [proof:prism]` (a piece with
  no declared `components` defaults to `[its own id]`), so the proof ability does not leak onto other
  mods' pieces the way an empty owner would.
- *Slice 8 (done)* — status and scheduled-event notification kinds are derived once from each
  recorded action list. Base content declares owned WAV cues for status application/expiry and
  event warning/execution; no pipeline site names presentation content.
- Slice 4 (done) — the menu reads each mode row's palette and uses the first deterministic
  catalog palette for page chrome, retaining UI constants only for the empty/unthemed fallback.
- Slice 6 (done) — the read-only Mods screen lists installed mods, flags code-bearing manifests,
  and renders attributed loader errors; failed startup loads remain available to that screen.

**Verified against source on 2026-07-18.** These are confirmed gaps, not speculation:
The remaining M6 gaps are now closed: the runtime consumes declared HUD widgets and status icons,
menus read mode palettes, shell navigation is available, proof content applies a visible status in
play, base and proof cues point at owned WAV assets, and the Mods screen reports installed metadata
and attributed load errors.

**Goal:** make the runtime render every presentation declaration the loader already validates, wire
real audio, give a finished game somewhere to go, and surface the trust and error information the
trust model promises — all without core naming a specific mod, widget, colour, or cue.

### Principle alignment

- **Declared data must be honoured or rejected, never ignored.** A validated `hud_layout` that the
  renderer does not read violates "core owns the loop; mods own what goes in it" — the widget list is
  the mod owning the layout, and today core overrides it. Rendering the declared widgets is the fix.
- **Restart is a fresh session, not an undo.** Returning to menu or restarting a mode starts a new
  action log; it does not reverse the current one, so the action-log invariant is untouched.
- **The mods surface is the trust model paying out, not a mod manager.** It only *reports* enabled
  mods, the manifest code flag, and load errors already produced by the loader. It does not enable,
  disable, reload, or install anything — that stays out of scope per `status.md`.

### Deliverables

- Render the declared `hud_layout` widgets by slot (`turn`/top, `resources`/side, `log`/side,
  `prompt`/bottom) in place of the hardcoded header and log; the `resources` widget draws per-side
  resource values from the read-only snapshot.
- Render status `icon` assets, not only `glyph`, and allow more than one visible status per piece.
- Theme the menu and every shell screen from catalog/mode theme data instead of `ui_constants`
  literals.
- Wire real sound cues: ship non-empty `cues` in base (and proof) using contract-legal WAV/OGG
  assets; retire or convert the unreferenced `sfx/*.mp3`.
- Add explicit shell actions — restart the current mode and return to menu — reachable during play
  and on the outcome screen, each starting a clean session rather than mutating the action log.
- Extend the proof mod to exercise these paths in live play: an ability or effect that applies
  `proof:glow`, a real sound cue, and a sprite/icon asset, so the acceptance fixture proves them by
  play, not only in headless tests.
- Add a minimal mods surface: list enabled mods, flag which ship code as a trust warning, and render
  any load error with mod, file, and field attribution.

### Acceptance criteria

- Editing a mode's `hud_layout` widget list changes the on-screen layout with no `src/` edit; removing
  the `resources` widget removes the panel.
- Base and proof play with audible cues from contract-legal assets; no shipped content references an
  `.mp3` or a missing file.
- From a finished game the player can restart or return to menu without closing the window, and the
  fresh session carries none of the previous session's action log.
- The proof mod visibly applies a status, plays a cue, and shows a sprite or icon during a normal
  session.
- The mods surface names each enabled mod, flags code-bearing mods, and renders any load error with
  full attribution; core still names no specific mod, widget, colour, or cue.

## Milestone 7 — Presentation effects vocabulary ("juice")

**Status:** proposed. Post-v1 presentation depth; does not change the v1 finish definition satisfied
by M5, and depends on M6 rendering the static presentation contract faithfully first. Opt-in — a mode
that declares no effects renders exactly as it does today.

**Goal:** extend the declarative presentation vocabulary so a mod can make the board *move and react*
— animated moves, particle bursts, screenshake, flashes, and transient banners — without any engine
edit, driven entirely by the notifications M3 already defines. The forcing content is a **Full Chaos**
presentation mod (saturated theme, capture/fusion/event particles, screenshake, `FUSION!` banners);
if the vocabulary cannot express it, the vocabulary is incomplete.

Why this is earned, not speculative: the current contract renders a static frame. "Looks like a real
game" is, mechanically, *feedback on state change* — and the project has real content (captures,
fusion, the event pool) that produces nothing visible beyond a glyph swap and a sound. The vocabulary
is added because that content cannot express its own feedback, which is the standard in Scope
discipline, not on speculation.

### Principle alignment (must hold, or the milestone is wrong)

- **Effects are content; core owns the loop.** Core gains a fixed set of effect *primitives* it knows
  how to draw and tick; mods **declare** which notification triggers which primitive with which
  parameters. Core never names a specific effect, cue mapping, colour, or piece. A code mod may
  register a **new** primitive kind through the same public path base content uses, after which every
  data mod can use it as ordinary vocabulary.
- **Effects never touch the action log.** They subscribe to the read-only `PresentationNotification`
  stream emitted *after* a completed action; they emit no actions and mutate no game state. Therefore
  undo stays a pure reversal of the log — an effect the engine has never heard of cannot break it,
  and `undo_completed` is itself just another notification a mod may decorate. This is the
  observation boundary from the presentation spec, unchanged.
- **No parameter is a Python drawing callback.** Effect parameters are data (counts, durations,
  easings, palette-token references). Colours reference the nine theme tokens, never literals.
- **Base and Chaos travel the same path.** The Chaos mod is a third-party-shaped mod, not a core
  branch; `base-chess` may adopt a restrained subset (a move slide, a capture puff) through the
  identical schema.

### Deliverables

- Specify an `effects` (vfx) content type: a declarative map from notification/cue to an ordered list
  of effect descriptors, loaded, validated, patched, and linked through the standard path.
- Define the initial effect primitive set from actual Chaos + base needs — candidates: `slide`
  (tweened move, easing + duration), `particles` (burst: count, spread, lifetime, palette token),
  `shake` (intensity, duration), `flash` (token, duration), `banner` (text template interpolated from
  notification fields, duration). Add a primitive only when the Chaos or base mod cannot render
  without it.
- Extend the read-only presentation snapshot/notification surface with exactly the fields a primitive
  needs (e.g. move start/end squares, captured-square, event id) — no mutation path.
- Give the core render loop an effect scheduler that owns timing, layering, and teardown; mods supply
  only the descriptors. Respect a reduced-motion / effects-off setting.
- Define the action-safe public API for a code mod to register a new effect primitive kind.
- Ship the **Full Chaos** presentation mod as the acceptance fixture, plus a restrained base adoption.

### Acceptance criteria

- The Chaos mod loads through the standard loader; a bad effect field or unknown primitive is an
  attributed load error naming mod, file, and field.
- Undo remains a pure log reversal with effects enabled; no effect appears on the action log, and a
  session with effects disabled is behaviourally identical to one without the mod.
- Core imports and names no concrete effect, cue mapping, colour, piece, or event.
- A data mod expresses the entire Chaos look with zero Python; the one code-registered primitive (if
  any) is then usable from data alone.

## Dependency order

```text
M0 documentation hygiene
  -> M1 contract parity
    -> M2 generic runtime
      -> M3 presentation specification
        -> M4 presentation runtime
          -> M5 independent-mod release proof
            -> M6 presentation fidelity and application shell (post-v1)
              -> M7 presentation effects vocabulary (post-v1, opt-in)
```

Do not pull event triggers, AI, multiplayer, localization, hot reload, distribution, or a full mod
manager into these milestones. They are not required by the approved v1 finish definition. Milestones
6 and 7 are post-v1 presentation-depth additions and are optional to that definition; the M6 mods
surface reports trust and errors but never enables, disables, reloads, or installs a mod.

## Standing constraint — gameplay scope

Expand gameplay only when content earns it. New events or triggers, alternative win conditions, and
additional reusable code-mod verbs are added when real content cannot be expressed without them, never
on speculation — the earned-vocabulary rule from Scope discipline. This is a permanent guardrail on
every milestone above, not a deliverable: none of M6 or M7 introduces a gameplay mechanic, only the
presentation surface that existing mechanics already need.
