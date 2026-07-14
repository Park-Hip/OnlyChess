"""Asset-loading helpers for chess piece sprites."""

import pygame as p

from ..constants import (
    ARCHBISHOP_CODE,
    BISHOP_CODE,
    BLACK,
    CHANCELLOR_CODE,
    INQUISITOR_CODE,
    KING_CODE,
    KNIGHT_CODE,
    PAWN_CODE,
    QUEEN_CODE,
    ROOK_CODE,
    SQ_SIZE,
    WARDEN_CODE,
    WHITE,
    get_resource_path,
)


STANDARD_SPRITE_KEYS = [
    WHITE + PAWN_CODE,
    WHITE + ROOK_CODE,
    WHITE + KNIGHT_CODE,
    WHITE + BISHOP_CODE,
    WHITE + KING_CODE,
    WHITE + QUEEN_CODE,
    WHITE + ARCHBISHOP_CODE,
    WHITE + CHANCELLOR_CODE,
    WHITE + WARDEN_CODE,
    WHITE + INQUISITOR_CODE,
    BLACK + PAWN_CODE,
    BLACK + ROOK_CODE,
    BLACK + KNIGHT_CODE,
    BLACK + BISHOP_CODE,
    BLACK + KING_CODE,
    BLACK + QUEEN_CODE,
    BLACK + ARCHBISHOP_CODE,
    BLACK + CHANCELLOR_CODE,
    BLACK + WARDEN_CODE,
    BLACK + INQUISITOR_CODE,
]


def get_standard_sprite_keys():
    """Return the current set of standard sprite keys used by the UI."""
    return list(STANDARD_SPRITE_KEYS)


def build_image_path(sprite_key, images_dir="images"):
    """Build the filesystem path for a sprite image."""
    return get_resource_path(f"{images_dir}/{sprite_key}.png")


def load_images(
    sprite_keys=None,
    image_loader=None,
    scaler=None,
    square_size=SQ_SIZE,
    images_dir="images",
):
    """Load and scale piece images keyed by their sprite identifiers."""
    if image_loader is None:
        image_loader = p.image.load
    if scaler is None:
        scaler = p.transform.scale
    if sprite_keys is None:
        sprite_keys = get_standard_sprite_keys()

    images = {}
    for sprite_key in sprite_keys:
        path = build_image_path(sprite_key, images_dir)
        try:
            image = image_loader(path)
        except Exception as e:
            print(f"Warning: could not load {path} ({e}). Using Queen fallback.")
            color = sprite_key[0]
            image = image_loader(build_image_path(color + QUEEN_CODE, images_dir))
        images[sprite_key] = scaler(image, (square_size, square_size))
    return images
