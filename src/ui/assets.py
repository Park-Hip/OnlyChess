"""Asset-loading helpers for chess piece sprites."""

import pygame as p

from ..constants import (
    BISHOP_CODE,
    BLACK,
    KING_CODE,
    KNIGHT_CODE,
    PAWN_CODE,
    QUEEN_CODE,
    ROOK_CODE,
    SQ_SIZE,
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
    BLACK + PAWN_CODE,
    BLACK + ROOK_CODE,
    BLACK + KNIGHT_CODE,
    BLACK + BISHOP_CODE,
    BLACK + KING_CODE,
    BLACK + QUEEN_CODE,
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

    from ..config import game_config

    images = {}
    for sprite_key in sprite_keys:
        color = sprite_key[0]
        piece_type = sprite_key[1:]
        # Always use the white piece as the base for dyeing
        base_key = WHITE + piece_type
        path = build_image_path(base_key, images_dir)
        
        try:
            image = image_loader(path).convert_alpha()
        except Exception as e:
            print(f"Warning: could not load {path} ({e}). Using Queen fallback.")
            image = image_loader(build_image_path(WHITE + QUEEN_CODE, images_dir)).convert_alpha()
        
        # Determine dye color
        hex_color = game_config.color_white_piece if color == WHITE else game_config.color_black_piece
        dye_color = p.Color(hex_color)
        
        # Apply dye
        image.fill(dye_color, special_flags=p.BLEND_RGBA_MULT)
        
        images[sprite_key] = scaler(image, (square_size, square_size))
    return images

def generate_dynamic_sprite(base_image, components, square_size=SQ_SIZE):
    """Draw text indicating additional fusion components over the base image.
    
    Args:
        base_image (pygame.Surface): The already loaded and dyed base image.
        components (list[str]): List of additional piece codes (e.g. ['N', 'B']).
        square_size (int): Size of the square.
    """
    if not components:
        return base_image
        
    new_image = base_image.copy()
    font = p.font.SysFont("Segoe UI", square_size // 4, bold=True)
    
    # Format text: e.g., "+N+B" or "+N*" if too many
    text_str = "+" + "+".join(components[:2])
    if len(components) > 2:
        text_str += "*"
        
    text_surface = font.render(text_str, True, p.Color("#C9A84C")) # Gold
    # Add a small black outline for readability
    outline_surface = font.render(text_str, True, p.Color("black"))
    
    rect = text_surface.get_rect(bottomright=(square_size - 2, square_size - 2))
    new_image.blit(outline_surface, rect.move(1, 1))
    new_image.blit(outline_surface, rect.move(-1, -1))
    new_image.blit(outline_surface, rect.move(1, -1))
    new_image.blit(outline_surface, rect.move(-1, 1))
    new_image.blit(text_surface, rect)
    
    return new_image
