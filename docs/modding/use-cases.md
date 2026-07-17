# Phase A2 — Modder Use Cases

**Status:** Gate 1 answered. Priorities below are decided; scope of the ambitious cases is open.
**Companion:** [`content-audit.md`](content-audit.md). Cost estimates are grounded in that audit.

## Why this exists

The spec needs a definition of done. "Mods can extend the game" is not one. These are the concrete
things a person should be able to do, ordered by how much we care — so that when a schema decision
is contested, we can ask *which use case does this serve?*

## Personas

| Persona | Writes code? | Cares about |
|---|---|---|
| **Tuner** | no | numbers — costs, durations, odds, values |
| **Content adder** | no | new pieces, events, abilities, fusion pairs |
| **Reskinner** | no | sprites, sounds, names, text |
| **Rule bender** | maybe | changing how existing systems behave |
| **Total converter** | yes | replacing the game entirely |

The **Tuner** and **Content adder** are the project goal. If they need to read Python, the project
has failed regardless of how elegant the engine is. **Total conversion is a stated goal**, not just
a design check — see UC12.

## The use cases

Ranked. Cost cites audit findings. UC13–15 are stated project goals from Gate 1.

| # | Use case | Persona | Cost | Blocked by |
|---|---|---|---|---|
| **UC1** | Change an ability's AP cost 3 → 2 | Tuner | **trivial** | — |
| **UC2** | Change an event's duration or odds | Tuner | **trivial** | — |
| **UC3** | Add a fusion pair (Queen+Knight → Amazon) | Content adder | **trivial** | table entry + F10 ordering |
| **UC4** | Add a piece that leaps like a knight but 3 squares | Content adder | **easy** | movement is already `(directions × limit)` |
| **UC5** | Add an event that freezes 2 random enemy pieces for 2 turns | Content adder | **easy** | it *is* `viec_nhe_vol_cao` with another selector |
| **UC6** | Use my own sprites and sounds | Reskinner | **medium** | `src/ui/assets.py` builds fixed paths |
| **UC7** | Add a new ability (teleport to any empty square, 4 AP) | Content adder | **medium** | needs a movement effect + target validator |
| **UC8** | **Add a new status — "burning: dies after 3 turns"** | Content adder | **hard** | **F1** — status meaning is decentralized |
| **UC9** | Event that fires when a queen is captured | Content adder | **hard** | **F5** — one hardcoded trigger for all events |
| **UC10** | Make fusion need two captures instead of one | Rule bender | **hard** | fusion flow is engine-side |
| **UC11** | **Play vanilla chess — disable fusion and events** | Tuner | **medium** | base mod granularity — **now decided, see below** |
| **UC12** | **Turn it into shogi (drops, promotion zones, 9×9)** | Total converter | **very hard** | board size is a constant; drops have no concept |
| **UC13** | *(probe)* Pieces have HP; captures deal damage instead of removing | Rule bender | **very hard** | capture is atomic; no custom piece properties |
| **UC14** | *(probe)* A piece gains a power when a condition is met | Content adder | **hard** | all abilities are active/AP-gated; no conditions |
| **UC15** | *(probe)* Missions that track progress and grant rewards | Content adder | **hard** | new content type; no counters; no reward vocabulary |
| **UC16** | **Undo / Ctrl-Z the last turn** | Player *(new persona)* | **medium** | **shape, not vocabulary** — needs every state change to be a reversible action. Free if Wave 3 does it; unbuildable if it doesn't |
| **UC17** | **A mod adds UI — a chess clock, a live colour theme** | UI modder *(new persona)* | **hard** | rendering was core-only until CLAUDE.md was amended. Needs a UI extension surface the rebuild did not plan for |

**UC16–17 added 2026-07-17, by the project owner, after Wave 0.** They are **features, not probes** —
the distinction that governs UC13–15 does not apply here. Both are wanted in the product.

---

## UC16 — Undo, and why the mechanism is the whole decision

**The requirement is ordinary; the game is not.** Chess undo is trivial. *This* game has random
events, fusion that merges two pieces into one, and statuses that tick — so "undo the last turn"
has to reverse things that were never designed to be reversed.

**Decided: undo reverses a recorded action log. It does not replay effects.**

migration-plan §2.3 already commits to `Move` being a list of actions (`Relocate`, `Remove`,
`Replace`) with one `undo(action)` per type, because `get_valid_moves` needs to simulate and roll
back thousands of times per turn. **UC16 is that same mechanism, extended from moves to every state
change** — including what effects, events and abilities do.

**Why this beats the obvious alternative, and why it is an extensibility decision rather than a game
design one.** The competing option is to capture an RNG seed per turn and replay deterministically.
It works for the base game and **fails the moment a mod is involved**: seeds require every random
effect to draw from an RNG core owns, so a code mod calling `random.random()` breaks undo silently.
An action log cannot break that way — it records *what happened*, never *why*, so it reverses a
third-party effect the engine has never heard of exactly as well as `tai_xiu`.

