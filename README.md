# Chess Fusion

Chess Fusion is a university-level Object-Oriented Programming project built with Python and Pygame.

The current codebase is the **stable advanced-mode baseline** after the event, fusion, Action Points, and active ability implementation phases. It includes:

- standard chess movement and rule handling
- internal move-simulation rollback for legal move validation
- extracted event lifecycle/orchestration
- the full `mode.md` global event pool
- capture-based Fusion resolution with Archbishop, Chancellor, and Tempo Burst
- Action Points tracked separately for both players and displayed on the player panels
- active abilities: Knight Swap, Bishop Snipe, Rook Shield, and Pawn Sprint
- extracted UI rendering and input helpers

Future work can focus on gameplay polish, custom art for fused pieces, and additional UI feedback.

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
uv run python -m unittest discover -s tests/fusion -p "test_*.py" -v
uv run python -m unittest discover -s tests/abilities -p "test_*.py" -v
uv run python -m unittest discover -s tests/pieces -p "test_*.py" -v
uv run python -m unittest discover -s tests/game -p "test_*.py" -v
uv run python -m unittest discover -s tests/events -p "test_*event*.py" -v
uv run python -m unittest discover -s tests/ui -p "test_*.py" -v
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

That document describes the verified advanced-mode baseline.

## Technical Documentation

The focused technical documentation set starts here:

- [docs/system-overview.md](docs/system-overview.md)
- [docs/oop-design.md](docs/oop-design.md)
- [docs/extensibility-and-change-impact.md](docs/extensibility-and-change-impact.md)
- [docs/file-map.md](docs/file-map.md)

Subsystem guides:

- [docs/game-domain.md](docs/game-domain.md)
- [docs/events-system.md](docs/events-system.md)
- [docs/fusion-system.md](docs/fusion-system.md)
- [docs/abilities-system.md](docs/abilities-system.md)
- [docs/ui-and-input.md](docs/ui-and-input.md)

Presentation support:

- [docs/presentation-summary.md](docs/presentation-summary.md)
