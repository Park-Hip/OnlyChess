# Wave 1: Loader Seam

**Status:** complete in `ada54c6`. This is the smallest target-engine surface that reads a mod,
registers its vocabulary, and returns an activation result. It does not run the game yet.

## Source map

| Module | Owns | Read this when |
|---|---|---|
| `src/modding/loader.py` | staged orchestration and load result | changing lifecycle or attribution flow |
| `src/modding/parse.py` | YAML 1.2 parsing, source positions, file shape/type checks | changing content-file input or diagnostics |
| `src/modding/registries.py` | collision-safe runtime vocabulary | adding a registry kind or ID rule |
| `src/modding/api.py` | capability object passed to trusted code mods | adding an extensibility verb |
| `src/modding/errors.py` | user-facing error format and suggestions | changing how malformed content is reported |
| `tests/modding/` | executable Wave 1 contracts | before changing any of the above |

`src/modding/__init__.py` is the package's intended public import surface. Prefer it over importing
private helpers across the rest of `src/`.

## Implemented lifecycle

```text
mods directory
  -> discover manifests
  -> parse YAML content
  -> load declared trusted code
  -> register content and verbs
  -> activate result
```

Errors are accumulated when later work still makes sense, then returned in one `LoadResult`. A
modder should see their mod ID, file, field/source location where available, expected correction,
and a suggestion for misspelled IDs where possible.

## What Wave 2 added

The walking skeleton adds opt-in validation and linking for `piece`, `board`, and `game_mode`.
`load(..., validate=True, link=True)` validates structure, resolves `game_mode → board → piece`, and
returns a render-only linked layout. The optional flags protect Wave 1's registry-only contract while
the other seven content types remain outside the active engine slice.

## Deliberately not implemented yet

The complete nine-stage loader design still needs dependency resolution, patching, and validation /
linking for the remaining content types. Do not add no-op functions for these stages and do not claim
other content is valid merely because Wave 1 can parse/register it. Their ordering is constrained:
vocabulary must be registered before content that uses it can be validated.

The authoritative full contract is
[loader-lifecycle.md](../modding/spec/loader-lifecycle.md). The point of this page is to make the
current boundary obvious, not to replace that specification.

## Safe changes in this wave

- Improve error attribution, deterministic discovery, registry collision handling, or public API
  clarity with focused tests.
- Add the standing architecture gates described in the migration plan when they genuinely test an
  already-implemented invariant.

## Changes that belong to a later wave

- Move generation, actions, turns, or statuses: Wave 3.
- Castle, en passant, resources, abilities, or base chess content: Wave 4.
- Fusion, event effects, conditions, or selectors: Wave 5.
