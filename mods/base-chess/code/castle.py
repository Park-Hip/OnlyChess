"""The base mod's castle rule; core never names a rook or a king."""

def generate_castle(context, piece, part, threat):
    if threat or piece.has_moved or not context.safe_after(piece.side, []):
        return []

    row, column = piece.pos
    candidates = []
    for other in context.pieces():
        if other.side == piece.side and other.pos[0] == row and not other.has_moved:
            if context.matches(other, part.get("with", {})):
                candidates.append(other)

    moves = []
    for partner in candidates:
        direction = 1 if partner.pos[1] > column else -1
        king_target = (row, column + 2 * direction)
        partner_target = (row, column + direction)
        if not context.inside(king_target):
            continue
        between = range(column + direction, partner.pos[1], direction)
        if any(context.at((row, col)) is not None for col in between):
            continue
        king_step = context.relocate(piece, (row, column + direction))
        king_finish = context.relocate(piece, king_target)
        partner_move = context.relocate(partner, partner_target)
        if not context.safe_after(piece.side, [king_step]):
            continue
        if not context.safe_after(piece.side, [king_finish, partner_move]):
            continue
        moves.append(context.move(piece, king_target, extra=(partner_move,)))
    return moves
