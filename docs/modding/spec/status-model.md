# Spec — Status Effects

**Status:** current status-effect contract.
**Satisfies:** UC8 (*add a new status* — the confirmed must-have).

## Why shield first

Phase B flagged shield as the awkward case. Reading the code, it is worse than "a countdown with
quirks" — **it is not a countdown at all**:

```python
def expire_after_turn(self, completed_turn_color):
    for piece in list(self.active_pieces):
        if getattr(piece, "shield_owner", None) == completed_turn_color:
            continue                      # your own turn ending → survive
        # any other turn ending → expire
```

The rule is *survive your own turn-end, die on the opponent's turn-end*. `shield_turns = 1` is
vestigial — nothing reads it as a counter. Design against this first; a naive `duration: N` model
cannot express it, and retrofitting shield into a countdown would silently change the game.

There is a second, quieter rule: **poison and stun tick on full turns**
runs at full-turn boundaries), while **shield expires on half-turns** (`expire_shields_after_turn`
fires after every move *and* every ability). Two granularities, undocumented.

## The model

A status is content, defined in data, in a mod's namespace — **the seventh content type**, subject to
every universal rule in [content-schemas.md](content-schemas.md): it declares `type` and `id`,
unknown keys are load errors, and it may be patched or replaced like anything else.

```yaml
type: status
id: base:poison
expiry: { turns: 3 }        # default; the application may override
modifies:
  movement:
    slide: { limit: 1 }     # squares — author-facing, like a piece's `limit`. See below.
    leap:  { disable: true }
```

> **`limit` here is the same unit as a piece's `limit`** — squares, converted by the loader
> (`internal = N + 1`, C3 finding 5). It is written in a different schema, which is exactly why it is
> easy to miss: normalization is defined over the **vocabulary**, not over the piece content type. A
> loader that converts only `moves` gives a poisoned bishop a zero-square slide, and nothing in the
> data looks wrong. Found at Gate 3.

Applied by an effect, which supplies the duration:

```yaml
effect: { type: apply_status, status: base:poison, duration: 3 }
```

**Duration lives on the application, not the definition.** This is what lets `nguoi_chong_bat_luc`
(immobilize kings, 1 turn) and `viec_nhe_vol_cao` (stun pawns, 2 turns) share **one** status — the
audit found they are mechanically identical, differing only in name and duration. The definition
owns the *model*; the application owns the *number*.

## Expiry policies

| Policy | Written as | Meaning | Ticks on | Used by |
|---|---|---|---|---|
| `turns` | `expiry: { turns: 3 }` | countdown | full turns | poison, stun |
| `after_opponent_turn` | `expiry: after_opponent_turn` | survive your turn-end, die on the opponent's | half turns | shield |

Two policies, both earned by real content. **`plies: N` is not earned — do not add it.**

The two spellings are not an inconsistency: `expiry` follows the convention that a **parameterless
choice is written bare and a parameterised one is a single-key mapping** (content-schemas.md,
"Universal rules"), the same way `pick: all` and `pick: { random: 1 }` differ. `turns` takes a
number; `after_opponent_turn` takes nothing and would only gain a `: true` to look like its sibling.

## Modifier vocabulary

The complete v1 set, each earned by base-game content:

| Modifier | Effect | Earned by |
|---|---|---|
| `movement.slide.limit: N` | sliding moves capped at N | poison |
| `movement.leap.disable: true` | leaping moves cancelled | poison |
| `movement.disable: true` | no moves at all | stun / immobilize |
| `capturable: false` | this piece cannot be captured | shield |

Nothing else. A modder needing more ships a code mod registering a new modifier — which then becomes
available to every data mod (`CLAUDE.md`: *code adds verbs*).

## Lifecycle hooks

```yaml
type: status
id: mymod:burning
expiry: { turns: 3 }
on_expire:
  effect: { type: destroy }
```

`on_expire` only. `on_apply` and `on_tick` are **not earned** — no base-game content needs them, and
UC8 does not. Add them when content demands it.

**This is UC8 satisfied as pure data**, which was the acid test for the whole design.

## Ticking and ownership — the architectural change

**Today, the event that applied a status ticks it.** `kho_ga_tron_ba_mia` owns a `poisoned_pieces`
list, decrements its own `duration`, and clears poison in `cleanup()`. The status's lifetime is
welded to its source event's lifetime, and the event's `duration` field does double duty as both.

**Under this spec, a central status system ticks every status on every piece**, decoupled from
whatever applied it.

Consequences, all of them improvements:

- **Statuses outlive their source.** An ability and an event can apply the same status with the same
  semantics — impossible today, which is why shield needed its own tracker (F7).
- **`ChessEvent.tick()`/`cleanup()` disappear.** Events become fire-and-forget; the `duration` field
  stops meaning two things at once.
- **Two storage mechanisms collapse into one.** Raw attributes (`poisoned_turns`) and
  `ShieldTracker` become one system. F7 resolved.
