# ADR-001 — Data format for mod content

**Status:** accepted (roadmap C1 / D3)
**Date:** 2026-07-16

## Context

Content must be authored by non-coders. Phase B established two hard requirements the format has to
meet:

1. **Deep, irregular nesting.** Conditions nest arbitrarily (`and`/`or`/`not` trees), effects carry
   nested selectors, and events are lists of steps. Example from the feasibility study:

   ```yaml
   effect:
     type: apply_status
     status: base:shield
     to:
       - self
       - { scope: adjacent_orthogonal, filter: { friendly: true } }
   ```

2. **Comments.** The primary persona learns by copying an annotated template and changing values.
   The comment *is* the documentation, at the point of use. A format without comments moves the
   explanation somewhere the modder is not looking.

## Decision

**YAML, pinned to the YAML 1.2 core schema.**

Parsed with a library that actually implements 1.2 — `ruamel.yaml`, `pyyaml-core`, or `yaml12`.
**Not stock PyYAML**, which implements YAML 1.1; its 1.2 core schema support is a
[long-blocked pull request](https://github.com/yaml/pyyaml/issues/486).

Paired with **strict schema validation** (see roadmap C4). Format choice and validation quality are
not independent decisions — validation is what makes this one survivable.

## Rationale

**TOML is out** — weak at deep nesting. Our conditions would become `[[effect.to]]` table arrays,
which is painful to write and worse to read.

**JSON is out** — no comments, and the primary persona is a non-coder learning from templates.
Minecraft is the cautionary case: data packs are JSON, and the absence of comments is a standing
complaint in its modding community. JSON also punishes hand-editing with trailing commas and
mandatory quoting.

**YAML wins on ergonomics** but ships a real trap. Under **YAML 1.1**, bare `no`, `yes`, `on`,
`off`, `y`, and `n` [parse as booleans](https://yaml.org/type/bool.html) — the
["Norway problem"](https://tidyverse.org/blog/2026/01/yaml12-0-1-0/), where `["DE", "FR", NO, "SE"]`
silently becomes `["DE", "FR", False, "SE"]`.

This is **not hypothetical for us**. Our own sketched notation uses `on:` as the trigger key, and
direction values like `n`/`s`/`e`/`w` are an obvious way for a modder to write a move. Under 1.1,
`dirs: [n, s, e, w]` silently yields `[False, "s", "e", "w"]`.

**YAML 1.2's core schema fixes this at the root**: plain `on`/`off`/`yes`/`no`/`y`/`n` are strings;
only `true` and `false` are booleans. Pinning to 1.2 removes the entire class of bug rather than
documenting it as a gotcha.

## Consequences

- **A YAML dependency.** The project currently depends only on `pygame`. Acceptable — a modding
  system needs a parser, and writing one is far worse than depending on one.
- **The 1.2 pin is load-bearing and easy to lose.** Someone will eventually `import yaml` out of
  habit and reintroduce 1.1 semantics silently. The loader must go through one chokepoint module,
  and stock PyYAML should be actively rejected, not merely avoided.
- **Whitespace significance is the residual risk.** It is YAML's genuine weakness for non-coders —
  tabs, misaligned nesting. Mitigated by validation with precise line/column errors and by shipping
  annotated templates, but not eliminated. This is the cost we are knowingly accepting.
- Format is *reversible in principle* — the schemas are format-agnostic — but reversing it after
  mods exist in the wild breaks every one of them. Treat as effectively permanent once published.

## Alternatives rejected

| Option | Why not |
|---|---|
| JSON | no comments; hostile to hand-editing; the persona is a non-coder |
| JSON5 / JSONC | comments, but a niche parser and unfamiliar to modders |
| TOML | poor at the deep nesting conditions require |
| XML (RimWorld's choice) | comments and nesting, but verbose and dated; a harder sell to newcomers |
| YAML 1.1 (stock PyYAML) | the Norway problem, live in our own notation |
| Custom DSL | inventing a language and its tooling; see the Phase B trap |
