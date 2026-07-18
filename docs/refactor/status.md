# Current Runtime Status

**State:** the mod-driven gameplay runtime is the only playable runtime. The former hardcoded
runtime and its implementation-specific tests have been removed. The loader, generic mode runtime,
and static presentation contract are implemented; post-v1 presentation depth and broader gameplay
vocabulary remain intentionally limited. See [product-completion-spec.md](product-completion-spec.md)
and [milestones.md](milestones.md) for the approved completion plan.

## Supported now

| Area | Current behavior |
|---|---|
| Loading | Discovers installed mods automatically or from an explicit selection; resolves dependency versions in deterministic topological order; loads trusted code; validates, patches, normalizes, registers, and links content before a runtime session activates it. The `engine:` range is enforced against `ENGINE_VERSION`; an incompatible mod is disabled with attribution. |
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
not use the repository's `.venv`, while the system Python lacked `pygame` and `ruamel.yaml`.

**Automated suite: reproduced on Linux 2026-07-18.** 207 tests, all passing, from a clean checkout with
a plain `venv` and no `uv`:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
MODS=$(find tests -name 'test_*.py' | sed 's|/|.|g; s|\.py$||' | sort)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m unittest $MODS -q
```

The canonical PowerShell command in [Verification](#verification) is Windows-only, so the suite had
never been run on another platform. Doing so exposed one genuinely platform-dependent assertion in
`tests/modding/test_walking_skeleton.py`, which compared a path with hardcoded `\` separators; the
source under test was already correct. It now compares `Path.parts`. Neither `uv` nor a `.venv` inside
the repository is required to run the suite.

**Manual checklist: partially run, two blockers found.** Steps 1–2, 4 and 8 pass. Steps 3 and 5–7 were
driven headlessly on 2026-07-18 through the real screens' `handle_event`/`draw` path under the dummy SDL
driver, with rendered frames inspected as images. See the two P0 items below.

Step 2 was exercised by temporarily setting `base:events` to `engine: "^2.0"`: it was disabled with an
attributed error while the other three mods still loaded, and the fixture was reverted. Step 8 reports
mod, file, `line:col`, field, problem, and expected, as contracted.

Not yet exercised, and still needing a human: castling, en passant, promotion choice, ability targeting,
fusion, and scheduled event warning/execution all require specific game states rather than the opening
position, and audible sound output cannot be checked headlessly — only cue dispatch was confirmed
(`move_completed`, `undo_completed` fire correctly).

### Resolved 2026-07-18 — Royal-less sides crashed instead of failing to load

`mods/skeleton/` is the walking-skeleton fixture. It is discovered like any other mod, links a
`game_mode`, and appears in the menu as a fourth entry, "Walking Skeleton Preview (1 x 1)". Selecting it
raises an uncaught `ValueError: side 'skeleton:blue' has no royal piece` and takes the application down.

The chain: `skeleton:beacon` declares no `royal` property, `EngineSession.outcome` (`src/runtime.py:166`)
unconditionally calls `threatened()`, and `state.royal_piece()` (`src/engine/state.py:38`) raises when no
piece on that side is royal. `outcome` is read while drawing the HUD, so the crash happens on the first
frame.

The assumption ran deeper than `outcome`. `movegen.legal_moves` filters every candidate move on
`threatened()`, so "a move is legal if it does not leave your royal piece attacked" — a chess rule — is
core's definition of legality. The skeleton reached the draw call only because `skeleton:beacon` has
`moves: []`, so the filter's body never ran; a fixture with one move would have crashed a layer earlier.

**Decision: royalty is required, and the loader says so.** The alternative — royal-less sides are legal,
`threatened()` returns `False` with nothing to defend — needs an outcome model that does not involve
checkmate, and no content has asked for one. That is the earned-vocabulary rule: it stays available if a
mod ever needs it.

`linking.py` now rejects a starting position that leaves a declared side without a royal piece, naming
the mod, board file, `sides[n]`, and the fix. Three regression tests cover the rejection, the same board
passing once a placed piece is royal, and the mode not reaching the catalog. The requirement is now
stated at load time instead of being discovered by crashing mid-frame.

Consequences: `mods/skeleton/`'s beacon and two test fixtures gained `properties: { royal: true }`, since
none of them were testing royal-less boards.

**Still open, and separate:** `mods/skeleton/` remains a test fixture shipped as a selectable mode. It no
longer crashes — it resolves immediately to "Stalemate" — but a 1x1 board in the player's menu is still
wrong. Whether a fixture belongs in the distributed `mods/` directory is part of the release-kind
decision below.

### Resolved 2026-07-18 — Declared piece glyphs were unrenderable off Windows

`src/main.py:20-23` loads fonts with `p.font.SysFont("Segoe UI", ...)`. Segoe UI is a Windows family; on
a machine without it pygame fuzzy-matches to whatever is installed. The base mods survive because their
glyphs are ASCII (`K`, `Q`, `R`), but `proof:prism` declares `glyph: "◆"` (U+25C6) and every piece in
Prism Arena renders as an empty tofu box on Linux — the release proof fixture, the mod whose entire job
is to demonstrate that third-party content works, is the one that breaks.

Nothing errored, because `Font.metrics("◆")` reports a glyph even when the resolved face draws `.notdef`.
A mod could not fix it either: the font is core's, and the mod's declared glyph is valid content.

`_load_fonts` now picks the first genuinely installed face from a preference list — Segoe UI, DejaVu
Sans, Noto Sans, Liberation Sans, FreeSans — falling back to pygame's default. The check is against
`p.font.get_fonts()`, not a comma-separated `SysFont` list, because `match_font` resolves an *absent*
family to its nearest neighbour: asking for Segoe UI on this Linux box returns Ubuntu, so a preference
list passed to `SysFont` never reaches its own fallbacks. Of the faces available here, only DejaVu Sans
draws `◆`, `●`, `▲` and `♛`. Prism Arena now renders its diamonds.

The remaining fix belongs in the project setup/workflow, not in individual developer machines. Record
the exact setup command and the successful command output in the release notes or CI once established.

### Resolved 2026-07-18 — Enforce engine compatibility

`manifest.yaml`'s `engine: "^1.0"` is now validated as a caret range at manifest read and compared
with `ENGINE_VERSION` during resolve. An incompatible mod is disabled with an attributed error naming
the mod, `manifest.yaml`, the `engine` field, its range, and the running version; its dependents are
disabled through the same propagation a missing dependency uses. Four regression tests cover the
incompatible, compatible, absent, and malformed-range cases.

Previously the field was described as syntax-validated, but only its type was checked — `engine: ">=1.0"`
was accepted. That is now a manifest error.

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
