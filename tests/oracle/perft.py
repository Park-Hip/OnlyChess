"""Perft — node counting, and the external ground truth the oracle needs.

**Why this is here at all.** The differential oracle is old-vs-old until Wave 3,
which makes it trivially green: same engine both sides, so it cannot detect a bug
in itself. If `position.py` silently dropped castling rights, both sides would
drop them identically and the comparison would still pass — and Wave 3 would
inherit a broken oracle with a clean record.

Perft fixes that. The counts below are published, verified by every chess engine
ever written, and owe nothing to this project:
https://www.chessprogramming.org/Perft_Results

So perft tests three things at once, none of which old-vs-old can:

1. **The harness.** A FEN adapter that loses castling rights or the en-passant
   target cannot hit these numbers.
2. **The old engine**, against ground truth rather than against itself.
3. **The divergence list** — a documented difference should show up *here*, as a
   specific count mismatch, rather than as a vague sense that chess is hard.
"""

from .position import STARTING_FEN

# name -> (fen, {depth: nodes}). The standard suite; each position exists to
# break a specific class of engine, which is why they are worth more than the
# start position alone.
POSITIONS = {
    # The opening. Catches nothing exotic; proves the basics.
    "start": (STARTING_FEN, {1: 20, 2: 400, 3: 8902, 4: 197281}),

    # "Kiwipete" — the standard castling/pins torture test. Both sides can castle
    # both ways, and squares around the king are attacked. This is the position
    # that should speak to migration-plan §1's castling-through-check claim.
    "kiwipete": (
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        {1: 48, 2: 2039, 3: 97862},
    ),

    # Sparse, en-passant heavy, with a rook pin along the 5th rank.
    "position3": ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", {1: 14, 2: 191, 3: 2812}),

    # Promotion-heavy: a white pawn on a7 and a black pawn on b2. This is the
    # position that catches an engine collapsing four promotions into one move.
    "position4": (
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
        {1: 6, 2: 264, 3: 9467},
    ),

    # Promotions plus a cramped king. Catches move-generation edge cases.
    "position5": (
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        {1: 44, 2: 1486, 3: 62379},
    ),
}


def perft(engine, fen, depth):
    """Count leaf nodes `depth` plies below `fen`.

    Deliberately naive — no hashing, no bulk counting at depth 1. The oracle is
    correctness infrastructure; a clever perft that disagrees with a simple one
    costs more to debug than it ever saves.

    **The real cost is the FEN round-trip, not this loop, and it is a conscious
    trade.** `apply` rebuilds a whole `GameState` per node and regenerates its
    move list to resolve the UCI string, so kiwipete depth 3 costs ~10s where
    make/unmake on a single state would be far cheaper. That price buys the thing
    the oracle exists for: the interface is FEN in, FEN out, so **no engine
    internals cross it** and the new engine plugs in at Wave 3 without the
    comparison knowing anything about either side. An engine-specific fast path
    would compare representations instead of chess. migration-plan §4 says not to
    optimise the engine; this says the same about the harness.
    """
    if depth == 0:
        return 1
    moves = engine.legal_moves(fen)
    if depth == 1:
        return len(moves)
    return sum(perft(engine, engine.apply(fen, uci), depth - 1) for uci in moves)


def perft_divided(engine, fen, depth):
    """Nodes per first move — `{uci: count}`.

    The debugging tool, not the test. When a total is wrong, comparing this
    against a reference engine's divided output localises the fault to a single
    move in one step, instead of bisecting a tree by hand.
    """
    if depth < 1:
        raise ValueError("divided perft needs depth >= 1")
    return {
        uci: perft(engine, engine.apply(fen, uci), depth - 1)
        for uci in sorted(engine.legal_moves(fen))
    }
