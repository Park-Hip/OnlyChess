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

## The preview sign-off gate

**Decision, 2026-07-19: the first release is a developer preview, and it ships when this list is
empty — not when the engine stops growing.**

| # | Item | Kind |
|---|---|---|
| ~~1~~ | ~~P2 — a mode with no `presentation:` hides the promotion prompt~~ — done 2026-07-19 | Code |
| 2 | P0 — audible sound output confirmed by a human | Manual |
| 3 | P1 — name the audience in `product-completion-spec.md` | Drafted 2026-07-19, awaiting sign-off |
| 4 | P1 — keep the documented extension limits as the release promise | Drafted 2026-07-19, awaiting sign-off |

Items 3 and 4 are written into `product-completion-spec.md` under "Audience for the first release".
They are marked drafted rather than done because a declaration is only worth what the person making it
says it is worth — read them and either agree or change them.

Everything else currently known is already resolved below, and all four product-completion gates pass.

**Why the list is written down rather than remembered.** This project's premise is that content is
extensible, so there is always another verb, widget, or trigger that could land first. Without a stated
boundary "when everything is finished" has no false condition, and a finished-but-unsigned build stays
unsigned indefinitely. Clocks, custom HUD widgets, event triggers, and presentation effects are M7+ by
the completion spec's own scoping; pulling any of them into this gate is what would make the finish line
recede.

Item 1 is on the list rather than deferred *because* this is a preview. Its victim is a modder writing
their first minimal mod, which in a player release is an edge case and here is the entire audience.

**Switching to a general-player release later is a milestone, not a relabel.** It needs a packaged
executable, an installer, a mod-install flow, an enable/disable manager, and multi-root mod discovery —
`load()` and `discover()` each take a single directory, and an installed application directory is not
user-writable on Windows or macOS, so packaging cannot land without the loader change. The decision is
cheap to defer; the delivery is not.

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

**Steps 5–7 in full, 2026-07-18.** The remaining interactions were driven through
`EngineGameScreen.handle_event` from positions reached by scripted play, or from scenario boards loaded
as an ordinary mod depending on `base:chess` and `base:fusion`. 25 assertions, all passing:

| Interaction | Verified |
|---|---|
| Castling | King moves two files, rook jumps to f1, h1 empties, and one undo restores all three |
| En passant | Capturing pawn lands behind the target, the target leaves its own square, undo restores it |
| Promotion | Move is held pending a choice of queen/rook/bishop/knight; the keypress promotes; undo restores the pawn |
| Ability targeting | AP accrues over eight moves, the knight's modal offers Knight Swap, targeting swaps the pieces, AP is spent, undo restores both |
| Fusion | Rook takes bishop as a displacing capture and becomes a Warden; undo splits them |
| Scheduled events | Warning fires on the ninth completed move, execution on the tenth, with a message for the log |

Still needing a human: audible sound output. Cue dispatch is confirmed, but whether a clip is heard is not
checkable headlessly.

### Resolved 2026-07-19 — A mode without `presentation:` hid the promotion prompt

A `game_mode` that declares no `presentation:` block renders no HUD, and the promotion prompt lives in the
HUD. `_prompt_text()` still returns `"Promote: Q/R/B/K"`, but there is nowhere to draw it, and
`handle_event` ignores clicks while a move is pending — so the board simply stops responding until the
player guesses one of four keys. The same position in a mode that declares `presentation:` shows the
prompt correctly.

Every shipped mode declares presentation, so no player hit this. A modder writing their first minimal
mode did, which is the audience the prime directive cares most about.

**Fixed by having core draw a fallback prompt** (`EngineGameScreen._draw_fallback_prompt`), rather than by
requiring `presentation:` at link. Core already owns the render loop, and the text is derived from the
pending move's own choices, so nothing here names content; requiring presentation would have made the
smallest possible mod harder to write, which is the wrong trade for this audience. The fallback also
covers a layout that declares `hud_layout` but omits the `prompt` widget, which is the same trap.

The regression test asserts on pixels, because the defect was invisible at every other layer:
`_prompt_text()` already returned the string and the snapshot already carried it — only the draw call was
missing. Its first version compared the bottom strip against a blank surface and passed even with the fix
removed, since other widgets colour that strip too; it now compares the same screen with and without a
pending move, which fails when the fallback is disabled.

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

**Also resolved:** the skeleton was a test fixture shipped as selectable content, so it appeared in the
menu as a fourth "Walking Skeleton Preview (1 x 1)" entry. It moved to `tests/fixtures/skeleton/` and its
tests now load from there. The menu lists exactly the three modes the checklist names.

Worth recording why the fix had to be a directory move. Core cannot skip a fixture mod at discovery
without naming it, and naming a mod is what the prime directive forbids; there is also no "hidden" or
"fixture" manifest flag, and adding one would be vocabulary invented on speculation. The only place the
shipped/not-shipped distinction can live is the directory itself, which `tests/fixtures/wave3_mods/`
already established as the pattern.

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

The POSIX equivalent, which needs neither `uv` nor `rg`:

```bash
MODS=$(find tests -name 'test_*.py' | sed 's|/|.|g; s|\.py$||' | sort)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest $MODS -q
```

Only the PowerShell form was documented until 2026-07-18, which is why the suite had never run on
another platform and a Windows-only path assertion survived in it. Keep both forms working.

The runtime interaction coverage includes promotion, abilities, fusion, scheduled-event warning and
execution, and undo, and `tests/test_ui_interactions.py` covers the same interactions through the
screen's event handler rather than the session API.

The independent `proof:arena_mode` provides the 6x6 Prism Arena release fixture. It moved to
`tests/fixtures/proof-mod/` on 2026-07-19 so it is not offered to players; a test that needs it
stages it alongside the shipped mods through `tests/support.py`. It is still the check that core
holds no chess assumption — a 6x6 board, sides that are not white and black, and a piece whose glyph
no chess notation could produce — and it still fails loudly if any of that stops being true. The automated suite and the 2026-07-17 manual checklist passed historically with no
bugs detected; rerun both from a clean environment before a new release sign-off.

## Documentation ownership

- [start-here.md](start-here.md): contributor orientation.
- [product-completion-spec.md](product-completion-spec.md): approved v1 finish definition and
  architectural decisions.
- [milestones.md](milestones.md): dependency-ordered delivery plan and acceptance criteria.
- [architecture.md](architecture.md): active component boundaries.
- `docs/modding/`: modder guide and normative contracts.
- [contributing.md](contributing.md): documentation check for a change.
