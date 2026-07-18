# Test Map

Tests are part of the refactor's documentation: each group protects a different contract.

| Tests | Contract protected |
|---|---|
| `tests/modding/` | Loader, parser, validation, linking, registries, code-mod API, and mod-owned asset preview. |
| `tests/engine/` | Data-defined movement, actions, abilities, fusion, status expiry, events, and undo. |
| `tests/oracle/` | New-engine standard-chess perft and differential behaviour checks. |
| `tests/test_runtime_cutover.py` | Application-facing sessions: vanilla/advanced modes, promotion, abilities, and undo. |
| `tests/test_ui_interactions.py` | The same rules reached through `EngineGameScreen.handle_event`: selection, castling, en passant, the promotion prompt, the ability modal, fusion, and undo. |

The last two rows are deliberately not redundant. The cutover tests call `EngineSession` directly, so
they prove the engine is right; the interaction tests prove the screen reaches it. A break in square
hit-testing, selection state, or the ability modal leaves the first group green and the game unplayable.

Run the canonical project verification command from the repository root:

```powershell
$test_modules = rg --files tests -g 'test_*.py' | ForEach-Object { $_.Replace('\\', '.').Replace('/', '.').Replace('.py', '') }
uv run python -m unittest @test_modules -q
```

The POSIX equivalent, which needs neither `uv` nor `rg`:

```bash
MODS=$(find tests -name 'test_*.py' | sed 's|/|.|g; s|\.py$||' | sort)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest $MODS -q
```

The dummy SDL drivers let the Pygame suites run without a display or an audio device. Do not use
`uv run` for a focused module: it drops the repository root from `sys.path` and every test dies with
`ModuleNotFoundError: No module named 'src'`.

The command uses the declared project dependencies and discovers all active suites. Read
`docs/refactor/status.md` before choosing a focused suite for target-engine work. Unit tests prove
local contracts; the oracle is the additional gate for standard-chess behaviour.
