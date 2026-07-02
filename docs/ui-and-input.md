# UI And Input

## Purpose

This document explains how the Pygame UI is separated from gameplay rules. The UI presents state, collects player intent, and delegates rule decisions to game-domain and ability code.

The UI layer is intentionally small and helper-based. It should make the game readable for a university OOP project without turning the interface into a heavy framework.

## Responsibility

The UI layer owns:

- transient click and drag state
- board-square conversion from mouse coordinates
- promotion menu display and click resolution
- ability menu display and click resolution
- board drawing
- piece drawing
- selected-square, legal-target, and last-move highlights
- shield overlays
- event overlays
- player panels
- captured-piece rows
- AP text
- the message log panel
- the help overlay

The UI layer does not own legal move rules, event rules, fusion rules, or ability effects. Those decisions belong in domain, event, fusion, and ability modules.

## Main Classes And Files

- `src/main.py`: Pygame entry point. It initializes the game, receives Pygame events, calls input helpers, delegates real moves and abilities, and calls rendering helpers each frame.
- `src/ui/input_handler.py`: Defines `InputState` and functions for click selection, drag release, board-square conversion, promotion state, ability state, and move or ability attempt readiness.
- `src/ui/render_board.py`: Draws the board, pieces, highlights, shield overlays, dragged pieces, event overlays, and endgame text.
- `src/ui/render_panels.py`: Draws player panels, captured rows, material advantage text, AP text, and event countdown text. It also exposes `get_ability_error_text()` for transient ability errors.
- `src/ui/message_log.py`: Defines `MessageLog` (scrollable move/ability/event history), draws the log side panel and help button, and formats move and ability entries.
- `src/ui/help_overlay.py`: Draws the modal help overlay and resolves its close control.
- `src/ui/ability_menu.py`: Positions and draws the ability menu, finds affordable ability keys, and resolves ability-menu clicks.
- `src/ui/promotion_menu.py`: Positions and draws the promotion menu and resolves promotion-choice clicks.
- `src/ui/assets.py`: Loads piece images and maps sprite keys to image assets.
- `src/ui/ui_constants.py`: Stores UI-only colors and display constants.

## Input Flow

1. `src/main.py` reads Pygame events from `p.event.get()`.
2. Mouse down, motion, and mouse up events update `InputState` through `src.ui.input_handler`.
3. Normal board clicks and drags become source and target squares in `InputState.player_clicks`.
4. `move_attempt_ready(input_state)` returns true when two board squares are ready.
5. `process_move_attempt(input_state, game_state, valid_moves)` creates a `Move` from the selected squares and compares it with moves from `GameState.get_valid_moves()`.
6. If the matching valid move is a promotion, the UI stores it as promotion pending with `set_promotion_pending()` and waits for a promotion-menu click.
7. If the matching valid move is not a promotion, `GameState.make_move(valid_move, is_real_move=True)` performs the real move.
8. Right-clicking any friendly piece stores an ability-menu source square.
9. Clicking an ability stores the ability key and source square in `InputState`.
10. Clicking a target square makes `ability_attempt_ready(input_state)` true.
11. `process_ability_attempt(input_state, game_state)` calls `use_ability()` with the selected key, source square, and target square.

This means input helpers package user intent. They do not decide whether a chess move, event effect, fusion result, or ability target is legally valid.

## Promotion Menu Behavior

Promotion is detected only after a move has already matched one of `GameState.get_valid_moves()`. The matching move carries `is_pawn_promotion`, so `process_move_attempt()` stores it in `InputState.promotion_move_pending`.

While promotion is pending, board drag-release updates are ignored. A later click is resolved by `resolve_promotion_click()`. If the click is inside the promotion menu, `handle_promotion_click()` passes the chosen piece code to `GameState.make_move()`, clears the pending promotion state, and resets selection state.

The UI chooses the promotion option visually. The game layer still applies the move and owns the final board update.

## Ability Menu Behavior

A right-click on any friendly piece stores `InputState.ability_menu_square`. `draw_ability_menu()` uses the selected piece and `get_available_ability_keys()` to show affordable ability keys. As a current limitation, a friendly piece with no affordable abilities can still become the selected menu source, but the menu has no options to draw or resolve. The menu does not execute abilities directly.

