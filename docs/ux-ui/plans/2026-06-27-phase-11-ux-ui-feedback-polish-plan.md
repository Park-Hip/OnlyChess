# Phase 11: UX/UI Feedback Polish Plan

**Goal:** Make the advanced-mode systems easier to understand while preserving the current game rules and simple OOP structure.

**Architecture:** Add a small message-log model owned by `GameState`, then render it through UI helpers. Keep game-rule logic in the domain layer and visual presentation in `src/ui/`. Avoid introducing a complex event bus or framework.

## Planned File and Folder Structure

```text
src/
+-- game/
¦   +-- board.py                 # Owns GameMessageLog through GameState
¦   +-- message_log.py           # Small bounded message log helper
+-- game/rules.py                # Reports move-side effects at existing seam
+-- events/manager.py            # Reports event warnings/executions
+-- fusion/manager.py            # Reports fusion results
+-- ui/
¦   +-- render_board.py          # Status and tempo-burst overlays
¦   +-- render_panels.py         # Message log and help hints
¦   +-- help_overlay.py          # Rules/help overlay drawing helper
+-- main.py                      # Toggles help overlay and passes UI state

tests/
+-- game/test_message_log.py
+-- ui/test_render_panels.py
+-- ui/test_render_board.py
+-- ui/test_help_overlay.py
```

## Task 1: Add a Small Game Message Log

**Purpose:** Give players a readable history of important gameplay events.

- [ ] Add `src/game/message_log.py` with a bounded `GameMessageLog` class.
- [ ] Add `message_log` to `GameState`.
- [ ] Add tests for adding messages, max-size trimming, and newest-first UI access.

## Task 2: Report Important Gameplay Events

**Purpose:** Let the message log explain what just happened without duplicating rule logic.

- [ ] Report AP gain after real moves and ability turns.
- [ ] Report fusion outcomes, including Tempo Burst.
- [ ] Report event warnings and event execution.
- [ ] Report successful abilities from the main UI flow.

## Task 3: Draw the Message Log and Better Panel Hints

**Purpose:** Make the side panels teach the player while they play.

- [ ] Render recent messages in the top panel.
- [ ] Add a short right-click ability hint.
- [ ] Keep existing AP/captured-piece/event countdown layout readable.
- [ ] Add tests for message-log formatting helpers.

## Task 4: Add Board Status Indicators

**Purpose:** Make status effects visible directly on pieces.

- [ ] Extend board overlays for shield, stun, poison, and Tempo Burst.
- [ ] Keep overlays simple: colored outlines/circles/text markers instead of new art assets.
- [ ] Add helper tests for status marker detection.

## Task 5: Add a Help Overlay

**Purpose:** Give players a quick in-game rule reference without leaving the game.

- [ ] Add `src/ui/help_overlay.py` with static help text sections.
- [ ] Toggle the help overlay with `H` in `src/main.py`.
- [ ] Include controls, fusion pairs, AP/ability costs, and event timing.
- [ ] Add tests for help text content.

## Verification Plan

```bash
uv run python -m unittest tests.game.test_message_log tests.ui.test_render_panels tests.ui.test_render_board tests.ui.test_help_overlay -v
uv run python -m unittest discover -s tests/game -p "test_*.py" -v
uv run python -m unittest discover -s tests/fusion -p "test_*.py" -v
uv run python -m unittest discover -s tests/abilities -p "test_*.py" -v
uv run python -m unittest discover -s tests/events -p "test_*event*.py" -v
uv run python -m unittest discover -s tests/ui -p "test_*.py" -v
```

## Reporting

After implementation, summarize:

- What UX/UI feedback was added.
- Which files changed.
- Which tests passed.
- Any remaining UX polish ideas.
