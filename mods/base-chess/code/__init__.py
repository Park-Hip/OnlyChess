"""Standard chess extends the engine through the same public API as any mod."""

from .castle import generate_castle
from .enpassant import generate_enpassant


def register(api):
    api.move_type("castle", generate_castle, threatens=False)
    api.move_type("enpassant", generate_enpassant)
