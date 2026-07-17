# Wave 5: Fusion and Events

**Status:** complete, 2026-07-17. `base:fusion` and `base:events` load alongside `base:chess`
through generic capture, selection, scheduled-event, and reversible-effect machinery.

## What runs as data

- A `FusionResolver` listens to generic displaced-capture events and reads the loaded ordered fusion
  table. It replaces the capturer through a reversible action only when the table matches.
- `EventRunner` selects pieces deterministically from loaded event filters and turns `destroy`,
  `transform`, `set_color`, and `apply_status` declarations into actions.
- Random event selection uses an injected seeded RNG, so tests can reproduce a result.
- Event pools now record a warning-time selected event and execute that same pending event on the
  configured later turn; both the counter and pending selection are reversible actions.
- Warning declarations can bind a seeded random zone. The stored rectangle is supplied to a later
  `scope: { zone: $name }` selector, so execution never rerolls it.
- Warning and per-target execution templates are recorded as reversible event messages.
- Optional loader validation/linking now checks event step shape, pool members, and fusion rule piece
  references before activation.

Wave 6 has since routed the playable game to the new engine and retired the legacy runtime.

## Verification

`tests/engine/test_wave5_data_mods.py` proves a table-driven fusion and a reversible event transform.
The complete suite remains the regression gate.

## Completion evidence

Every shipped base event has deterministic structural execution-and-undo coverage. Fusion tables,
event-pool members, transform/status references, warning-time bindings, pool scheduling, messages,
and the code-mod-to-data-mod vocabulary probe are covered by the Wave 5 tests.

Wave 6 may now begin the playable-runtime cutover.
