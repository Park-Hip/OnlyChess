# ADR-003 — Content validation and source positions

**Status:** accepted (roadmap C4 / research backlog; unblocked by Wave 0 spike S1)
**Date:** 2026-07-17

## Context

The loader must validate every mod's content at stage 5 and report failures under the error contract
in [loader-lifecycle.md](../spec/loader-lifecycle.md#the-error-contract):

```
ERROR  base:chess  pieces/pawn.yaml:11:35
  field:     moves[0].limt
  problem:   unknown key 'limt'
  expected:  one of capture, dirs, limit, type, when
```

Every error carries **mod id · file · line:col · field path · what was wrong · what was expected**,
with no exceptions. The reader does not write Python, and `CLAUDE.md` makes this an invariant: *fail
loud, with attribution*. The unknown-key rule specifically is
[called "the highest-value rule in the loader"](../spec/loader-lifecycle.md#5-validate) — it is what
turns `limt: 3` from silent wrong behaviour into a message.

The research backlog framed this decision as **pydantic v2 vs jsonschema**, on error quality. C4
argued the framing was wrong — we write our own message layer either way, so native message quality
cannot decide it — and named two constraints that actually bite:

1. **Source positions.** Validators check a parsed structure; by then positions are gone. C4 recorded
   these as library-independent: *"neither library helps."*
2. **The vocabulary is runtime-extensible.** Code mods register verbs at stage 4, so `moves` is a
   discriminated union over a registry that does not exist at import time.

C4 then **deliberately deferred the decision to this ADR**, because the `.lc` spike was a real input
and deciding without it would be guessing. S1 ran on 2026-07-17. This ADR is written against its
results, and both candidates were tested on real base-mod content rather than argued.

## Decision

**A registry-driven validator, written by us. No validation library.**

The verb registry left behind by stage 4 already maps verb name → allowed keys. By stage 5 **the
registry *is* the schema**, so validation is a walk over the position-bearing tree, discriminating on
the `type` key and diffing key sets against the registry.

**Positions come from `ruamel`'s `.lc` data** (ADR-001, confirmed by S1), carried through validation
by *not converting to plain dicts*. `CommentedMap` is a `dict` subclass, so nothing downstream needs
to know.

**Provenance is stamped by the patch stage.** When stage 6 applies a `set` or `add`, it records
`(mod_id, file, line:col)` — the position in the **patch's** file — for the field it wrote, in a side
table keyed by node identity. The resolver consults `.lc` first and the provenance table second.

## Rationale

**Pydantic is disqualified on the constraint C4 ranked first, and C4 was wrong to call that
constraint neutral.** Tested, both libraries installed:

| | positions after validation |
|---|---|
| **pydantic v2** | ❌ **destroyed by construction** — it copies input into new model objects; `.lc` does not survive |
| **jsonschema** | ✅ preserved — validates in place and returns nothing |

This is not a tie broken by taste. Recovering positions under pydantic means keeping the original
tree alongside the model and walking it by the error's field path — **writing the resolver anyway,
and paying for pydantic on top.**

**jsonschema loses on the highest-value rule, and it loses on our own content.** The pawn is the
fixture that matters: `type: enpassant` is a verb `base:chess` registers *in Python at stage 4*, so
`moves` is exactly the runtime discriminated union of constraint 2. Given the real `pieces/pawn.yaml`
with one realistic typo (`limit` → `limt`):

```
jsonschema:  "{'type': 'slide', …} is not valid under any of the given schemas"
             absolute_path: ['moves', 0]        ← stops at the move, not the key
             + 7 sub-errors, one per oneOf arm:
                 "Additional properties are not allowed ('limt' was unexpected)"
                 "'leap' was expected"          ← false: `type: slide` was correct
                 "'enpassant' was expected"     ← false
                 …
```

**`oneOf` cannot know which arm the author meant.** It reports that the object matched no branch and
returns one sub-error per arm, most of them lies about `type`. The true fault is one message among
seven with nothing marking it as true, and `absolute_path` stops at `moves[0]`, so the `.lc` position
points at the whole move rather than the typo.

Producing the contract's block from that requires: discriminate on `type` ourselves → pick the right
arm → diff the keys ourselves → regex the key out of prose. **That is the registry-driven walk,
wearing jsonschema as a hat.** The same walk, standalone, produced the contract's block exactly — the
header of this document is its real output — in ~25 lines and no dependency.

**So the library saves nothing.** This is the decisive point, and it is why "less to maintain" is not
the trade it appears to be: the walk is not the *cost* of rejecting a library, it is a thing we write
**either way**. The only question is whether a dependency sits underneath it producing errors we
discard.

**Why discriminating first is what makes it work.** Once `type: slide` selects the arm, an unknown key
is a set difference and `.lc.key(key)` positions the typo itself. The union is the entire difficulty,
and knowing the discriminator dissolves it. A general-purpose validator cannot use that knowledge;
we have it for free.

**Why provenance is stamped rather than degraded.** `.lc` raises `KeyError` for any key not parsed
from the file, and stage 6 **re-validates after patching**. So a patch that introduces a bad key hits
the one path the contract says must always carry `file:line:col`, and the naive resolver crashes
instead. The position is not missing — it is in the *patch's* file. Stamping it keeps ADR-002's blame
rule intact ("patch produces invalid content → blame the patch, not the original author") **with a
position attached**, which is the difference between an actionable error and a shrug. Degrading
gracefully would weaken the contract from "no exceptions" to "except when patched", and patches are
precisely where attribution is hardest to work out by hand.

**Is writing a validator the Phase B trap?** No. The trap is inventing a *language* for content
authors. This is the loader reading its own registry — the vocabulary stays exactly as small as the
verbs earn, and the walk gets no more general than the registry it reads.

## Consequences

- **We own the walk, and it grows with the vocabulary.** A new verb kind means a new arm. Accepted:
  the head-to-head shows we were writing it regardless, and it is the only version where the error
  contract is achievable rather than aspirational.
- **The tree stays position-bearing end to end.** Nothing between parse and register may convert to
  plain dicts — that discards `.lc` irrecoverably and is invisible until an error fires. **This is a
  standing invariant, not a style note**, and belongs in the gates (migration-plan S4).
- **`ruamel` is load-bearing beyond ADR-001.** It was chosen for the 1.2 pin; it is now also the
  source of every error position. Replacing it means replacing both.
- **The resolver has two sources and must consult both** — `.lc` for authored keys, the provenance
  table for patched ones. A resolver that knows only `.lc` crashes at stage 6.
- **`patch.py` carries a provenance write on every op.** Small, but it is a correctness requirement
  rather than bookkeeping: skip it and the error path breaks for exactly the mods that are hardest
  to debug.
- **No new dependency.** The project stays at `pygame` + `ruamel.yaml`. Notably `pyyaml`, `pydantic`
  and `jsonschema` are all *installed* in the dev environment and none are declared — the chokepoint
  rule (below) is what keeps that from mattering.
- **"Actively reject stock PyYAML" cannot be a runtime import guard.** S1 confirmed `import yaml`
  succeeds and always will, since PyYAML is installed. It has to be a test or lint check on what
  `parse.py` imports. Owner: migration-plan S4's standing gates.

## Alternatives rejected

| Option | Why not |
|---|---|
| **pydantic v2** | Destroys `.lc` by construction (tested). Fails constraint 1 — the one C4 ranked first — and we would write the resolver anyway |
| **jsonschema** | `oneOf` cannot discriminate a runtime union; reports the parent path with the bad key only in prose, plus false sub-errors per arm. Loses on the unknown-key rule, which is the highest-value rule in the loader |
| **Hybrid — jsonschema for structure, walk for vocabulary** | Two error paths translated into one contract, a dependency, and a split boundary every future contributor must re-derive per field. The structural half is the cheap half |
| **Resolver degrades gracefully on patched keys** | Weakens "no exceptions" to "except when patched"; loses ADR-002's blame position exactly where attribution is hardest |
| **Defer provenance to Wave 1** | The loader's data model is what the spec says is expensive to retrofit. The side table is cheap now and architectural later |
