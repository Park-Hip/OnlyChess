# Phase B — Declarative Feasibility Study

**Status:** complete. Answers the mod power question (roadmap D1) with evidence.
**Method:** every item from [`content-audit.md`](content-audit.md) was written out as data in a
throwaway notation, then bucketed. The notation below is **illustrative only** — the format
decision (C1) is still open and nothing here depends on YAML.

**Buckets:** 1 = trivially declarative · 2 = needs a new verb · 3 = resists declaration

---

## Headline result

**Pure data expresses the entire base game. Bucket 3 is empty.**

But that result comes with a caveat that turns out to matter more than the result itself: two
items (en passant, castling) only reach bucket 2 by being handed **opaque engine verbs** — a modder
can *use* `castle: true` but cannot *invent* anything like it. That caveat, not the bucket counts,
drives the recommendation in [B2](#b2--the-mod-power-decision).

| Content | Bucket 1 | Bucket 2 | Bucket 3 |
|---|---|---|---|
| Events (10) | 8 | 2 | 0 |
| Abilities (4) | 2 | 2 | 0 |
| Pieces (10) | 8 | 2 (Pawn, King — *opaque verbs*) | 0 |
| Fusion (6) | 6 | 0 | 0 |

---

## B1 — Results

### Events: 8 bucket 1, 2 bucket 2

Eight events are `select → pick → effect`, verbatim. Example — `gia_xang_tang`, using the
`primary` axis from finding F3:

```yaml
id: base:gia_xang_tang
select:
  filter: { primary: rook }     # Rook, Chancellor, Warden — not Inquisitor
  pick: all
effect: { type: transform, into: base:knight, preserve: [has_moved] }
```

`kho_ga_tron_ba_mia`'s seven-code list collapses to one tag query — `tag_any: [rook, knight,
bishop]` — confirming F3's prediction exactly.

**The two bucket-2 events, and what they cost:**

- **`mat_quyen_cong_dan`** does two unrelated things (destroy a black pawn, convert a white one).
  An event must therefore be a **list of steps**, not a single effect. Cheap, structural.
- **`my_danh_iran`** picks its 2×2 zone *at warning time* and reuses it at execution (F9). This
  forces a genuinely new concept: **events are two-phase, and the warning phase can compute and
  bind state that execution reads**. This is the only place the notation needs variables, and it is
  worth watching — bindings are how data formats start becoming languages.

`tai_xiu`'s random side does **not** need bindings; a `color: random_one` selector covers it,
because its message never references which side was chosen. Small mercy, and a reminder to check
whether a binding is actually load-bearing before adding one.

### Abilities: 2 bucket 1, 2 bucket 2

`knight_swap` and `rook_shield` are trivial (the latter needs an adjacency selector).

- **`bishop_snipe`** needs a **ray / line-of-sight** targeting primitive — but `_get_sliding_moves`
  is already that primitive, so it is reuse rather than invention.
- **`pawn_sprint`** needs *direction-relative offsets* (`forward` depends on colour) and a
  **conditional effect** — "promote if you land on the last rank":

```yaml
effect:
  - { type: move }
  - { type: promote, into: base:queen, when: { at_promotion_rank: true } }
```

Note what that is: **trigger → condition → effect, appearing spontaneously inside an ability.** The
shape we committed to for UC13–15 turns out to be needed by the *existing* base game. That is
independent corroboration that the shape is right, arrived at from the opposite direction.

### Pieces: 8 bucket 1, 2 bucket 2

Every piece except Pawn and King is `(directions × limit)` composed with `+`. **Fused pieces are
literally the sum of their parts** — Warden, the piece that needed a hand-written class with
bespoke poison handling, is four lines:

```yaml
id: base:warden
moves:
  - { type: slide, dirs: orthogonal, limit: unlimited }
  - { type: slide, dirs: diagonal,   limit: 3 }
