# Current Runtime Status

**State:** the mod-driven gameplay runtime is the only playable runtime. The former hardcoded
runtime and its implementation-specific tests have been removed. The loader, generic mode runtime,
and static presentation contract are implemented; post-v1 presentation depth and broader gameplay
vocabulary remain intentionally limited. See [product-completion-spec.md](product-completion-spec.md)
and [milestones.md](milestones.md) for the approved completion plan.

## Supported now

| Area | Current behavior |
|---|---|
| Loading | Discovers installed mods automatically or from an explicit selection; resolves dependency versions in deterministic topological order; loads trusted code; validates, patches, normalizes, registers, and links content before a runtime session activates it. The `engine:` range is syntax-checked but is not yet enforced against `ENGINE_VERSION`. |
| Rules | Data-defined slide/leap movement plus code-mod castle and en-passant verbs. |
| Turns and undo | Every completed move, ability, fusion reaction, status expiry, and scheduled event is recorded as reversible actions. |
| Modes | Startup discovers compatible mods once and exposes every linked game mode in an alphabetically stable player-facing catalog. |
| Content | The shipped pieces, boards, modes, abilities, resources, statuses, fusion tables, event pools, and events load through the same validation, replacement, patch, and reference-linking path as third-party content. |
| UI | The Pygame screen resolves selected-mode themes and HUD data, uses board-aware geometry, renders explicit piece glyphs or owned sprites, and dispatches sound cues from session notifications. |
| Presentation contract | Themes, HUD layouts, sound cues, explicit owned assets, and piece/status presentation declarations validate and link as mod content. |

## Deliberate current limits

- The playable runtime renders mod themes, piece sprites/glyphs, the declared `hud_layout` widgets
  (turn, resources, log, prompt) into top/side/bottom slots (Milestone 6 slice 1), and — as of
  Milestone 6 slice 2 — plays the mode's declared sound cues: base ships clips for `move_completed`,
  `capture_completed`, `ability_used`, `promotion_chosen`, `undo_completed`, and `outcome_reached`,
  and the proof mod ships its own owned move cue. As of Milestone 6 slice 3, a finished game offers
  restart (fresh `EngineSession`, same mode) and return-to-menu, from the outcome overlay and via
  keyboard during play. As of Milestone 6 slice 5, a piece renders every visible status — its declared
  `icon` sprite when present, else its `glyph` — not just the first. Milestone 6 is now complete.
  The proof mod offers a `proof:glow_up` ability (scoped to its prism, so it does not leak onto other
  mods' pieces) that applies its owned visible `proof:glow` icon during normal play. Status and scheduled-event notifications
  are now derived from recorded action lists, and base declares owned cues for all four kinds.
  The menu now previews each mode's palette per row and uses the first catalog palette for chrome;
  it falls back to UI constants only when no mode supplies a palette.
  The read-only Mods screen now lists installed metadata, flags code-bearing mods, and renders
  attributed load errors; a failed application load returns an empty catalog instead of crashing.
- Registry-only test helpers may opt out of strict validation/linking; the playable runtime always
  enables them. They exist only for isolated loader tests, not as a game-loading path.
- Event triggers beyond scheduled pools are not part of the data vocabulary.
- Hot reload, a mod-manager UI, distribution, sandboxing, multiplayer, localization, and AI are out of scope.

## Release-readiness blockers

These are the items to fix or consciously sign off before calling the project release-ready. They are
ordered by risk, not by feature excitement.

### P0 — Clean verification must be reproducible

The release claim requires both the documented automated suite and the manual checklist to pass from a
clean checkout. The 2026-07-18 audit could not reproduce that gate in the local environment: `uv` could
not use the repository's `.venv`, while the system Python lacked `pygame` and `ruamel.yaml`. Treat the
release gate as **unverified**, not passed, until a clean dependency setup runs the full suite and the
manual checklist again.

The fix belongs in the project setup/workflow, not in individual developer machines. Record the exact
setup command and the successful command output in the release notes or CI once established.

### P0 — Enforce engine compatibility

`manifest.yaml` accepts an `engine: "^1.0"` range and validates its shape, but the loader does not yet
compare that range with `ENGINE_VERSION` or disable an incompatible mod. Implement the check with an
attributed load error and tests, or remove engine compatibility from the release promise. Do not keep
describing these mods as fully compatible while this remains open.

### P1 — Decide what kind of release this is

The current install is a developer preview: it requires Python and `uv`, and mods are copied manually
under the application's `mods/` directory. There is no packaged executable, installer, per-user mod
directory, marketplace, or enable/disable manager. This is acceptable for a contributor release, but
is a blocker for a general-player release unless the product scope explicitly says so.

### P1 — Do not overpromise mod extensibility

The current public extension surface is smaller than the phrase “anything can be a mod” suggests. Data
mods can compose the existing vocabulary, and code mods can register `move_type` verbs only. They cannot
yet add clocks, custom HUD widgets, arbitrary text overlays, visual-only piece colours, new event
triggers, or presentation effects. These are documented limitations, not hidden bugs; either keep them
out of the release promise or implement them through the normal loader, action, snapshot, and proof-mod
path.

### P2 — UI polish is optional, readability is not

The UI is intentionally basic and static. Do not block a developer-preview release on visual polish.
Do block it for clipped or unreadable text, broken board bounds, missing interaction feedback, or a
manual checklist failure. Animation, particles, banners, and richer overlays are post-v1 work.

## Verification

Run the suite from the repository root:

```powershell
$test_modules = rg --files tests -g 'test_*.py' | ForEach-Object { $_.Replace('\\', '.').Replace('/', '.').Replace('.py', '') }
uv run python -m unittest @test_modules -q
```

The runtime interaction coverage includes promotion, abilities, fusion, scheduled-event warning and
execution, and undo.

The independent `proof:arena_mode` is automatically discovered and provides the 6x6 Prism Arena
release fixture. The automated suite and the 2026-07-17 manual checklist passed historically with no
bugs detected; rerun both from a clean environment before a new release sign-off.

## Documentation ownership

- [start-here.md](start-here.md): contributor orientation.
- [product-completion-spec.md](product-completion-spec.md): approved v1 finish definition and
  architectural decisions.
- [milestones.md](milestones.md): dependency-ordered delivery plan and acceptance criteria.
- [architecture.md](architecture.md): active component boundaries.
- `docs/modding/`: modder guide and normative contracts.
- [contributing.md](contributing.md): documentation check for a change.
