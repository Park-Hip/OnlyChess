# Spec — Code Mod API

**Status:** current API surface.

Code mods are trusted Python packages. They extend the vocabulary available to data mods; they do
not define pieces directly, receive Pygame objects, or mutate engine state outside actions.

## Package shape

```text
mods/my-code-mod/
  manifest.yaml        # code: true
  code/
    __init__.py        # defines register(api)
    my_moves.py        # optional relative-imported helpers
```

```yaml
id: mymod:language
name: My Movement Language
version: 1.0.0
code: true
```

The loader loads `code/__init__.py` as a package from its path, so relative imports inside the
`code/` directory work. It calls `register(api)` once, then retires the API before content
validation begins.

## Current method

The only registered verb kind is `move_type`:

```python
from .my_moves import generate_dash


def register(api):
    api.move_type("dash", generate_dash, threatens=True)
```

Data can then use the verb in a piece definition:

```yaml
type: piece
id: mymod:runner
name: Runner
moves:
  - type: dash
    distance: 3
presentation: { glyph: R }
```

`api.move_type()` qualifies an unqualified name into the code mod's namespace. The function
receives an action-safe `MoveContext`, the current piece, the move declaration, and the threat-mode
flag. It may inspect the board and return `Move` objects built from action helpers; it must not
mutate the state directly. `threatens=False` means the verb contributes no attacked squares during
check/threat generation.

## Constraints and errors

- The manifest must say `code: true`; a `code/` directory in a `code: false` mod is a load error.
- Code runs with full local user privileges. There is no Python sandbox.
- Registration must happen during `register(api)`. Calling the API after it returns raises an
  attributed error because the vocabulary is frozen before validation.
- Names are namespaced and duplicate verb IDs are errors.
- A code-mod exception disables that mod and includes its traceback in the load report.
- A data mod can compose a registered movement verb, but cannot call Python or define content in
  code.

## Not registered yet

`ModApi` does not currently expose effect, condition, selector, trigger, HUD-widget, drawing, timer,
or other presentation registration. A clock, arbitrary per-piece overlay, or new event trigger needs
an engine/API design and a corresponding data consumer before it can become a mod feature.
