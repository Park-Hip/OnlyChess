"""The base mod's history-aware pawn capture rule."""


def generate_enpassant(context, piece, part, threat):
    if threat:
        return []
    previous = context.last_move
    if previous is None or previous.piece.side == piece.side:
        return []
    if abs(previous.start[0] - previous.end[0]) != 2:
        return []
    adjacent = context.at((piece.pos[0], previous.end[1]))
    if adjacent is not previous.piece or abs(piece.pos[1] - adjacent.pos[1]) != 1:
        return []
    if not any(move.get("type") == "enpassant" for move in adjacent.definition.moves):
        return []
    target = (piece.pos[0] + context.side(piece).forward, adjacent.pos[1])
    if not context.inside(target) or context.at(target) is not None:
        return []
    return [context.move(piece, target, remove=(adjacent,), captured=adjacent)]
