# OnlyChess

A moddable chess game (Python 3.12 / Pygame). Standard chess is the starting point, not the
product: pieces fuse when they capture, and global events reshape the board mid-game.

The project is mid-refactor from a hardcoded game into a mod-driven one. Read "Current state"
below before assuming the code matches this document — right now it largely does not.

## Prime directive

**The core is an engine. All content is a mod.**

Content — pieces, abilities, events, fusion rules, board setup, tuning — must be definable
without editing `src/`. The target audience includes people who do not write code. If a feature
can only be added by editing core, that is a defect in the engine, not a task for the modder.

**The base game is a mod.** Standard chess, fusion, and the event set load from `mods/base/`
through exactly the same path a third-party mod uses. The base mod gets no privileges, no
private APIs, no shortcuts. This is the project's forcing function: if the mod API cannot
express the base game, the API is incomplete — and the game visibly breaks, which is the point.
Never special-case the base mod in the engine, not even temporarily.

## Core vs content

| Core (`src/`) | Content (`mods/`) |
|---|---|
| Board geometry, move pipeline, turn lifecycle | Pieces, abilities, events, fusion rules |
| Loader, registries, validation | Board layouts, event pools, tuning values |
| The render loop, input dispatch, audio playback | Sprites, sounds, text, **HUD elements, themes** |

**The UI row was amended on 2026-07-17, and the reason matters more than the change.** It used to
read *"Rendering, input, audio playback | Sprites, sounds, text"* — putting everything drawn in core
and leaving mods only the pictures. That **contradicted the prime directive above**: if a modder
wants a chess clock and cannot draw one without editing `src/`, then by this document's own rule that
is *"a defect in the engine, not a task for the modder."* The table was the thing that was wrong.

**Core owns the loop; mods own what goes in it.** Core draws, dispatches input, and plays audio —
mods **register** what to draw. A timer mod registers a HUD element; a theme mod registers a palette.
Neither gets to call into pygame directly, and core never names one. See UC16–UC17 in
the modding contracts under `docs/modding/spec/`.

Core may never:

- import a concrete piece, event, ability, or fusion rule
- name specific content (`if piece_code == "Q"`, `if event_key == "tai_xiu"`)
- hardcode the piece roster, event pool, or fusion table
- **hardcode a HUD element, panel, or colour** that a mod could have registered
- treat `mods/base/` differently from any other mod

When a change requires core to know about a specific piece or event, stop. That is the signal
that a capability is missing from the engine. Add the capability; don't add the special case.

## Scope discipline

This project used to ban anything beyond "basic level" patterns, to keep it explainable to a
lecturer. **That constraint is retired** — a mod loader needs real machinery. It is replaced by
a narrower rule that does the same job:

**Get the shape right; keep the vocabulary small.**

**The goal is to make adding features seamless — not to add features.** Every temptation to build a
mechanic into the engine is a failure to make that mechanic addable. Prefer the version of the work
where a modder could have done it.

The **shape** is fixed and non-negotiable: trigger → condition → effect, over content with open
properties, an event bus, and a move/capture pipeline with hookable stages. Retrofitting that later
means rewriting everything above it, and without it seamless extension is impossible.

**Every state change is an action, and every action has an inverse.** Nothing — no effect, no event,
no ability, no mod — mutates game state directly; it emits actions, and the engine records them.
Added 2026-07-17, when undo became a requirement (UC16), and it belongs in *shape* rather than
*vocabulary* for a reason worth understanding:

> Undo does not replay effects. **It reverses the recorded log.** So it never asks what an effect
> *meant*, only what it *did* — which means it works for a mod's effect the engine has never heard
> of, including a random one. The alternative (replay from a captured RNG seed) forces every random
> effect to draw from an RNG core owns, and a code mod calling `random.random()` silently breaks it.
> An action log cannot be broken that way, because the outcome is recorded rather than recomputed.

This is the whole *"prefer the version where a modder could have done it"* rule paying out: undo is
not a feature we build, it is a property the shape has. **Write the effect verbs as direct mutations
and undo becomes unbuildable without rewriting all of them.**

The **vocabulary** is earned. Add a verb when real content cannot be expressed without it — never on
speculation. Generality no content exercises is dead weight that constrains every future refactor.

The base mod is the spec for the **vocabulary**, but not for the **shape**. The shape is earned by
the extensibility requirement itself, and validated against the probes in
the modding contracts (HP, conditional powers, missions). **Those probes are acceptance tests,
never deliverables.** A modder wanting HP ships a code mod registering a damage hook and a
`modify_property` verb; HP is then data. We never write HP — we make HP writable. If you find
yourself implementing a probe, stop: you have misread this file.

## Invariants

- **Namespaced string IDs.** `base:queen`, `mymod:dragon`. Two authors will both invent a
  "Dragon"; unnamespaced IDs make that a silent collision. IDs are data, never Python constants.
