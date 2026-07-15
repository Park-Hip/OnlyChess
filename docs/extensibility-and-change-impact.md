# Extensibility and Change Impact

## Purpose

This document explains how easy it is to add or change features in the current Chess Fusion codebase. It uses concrete file-level scenarios instead of claiming that the project is perfectly Open/Closed.

The current design is a practical, basic Open/Closed improvement: common feature additions can be made through focused files such as registries, rule tables, and post-move systems. Some changes still require editing core coordination code, especially when the feature changes turn flow or board state ownership.

## What Counts As Core

For this project, "core" means files that coordinate the whole game or define shared constants used by many systems. These files should not need frequent edits for every new feature:

- `src/main.py`
- `src/game/board.py`
- `src/game/rules.py`
- `src/game/post_move_systems/__init__.py`
- `src/game/move.py`
- `src/constants.py`

Changing these files is not automatically bad, but it has higher impact because these files are close to the main turn loop, board model, move model, or shared names.

## Main Extension Seams

The strongest extension seams are:

- Events: add a concrete event class in `src/events/`.
- Event registry: register and create event classes through `src/events/registry.py`.
- Abilities: add a concrete ability class in `src/abilities/`.
- Ability registry: expose abilities through `src/abilities/registry.py`.
- Fusion rules: add capture-pair mappings in `src/fusion/rules.py`.
- Fused pieces: add fused-piece classes in `src/pieces/fused.py`.
- Piece registry: create pieces by stable code through `src/pieces/registry.py`.
- Ordered post-move systems: add turn-side-effect classes under `src/game/post_move_systems/`.
- UI helpers: update display-only behavior in files such as `src/ui/render_board.py`, `src/ui/render_panels.py`, `src/ui/ability_menu.py`, `src/ui/assets.py`, and `src/ui/ui_constants.py`.

These seams reduce pressure on `GameState` and the move pipeline because many feature changes can be localized to subsystem files.

## Ordered Post-Move Systems

`src/game/rules.py` now keeps the real-move side-effect loop small:

```python
def run_post_move_systems(game_state, move):
    """Run ordered post-move systems that should only happen after real moves."""
    for system in game_state.post_move_systems:
        system.apply(game_state, move)
```

The default order is created in `src/game/post_move_systems/__init__.py`:

- `CaptureTrackingPostMoveSystem`
- `FusionPostMoveSystem`
- `ActionPointsPostMoveSystem`
- `ShieldExpiryPostMoveSystem`
- `EventUpdatePostMoveSystem`

This reduces change pressure because `run_post_move_systems` does not need to grow every time a new post-move rule is added. A new mechanic can usually live in a new `PostMoveSystem` class, then be inserted into the ordered list. That is still a small core edit in `src/game/post_move_systems/__init__.py`, but it is much safer than repeatedly editing a long hardcoded function in `src/game/rules.py`.

## Scenario 1: Add a New Global Event

Example: add a new event that damages all pawns after a warning turn.

Files changed:

- Add `src/events/new_event_name.py`.
- Update `src/events/__init__.py` so the class is imported and registered.
- Update the event pool configuration, currently reached through `src/game/mode_config.py`, if the new event should appear in advanced mode.
- Optionally update UI text or rendering in `src/ui/render_panels.py` if the display needs special wording.

Core impact:

- `GameState`: no direct change expected.
- `run_post_move_systems`: no change expected because `EventUpdatePostMoveSystem` already calls `game_state.event_manager.update()` after full turns.
- `finish_ability_turn`: no direct change expected if ability turns should keep updating events the same way they do now.

Assessment:

This is a strong extension point. The concrete behavior lives in a new event file, and the registry/manager handles creation and timing. The remaining limitation is that adding the event to a mode still requires changing configuration.

## Scenario 2: Add a New Active Ability for an Existing Piece Type

Example: add a new Bishop ability that spends Action Points and affects a target square.

Files changed:

- Add `src/abilities/new_ability_name.py`.
- Update `src/abilities/__init__.py` so the ability class is imported and registered.
- Use `owner_piece_codes` on the ability class to attach it to an existing piece code.
- Optionally update UI presentation in `src/ui/ability_menu.py` if the ability needs special display behavior.

Core impact:

- `GameState`: no direct change expected for normal target-based abilities.
- `run_post_move_systems`: no change expected because active abilities do not use the normal move pipeline.
- `finish_ability_turn`: no change expected if the ability should consume a turn, grant Action Point progress, expire shields, and update events like existing abilities.

Assessment:

This is a good Open/Closed seam for basic active abilities. The `Ability` base class in `src/abilities/base.py` owns the common spending and turn-ending flow. A limitation remains for abilities that need a completely different turn flow; those may require changes in `GameState.finish_ability_turn`.

## Scenario 3: Add a New Fusion Pair That Produces an Existing Fused Result

Example: make a Bishop capturing a Knight also produce the existing Archbishop result.

Files changed:

- Update `FUSION_RESULTS` in `src/fusion/rules.py`.
- No new piece class is needed if the result already exists.
- No `src/pieces/registry.py` change is needed if the fused result code is already registered.

Core impact:

- `GameState`: no direct change expected.
- `run_post_move_systems`: no change expected because `FusionPostMoveSystem` already delegates to `game_state.fusion_manager.handle_move(move)`.
- `finish_ability_turn`: not relevant.

Assessment:

This is one of the cleanest extension cases. The change is a rule-table edit, and fusion resolution already uses the table through `get_fusion_result()` in `src/fusion/rules.py`.

