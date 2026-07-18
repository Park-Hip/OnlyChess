# Current Runtime Status

**State:** the mod-driven gameplay runtime is the only playable runtime. The former hardcoded
runtime and its implementation-specific tests have been removed. The full loader contract remains
in progress; see [product-completion-spec.md](product-completion-spec.md) and
[milestones.md](milestones.md) for the approved completion plan.

## Supported now

| Area | Current behavior |
|---|---|
| Loading | Discovers compatible mods automatically or from an explicit selection; resolves dependencies in deterministic topological order; loads trusted code; validates, patches, normalizes, registers, and links content before a runtime session activates it. |
| Rules | Data-defined slide/leap movement plus code-mod castle and en-passant verbs. |
| Turns and undo | Every completed move, ability, fusion reaction, status expiry, and scheduled event is recorded as reversible actions. |
| Modes | Startup discovers compatible mods once and exposes every linked game mode in an alphabetically stable player-facing catalog. |
| Content | The shipped pieces, boards, modes, abilities, resources, statuses, fusion tables, event pools, and events load through the same validation, replacement, patch, and reference-linking path as third-party content. |
| UI | The Pygame screen resolves selected-mode themes and HUD data, uses board-aware geometry, renders explicit piece glyphs or owned sprites, and dispatches sound cues from session notifications. |
| Presentation contract | Themes, HUD layouts, sound cues, explicit owned assets, and piece/status presentation declarations validate and link as mod content. |

## Deliberate current limits

- Mod sprites, sounds, themes, and HUD elements are not yet rendered by the playable runtime.
- Side colours, themes, HUD definitions, sprites, and sounds remain presentation-contract work for
  Milestones 3 and 4; M2 deliberately uses the neutral core palette and glyph fallback.
- Registry-only test helpers may opt out of strict validation/linking; the playable runtime always
  enables them. They exist only for isolated loader tests, not as a game-loading path.
- Event triggers beyond scheduled pools are not part of the data vocabulary.
- Hot reload, a mod-manager UI, distribution, sandboxing, multiplayer, localization, and AI are out of scope.

## Verification

Run the suite from the repository root:

```powershell
$test_modules = rg --files tests -g 'test_*.py' | ForEach-Object { $_.Replace('\\', '.').Replace('/', '.').Replace('.py', '') }
uv run python -m unittest @test_modules -q
```

The runtime interaction coverage includes promotion, abilities, fusion, scheduled-event warning and
execution, and undo.

The independent `proof:arena_mode` is automatically discovered and provides the 6x6 Prism Arena
release fixture. The automated suite and the 2026-07-17 manual checklist both passed with no bugs
detected.

## Documentation ownership

- [start-here.md](start-here.md): contributor orientation.
- [product-completion-spec.md](product-completion-spec.md): approved v1 finish definition and
  architectural decisions.
- [milestones.md](milestones.md): dependency-ordered delivery plan and acceptance criteria.
- [architecture.md](architecture.md): active component boundaries.
- `docs/modding/`: modder guide and normative contracts.
- [contributing.md](contributing.md): documentation check for a change.
