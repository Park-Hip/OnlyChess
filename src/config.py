"""Configuration manager for game settings."""

import json
import os
import math

from .constants import get_resource_path

CONFIG_FILE = get_resource_path("config.json")

def hex_to_rgb(hex_str):
    """Convert hex string to RGB tuple."""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """Convert RGB tuple to hex string."""
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def color_distance(c1, c2):
    """Calculate Euclidean distance between two RGB colors."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])))

class Config:
    """Manages global game settings like time and colors."""
    
    def __init__(self):
        self.clock_minutes = 10
        self.color_white_piece = "#FFFFFF"   # White
        self.color_black_piece = "#333333"   # Dark Grey
        self.color_light_square = "#E8D5B5"  # Cream
        self.color_dark_square = "#8B6F47"   # Warm brown
        
        self.load()

    def load(self):
        """Load settings from config file if it exists."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.clock_minutes = data.get("clock_minutes", self.clock_minutes)
                    self.color_white_piece = data.get("color_white_piece", self.color_white_piece)
                    self.color_black_piece = data.get("color_black_piece", self.color_black_piece)
                    self.color_light_square = data.get("color_light_square", self.color_light_square)
                    self.color_dark_square = data.get("color_dark_square", self.color_dark_square)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        """Save current settings to config file."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    "clock_minutes": self.clock_minutes,
                    "color_white_piece": self.color_white_piece,
                    "color_black_piece": self.color_black_piece,
                    "color_light_square": self.color_light_square,
                    "color_dark_square": self.color_dark_square
                }, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_color_validation_error(self):
        """Check if colors are too similar and return error message, else None."""
        colors = {
            "White Piece": hex_to_rgb(self.color_white_piece),
            "Black Piece": hex_to_rgb(self.color_black_piece),
            "Light Square": hex_to_rgb(self.color_light_square),
            "Dark Square": hex_to_rgb(self.color_dark_square)
        }
        
        threshold = 60 # Min distance for visibility
        keys = list(colors.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                if color_distance(colors[keys[i]], colors[keys[j]]) < threshold:
                    return f"{keys[i]} and {keys[j]} are too similar!"
        return None

# Global config instance
game_config = Config()