That is the project's own rule applied literally: *prefer the version of the work where a modder could
have done it.* Undo stops being a feature and becomes **a property the shape has**.

| | Action log ✅ | RNG seed replay ❌ |
|---|---|---|
| A mod's custom effect | reversed; no engine knowledge needed | must use core's RNG or it breaks |
| A code mod using `random` | works | **silently broken** |
| Fusion (2 pieces → 1) | `Replace` inverts | works |
| Cost | effects must emit actions, never mutate | seed plumbing through every effect |

**The one hard requirement, and its deadline: effects emit actions; they never mutate state
directly.** This must land with the effect engine in **Wave 3**. Write the six effect verbs as direct
mutations and undo is unbuildable without rewriting all six. There is no cheap retrofit.

**What is *not* decided, deliberately.** Whether a player may undo past a random event to fish for a
better roll is **policy**, not mechanism — a balance question, and mods will disagree about it. The
action log makes either answer implementable, which is the point. Do not bake one in.

> ⚠️ **E1 already found the landmine, before undo was a requirement.**
> `engine-gap-analysis.md` §on the move log: *"`_rollback_last_move` pops the log and immediately
> touches `move.piece_moved`. On a dict that is an `AttributeError` … any future undo feature pops
> whatever is on top. A landmine, not a bug."* The move log mixes `Move` objects with
> `{"ability_turn": color}` dicts. **UC16 is precisely the feature E1 predicted would detonate it**,
> and the fix it named — one turn-record type covering moves and abilities — is now required rather
> than tidy.

---

## UC17 — UI mods, and the contradiction they exposed

**The requirement:** a mod can add a chess clock, or switch the piece colour scheme at runtime.

**This was impossible by construction, and CLAUDE.md has been amended.** The core/content table read
*"Rendering, input, audio playback | Sprites, sounds, text"* — everything drawn was core, and mods got
only the pictures. migration-plan §4 reinforced it: *"Scope creep into UI → Four touch points.
Nothing else."*

**But the table contradicted the prime directive sitting three paragraphs above it**, which says that
if a feature can only be added by editing core, *"that is a defect in the engine, not a task for the
modder."* A timer mod that cannot draw a clock is exactly that. The prime directive is the older and
stronger claim, so **the table was what was wrong** — this is a correction, not a new ambition.

**The line now: core owns the loop, mods own what goes in it.** Core draws, dispatches input, plays
audio. Mods *register* what to draw — a HUD element, a palette. No mod calls pygame directly; core
never names a mod's panel.

**What the two examples actually need**, which is smaller than "make the UI moddable" sounds:

| Capability | Status |
|---|---|
| A quantity that counts down | ✅ **exists** — `resource` (`base:ap`) already models per-side quantities. A clock is a resource in seconds |
| Somewhere to draw it | ❌ **missing** — no HUD registry. This is the real gap |
| A real-time tick | ❌ **missing** — the engine is turn-based; the 60fps loop exists in `main.py` but nothing turn-side listens to wall-clock time |
| Lose on flag fall | ⚠️ **needs a game-over condition**, which core currently hardcodes as checkmate/stalemate |
| A live colour theme | ❌ **missing** — `assets.py` builds fixed paths at load; nothing re-reads them |

**Note what this reveals: a clock is mostly a `resource` plus a place to put it.** The vocabulary is
closer than the plumbing — which is the usual shape of this project's findings, and a decent sign the
spec is sound.

**Sequencing, honestly stated.** UC17 is **not** Wave 1–4 work; the rebuild's scope is the engine, and
the UI's four touch points remain the plan through cutover. But **UC16's deadline is real and UC17's
is not**: undo constrains the effect engine in Wave 3, whereas a HUD registry can be added after the
engine runs without rewriting it. Do not let UC17 expand the rebuild. Do not let UC16 slip past
Wave 3.

---

## UC13–15 are probes, not features

**We are not building HP, missions, or conditional rewards.** They are examples of the *class* of
thing a modder must be able to add seamlessly. The project's goal is frictionless extension — not
accumulating features.

They earn their place as **acceptance tests**. Each asks: *could someone add this without us
touching `src/`?* If the answer is no, the engine has failed, and we learn it on paper instead of
after shipping. They are load-bearing precisely because they are things we will never write.

This also resolves a question that looked blocking: *"with HP, does fusion trigger on capture or on
kill?"* It is not ours to answer. Whoever adds HP decides. We only owe them a pipeline with stage
boundaries they can hook.

### What they have in common

Read separately, HP, conditional powers, and missions look like three unrelated features. They are
not — each reduces to the same machinery, which is why three probes are enough to test the shape:

| Use case | Trigger | Condition | Effect | Custom state |
|---|---|---|---|---|
| **UC13** HP | piece attacked | damage ≥ HP? | destroy / reduce HP | `hp` on each piece |
| **UC14** Power | any game event | arbitrary predicate | grant ability / status | condition inputs |
| **UC15** Mission | any game event | progress ≥ target? | reward effect | per-player counters |

