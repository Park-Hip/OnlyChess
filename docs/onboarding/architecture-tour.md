# Architecture Tour

The shortest useful mental model is:

```text
mods/
  → loader
  → registries
  → linked mode
  → EngineState
  → Pipeline
  → action log
  → presentation snapshot/notifications
  → Pygame screens
```

## Important modules

| Module | Responsibility |
|---|---|
| `src/modding/loader.py` | Discovers manifests, resolves dependencies, loads code, validates, patches, normalizes, registers, and links. |
| `src/modding/registries.py` | Runtime registries for content and verbs. |
| `src/modding/validation.py` | Load-time shape and vocabulary validation. |
| `src/modding/linking.py` | Cross-reference checks and linked board/mode structures. |
| `src/modding/patching.py` | `replaces`, `set`, `add`, and `remove` operations before normalization. |
| `src/modding/api.py` | Public trusted code-mod API; currently movement verbs only. |
| `src/engine/factory.py` | Builds a generic `EngineState` from registries and the selected mode. |
| `src/engine/state.py` | Mutable runtime state container; state changes still go through actions. |
| `src/engine/movegen.py` | Generic slide/leap generation and registered move dispatch. |
| `src/engine/pipeline.py` | Applies moves/abilities, runs reactions, advances turns/events, and records actions. |
| `src/engine/actions.py` | Reversible state transitions. |
| `src/engine/events.py` | Data-driven event selection, effects, scheduling, and messages. |
| `src/engine/status.py` | Status movement modifiers, capture protection, and expiry actions. |
| `src/engine/fusion.py` | Fusion reaction over captured pieces. |
| `src/runtime.py` | Application context, mode catalog, session boundary, and presentation observations. |
| `src/ui/presentation_runtime.py` | Resolves mod-owned presentation assets, palettes, widgets, and sounds. |
| `src/ui/screens/engine_game_screen.py` | Generic board input and rendering for the selected mode. |

## Loader to session

`ApplicationContext.load()` calls the loader with validation and linking enabled, activates the
result, and builds the mode catalog. `EngineSession` receives the already-loaded result plus one
mode ID. `build_state()` then constructs definitions and board pieces without knowing chess content.

## Move path

```text
input
  → EngineGameScreen
  → EngineSession.move
  → Pipeline.apply
  → move actions
  → fusion reactions / status expiry / resource gains / scheduled pools
  → RecordMove
  → state.action_log
  → PresentationNotification
```

Move legality uses `Pipeline.legal_moves()`. Candidate moves are simulated by applying and undoing
their actions before the real move is accepted. Threat generation uses the same move primitives with
the threat flag.

## Ability and event path

Abilities are selected by the UI, but their owner, cost, target, condition, and effect come from
content. `Pipeline.use_ability()` builds actions, applies them, advances the turn, expires statuses,
and records the complete operation.

Scheduled events are advanced by the active event pools after a completed move. `EventRunner` selects
pieces, builds effect actions, appends messages, and returns one action list to the pipeline.

## Presentation path

The engine does not call Pygame. After an action, `EngineSession` exposes a read-only
`PresentationSnapshot` and queues immutable `PresentationNotification` values. The screen draws
from the snapshot; `PresentationRuntime` resolves the mode's theme/HUD/sound declarations.

If a presentation feature needs mutable game state, a new notification or snapshot field is needed;
do not make the UI reach into `EngineState` as a shortcut.
