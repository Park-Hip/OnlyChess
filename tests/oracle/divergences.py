"""The written list of deliberate differences between the old and new engines.

**This list is what makes the oracle an oracle.** Without it, "the engines
disagree" is a judgement call every time, and the project drifts into explaining
away failures one at a time. With it, every difference the oracle reports is
either a bug or it is *here* — and migration-plan §4 names the failure mode
precisely: the list growing until it explains everything.

    | The oracle's divergence list grows until it explains everything
    | -> Cap it. Four entries are known. A fifth needs a written argument.

`test_divergences.py` enforces that cap, so adding one is a deliberate act with a
reviewer rather than a quiet append.

**Nothing here is live yet.** Until Wave 3 both sides of the oracle are the old
engine, so no divergence can fire. The list is written now, while the entries are
still fresh in the spec, because reconstructing "was that a bug or a decision?"
six weeks from now is exactly the archaeology this project keeps paying for.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Divergence:
    """One deliberate old-vs-new difference, with its receipt.

    `source` is mandatory and is the point of the whole structure: a divergence
    without a document behind it is an excuse.
    """

    id: str
    summary: str
    source: str
    wave: int
    detection: str


# migration-plan §4: "Four entries are known. A fifth needs a written argument."
#
# ⚠️ The number is genuinely ambiguous in the specs, and it is recorded here
# rather than silently resolved. migration-plan §0's box names THREE
# (`pawn_double_step`, `status_stacking`, `castling_through_attack`) but says
# "here are the four places we didn't, on purpose". §4 says four are known.
# roadmap's E2 table says the castling fix took the list "4 -> 5". The three
# named below are the ones with an unambiguous source; `ability_turn_rule` is
# added on the strength of E1 §5.2 + migration-plan §2.6, which say outright
# that the rule must be BUILT rather than preserved — that is a behaviour change
# by definition, so it belongs on the list whatever the count says.
#
# CAP EQUALS THE CURRENT COUNT, deliberately. Setting it any higher would let the
# next entry land silently — which is precisely what §4 says must not happen, so a
# cap with headroom is not a cap at all. Raising this number IS the written
# argument: it forces a commit, a diff, and a reviewer.
CAP = 4

DIVERGENCES = (
    Divergence(
        id="pawn_double_step",
        summary=(
            "The pawn's first double-step gates on `has_moved` in the new engine, "
            "and on the pawn's RANK in the old one."
        ),
        source="content-schemas.md finding 3; migration-plan §0",
        wave=3,
        detection=(
            "Invisible in positions reached by legal play — pawns never move "
            "backwards, so a white pawn on rank 2 has provably never moved and the "
            "two rules agree. It fires only under colour conversion "
            "(`mat_quyen_cong_dan`), which makes it a Wave 5 concern in practice. "
            "See position.py for why this dictates how random positions are made."
        ),
    ),
    Divergence(
        id="status_stacking",
        summary=(
            "Stacking across different statuses is order-independent in the new "
            "engine (most-restrictive wins); the old engine has no rule at all."
        ),
        source="status-model.md (left open); migration-plan §0 and §2.7",
        wave=3,
        detection=(
            "Not reachable through move generation alone; needs two statuses on one "
            "piece, which only events produce. Structural tests, not the oracle."
        ),
    ),
    Divergence(
        id="castling_through_attack",
        summary=(
            "The old engine allows castling through an attacked square in a case it "
            "should not: it offers `e1g1` while a black pawn on e2 attacks f1."
        ),
        source="migration-plan §1 and §6.3 (decided: FIXED, not preserved)",
        wave=4,
        detection=(
            "The new engine will offer FEWER moves than the old one in positions "
            "where a pawn attacks a castling transit square. A pawn is required: "
            "`square_under_attack` asks 'does any enemy MOVE end here?' rather than "
            "'does any enemy piece THREATEN here?', and for pawns those differ in "
            "both directions. Perft is the check — see test_perft.py::kiwipete."
        ),
    ),
    Divergence(
        id="ability_turn_rule",
        summary=(
            "The new engine enforces one action per turn for abilities. The old "
            "engine enforces nothing — only the UI stops white sniping twice."
        ),
        source="engine-gap-analysis.md §5.2; migration-plan §2.6",
        wave=3,
        detection=(
            "Not visible to move generation; abilities are not moves. Needs a "
            "direct test that white cannot act twice."
        ),
    ),
)


def by_id(divergence_id):
    """Look up a divergence, or raise. Callers should not guess ids."""
    for divergence in DIVERGENCES:
        if divergence.id == divergence_id:
            return divergence
    known = ", ".join(d.id for d in DIVERGENCES)
    raise KeyError(f"unknown divergence {divergence_id!r}; known: {known}")