When the player clicks an ability menu item, `resolve_ability_menu_click()` returns an ability key. `select_ability()` stores that key and the source square in `InputState`. The next board click becomes the target square. `process_ability_attempt()` then calls `use_ability()`.

If `use_ability()` succeeds, ability and selection state are cleared. If it fails, `InputState.ability_error` is set to `"Invalid ability target"`. `src.main.main()` renders that temporary error near the board using text exposed by `get_ability_error_text()`.

## Rendering Flow

Each frame, `src/main.py` redraws the visible game state in a fixed order:

1. `draw_game_board()` draws the board, highlights, pieces, shield overlays, and dragged piece if needed.
2. `draw_info_panels()` draws player panels, captured rows, AP text, turn text, and event countdown text.
3. `draw_message_log()` draws the scrollable move/ability/event log side panel and help button.
4. `src.main.main()` renders any transient ability error near the board using `get_ability_error_text()`.
5. `draw_promotion_menu()` draws the promotion menu when a promotion is pending.
6. `draw_ability_menu()` draws the ability menu when an ability source square is selected.
7. `draw_event_overlays()` delegates overlay drawing to active event objects.
8. `draw_endgame_text()` draws checkmate or stalemate text over the board.
9. `draw_help_overlay()` draws the modal help screen when it is toggled on.

Rendering reads public game state and display-oriented fields. It should not modify gameplay state except through explicit input flows handled by `src/main.py`.

## Interactions With Other Subsystems

- Game domain: UI asks `GameState.get_valid_moves()` for legal moves and calls `GameState.make_move()` for accepted real moves.
- Pieces: UI renders pieces through sprite keys returned by piece objects.
- Fusion: fused pieces render through their sprite keys like any other piece, while fusion eligibility and results stay in `src/fusion/`.
- Events: UI calls event drawing hooks through `draw_event_overlays()`, while event rules and timing stay in `src/events/`.
- Abilities: UI shows available ability keys and target intent, while ability validation, AP spending, and effects stay in `src/abilities/`.
- Action Points: UI renders AP values through panel helpers, while AP storage and spending rules stay in the game and ability layers.

## OOP Design Notes

The UI uses focused modules instead of one large UI class. `InputState` groups transient interaction fields in one simple data object. Rendering functions are separated by display responsibility: board, panels, ability menu, promotion menu, and assets.

This is a basic Single Responsibility design. `src/main.py` remains the orchestrator, while helper modules own small UI tasks. The design avoids a God Object without adding complex patterns that would be difficult to explain in an OOP course presentation.

## Extension Points

- Add a new board highlight style in `src/ui/render_board.py`.
- Add new panel text in `src/ui/render_panels.py` when the text reflects already-existing public game state.
- Change ability menu appearance or placement in `src/ui/ability_menu.py`.
- Change promotion menu appearance or placement in `src/ui/promotion_menu.py`.
- Add or update sprite loading in `src/ui/assets.py`.
- Add UI tests in `tests/ui/` for input state, menu resolution, and rendering helpers.

Changes that alter what moves or abilities are legal must be implemented in domain or ability code, not UI rendering or input helpers.

## Change Impact

UI-only presentation changes should usually stay inside `src/ui/` and matching `tests/ui/`. Examples include changing colors, drawing extra text, repositioning menus, or adjusting highlight behavior.

Input behavior changes can affect `InputState`, `src/main.py`, and UI tests because the main loop coordinates when a packaged intent becomes a real domain call.

Gameplay changes have a wider impact. Legal move rules belong in `GameState` and piece classes. Event rules belong in event classes and the event manager. Fusion rules belong in fusion modules. Ability effects belong in ability classes.

## Risks And Limitations

The main loop wires many pieces together: Pygame events, `InputState`, move attempts, promotion handling, ability handling, rendering, and endgame display. Future UI changes should stay in helpers so `src/main.py` remains orchestration code rather than a place for new rules.

The current ability menu lists ability keys directly. That is simple and testable, but a more polished UI may later need display names or descriptions from the ability layer.

The UI consumes some public runtime state directly for display. That is acceptable for a small Pygame project, but rule decisions should continue to stay outside the UI layer.
