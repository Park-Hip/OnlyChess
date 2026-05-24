# Chess Fusion

Chess Fusion is a university-level Object-Oriented Programming project built with Python and Pygame.

The current codebase is the **stable classic-plus-events baseline after Phase 5** of the refactor.  
It includes:

- standard chess movement and rule handling
- internal move-simulation rollback for legal move validation
- extracted event lifecycle/orchestration
- extracted UI rendering and input helpers

It **does not yet include** Fusion resolution, AP, or active abilities. Those systems are intentionally deferred until after this documented baseline.

## Run the Game

Recommended command:

```bash
uv run python run.py
```

Supported compatibility entrypoint:

```bash
uv run python main.py
```

Both wrappers forward to `src.main.main()`, but `run.py` should be treated as the canonical launch command for normal use.

## Run the Regression Suite

Canonical command:

```bash
uv run python -m unittest tests.ui.test_assets tests.ui.test_promotion_menu tests.ui.test_input_handler tests.ui.test_render_board tests.ui.test_render_panels tests.events.test_event_base_contract tests.events.test_event_registry tests.events.test_gia_xang_tang_event tests.events.test_event_manager_flow tests.game.test_castling_helpers tests.game.test_capture_tracker tests.game.test_material_scoring tests.game.test_game_rules_pipeline tests.game.test_board_helpers tests.game.test_board_piece_creation tests.game.test_move_and_undo tests.game.test_pawn_boundaries tests.pieces.test_piece_metadata tests.pieces.test_piece_registry tests.pieces.test_piece_extension_hooks -v
```

## Smoke Test

The project also uses a Pygame dummy-driver smoke test to verify that the app boots cleanly without opening a visible window.

Example:

```bash
uv run python -c "import os; os.environ['SDL_VIDEODRIVER']='dummy'; import pygame as p; p.init(); p.event.post(p.event.Event(p.QUIT)); import run; run.main(); print('smoke-ok')"
```

## Architecture Note

For the current project structure and package responsibilities, see:

- [docs/architecture-current-baseline.md](docs/architecture-current-baseline.md)

That document describes the verified baseline before any Fusion, AP, or advanced-mode implementation begins.
