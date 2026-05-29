# Chess Fusion

Chess Fusion is a university-level Object-Oriented Programming project built with Python and Pygame.

The current codebase is the **stable event-complete baseline** after the full `mode.md` global event pool has been implemented. It includes:

- standard chess movement and rule handling
- internal move-simulation rollback for legal move validation
- extracted event lifecycle/orchestration
- the full 10-event `mode.md` global event pool
- extracted UI rendering and input helpers

Fusion, Action Points, and active piece abilities are not part of this checkpoint.

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

That document describes the verified event-complete baseline.
