"""Generic capture-bus listener for loaded fusion tables."""

from .actions import Replace
from .piece import Piece, PieceDef


class FusionResolver:
    def __init__(self, state): self.state = state

    def __call__(self, event):
        if not event.displaced:
            return []
        for table in self.state.fusion_defs:
            if table.get("fuses_on") != "displacing_captures":
                continue
            replacement = self._composed(table, event) if table.get("compose") == "union" else self._from_rules(table, event)
            if replacement is not None:
                return [Replace(event.capturer, replacement)]
        return []

    def _from_rules(self, table, event):
        """The ordered-pair table: a declared pair becomes a declared piece."""
        for rule in table.get("rules", []):
            if event.capturer.definition.id != rule["capturer"]:
                continue
            if event.captured.definition.components[0] != rule["captured"]:
                continue
            definition = self.state.piece_defs[rule["into"]]
            return self._replace_with(event, definition)
        return None

    def _composed(self, _table, event):
        """Absorb the captured piece's components and rebuild moves from all of them.

        The alternative — the ordered-pair table above — names a hand-authored result per pair, so
        it can only fuse combinations someone wrote down. Composition fuses anything, which is the
        point, but it means a fused piece's moves are recomputed rather than authored: a piece whose
        components say rook and bishop moves exactly like a rook and a bishop, with no room for the
        tuned exception an authored piece could express.

        The identity stays the capturer's. Components accumulate in capture order, so `components[0]`
        remains the original piece and every selector reading `primary` keeps working; the id is
        unchanged, so the piece still resolves its own sprite and abilities. That mirrors what a
        captured piece contributes: vocabulary, not identity.
        """
        if event.captured.definition.royal:
            # Royalty is not absorbed. Stated as a property rather than a piece id, because core
            # naming a king would be exactly the special-casing the prime directive forbids.
            return None

        components = list(event.capturer.definition.components)
        for component in event.captured.definition.components:
            if component not in components:
                components.append(component)
        if components == list(event.capturer.definition.components):
            return None

        moves = []
        for component in components:
            source = self.state.piece_defs.get(component)
            if source is not None:
                moves.extend(source.moves)

        definition = PieceDef(
            id=event.capturer.definition.id,
            moves=tuple(moves),
            components=tuple(components),
            properties=dict(event.capturer.definition.properties),
        )
        return self._replace_with(event, definition)

    def _replace_with(self, event, definition):
        capturer = event.capturer
        return Piece(capturer.uid, definition, capturer.side, capturer.pos, capturer.has_moved, dict(capturer.statuses))