## Scenario 4: Add a Brand-New Fused Piece

Example: add a new fused piece that combines Queen and Knight movement.

Files changed:

- Add a stable piece code in `src/constants.py`.
- Add a class in `src/pieces/fused.py`.
- Update `_PIECE_REGISTRY` in `src/pieces/registry.py`.
- Update `FUSION_RESULTS` in `src/fusion/rules.py`.
- Optionally update sprites or UI assets through `src/ui/assets.py`.

Core impact:

- `GameState`: no direct change expected if the piece follows the existing `Piece` interface.
- `run_post_move_systems`: no change expected because fusion still flows through `FusionPostMoveSystem`.
- `finish_ability_turn`: not relevant unless the new fused piece also introduces a new active ability.

Assessment:

This is a moderate extension point. The piece system supports new classes and registry creation, but adding a new stable code touches `src/constants.py`, which is a core file. This is acceptable for a new piece identity because constants are the shared vocabulary of the game.

## Scenario 5: Add a New Persistent Gameplay Mechanic Across Turns

Example: add a poison status that lasts for three turns and damages affected pieces after each real move.

Files changed:

- Add a state owner such as `src/game/poison_tracker.py`.
- Add a post-move system such as `src/game/post_move_systems/poison.py`.
- Update `src/game/post_move_systems/__init__.py` to insert the system at the correct order.
- Add a field to `GameState` in `src/game/board.py` only if the mechanic needs shared runtime ownership like `shield_tracker`.
- Optionally update UI display files such as `src/ui/render_board.py` or `src/ui/render_panels.py`.

Core impact:

- `GameState`: possible change if the mechanic needs persistent state reachable from abilities, events, or UI.
- `run_post_move_systems`: no change expected because the loop already runs all configured systems.
- `finish_ability_turn`: possible change if the mechanic must also tick after ability turns, because ability turns currently use their own flow instead of calling `run_post_move_systems`.

Assessment:

This is improved but not perfectly Open/Closed. The ordered post-move system keeps the new real-move behavior out of `src/game/rules.py`, but persistent cross-turn state may still need a new `GameState` field. If the mechanic must behave identically after moves and ability turns, `finish_ability_turn` is a remaining change pressure point.

## Scenario 6: Change Only the UI Presentation of an Existing Mechanic

Example: change how active events or shielded pieces are shown without changing the game rules.

Files changed:

- Update `src/ui/render_panels.py`, `src/ui/render_board.py`, `src/ui/ability_menu.py`, `src/ui/assets.py`, or `src/ui/ui_constants.py`, depending on the display area.
- No gameplay subsystem files should change if the rule behavior stays the same.

Core impact:

- `GameState`: no change expected.
- `run_post_move_systems`: no change expected.
- `finish_ability_turn`: no change expected.

Assessment:

This is a strong separation-of-concerns case. Presentation changes can stay in UI helper files. The main risk is accidentally mixing display decisions into gameplay classes; avoiding that keeps the core closed to UI-only changes.

## Scenario 7: Rename or Clean Up the Ordered Post-Move Pipeline Without Changing Behavior

Example: rename `ShieldExpiryPostMoveSystem` to `ShieldExpirationPostMoveSystem` while keeping the same order and behavior.

Files changed:

- Rename or edit the relevant file in `src/game/post_move_systems/`.
- Update imports and class names in `src/game/post_move_systems/__init__.py`.
- Update tests or documentation that reference the old name.

Core impact:

- `GameState`: no behavioral change expected as long as `create_default_post_move_systems(self)` still returns equivalent system objects.
- `run_post_move_systems`: no change expected.
- `finish_ability_turn`: no change expected.

Assessment:

This is a low-risk cleanup if the order and system behavior remain the same. The main thing to protect is the list order in `src/game/post_move_systems/__init__.py`, because order is part of the gameplay contract.

## Honest Open/Closed Assessment

Stronger extension points:

- New events mostly extend `src/events/` and event configuration.
- New active abilities mostly extend `src/abilities/`.
- New fusion pairs can be added through `src/fusion/rules.py`.
- Existing fused piece creation is centralized through `src/pieces/registry.py`.
- Real-move side effects are now separated into ordered post-move systems instead of being hardcoded directly in `src/game/rules.py`.
- UI-only changes can stay in `src/ui/` helper files.

Remaining limits:

- New post-move systems still need registration in `src/game/post_move_systems/__init__.py`.
- New piece identities usually need constants in `src/constants.py`.
- `GameState` in `src/game/board.py` is still the main coordinator, so persistent cross-turn state may still add fields or helper methods there.
- `finish_ability_turn` is separate from `run_post_move_systems`, so mechanics that must happen after both moves and abilities may need careful changes in both flows.
- Core chess rules such as castling, en passant, promotion, and move rollback still live close to `GameState`.

The best honest claim is that the project has practical Open/Closed improvement, not perfect OCP. The code is more open for common extensions and less dependent on editing one large central function, while still staying basic enough for an OOP course project.

## Presentation Answer

If a lecturer asks whether the project follows Open/Closed, a concise answer is:

"The project follows Open/Closed in a practical way, not a perfect theoretical way. Events, abilities, fusion rules, fused pieces, and post-move side effects have clear extension seams, so many new features can be added by creating a new class or updating a small registry or rule table. The ordered post-move pipeline is the clearest improvement because `run_post_move_systems` stays stable while new systems can be added around it. Some core files still change for new piece codes, persistent state, or ability-turn behavior, so the design is honestly more Open/Closed than before, but not completely closed to modification."
