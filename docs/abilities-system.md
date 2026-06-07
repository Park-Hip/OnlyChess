# Abilities System

## Purpose

The abilities system adds AP-backed active abilities to Chess Fusion without putting all special rules in `GameState` or the UI. Each ability owns its own target rules and effect, while the game layer owns shared turn state and Action Point storage.

This keeps active abilities easy to extend: a normal new ability should usually be added as a new class in `src/abilities/`, then registered through the existing registry pattern.

## Responsibility

The abilities subsystem is responsible for:

- ability registration and lookup
- AP cost checks before use
- ownership checks based on standard piece codes and fusion tags
- target validation for each ability
- ability effects such as moving, swapping, shielding, or capturing pieces
- public execution through `use_ability()`

AP storage is owned by `ActionPointTracker` in the game layer. Abilities ask the tracker whether AP can be spent, then spend AP only after all common checks and target validation pass.

The abilities subsystem is not responsible for:

- standard chess move validation
- standard move post-processing
- rendering the board
- mouse input handling
- capture-triggered fusion resolution

## Main Classes And Files

- `src/game/action_points.py`: defines `ActionPointTracker`, which stores AP and completed move counts by color.
- `src/abilities/base.py`: defines the `Ability` base class and shared execution checks.
- `src/abilities/registry.py`: stores registered ability instances and exposes lookup helpers plus `use_ability()`.
- `src/abilities/knight_swap.py`: defines `KnightSwap`.
- `src/abilities/bishop_snipe.py`: defines `BishopSnipe`.
- `src/abilities/rook_shield.py`: defines `RookShield`.
- `src/abilities/pawn_sprint.py`: defines `PawnSprint`.
- `src/game/board.py`: defines `GameState.finish_ability_turn()`, the completion path after a successful ability.
- `src/ui/ability_menu.py`: lists affordable abilities for the selected piece and resolves ability menu clicks.

## Action Points

Action Points are stored by color in `ActionPointTracker.ap_by_color`. The tracker also stores completed move counts by color in `move_count_by_color`.

Important methods:

- `get_ap(color)`: returns the current AP for a player.
- `get_move_count(color)`: returns the player's completed move count.
- `can_spend(color, amount)`: checks whether the player has enough AP.
- `spend(color, amount)`: subtracts AP if the player can afford the amount.
- `gain_for_move(color)`: records one completed move and may gain AP when the configured interval is reached.

Standard moves gain AP through the post-move system in `src/game/post_move_systems/action_points.py`. That system calls `game_state.action_points.gain_for_move(move.piece_moved.color)` after a real move.

Successful abilities spend AP first, apply their effect, then call `GameState.finish_ability_turn(color)`. `finish_ability_turn()` records ability-turn progress by calling `action_points.gain_for_move(color)`, appending an ability entry to `move_log`, switching the turn, expiring shields, and updating events when a full turn has completed.

## Ability Base Class

`Ability` in `src/abilities/base.py` is the shared contract for active abilities.

Class fields:

- `ability_key`: stable internal key used by the registry and UI.
- `display_name`: human-readable name for presentation.
- `ap_cost`: AP required to use the ability.
- `owner_piece_codes`: piece codes that grant access to the ability.

Main methods:

- `can_use(game_state, piece)`: verifies that a piece exists, no ability is already being used in the current turn, the owner can afford the AP cost, and the piece has the needed ability access.
- `use(game_state, piece, target_square)`: runs common checks, validates the target, spends AP, applies the ability, and finishes the ability turn.
- `is_valid_target(game_state, piece, target_square)`: implemented by each concrete ability to decide whether the selected target square is legal.
- `apply(game_state, piece, target_square)`: implemented by each concrete ability to mutate game state.

The ownership check uses `piece.get_fusion_tags()`. This means a standard piece can use the ability for its own code, and a fused piece can inherit ability access from any component tag listed in `owner_piece_codes`.

## Ability Registry

`src/abilities/registry.py` uses a simple dictionary of ability instances keyed by `ability_key`.

Registry helpers:

- `register_ability(ability_class)`: decorator that creates and stores one ability instance.
- `get_ability(ability_key)`: returns a registered ability instance.
- `get_registered_ability_keys()`: returns all registered keys.
- `get_abilities_for_piece(piece)`: returns abilities available to a piece through standard or fused identity.
- `use_ability(ability_key, game_state, source_square, target_square)`: public execution helper used by callers that know the source and target squares.

`use_ability()` reads the source piece from `game_state.board`, then delegates the rule checks and effect to the registered `Ability` instance. This keeps public ability use out of UI code and avoids adding every ability rule to `GameState`.

## Current Abilities

`KnightSwap`:

- key: `knight_swap`
- AP cost: 2
- owner code: knight
- effect: swaps the knight with a friendly target piece and updates cached king positions if needed

`BishopSnipe`:

