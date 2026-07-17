"""The differential oracle — migration-plan Wave 0, S2.

The migration is a rebuild, and the whole argument rests on keeping the old
engine alive as a differential oracle: build the new engine behind the loader,
compare the two on the same positions, cut over when they agree. See
`docs/modding/migration-plan.md` §0.

This package is that comparison. Today both sides are the old engine, which is
why it is built now — while it is trivially green, and cheap to get right.

**It is an equality-modulo-a-list test, not an equality test.** The spec has
deliberate divergences (the pawn's `has_moved` double-step, `max` status
stacking, the castling fix). Every difference the oracle reports is either a bug
or on `divergences.py`'s list, and the list is short enough to review.

Layout:

    position.py     FEN <-> GameState. The position description.
    adapters.py     The engine-agnostic interface, and the old engine behind it.
    perft.py        Node counting, and published ground truth.
    divergences.py  The written list of deliberate differences.
"""
