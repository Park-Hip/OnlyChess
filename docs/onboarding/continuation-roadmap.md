# Continuation Roadmap

Use this page to decide what to work on after onboarding. The detailed historical sequence is in
[refactor milestones](../refactor/milestones.md); this page is the practical current direction.

## Current position

Milestones 0–6 are treated as delivered in the runtime and documentation. The current product can:

- load namespaced data mods and trusted code mods;
- expose arbitrary linked game modes in the menu;
- run data-defined pieces, abilities, statuses, resources, fusion, and scheduled events;
- record reversible actions and undo a complete operation;
- render mod-owned themes, glyphs/sprites, status markers, sounds, and the four built-in HUD widgets;
- report installed-mod trust metadata and attributed load errors.

The project is not finished in the broad “anything can be a mod” sense. The current presentation and
code vocabularies are intentionally small.

## Known gaps to close or consciously accept

These are the gaps a new contributor should know before choosing a feature:

| Gap | Current state | Decision needed |
|---|---|---|
| `engine:` compatibility | Manifest range syntax is validated, but the loader does not enforce it against the running engine version. | Implement enforcement or explicitly defer it. |
| Code-mod verbs | `ModApi` exposes `move_type` only. | Add a verb only when real content needs it. |
| Event triggers | Events run from pools; “on capture” and “on turn start” are not data vocabulary. | Design a trigger contract only for an earned use case. |
| Custom HUD | Mods arrange `turn`, `resources`, `log`, and `prompt`; they cannot add a widget. | Add declarative widget registration if a real mod needs it. |
| Clock | No clock state, timer action, snapshot field, or clock widget exists. | Define timing, pause, undo, restart, and multiplayer semantics first. |
| Piece annotations | Glyph/sprite and status markers exist; arbitrary text or per-piece visual colour does not. | Define a small overlay/label contract before adding renderer branches. |
| Presentation effects | Static presentation and sounds exist; particles, banners, animation, and screenshake are proposed as M7. | Continue with M7 only after static presentation remains stable. |
| Installation | Mods are manually placed under `mods/`; no installer, marketplace, hot reload, or enable/disable UI exists. | Out of scope unless product direction changes. |

## Release gate before feature work

The current branch is suitable for a developer preview only until these checks are closed or explicitly
accepted by the project owner:

1. Recreate the environment from a clean checkout and run the complete documented test command. A local
   audit on 2026-07-18 could not do this because `uv` could not use the repository `.venv`, and the
   system Python did not have the declared dependencies. This is an unverified release gate, not proof
   that the tests are failing.
2. Enforce `manifest.yaml`'s `engine:` range against `src/modding/loader.py:ENGINE_VERSION`, with an
   attributed load error and regression tests. The syntax is currently checked but compatibility is
   not enforced.
3. Run [manual-release-checklist.md](../refactor/manual-release-checklist.md) from that clean setup.
4. Choose the release audience. Manual Python/`uv` setup and folder-based mod installation are fine for
   contributors; a general-player release needs packaging and an installation story.

Ugly visuals are not a sign-off blocker while the game remains readable and the interaction checklist
passes. The incomplete presentation vocabulary is a sign-off blocker only if the release claims that
modders can add arbitrary UI or presentation features.

## Recommended milestone order

### M8 — Contract and developer-experience hardening

Do this before adding a large feature.

- Reconcile the M1 acceptance text with the actual loader, especially `engine:` enforcement; do not
  mark M1 fully complete while the compatibility gate is missing.
- Make the clean-checkout dependency setup reproducible, then run the complete suite and repair the
  project setup if it cannot start.
- Add focused tests for every documented current limitation that must not silently change.
- Keep `status.md`, the specs, and the onboarding roadmap synchronized.
- Add a small fixture or proof-mod assertion for every new public extension surface.

Done means a new contributor can install dependencies, run the suite, identify the relevant contract,
and get an attributed failure instead of a late runtime error.

### M9 — First contributor feature

The first feature should exercise the complete public path without requiring a large redesign. Good
choices are:

- a new data-defined piece and mode in a temporary fixture;
- a new status with a visible glyph/icon;
- a new code-defined movement verb plus a data piece that uses it;
- an improvement to loader diagnostics.

The feature must include content, a focused test, an undo check if state changes, and a status/spec
update if the public contract changed. This is the best way for the new coder to learn the project
with you rather than by reading every file first.

### M10 — Clock and richer presentation, if still wanted

Treat a clock as an engine-plus-presentation feature, not just a HUD label.

Plan the contract before coding:

1. Define clock ownership, start time, pause behavior, active-side behavior, and expiration outcome.
2. Define clock state as reversible actions so undo/restart semantics are explicit.
3. Add read-only clock data to `PresentationSnapshot`.
4. Add a declarative clock widget or a registered widget vocabulary.
5. Add a proof mod/mode that uses it without editing core content names.
6. Test headlessly and manually, including undo, restart, menu return, and terminal timeout.

Do not implement a clock by reading wall time directly from the renderer or by adding a hardcoded
clock panel to `EngineGameScreen`.

### M11 — Piece overlays and presentation effects

Only start this after M10 or another real mod demonstrates the need.

Potential scope:

- declarative per-piece visual colour/palette selection;
- short text labels or multi-character annotations;
- notification-driven animation primitives;
- reduced-motion/effects-off behavior;
- a data-only acceptance mod.

Keep these as read-only presentation effects. They must not mutate engine state or enter the action
log.

### M12 — Earned gameplay vocabulary

Add triggers, effects, selectors, conditions, or status modifiers only when a concrete mod cannot be
written without them. Each new verb needs:

- a public API shape;
- load-time validation;
- an action-safe execution path;
- an undo test;
- a data-mod consumer;
- documentation and an attributed-error test.

Do not build a general scripting language or speculative health/arithmetic system as a milestone.

## Contribution loop

For every milestone-sized change:

```text
real use case
  → smallest public contract
  → failing acceptance test
  → data/mod fixture
  → core implementation
  → undo/error/presentation verification
  → docs and status update
```

The base mods and the proof mod are acceptance consumers, not privileged implementation shortcuts.
If the feature only works after adding a base-specific branch, stop and redesign the extension seam.

## What the new coder should do first

1. Read the onboarding set.
2. Run the application and inspect Standard Chess, Advanced, Prism Arena, and Mods.
3. Run the full test command.
4. Trace one move from the screen to `Pipeline.apply()` and one status through undo.
5. Make one small proof-mod/data change with a focused test.
6. Choose M8 or a small M9 feature with the project owner before starting a larger branch.
