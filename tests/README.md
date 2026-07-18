# Test Map

Tests are part of the refactor's documentation: each group protects a different contract.

| Tests | Contract protected |
|---|---|
| `tests/modding/` | Loader, parser, validation, linking, registries, code-mod API, and mod-owned asset preview. |
| `tests/engine/` | Data-defined movement, actions, abilities, fusion, status expiry, events, and undo. |
| `tests/oracle/` | New-engine standard-chess perft and differential behaviour checks. |
| `tests/test_runtime_cutover.py` | Application-facing sessions: vanilla/advanced modes, promotion, abilities, and undo. |

Run the canonical project verification command from the repository root:

```powershell
$test_modules = rg --files tests -g 'test_*.py' | ForEach-Object { $_.Replace('\\', '.').Replace('/', '.').Replace('.py', '') }
uv run python -m unittest @test_modules -q
```

The command uses the declared project dependencies and discovers all active suites. Read
`docs/refactor/status.md` before choosing a focused suite for target-engine work. Unit tests prove
local contracts; the oracle is the additional gate for standard-chess behaviour.
