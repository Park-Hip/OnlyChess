# Refactor Documentation Check

Use this before merging a change that touches `src/modding/`, target-engine code, or `mods/`.

- Does the change belong to a named refactor wave and the engine/mod boundary it owns?
- Does it preserve the rule that base content and third-party content use the same public API?
- Did a public lifecycle stage, invariant, or current-wave boundary change? If so, update
  [status.md](status.md).
- Is the decision recorded once in the relevant spec/ADR/migration plan rather than copied into a
  second long narrative?
- Does the implementation have a minimal success test and an attributed-error test where it accepts
  mod content?
- If chess behaviour changes, is it compared through `tests/oracle/` or explicitly recorded as an
  allowed divergence?

Keep historical rationale in the relevant ADR or plan. Keep source comments focused on the local
constraint a reader needs to preserve.
