"""Base ability contract."""


def is_enemy_piece(piece, target):
    """Return whether target is an enemy of piece."""
    return target is not None and target.color != piece.color


class Ability:
    """Base class for active piece abilities."""

    ability_key = "base"
    display_name = "Base Ability"
    ap_cost = 0
    owner_piece_codes = ()

    def can_use(self, game_state, piece):
        """Return whether this ability can currently be used."""
        if piece is None:
            return False
        if game_state.tempo_burst_pending and piece is not game_state.tempo_burst_piece:
            return False
        if game_state.ability_used_this_turn:
            return False
        if not game_state.action_points.can_spend(piece.color, self.ap_cost):
            return False
        return self._piece_has_ability(piece)

    def use(self, game_state, piece, target_square):
        """Spend AP, execute the ability, and consume the turn if valid."""
        if not self.can_use(game_state, piece):
            return False
        if not self.is_valid_target(game_state, piece, target_square):
            return False
        if not game_state.action_points.spend(piece.color, self.ap_cost):
            return False
        self.apply(game_state, piece, target_square)
        game_state.finish_ability_turn(piece.color)
        return True

    def _piece_has_ability(self, piece):
        """Return whether the piece or fused components grant this ability."""
        return any(code in piece.get_fusion_tags() for code in self.owner_piece_codes)

    def is_valid_target(self, game_state, piece, target_square):
        """Return whether a target square is valid for the ability."""
        return False

    def apply(self, game_state, piece, target_square):
        """Apply ability behavior."""
        raise NotImplementedError
