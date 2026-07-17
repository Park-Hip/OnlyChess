"""★ The public verb path — the only way a verb comes to exist.

The loader calls `register(api)` at stage 4. **Mods do not import from `src`.** They are
handed this object and it is the entire surface.

```python
# mods/base-chess/code/__init__.py
def register(api):
    api.move_type("castle", castle_fn, threatens=False)
    api.move_type("enpassant", enpassant_fn)
```

Injection rather than imports, for four reasons that are worth keeping written down because
the cheaper design looks identical from the outside:

- **It answers a real open question.** `loader-lifecycle.md` asks whether `code/__init__.py`
  is imported or exec'd, since mods live outside `sys.path`. Injection dissolves the
  question — the mod never reaches toward us, so where we are stops mattering.
- **It makes privilege impossible to hide.** `CLAUDE.md` says the base mod gets no private
  API. Under imports, "no privilege" is a *convention*: nothing stops core reaching into a
  registry directly. Under injection this object **is** the surface, and if `base:chess`
  needed something extra it would have to be a visibly different object.
- **It makes the claim testable.** Pass a recording fake to `base:chess`'s `register` and
  assert exactly what it registers. That is the dogfooding claim as an executable test, and
  no other design has it.
- **It gives the loader control of the freeze.** The vocabulary freezes when the last
  `register(api)` returns, enforced by the object going dead rather than by discipline.

**Why this raises where the content path collects.** `loader-lifecycle.md`'s
collect-every-error rule exists for a specific person: a non-coder with six typos who would
otherwise run the game six times. A code mod's `register()` is not that person — stage 4's
own failure table says to report the traceback, "this reader *does* write Python". So an api
misuse raises immediately, the loader catches it, and the mod is disabled. Fail-fast is
correct here and wrong one stage later, for the same reason: the audience changed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .errors import ContentError
from .registries import Registries, qualify


class ModApiError(Exception):
    """A code mod used the api wrongly. Carries a contract-shaped error for the report."""

    def __init__(self, error: ContentError):
        self.error = error
        super().__init__(error.format())


@dataclass(frozen=True)
class MoveType:
    """A registered way of generating moves.

    `threatens` is not decoration. §1 of the migration plan traces a live chess bug to the
    engine conflating "moves I can make" with "squares I attack": `castle` is a move that
    threatens nothing, and today's `include_castle` flag is the hack that half-expresses it.
    Making the distinction a property of the verb is what lets threat generation stop being
    a special case — so the field exists because a bug earned it, not on speculation.
    """

    id: str
    generate: Callable[..., Any]
    threatens: bool


class ModApi:
    """What a code mod is handed. One instance per mod, per load.

    Scoped to one mod on purpose: the object knows whose namespace to qualify names into and
    whose id to put on an error, so a mod cannot register into someone else's namespace by
    forgetting a prefix. That check lives in the registry, but the api is what makes it
    unambiguous who is asking.
    """

    def __init__(self, mod_id: str, registries: Registries):
        self._mod_id = mod_id
        self._registries = registries
        self._live = True

    @property
    def mod_id(self) -> str:
        """The mod this api speaks for. Readable so a mod can log or namespace its own data."""
        return self._mod_id

    def move_type(self, name: str, generate: Callable[..., Any], *, threatens: bool = True) -> str:
        """Register a move type, making `type: <name>` available to every data mod.

        This is the escape hatch **growing the language, not bypassing it**: a modder who
        needs shogi drops adds a `drop` move type here, and from then on every data mod can
        write `type: drop` without touching Python. `base:chess` uses this exact call for
        `castle` and `enpassant` — if that path were privileged, the dogfooding claim would
        be a lie.

        `name` may be unqualified; it resolves into this mod's namespace, so `"castle"`
        registered by `base:chess` becomes `base:castle` — which is what the pawn's bare
        `type: enpassant` resolves to as well. Returns the qualified id.
        """
        return self._register("move_type", name, lambda entry_id: MoveType(entry_id, generate, threatens))

    def _register(self, kind: str, name: str, build: Callable[[str], Any]) -> str:
        if not self._live:
            raise ModApiError(
                ContentError(
                    mod_id=self._mod_id,
                    file="<registration>",
                    problem=(
                        f"tried to register the {kind} '{name}' after loading finished"
                    ),
                    expected=(
                        "every verb registered from register(api); the vocabulary is frozen "
                        "once the last mod's register() returns"
                    ),
                )
            )

        entry_id = qualify(name, self._mod_id)
        error = self._registries.verbs[kind].add(entry_id, build(entry_id), self._mod_id)
        if error is not None:
            raise ModApiError(error)
        return entry_id

    def _retire(self) -> None:
        """End this api's authority. Called by the loader when stage 4 closes.

        The vocabulary freeze is a real requirement rather than tidiness: a verb registered
        after validation would mean content was checked against an incomplete vocabulary,
        which is the `KeyError`-at-turn-20 failure wearing a hat.

        The object going dead is what makes the freeze structural. A mod that stashes its
        api and calls it from a later hook gets a clear error naming the verb it tried to
        add, rather than a mysterious half-registration — and core never has to police a
        global.
        """
        self._live = False
