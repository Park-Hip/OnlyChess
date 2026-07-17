"""Content registries and verb registries — populated by the loader, never by import.

`CLAUDE.md`: *"Registries are populated by the loader at runtime, never by import side
effects. Today's `@register_event` + `__init__.py` import list is the anti-pattern this
replaces: it makes registration a core edit, which defeats the entire goal."*

So there is no decorator here and no module-level mutation. A `Registries` object is
constructed, handed to the loader, filled, and frozen. Nothing registers itself by being
imported, which is what makes a mod folder a legitimate source of content rather than a
place core has to know about.

**Why registries are instances and not module globals.** Global registries make every test a
teardown problem and make "load these mods, but not that one" impossible — which is exactly
what gate G1 has to do to prove `castle` comes from `base:chess` and not from core. A
design where the dogfooding test cannot be written is a design that cannot support the
claim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from .errors import ContentError

#: The ten content types (content-schemas.md, "Universal rules"). `type` is what makes
#: folders cosmetic — the loader reads the declaration inside the file, never the path.
#:
#: This is not core naming content. `piece` is a *kind* of content; `base:queen` is content.
#: Core knowing the former is the schema; knowing the latter is the defect G2 hunts for.
CONTENT_TYPES = (
    "ability",
    "board",
    "event",
    "event_pool",
    "fusion",
    "game_mode",
    "patch",
    "piece",
    "resource",
    "status",
)

#: The kinds of verb a code mod can register. One, for now, and that is deliberate:
#: `CLAUDE.md` says vocabulary is earned, and `move_type` is earned by `base:chess` needing
#: `castle` and `enpassant` at Wave 4. Effects, conditions, selectors and triggers are named
#: by the specs but have no registrant until Wave 5 — and adding a kind is additive, so
#: deferring costs nothing and speculating costs a constraint on every later refactor.
VERB_KINDS = ("move_type",)

#: ID grammar (mod-package.md D4): `namespace:name`, `[a-z0-9_]+` both parts, lowercase, one
#: colon. Two authors will both invent a "Dragon"; unnamespaced IDs make that a silent
#: collision.
_ID_GRAMMAR = re.compile(r"^[a-z0-9_]+:[a-z0-9_]+$")


def is_valid_id(candidate: str) -> bool:
    return bool(_ID_GRAMMAR.match(candidate))


def namespace_of(mod_or_content_id: str) -> str:
    """The namespace part of an ID.

    A mod is identified by an ID under the same grammar as its content, so this works on
    both — `base:chess` claims `base`, and so `base:queen` is inside its namespace. The
    model closing over itself is not an accident (mod-package.md): it means there is one
    identity concept, not two.
    """
    return mod_or_content_id.split(":", 1)[0]


def qualify(name: str, mod_id: str) -> str:
    """Resolve an unqualified name against a mod's own namespace.

    mod-package.md: *"Unqualified IDs resolve to the current mod's namespace. Inside
    `base:chess`, `queen` means `base:queen`."* This is why `api.move_type("castle")` and
    the pawn's `type: enpassant` agree without either spelling `base:` — they are both
    qualified by the same rule.
    """
    return name if ":" in name else f"{namespace_of(mod_id)}:{name}"


@dataclass(frozen=True)
class Entry:
    """One registered thing and the mod that owns it.

    `mod_id` is not bookkeeping — a collision error must name *both* claimants, and it
    cannot do that unless the incumbent remembers who put it there.
    """

    id: str
    value: Any
    mod_id: str


@dataclass
class Registry:
    """One kind of thing, keyed by namespaced ID."""

    kind: str
    _entries: dict[str, Entry] = field(default_factory=dict)

    def add(self, entry_id: str, value: Any, mod_id: str) -> Optional[ContentError]:
        """Register one thing. Returns an error instead of raising, because the loader
        collects errors rather than failing fast.

        The two rules enforced here are both from mod-package.md, and both are about
        attribution rather than tidiness:

        - **A mod may only define IDs in its own namespace.** Without this, `mymod` could
          define `base:queen` and the resulting breakage would look like a bug in the base
          game.
        - **No silent overwrite.** Whoever loaded second would win, invisibly, and load
          order would become a thing modders had to reason about.
        """
        if not is_valid_id(entry_id):
            return ContentError(
                mod_id=mod_id,
                file="<registration>",
                problem=f"'{entry_id}' is not a valid id",
                expected="`namespace:name`, lowercase letters, digits and underscores only",
            )

        if namespace_of(entry_id) != namespace_of(mod_id):
            return ContentError(
                mod_id=mod_id,
                file="<registration>",
                problem=(
                    f"'{entry_id}' is in the '{namespace_of(entry_id)}' namespace, "
                    f"which this mod does not own"
                ),
                expected=f"an id starting with '{namespace_of(mod_id)}:'",
            )

        incumbent = self._entries.get(entry_id)
        if incumbent is not None:
            return ContentError(
                mod_id=mod_id,
                file="<registration>",
                problem=(
                    f"{self.kind} '{entry_id}' is already defined by {incumbent.mod_id}"
                ),
                expected="each id defined once, by one mod",
            )

        self._entries[entry_id] = Entry(id=entry_id, value=value, mod_id=mod_id)
        return None

    def get(self, entry_id: str) -> Optional[Entry]:
        return self._entries.get(entry_id)

    def drop(self, mod_id: str) -> None:
        """Remove everything one mod registered here.

        Serves `loader-lifecycle.md`'s failure policy: *"A mod with any error is disabled
        whole. Never half-loaded"* — a chess mod that loads every piece except the queen
        produces a game that looks fine and is wrong, and the player has no way to know.
        Registration happens before every error is in, so disabling whole means taking
        something back rather than never adding it.
        """
        for entry_id in [key for key, entry in self._entries.items() if entry.mod_id == mod_id]:
            del self._entries[entry_id]

    def ids(self) -> tuple[str, ...]:
        """Every registered id, sorted — so error messages and gate output are stable."""
        return tuple(sorted(self._entries))

    def __contains__(self, entry_id: object) -> bool:
        return entry_id in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[Entry]:
        return iter(self._entries.values())


class Registries:
    """Every registry, in one bag the loader fills and the engine reads."""

    def __init__(self) -> None:
        self.content: dict[str, Registry] = {name: Registry(name) for name in CONTENT_TYPES}
        self.verbs: dict[str, Registry] = {name: Registry(name) for name in VERB_KINDS}

    def drop(self, mod_id: str) -> None:
        """Disable one mod whole — content and verbs alike."""
        for registry in (*self.content.values(), *self.verbs.values()):
            registry.drop(mod_id)

    def verb_ids(self) -> tuple[str, ...]:
        """Every registered verb, across kinds — the vocabulary, as a flat list.

        Gate G3 diffs this against a golden list, which is how "is this verb earned?" ends
        up in a code review instead of in nobody's head.
        """
        return tuple(sorted(f"{kind}:{entry.id}" for kind in self.verbs for entry in self.verbs[kind]))
