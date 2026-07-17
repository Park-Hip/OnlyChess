# Test Map

Tests are part of the refactor's documentation: each group protects a different contract.

| Tests | Contract protected |
|---|---|
| `tests/modding/` | Loader seam plus Wave 2's selected-mod validation, linking, safe sprite lookup, and walking skeleton. |
| `tests/oracle/` | Differential standard-chess behaviour between legacy and replacement engines. |
| `tests/game/`, `tests/pieces/` | Legacy game state, movement, and rule behaviour. |
| `tests/events/`, `tests/fusion/`, `tests/abilities/` | Legacy content mechanisms that later become mod content. |
| `tests/ui/` | Rendering/input behaviour; the UI is presentation, not rule enforcement. |

Run the project command from `AGENTS.md`:

```powershell
python -m pytest
```

Read `docs/refactor/status.md` before choosing a suite for target-engine work. Unit tests prove
local contracts; the oracle is the additional gate for waves that replace chess behaviour.