```

**Pawn and King are the hard cases the audit predicted, and they resolve unsatisfyingly.** Pawn
needs move-only vs capture-only distinctions and first-move conditions (all fine) — plus **en
passant**, which captures a piece that is not on the destination square and depends on the
opponent's previous move. King needs **castling**: two pieces moving at once, gated on castle
rights and square-attack checks.

Neither composes from directions and limits. Both reach bucket 2 **only by being given an opaque
engine verb** (`enpassant: true`, `castle: true`). They are expressible in the sense that the base
game can be written down — and inexpressible in the sense that a modder cannot build anything
*like* them. **This is the real finding of Phase B**, and it is what B2 turns on.

### Fusion: 6 bucket 1

The ordered-pair table transcribes directly. Asymmetry preserved by keeping capturer and captured
as distinct keys (F10).

---

## The status finding: F1 is solvable as data

This is the strongest result of the study, and it resolves the audit's most serious coupling.

**Poison, defined centrally, is a movement modifier:**

```yaml
id: base:poison
modifies:
  movement:
    slide: { limit: 1 }      # sliding becomes one step
    leap:  { disable: true } # leaps are cancelled
```

The engine applies that uniformly to any piece's move parts. Checked against every current piece:

| Piece | Move parts | Central rule gives | Current hand-written behaviour | Match |
|---|---|---|---|---|
| Knight | leaps | no moves | `return []` | ✅ |
| Bishop | slide diagonal | 1 step | `_get_one_step_moves` | ✅ |
| Rook | slide orthogonal | 1 step | `_get_one_step_moves` | ✅ |
| Archbishop | slide + leap | 1-step diagonal only | same, via delegation | ✅ |
| Chancellor | slide + leap | 1-step orthogonal only | same, via delegation | ✅ |
| Warden | slide + slide(3) | 1 step both | same, hand-written twice | ✅ |
| Inquisitor | slide + slide(3) | 1 step both | same, hand-written twice | ✅ |
| Queen | slide 8-dir | 1 step | **no check — unaffected** | ⚠️ unreachable |
| Pawn / King | step / step | unaffected | no check | ✅ |

**One central rule reproduces all five hand-written poison checks exactly.** The only divergence is
Queen, and it is unreachable — `kho_ga_tron_ba_mia` never selects her. The central rule is also
*more correct*: if a mod ever poisons a Queen, she gets limited, which is obviously the intent. The
current code would silently do nothing.

**This makes UC8 (the confirmed must) a data task.** "Burning: dies after 3 turns" becomes:

```yaml
id: mymod:burning
on_expire: { effect: destroy }
```

F1's O(statuses × pieces) coupling dissolves. Statuses stop being conventions that each piece class
independently honours, and become data the engine enforces once.

**Shield remains the awkward one, as predicted (F7).** It expires *after the opponent's turn*, keyed
by `shield_owner` — not on a countdown. Statuses need two duration models (`turns: N` and
`until: opponent_turn_ends`). Design the system against shield first; poison and stun fall out easily.

---

## Shape validation: UC13–15

Sketched on paper per the Gate 1 addition. **The shape holds for all three**, using one machinery:

```yaml
# UC13 — HP
properties: { hp: 3 }
on: attacked
effect: { type: modify_property, target: defender, property: hp, delta: -1 }
---
on: property_changed
when: { property: hp, value: { lte: 0 } }
effect: { type: destroy }

# UC14 — conditional power
on: turn_start
when: { self: { adjacent_to: { code: king, friendly: true } } }
effect: { type: grant_ability, ability: mymod:teleport }