- **One tick site instead of N.** `_is_piece_on_board` — copy-pasted into three events, each an
  O(64) board scan — is deleted outright (F6).

> ### ❌ Corrected by E1 — the UI warning below was wrong
>
> This section originally warned: *"This changes what 'active event' means to the UI. `render_panels`
> currently displays events that are active because their status is still ticking. Once statuses are
> independent, an event is instant and there is nothing to display."*
>
> **`render_panels` does not read `active_events`. Nothing in `src/ui/` does.**
> The panels draw AP, captured pieces,
> material, turn number and a countdown. The only UI reads of event state are the warning banner
> (`message_log.py:175` → `queued.warning_active`) and the executed-message lines
> (`game_screen.py:354`), and **both survive the status rewrite untouched.** The flagged migration
> does not exist.
>
> **What is real is smaller and points the other way:** `render_board.py:122` draws the shield via
> `getattr(piece, "is_shielded", False)`. That one call site must become a generic status read, or a
> modder's `mymod:ward` is invisible on the board. The conclusion below — *the UI should show statuses
> on pieces* — stands; the claim about what the UI does today did not.
>
> Kept rather than deleted because **how it got here matters**: it described plausible behaviour
> nobody checked against the file. That is the same defect as `random_zone` (D1 finding 8) and the
> message model (finding 7) — three documents, one failure mode. Treat every unverified claim about
> `src/` in this spec as suspect until E-phase code touches it.

The UI should show **statuses on pieces**, which is what players actually care about — see the
correction above for what that does and does not require.

## Stacking

**Refresh, taking the longer:** `remaining = max(remaining, new)`.

> Deliberate divergence from current behaviour. Today `piece.poisoned_turns = self.duration` is a
> plain overwrite, so re-poisoning a piece that has 3 turns left with a 1-turn poison **shortens** it
> to 1. That is almost certainly unintended, and unreachable today (only one event applies poison, once
> per side). `max()` is what a player expects.

## F2 and F4, made explicit

**Shield-respect (F2).** The audit found three events respect shields, seven don't, and one does
both. There is no engine rule — it becomes a **selector filter**, visible in the data:

```yaml
select:
  filter: { not_status: [base:shield] }    # my_danh_iran, tai_xiu
```

`not_status` is generic, so it works for modded statuses too — a modder's `mymod:ward` is filterable
on day one. Engine-enforced protection is limited to `capturable: false`, which covers captures only.
Every other case is an explicit, readable choice in the event file. **The inconsistency does not get
fixed — it gets made visible**, and someone then decides deliberately.

**Statuses through transform (F4).** Statuses are piece state, so the transform `preserve` policy
governs them, explicitly:

```yaml
effect: { type: transform, into: base:knight, preserve: [has_moved] }     # drops statuses
effect: { type: transform, into: base:queen,  preserve: all_except_identity }  # keeps statuses
```

Both current policies survive, now named. `gia_xang_tang` dropping poison and `comeout` keeping it
becomes a visible decision rather than an accident of which helper was copied.

## The base game, expressed

```yaml
# base:chess
type: status
id: base:shield
expiry: after_opponent_turn
modifies: { capturable: false }

# base:events
type: status
id: base:poison
expiry: { turns: 3 }
modifies:
  movement:
    slide: { limit: 1 }
    leap:  { disable: true }

type: status
id: base:stun
expiry: { turns: 1 }
modifies: { movement: { disable: true } }
```

**Four statuses become three.** Stun and immobilize unify; `nguoi_chong_bat_luc` applies
`base:stun` with `duration: 1`, `viec_nhe_vol_cao` with `duration: 2`.

Verified in Phase B: the `base:poison` definition above reproduces all five hand-written poison
checks exactly (Knight → no moves; Bishop/Rook → 1 step; Archbishop/Chancellor → 1-step slide only;
Warden/Inquisitor → 1 step both). The one divergence is Queen, which is unreachable — no event
selects her — and where the central rule is *more* correct than the current silence.

## Where shield lives

`base:shield` belongs to **`base:chess`**, not `base:events` — `rook_shield` is an ability, and
abilities ship with the pieces. `base:poison` and `base:stun` belong to `base:events`.

This matters for UC11: disabling `base:events` must leave a coherent game. Poison and stun leave with
it; shield stays with the ability that applies it. A status defined in a disabled mod must not be
referenceable — the loader catches that as a missing dependency.

## Open

- **Does `capturable: false` block *all* removal, or only captures?** Today it blocks captures
  (`can_capture_target`), while events opt in via selectors. Keep that split — but the naming should
  not imply more protection than it gives.
- **Status visibility.** Are statuses public information? Today they are (rendered on the board).
  A modded hidden status would need this to be a declared field.
- **Do statuses stack across *different* statuses?** Two movement modifiers on one piece — poison
  (`slide.limit: 1`) plus a modded `slow` (`slide.limit: 2`). Proposal: most restrictive wins
  (`min`), but no content needs it yet, so leave unspecified rather than guess.
