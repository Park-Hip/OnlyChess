# Testing and Verification

Run commands from the repository root.

## Canonical commands

Start the game:

```powershell
uv run python main.py
```

Run all tests:

```powershell
$test_modules = rg --files tests -g 'test_*.py' | ForEach-Object { $_.Replace('\\', '.').Replace('/', '.').Replace('.py', '') }
uv run python -m unittest @test_modules -q
```

The project instructions prefer `python -m pytest` when pytest is available, but the repository's
current documented suite is `unittest` and must run from the repository root.

## Which tests to read

| Change | Start with |
|---|---|
| Loader, IDs, dependencies, patches, errors | `tests/modding/test_loader.py`, `test_parse.py`, `test_registries.py` |
| Public contract and anti-special-case rules | `tests/modding/test_contract_parity.py`, `test_gates.py` |
| Data-defined mode/board | `tests/test_milestone2_runtime.py`, `tests/modding/test_walking_skeleton.py` |
| Movement, promotion, abilities, fusion, events, undo | `tests/test_runtime_cutover.py`, `tests/test_consequence_notifications.py` |
| Themes, HUD, sounds, status icons | `tests/test_hud_rendering.py`, `test_menu_theming.py`, `test_sound_cues.py`, `test_status_icons.py` |
| Mods screen and shell navigation | `tests/test_mods_screen.py`, `test_shell_navigation.py` |

## Test shape

Loader tests normally create temporary mod folders, write manifests/content, call `load()`, and
assert either registries or attributed errors. Runtime tests use `ApplicationContext.load()`, create
an `EngineSession` for a mode, and often use dummy SDL drivers for headless Pygame.

When a test needs a visual guarantee, inspect the rendered surface or use the recording-font/audio
helpers already present in the tests. Do not assert only that a YAML field exists; prove that the
selected content reaches the runtime consumer.

## Before opening a change

- Add a focused success test for new behavior.
- Add an attributed-error test when new content can be malformed.
- Add an undo assertion for every new state-changing path.
- Add a proof-mod or fixture when the public mod surface changes.
- Run the full suite before handoff.

If the local environment cannot run the suite, report the missing dependency or interpreter failure
explicitly; do not claim a passing test run.
