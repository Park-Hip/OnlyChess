"""Generic capture-bus listener for loaded fusion tables."""

from .actions import Replace
from .piece import Piece


class FusionResolver:
    def __init__(self, state): self.state = state

    def __call__(self, event):
        if not event.displaced:
            return []
        for table in self.state.fusion_defs:
            if table.get("fuses_on") != "displacing_captures":
                continue
            for rule in table.get("rules", []):
                if event.capturer.definition.id != rule["capturer"]:
                    continue
                primary = event.captured.definition.components[0]
                if primary != rule["captured"]:
                    continue
                definition = self.state.piece_defs[rule["into"]]
                replacement = Piece(event.capturer.uid, definition, event.capturer.side, event.capturer.pos, event.capturer.has_moved, dict(event.capturer.statuses))
                return [Replace(event.capturer, replacement)]
        return []
