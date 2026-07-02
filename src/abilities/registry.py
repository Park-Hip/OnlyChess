"""Ability registry and public ability lookup helpers."""

from .base import Ability

_ABILITY_REGISTRY: dict[str, Ability] = {}


def register_ability(ability_class):
    """Register an ability class by stable key."""
    ability = ability_class()
    _ABILITY_REGISTRY[ability.ability_key] = ability
    return ability_class


def get_ability(ability_key):
    """Return a registered ability instance."""
    return _ABILITY_REGISTRY[ability_key]


def get_registered_ability_keys():
    """Return all registered ability keys."""
    return tuple(_ABILITY_REGISTRY.keys())


def get_abilities_for_piece(piece):
    """Return abilities available from a piece's standard or fused identity."""
    if piece is None:
        return []
    return [
        ability
        for ability in _ABILITY_REGISTRY.values()
        if any(code in piece.get_fusion_tags() for code in ability.owner_piece_codes)
    ]


def use_ability(ability_key, game_state, source_square, target_square):
    """Use an ability from a source square against a target square."""
    source_piece = game_state.board.get_piece_at(source_square[0], source_square[1])
    return get_ability(ability_key).use(game_state, source_piece, target_square)