- key: `bishop_snipe`
- AP cost: 3
- owner code: bishop
- effect: captures an unshielded enemy on an unobstructed diagonal without moving the bishop
- capture summary: records the captured piece through `capture_tracker`

`RookShield`:

- key: `rook_shield`
- AP cost: 3
- owner code: rook
- effect: shields the rook and adjacent friendly pieces for one opponent turn

`PawnSprint`:

- key: `pawn_sprint`
- AP cost: 1
- owner code: pawn
- effect: moves a pawn up to three clear forward squares and promotes to a queen if it reaches the promotion row
- special limit: requires the current piece code to still be a pawn, so fused pieces that only inherit a pawn tag do not automatically become valid Pawn Sprint users unless they are also pawn-coded

Fused pieces can inherit ability access through fusion tags. For example, a fused piece with knight and bishop tags can appear in both `KnightSwap` and `BishopSnipe` lookup results.

## Ability Turn Flow

The ability turn path is separate from normal move execution:

1. The UI selects a piece and calls `src/ui/ability_menu.py` helpers to show affordable ability keys.
2. The player chooses an ability key from the menu.
3. Input handling passes the ability key, source square, and target square to `src.abilities.registry.use_ability()`.
4. `use_ability()` gets the source piece from the board.
5. The registered `Ability.use()` method calls `can_use()`.
6. `Ability.use()` calls the concrete ability's `is_valid_target()`.
7. If the target is valid, `Ability.use()` spends AP through `ActionPointTracker.spend()`.
8. The concrete ability's `apply()` method mutates the board or trackers.
9. `Ability.use()` calls `GameState.finish_ability_turn(piece.color)`.
10. `finish_ability_turn()` records the ability turn, awards move-count AP progress, switches the active side, expires shields, and updates events when needed.

## Interactions With Move Flow And Capture Summaries

Standard moves go through `GameState.make_move(..., is_real_move=True)` and then the ordered post-move systems. Those systems handle capture tracking, fusion, AP gain, shield expiry, and event updates.

Abilities use a separate completion path through `finish_ability_turn()`. They do not create a normal `Move` object, and they do not run the exact `run_post_move_systems()` pipeline.

Some abilities can capture or update summaries themselves. `BishopSnipe` removes the target piece and records it with `capture_tracker.record_capture()`, so the captured-piece summary can still reflect the ability capture.

Ability captures do not currently trigger fusion. Capture-triggered fusion is handled by the normal move post-move fusion system, and ability turns bypass that system.

## OOP Design Notes

The system uses basic OOP:

- `Ability` defines a shared contract.
- concrete ability classes own their own target rules and effects.
- `ActionPointTracker` owns AP state.
- the registry owns ability discovery and public lookup.
- `GameState` coordinates turn completion without owning concrete ability behavior.
- the UI displays available options but does not decide ability legality.

This design keeps responsibilities separated without adding a complex framework. It is a simple base class plus concrete subclasses and a registry.

## Extension Points For Adding A Normal Ability

To add a normal ability:

1. Create a new file under `src/abilities/`.
2. Create a class that inherits from `Ability`.
3. Set `ability_key`, `display_name`, `ap_cost`, and `owner_piece_codes`.
4. Implement `is_valid_target()` for the ability's target rules.
5. Implement `apply()` for the board or tracker effect.
6. Add `@register_ability` above the class.
7. Import the class in `src/abilities/__init__.py` so registration happens.
8. Add focused tests under `tests/abilities/`.

Most normal abilities should not require edits to `GameState`, `Board`, or UI rendering. UI changes are only needed when an ability needs a new input style beyond selecting a source square, ability key, and target square.

## Change Impact

Adding a normal ability should mostly affect:

- one new concrete ability file
- `src/abilities/__init__.py`
- tests under `tests/abilities/`

Changing `Ability.use()` affects every active ability because it controls shared AP spending, target validation order, and turn completion.

Changing `ActionPointTracker` affects both standard move AP gain and ability AP spending.

Changing `get_abilities_for_piece()` affects standard and fused pieces because ability access is based on `get_fusion_tags()`.

Changing `finish_ability_turn()` affects ability turn order, AP progress, shield expiry, event timing, and move-log counting.

## Risks And Limitations

`finish_ability_turn()` is separate from exact standard move post-processing. This keeps abilities distinct from regular chess moves, but it also means ability turns must be reviewed separately when changing capture tracking, fusion, AP gain, shield expiry, or event timing.

Ability captures do not currently trigger fusion because they bypass the normal fusion post-move system. If future rules require ability-triggered fusion, that behavior should be added deliberately with tests instead of relying on the current move pipeline.

The current UI lists affordable abilities by ability key. It checks AP affordability before showing options, while the domain layer still performs the authoritative AP and legality checks in `Ability.use()`.

`PawnSprint` has stricter use rules than normal fusion-tag inheritance because it requires the current piece code to be a pawn. This is intentional in the current code, but it is a detail to remember when explaining fused-piece ability access.
