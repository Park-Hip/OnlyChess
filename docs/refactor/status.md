# Current Runtime Status

**State:** the mod-driven engine is the only playable runtime. The former hardcoded runtime and
its implementation-specific tests have been removed.

## Supported now

| Area | Current behavior |
|---|---|
| Loading | Discovers enabled mods, loads trusted code mods, validates, registers, links, and activates content. |
| Rules | Data-defined slide/leap movement plus code-mod castle and en-passant verbs. |
| Turns and undo | Every completed move, ability, fusion reaction, status expiry, and scheduled event is recorded as reversible actions. |
| Modes | `base:vanilla` loads standard chess; `base:advanced` additionally activates fusion and events. |
| Content | Pieces, boards, modes, abilities, resources, statuses, fusion tables, event pools, and events load from mods. |
| UI | The Pygame screen selects moves, abilities, promotion choices, and undo; it renders glyphs rather than mod assets. |

## Deliberate current limits

- Mod sprites, sounds, themes, and HUD elements are not yet rendered by the playable runtime.
- Event triggers beyond scheduled pools are not part of the data vocabulary.
- Hot reload, a mod-manager UI, distribution, sandboxing, multiplayer, localization, and AI are out of scope.

## Verification

Run the suite from the repository root:

```powershell
$testModules = rg --files tests -g "test_*.py" | ForEach-Object { $_.Replace("\", ".").Replace("/", ".").Replace(".py", "") }
uv run python -m unittest @testModules
```

The runtime interaction coverage includes promotion, abilities, fusion, scheduled-event warning and
execution, and undo.

## Documentation ownership

- [start-here.md](start-here.md): contributor orientation.
- [architecture.md](architecture.md): active component boundaries.
- `docs/modding/`: modder guide and normative contracts.
- [contributing.md](contributing.md): documentation check for a change.
