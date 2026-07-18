# Modding OnlyChess

Start with the [modder guide](modder-guide.md) to add ordinary data content. Read a specification
only when you need the exact contract for that content type.

Contributors porting the legacy implementation should start with
[new contributor onboarding](../onboarding/README.md) before reading the normative specs.

## Current modding surface

| Need | Read |
|---|---|
| Create a data mod, piece, event, or pool | [Modder guide](modder-guide.md) |
| Content fields, selectors, effects, and moves | [Content schemas](spec/content-schemas.md) |
| Manifest, namespaces, dependencies, and code-mod trust | [Mod package](spec/mod-package.md) |
| Write a trusted code mod | [Code-mod API](spec/code-mod-api.md) |
| Loading, errors, patches, and activation | [Loader lifecycle](spec/loader-lifecycle.md) |
| Status lifetime and modifiers | [Status model](spec/status-model.md) |
| Themes, HUDs, sprites, status icons, and sounds | [Presentation](spec/presentation.md) |
| Why a contract was chosen | `adr/` |

## Current limits

Data mods can define rules and content supported by the schemas. Trusted code mods can register
new movement verbs through `ModApi`; they do not bypass validation or mutate state directly.

The playable runtime renders mod-provided piece sprites/glyphs, status icons/glyphs, themes, sounds,
and the four built-in HUD widget types (`turn`, `resources`, `log`, and `prompt`). Presentation is
declarative and validated, but it is not an open drawing API: a data mod cannot define a new widget,
arbitrary per-piece overlay, or custom Pygame callback. There is no clock widget or clock state yet.

The runtime discovers all compatible folders under `mods/` at startup. There is no hot reload,
installer, load-order editor, or mod manager; adding a mod means placing its folder there and
restarting the application.