# UC15 — mission
on: piece_captured
when: { captured: { code: pawn } }
counter: { increment: 1, goal: 3 }
reward: { type: grant_ap, amount: 5 }
```

Requirements this confirms: **open piece properties** (`hp` is just data, not a schema field), an
**event bus** the engine emits into, **property conditions**, and **per-player counters**.

## Where the condition language stops

The sketches need comparisons (`lte`, `eq`), boolean combinators, property access, and relative
references (`self`, `defender`, `captured`). That is a predicate language, and it is exactly where
the roadmap's Phase B trap lives.

**Proposed line, to be enforced in Phase C:**

> Conditions are **pure predicates over game state**. No side effects, no loops, no variable
> assignment, no arithmetic beyond comparison. If something needs to *compute* rather than *ask*,
> it is an effect or it is code — never a condition.

This keeps conditions at the Minecraft-predicate level, which is well-precedented and stays
readable to a non-coder. The moment conditions grow arithmetic, we have built a programming
language with no debugger and bad ergonomics.

---

## B2 — The mod power decision

### What the evidence says

Bucket 3 is empty: **the base game needs no escape hatch at all.** Read naively, that argues for
pure declarative data — the option that maximises non-coder accessibility.

**That reading is wrong**, and the reason is Pawn and King. They only reach bucket 2 because we
grant them opaque verbs (`enpassant`, `castle`). Generalise that pattern:

> Every mechanic that does not compose from existing verbs needs a **new engine verb**.

If only we can add verbs, then every modder with a novel mechanic must ask us and wait. Shogi drops
(UC12, a **stated goal**) are exactly this: placing captured pieces back on the board composes from
nothing that exists. A pure-data system does not fail on the base game — **it fails on the second
interesting mod**, and it fails by making us the bottleneck for everyone else's ideas.

### Decision: data-first, with code that extends the *vocabulary*

> **Content is data. Code adds verbs.**
>
> - **Data mods** (non-coders) compose content from the verb vocabulary: pieces, events, abilities,
>   statuses, fusion pairs, missions. This is empirically ~100% of the base game.
> - **Code mods** (programmers) register *new verbs* — move types, effects, conditions, selectors —
>   which then become available to **all** data mods as ordinary vocabulary.

A modder wanting shogi drops writes a small plugin adding a `drop` move type. From that moment,
every data mod — theirs and everyone else's — can write `type: drop` without touching Python. The
escape hatch **grows the language rather than bypassing it**.

This also retroactively fixes the `enpassant` / `castle` wart: they stop being engine
special-cases and become *verbs registered by `base:chess`* — which is precisely what
"the base game is a mod, with no privileges" demands. The base mod adds its verbs the same way any
code mod would. The awkward finding and the architectural principle turn out to resolve each other.

### Why not the alternatives

- **Pure data**: fails UC12, and makes us the bottleneck for every unanticipated mechanic. The
  base game's success here is misleading — we designed both the verbs and the content.
- **Python plugins primary**: locks non-coders out, contradicting the project's reason to exist.
  It is also what the codebase already effectively is.

### Precedent

This is RimWorld's model (XML Defs naming C# classes via `workerClass`/`compClass`) and Factorio's
(declarative prototypes plus Lua). Both are large, long-lived modding ecosystems where most authors
never write code and the ones who do extend what the others can express. It is the consensus answer
found in the roadmap's research, arrived at here independently from our own content.

### Consequent: trust model (roadmap D2)

Code mods mean **arbitrary code execution**. Python cannot be meaningfully sandboxed —
`__subclasses__()` traversal defeats restricted namespaces, and real isolation needs VM/gVisor/WASM.

**Model: trusted local install.** Mods run with full user privileges; installing one is equivalent
to running any downloaded program, and must be documented as such. **Do not build a sandbox.**

Mitigation is honesty, not machinery: a mod's manifest declares whether it ships code, and the UI
surfaces that distinction. A pure-data mod is genuinely safe to install, and the majority of mods
will be pure data — that is a real security property worth exposing, and it costs nothing.

---

## Answers delivered

| Question | Answer |
|---|---|
| **D1 — mod power ceiling** | **Data-first; code registers new verbs, not new content** |
| **D2 — trust model** | Trusted local install; no sandbox; manifest declares code |
| **F1 — status coupling** | **Solved** — statuses are data with movement modifiers, enforced centrally |
| **UC8 — new status** | Confirmed a **data task**. Must-have is met. |
| **F5 — trigger variety** | Shape must be an event bus from day one; v1 vocabulary stays small |
| Shape holds for UC13–15? | **Yes** — one machinery, verified on paper |

## Carried into Phase C

1. **Design the status system against shield first** (F7) — two duration models, `turns: N` and
   `until: opponent_turn_ends`.
2. **Verb registration is a first-class spec concern**, not an afterthought. `base:chess` registers
   `castle` and `enpassant` through the same public path any code mod uses. If that path is
   privileged, the dogfooding claim is a lie.
3. **Enforce the condition line** above; revisit if real content bounces off it.
4. **Two selector axes** (`tag`, `primary`) per F3.
5. **Events are two-phase** with warning-time bindings (F9). Watch bindings closely — that is where
   this format would start becoming a language.
6. **Open the game-design question** blocking pipeline stages: with HP, does fusion trigger on
   capture or on kill? (roadmap D11)