- **Registries are populated by the loader at runtime**, never by import side effects. Today's
  `@register_event` + `__init__.py` import list is the anti-pattern this replaces: it makes
  registration a core edit, which defeats the entire goal.
- **Fail loud, with attribution.** A content error names the mod id, file, field, and what was
  expected. A modder who does not read Python must be able to act on the message alone. Never
  silently skip malformed content — a mod that half-loads is worse than one that refuses to.
- **Validate at load, not at use.** Bad data should not surface as a `KeyError` twenty turns in.
- **Status effects are first-class.** Poison and shields are currently ad-hoc attributes stuck
  onto pieces. Mods cannot target what has no formal existence.

## Current state (pre-refactor)

The seams are the right shape — registries, rule tables, ordered post-move systems — but they are
populated by hardcoded imports. Three known blockers, in dependency order:

1. **Registration requires a core edit.** `@register_event` only fires on import, and imports live
   in `src/events/__init__.py`. Same for abilities. Needs discovery-based loading from mod folders.
2. **Identity lives in core.** Piece codes are constants in `src/constants.py`. Needs namespaced
   IDs supplied by mod data.
3. **No status system.** `piece.poisoned_turns` and `getattr(target, "is_shielded", False)` are the
   same "status with a duration" pattern implemented ad-hoc, twice.

Working in our favour: movement is already primitive-based (`_get_sliding_moves(directions, limit)`,
`_get_one_step_moves(directions)`), so data-defined pieces map onto the existing engine closely.

The deleted legacy implementation is not a source of extension guidance. The current contracts
define the supported extension surface.

## The mod model — decided

**Content is data. Code adds verbs.**

- **Data mods** (non-coders) compose content from the verb vocabulary — pieces, events, abilities,
  statuses, fusion pairs. This is empirically ~100% of the base game.
- **Code mods** (programmers) register *new verbs* — move types, effects, conditions, selectors —
  which then become available to **every** data mod as ordinary vocabulary.

The escape hatch **grows the language; it does not bypass it**. A modder who needs shogi drops adds
a `drop` move type, and from then on every data mod can write `type: drop` without touching Python.
Never let code mods define content directly — that reintroduces the bottleneck this exists to remove.

This applies to us: `base:chess` registers `castle` and `enpassant` as verbs through the same public
path any code mod uses. **If that path is privileged, the dogfooding claim is a lie.**

**Trust model: trusted local install.** Code mods run with full user privileges. Python cannot be
meaningfully sandboxed (`__subclasses__()` traversal defeats restricted namespaces; real isolation
needs VM/gVisor/WASM). **Do not build a sandbox.** Instead, a manifest declares whether a mod ships
code, and the UI surfaces it — a pure-data mod is genuinely safe to install, and most mods will be
pure data. That is a real security property, and it is free.

The active contract is data-first: code mods register verbs, and data mods compose content from them.

## The condition line

Conditions are **pure predicates over game state**. No side effects, no loops, no variable
assignment, no arithmetic beyond comparison. If something needs to *compute* rather than *ask*, it
is an effect or it is code — never a condition.

Data formats become bad programming languages one convenience at a time. This is the line.

## Prohibitions

- **God Object.** Do not funnel movement validation, rendering, rules, and fusion into one class.
  `GameState` is already the main coordinator and is under pressure — move state out, not in.
- **Magic numbers/strings.** Doubly load-bearing now: content identifiers are data, not literals
  scattered through logic.
- **Import-time registration.** See Invariants.
- **Special-casing the base mod.** See Prime directive.

## Workflow

- Read the relevant `docs/` before coding; update them when behavior changes.
- Write docstrings. Use self-documenting English names.
- Comment only non-obvious rules or math — not what the code already says.
- Explain the reasoning behind design choices.

### Always end with TLDR and Next

Every response finishes with these two, in this order, however short the task:

- **TLDR** — what happened or what was found, in a sentence or two. The answer to "just tell me."
- **Next** — the single most useful thing to do now, and who has to do it. If it is blocked on the
  human, say so and say why. If there is genuinely nothing, say that rather than inventing work.

Keep both short; the detail goes above them, not inside them. **Next** is one recommendation, not a
menu — if there is a real fork, recommend one and name the alternative in a clause.

This exists because this project is long-running, heavily documented, and easy to lose the thread of
across sessions. A reply that is correct but leaves the reader hunting for the state of play has
failed at the only thing they needed it for.

## Commands

```
python main.py        # run the game
python -m pytest      # run tests
```

Use `python -m pytest`, **not** `uv run pytest` — the latter does not put the repo root on
`sys.path` and every test dies with `ModuleNotFoundError: No module named 'src'`.

## Git

- Do NOT add a `Co-Authored-By: Claude ...` trailer to commit messages.
- Do NOT add the "Generated with Claude Code" line to PR bodies.
