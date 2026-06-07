"""Action Point tracking for active abilities."""

from ..constants import AP_GAIN_MOVE_INTERVAL, BLACK, MAX_AP, STARTING_AP, WHITE


class ActionPointTracker:
    """Track AP and completed move counts for both players."""

    def __init__(self):
        self.ap_by_color = {WHITE: STARTING_AP, BLACK: STARTING_AP}
        self.move_count_by_color = {WHITE: 0, BLACK: 0}

    def gain_for_move(self, color):
        """Record one completed move and award AP when the interval is reached."""
        self.move_count_by_color[color] += 1
        if self.move_count_by_color[color] % AP_GAIN_MOVE_INTERVAL == 0:
            self.ap_by_color[color] = min(MAX_AP, self.ap_by_color[color] + 1)

    def get_ap(self, color):
        """Return the AP available to one player."""
        return self.ap_by_color[color]

    def get_move_count(self, color):
        """Return the number of completed moves by one player."""
        return self.move_count_by_color[color]

    def can_spend(self, color, amount):
        """Return whether a player has enough AP to spend."""
        return self.ap_by_color[color] >= amount

    def spend(self, color, amount):
        """Spend AP if possible and return whether the spend succeeded."""
        if not self.can_spend(color, amount):
            return False
        self.ap_by_color[color] -= amount
        return True