All three are **trigger → condition → effect, plus mod-defined state**. Build that once and all
three become *content* rather than engine work. That is the good news, and it is significant.

The bad news is what it implies:

1. **Piece properties must be open, not a fixed schema.** HP is just the first mod-defined stat.
   If the piece schema hardcodes `hp`, the next modder wants mana, armour, or morale. The schema
   needs an open property bag, and effects need to read and write arbitrary properties.
2. **The engine must emit game events.** UC14 and UC15 need to subscribe to things like
   `piece_captured`, `turn_started`, `piece_moved`, `property_changed`. Today the engine emits
   nothing — `run_post_move_systems` is a hardcoded ordered list, not a bus.
3. **The capture pipeline must decompose into hookable stages.** UC13 is impossible while capture
   is one atomic "remove the piece" step. It needs *attack → damage → death → fusion* as distinct,
   interceptable stages. This also raises a real game-design question: **with HP, does fusion
   trigger on capture or on kill?** That is yours to answer, not the engine's.
4. **Conditions must be data.** A predicate language over game state — the thing every declarative
   system eventually grows, and the thing most likely to metastasize into a bad programming
   language (see the Phase B trap in the roadmap).

## What the probes actually require

The probes are not requests for features, so they do not license building features. They divide
cleanly against the model from Phase B (*content is data; code adds verbs*):

**Shape — we build this.** Seamless extension is impossible without it, and retrofitting it means
rewriting everything above it:

- **open piece properties** — so `hp` can simply exist as data
- **an event bus** the engine emits into (`piece_captured`, `turn_started`, …)
- **a staged move/capture pipeline** — *attack → damage → death → fusion* as hookable boundaries,
  rather than one atomic "remove the piece"
- **trigger → condition → effect** as the universal content shape

**Vocabulary — we do not build this.** No base-game content needs `modify_property`, `grant_ap`, or
counters, so under the "vocabulary is earned" rule they stay unwritten. A modder who wants HP ships
a **code mod** registering a damage stage hook and a `modify_property` verb — and from that moment
HP is data, for them and for everyone else.

**We never write HP. We make HP writable.** That is the whole distinction, and the probes exist to
test exactly that path.

This keeps the anti-gold-plating rule intact rather than straining it. The shape is earned by the
extensibility requirement itself; the verbs are earned by real content. `CLAUDE.md` reflects this.

---

## Definition of done for v1

**Must support (non-coder, data only):** UC1, UC2, UC3, UC4, UC5, UC6, UC8, UC11

UC8 is a **confirmed must** (Gate 1). It is the acid test: it looks like a content-adder task and
prices like an engine rewrite, purely because of finding F1 — poison has no central meaning, so each
piece class independently decides what it does. If the spec makes UC8 easy, the status system is
right. If UC8 stays hard, we have moved the hardcoding rather than removed it.

**Architecture must not preclude (shape, not vocabulary):** UC9, UC12, UC13, UC14, UC15

These must be reachable by *adding verbs to a working system*, never by a rewrite or a fork. They
are acceptance tests, not deliverables — **none of them get built**.

**Out of scope for v1:** UC10.

## Decisions from Gate 1

- **UC8 (new status) is a must.** Confirmed. Primary Phase B target.
- **UC11 (vanilla chess) matters.** This **decides roadmap D2**: the base game splits into
  `base:chess`, `base:fusion`, `base:events` rather than one monolithic base mod. Disabling
  `base:events` must yield a playable standard chess game. This is no longer a coin flip — a
  requirement decided it, and it conveniently forces the base game to exercise dependency
  resolution (`base:fusion` depends on `base:chess`).
- **UC12 (total conversion) is a goal**, not a design check. Board dimensions, starting layout, and
  promotion rules must therefore leave `src/constants.py` in the **first** migration wave, not the
  last. Shogi-class conversion is the yardstick.
- **UC13, UC14, UC15 added as probes** — extensibility acceptance tests, explicitly **not features
  to build**. The project's goal is seamless extension, not feature accumulation.

## Open questions

1. ~~Are UC13–15 v1 content or later content?~~ **Neither — they are never built.** They are probes.
   We make HP writable; we do not write HP.
2. ~~With HP, does fusion trigger on capture or on kill?~~ **Dissolved.** Not our decision — whoever
   adds HP makes it. The engine owes only hookable stage boundaries. (Roadmap D11 retired.)
3. ~~How far does the condition language go?~~ **Answered in Phase B:** pure predicates over game
   state — no loops, no assignment, no arithmetic beyond comparison.
4. **Which use case is still missing?** This list covers the existing game plus three probes.
   Someone wanting something we never thought of is exactly who the project is for — and the probes
   only prove the shape against things we *did* think of.
