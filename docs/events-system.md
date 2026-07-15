# Events System

## Purpose

The events system adds timed special board events to Chess Fusion. Events create advanced-mode surprises while keeping event-specific logic out of the core move engine.

## Responsibility

The events subsystem owns:

- event lifecycle contract
- event registration and creation
- event warning timing
- event execution timing
- active-event ticking and cleanup
- event-specific board effects
- event-specific overlay drawing

## Main Classes And Files

- `src/events/base.py`: `ChessEvent` base contract.
- `src/events/manager.py`: `EventManager`.
- `src/events/registry.py`: event registry helpers.
- `src/game/mode_config.py`: default advanced-mode event pool.
- concrete event files under `src/events/`: implemented events.
- `src/ui/render_board.py`: draws active event overlays by calling event draw hooks.

## `ChessEvent` Contract

`ChessEvent` defines:

- `event_key`
- `name`
- `duration`
- `warning_active`
- `trigger_warning()`
- `execute()`
- `cleanup()`
- `tick()`
- `draw(screen, font, width, height, info_panel_height)`

Concrete events override the methods they need. The base implementation provides default warning and execution state changes, plus empty hooks for cleanup, ticking, and drawing.

## Registry-Based Event Creation

`src/events/registry.py` uses a simple dictionary:

- `register_event(event_class)` stores a concrete class by `event_key`
- `get_event_class(event_key)` returns the class
- `create_event(event_key, game_state)` constructs the event
- `get_registered_event_keys()` lists registered keys
- `choose_random_event_key(event_keys)` chooses from the configured pool

This is a basic registry, not a complex factory framework. It keeps event creation out of `GameState` and lets the manager work with stable event keys instead of importing every event class directly.

## Event Manager Lifecycle

`EventManager` stores:

- `turn_counter`
- `active_events`
- `queued_event`
- `queued_event_key`
- `event_pool`

On update:

1. it reads the completed full-turn count from `GameState`
2. it ticks active events after play has started
3. it triggers a warning when the full-turn count reaches the warning timing
4. it executes the queued event at execution timing
5. it cleans up zero-duration events immediately
6. it queues the next event from the pool

The manager coordinates timing only. Concrete event classes own the actual board effect, duration behavior, cleanup details, and overlay drawing.

## Timing

The current manager warns before a 10-turn boundary and executes on the 10-turn boundary. In code, warning happens when `turn_counter % 10 == 9`, and execution happens when `turn_counter % 10 == 0`.

`EventManager` relies on `GameState.get_full_turn_count()`. It is updated by post-move systems after real moves, plus by `GameState.finish_ability_turn()` when an ability completes a full turn.

## Interactions With Board State And UI

Events can read and mutate `GameState` through the game-state reference passed into each event. For example, concrete events may replace pieces, apply temporary piece status, clear those statuses during cleanup, or draw warning text and board overlays.

UI rendering does not implement event rules. `src/ui/render_board.py` draws event overlays by calling `draw_event_overlays()`, which loops through `active_events` and calls each event's `draw()` hook.

## Implemented Events

Concrete events live in `src/events/` and are covered by `tests/events/`. The current files include:

- `comeout.py`
- `gia_xang_tang.py`
- `kho_ga_tron_ba_mia.py`
- `long_toi_tan_nat_khi_nhan_ra_toi_la_gay.py`
- `mat_quyen_cong_dan.py`
- `my_danh_iran.py`
- `nguoi_chong_bat_luc.py`
- `tai_xiu.py`
- `umamusume.py`
- `viec_nhe_vol_cao.py`

Use the event files and matching tests for exact behavior when presenting or debugging a specific event.

## How To Add A New Event Safely

1. Create a new concrete event file under `src/events/`.
2. Inherit from `ChessEvent`.
3. Set a stable `event_key`.
4. Set a clear `name` and any duration constants needed by the event.
5. Implement warning, execution, ticking, cleanup, or drawing behavior as needed.
6. Register the event using the existing `@register_event` pattern used by other event files.
7. Import the event from `src/events/__init__.py` so registration happens when the package loads.
8. Add the event key to `src/game/mode_config.py` if it should be in the default advanced-mode event pool.
9. Add focused tests under `tests/events/`.

Keep new event logic inside the event class unless the feature needs a shared rule or helper. Avoid changing `GameState`, move execution, or UI rendering just to add a normal event.

## OOP Design Notes

The event subsystem uses inheritance for a shared lifecycle contract and composition through `EventManager`. Concrete events own behavior; the manager owns timing.

This is intentionally basic OOP. The design uses one base class, concrete subclasses, and a direct registry. It avoids heavy event buses, large factory layers, and complex dependency injection.

## Extension Points

- new event class
- new event key in the default event pool
- event-specific drawing hook
- event-specific cleanup behavior
- event-specific duration and ticking behavior
- tests for event warnings, execution, cleanup, and board effects

## Change Impact

Adding a normal event should not require changes to `GameState`, move execution, or `run_post_move_systems()`. The new behavior should usually stay in one concrete event file, `src/events/__init__.py`, `src/game/mode_config.py`, and matching tests.

Changing global timing rules requires editing `EventManager` and its tests. Changing how overlays are generally drawn may require UI changes in `src/ui/render_board.py`, but event-specific overlay content should stay in the event's `draw()` method.

## Risks And Limitations

Events can mutate game state through `GameState`, so concrete event code should stay focused and covered by tests. Event behavior should not duplicate core movement validation unless the event specifically changes movement rules.

The manager uses one queued event at a time from the configured pool. If the game later needs multiple queued events, player-selected events, or more complex timing, `EventManager` will need a careful redesign and additional tests.
