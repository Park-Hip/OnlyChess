# New Contributor Start Here

This is the fast path for a contributor who knows the deleted legacy game.

OnlyChess is now an engine plus mods. The base game is loaded from `mods/` through the same path
as third-party content. Do not copy legacy classes or registrations into `src/` to make a feature
work; if content cannot express it, identify the missing engine capability first.

## Read these in order

1. [Legacy to current](legacy-to-current.md) — what moved and what was deliberately deleted.
2. [Architecture tour](architecture-tour.md) — how a move travels through the system.
3. [Actions and undo](actions-and-undo.md) — the invariant every state-changing change must obey.
4. [Testing](testing.md) — how to run and target the test suites.
5. [Continuation roadmap](continuation-roadmap.md) — what is done, missing, and next.
6. [Modding README](../modding/README.md) — the public content surface.
7. [Code-mod API](../modding/spec/code-mod-api.md) — the current trusted-Python extension point.

Use the normative specs only when changing a contract:

- [Content schemas](../modding/spec/content-schemas.md)
- [Loader lifecycle](../modding/spec/loader-lifecycle.md)
- [Mod package](../modding/spec/mod-package.md)
- [Presentation](../modding/spec/presentation.md)
- [Status model](../modding/spec/status-model.md)

## Run it

```powershell
uv run python main.py
```

The application discovers compatible folders under `mods/` at startup and offers every linked
`game_mode`. There is no hot reload; restart after changing content.

## The safe first change

Start with an isolated data change in a new or existing mod, then add a focused test. Good first
changes are a piece movement declaration, a theme token, a status marker, or a new mode fixture.
Avoid changing `src/` and `mods/base-*` in the same first patch.

## Non-negotiables

- Core must not name concrete content IDs or special-case the base mods.
- Registries are populated by the loader, never by import side effects.
- Conditions ask questions; effects emit actions; actions are reversible.
- Data mods compose existing vocabulary. Code mods grow vocabulary; they do not define content
  directly.
- Update the current-status document when executable behavior changes.
