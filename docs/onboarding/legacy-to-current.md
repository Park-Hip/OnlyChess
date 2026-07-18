# Legacy to Current Map

The legacy game was class-driven and core-owned. The current game is data-first and loader-owned.
Use this map before porting an old feature.

| Legacy idea | Current home | What to do now |
|---|---|---|
| Piece subclasses and piece constants | `mods/*/pieces/*.yaml` plus `src/engine/movegen.py` | Define ordinary movement as data. Add a code-mod movement verb only when primitives cannot express it. |
| Event classes and import lists | `mods/*/events/*.yaml`, `event_pool`, `src/engine/events.py` | Define selection/effect/message data. Events enter play through a mode's pool. |
| Hardcoded game modes | `type: game_mode` content and the startup catalog | Add a mode file; do not add a menu branch. |
| Board setup constants | `type: board` content | Define size, sides, starting rows, and promotion ranks in the mod. |
| Ability classes | `type: ability` content and `src/engine/abilities.py` | Compose owner, cost, target, condition, and effect data. |
| AP constants | `type: resource` content and `EngineState` | Define starting value, maximum, and gain rule as resource data. |
| Poison/shield attributes or trackers | `Piece.statuses`, `src/engine/status.py` | Define a status and apply it through an action-producing effect. |
| Fusion manager tables | `type: fusion` content and `src/engine/fusion.py` | Add or patch ordered fusion rules. |
| `@register_event` / `__init__.py` imports | `src/modding/loader.py` discovery and registries | Never add a core import to register content. |
| Direct mutation in effects | `src/engine/actions.py` | Return/apply reversible actions and include them in the record. |
| Fixed piece glyph map | Piece `presentation` and `PresentationRuntime` | Declare `glyph` or an owned PNG sprite in the mod. |
| Fixed panels and colours | `theme` and `hud_layout` content | Use the four current widgets: `turn`, `resources`, `log`, `prompt`. |
| Legacy sound calls | `sound` content and notifications | Map notification names to mod-owned WAV/OGG assets. |
| Old UI reads of game internals | `PresentationSnapshot` and `PresentationNotification` | Add read-only presentation data; do not pass mutable state to UI code. |

## Concepts that changed shape

- A piece identity is a namespaced string such as `base:queen`, not a Python constant.
- A move is a data declaration or registered move verb that produces actions.
- A capture is part of the move pipeline; fusion listens to the recorded capture reaction.
- A status is a `StatusInstance` stored on the piece and expired centrally.
- An event is not a class with its own timer. A pool schedules it, and its steps emit actions.
- Undo reverses the recorded action list. It does not replay effects or recompute random choices.
- Presentation observes immutable snapshots and notifications. It does not own rules or mutation.

## Things not to port from legacy

- Hardcoded `white`/`black` assumptions in engine or UI code
- Content-specific `if` branches such as `if piece_id == ...`
- Import-time registration decorators/lists
- Direct writes to board, piece, status, resource, or turn state
- A new UI panel added directly to `src/` when it could be declared by a mod
- A new general-purpose vocabulary verb without a real content consumer

When an old feature has no current home, write down the missing capability and its smallest public
shape before implementing it.
