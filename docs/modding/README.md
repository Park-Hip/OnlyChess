# Modding OnlyChess

Start with the [modder guide](modder-guide.md) to add ordinary data content. Read a specification
only when you need the exact contract for that content type.

## Current modding surface

| Need | Read |
|---|---|
| Create a data mod, piece, event, or pool | [Modder guide](modder-guide.md) |
| Content fields, selectors, effects, and moves | [Content schemas](spec/content-schemas.md) |
| Manifest, namespaces, dependencies, and code-mod trust | [Mod package](spec/mod-package.md) |
| Loading, errors, patches, and activation | [Loader lifecycle](spec/loader-lifecycle.md) |
| Status lifetime and modifiers | [Status model](spec/status-model.md) |
| Why a contract was chosen | `adr/` |

## Current limits

Data mods can define rules and content supported by the schemas. Trusted code mods can register
new verbs through `ModApi`; they do not bypass validation or mutate state directly.

The playable runtime does **not** yet render mod-provided sprites, sounds, themes, or HUD elements.
Do not rely on those presentation features when authoring a mod today.
