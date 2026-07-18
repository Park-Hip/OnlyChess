"""Data definitions and per-instance state for the generic engine."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PieceDef:
    id: str
    moves: tuple[dict, ...]
    components: tuple[str, ...]
    properties: dict
    #: Relative worth, declared by content and validated but until now dropped at normalization.
    #: The engine never reads it — it exists so presentation can total up who is ahead — which is
    #: why an undeclared piece is worth 0 rather than an error: a mod that does not care about
    #: material should not have to say so on every piece.
    material: int = 0

    @property
    def royal(self) -> bool:
        return bool(self.properties.get("royal", False))


@dataclass
class Piece:
    uid: int
    definition: PieceDef
    side: str
    pos: tuple[int, int]
    has_moved: bool = False
    statuses: dict[str, "StatusInstance"] = field(default_factory=dict)


@dataclass(frozen=True)
class StatusDef:
    id: str
    expiry: object
    modifies: dict


@dataclass
class StatusInstance:
    definition: StatusDef
    remaining: int | None


@dataclass(frozen=True)
class ResourceDef:
    id: str
    starting: int
    maximum: int
    gain: dict


@dataclass(frozen=True)
class AbilityDef:
    id: str
    name: str
    owner: dict
    cost: dict
    target: object
    effect: object
    when: dict
