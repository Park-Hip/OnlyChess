"""Player preferences: the one layer that is allowed to overrule a mod.

Everything else on screen belongs to the active mode — themes, glyphs, sprites, HUD layout — and
core only renders what content declares. Settings are the exception, and the reason is that they
answer a different question. A theme says what the mod's author wants the game to look like; a
setting says what this player can actually see and how long they want to play for. A mod cannot
know either.

The override is deliberately narrow. Settings may replace named palette tokens and supply a clock
length; they cannot introduce colours a theme did not have, and an unset value leaves the mod's own
choice untouched. `Settings()` with nothing configured is exactly today's behaviour.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

#: Where preferences live. `development` used the same filename at the project root.
SETTINGS_FILE = "config.json"

#: Offered clock lengths, in minutes. `None` means no clock, which is what every mode has today and
#: must stay reachable — a timed game is an option, not the default.
CLOCK_CHOICES = (None, 5, 10, 15, 30)

#: Palette tokens a player may override, mapped to the setting key that overrides them.
OVERRIDABLE = {"board_light": "light_square", "board_dark": "dark_square"}

#: Piece colours are not palette tokens: a piece is drawn from its own artwork, so the colour has to
#: dye that artwork rather than replace a colour name. Keyed by seat — the side that moves first and
#: the one after it — because side ids belong to content and a setting must not name them.
PIECE_KEYS = ("piece_first", "piece_second")

#: Presets per setting. Cycling beats a colour picker for a keyboard-and-mouse menu, and a curated
#: list cannot produce a combination that fails the contrast check below by accident.
COLOR_CHOICES = {
    "light_square": ("#E8D5B5", "#EEEED2", "#D9C7A7", "#CFD8DC", "#F0D9B5"),
    "dark_square": ("#8B6F47", "#769656", "#6B4F3A", "#546E7A", "#B58863"),
    "piece_first": ("#FFFFFF", "#F5DEB3", "#B0C4DE", "#E9967A", "#98D8A0"),
    "piece_second": ("#3A3A3A", "#8B3A3A", "#3A5A8B", "#5A3A6B", "#6B5A3A"),
}

#: Below this Euclidean RGB distance two colours read as the same at a glance, and pieces vanish
#: into the board. `development` used the same threshold.
MIN_CONTRAST = 60.0


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def contrast(first: str, second: str) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(hex_to_rgb(first), hex_to_rgb(second))))


@dataclass
class Settings:
    """Player preferences, loaded once at startup and applied over mod content."""

    clock_minutes: int | None = None
    colors: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path) -> "Settings":
        """Read preferences, falling back to defaults on anything unreadable.

        A corrupt or hand-edited settings file must not stop the game starting: unlike mod content,
        which fails loudly because a modder needs to know, this is a preferences file whose worst
        case is the player seeing default colours and setting them again.
        """
        path = Path(root) / SETTINGS_FILE
        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(stored, dict):
            return cls()
        minutes = stored.get("clock_minutes")
        colors = stored.get("colors")
        return cls(
            clock_minutes=minutes if minutes in CLOCK_CHOICES else None,
            colors={key: value for key, value in colors.items() if key in COLOR_CHOICES and isinstance(value, str)} if isinstance(colors, dict) else {},
        )

    def save(self, root: Path) -> None:
        path = Path(root) / SETTINGS_FILE
        path.write_text(json.dumps({"clock_minutes": self.clock_minutes, "colors": self.colors}, indent=2), encoding="utf-8")

    @property
    def time_limit(self) -> float | None:
        """Seconds for a new session, or None when the player wants no clock."""
        return self.clock_minutes * 60 if self.clock_minutes else None

    def apply(self, palette: dict | None) -> dict | None:
        """Return the mode's palette with the player's overrides laid on top.

        Returns the palette unchanged when nothing is set, so a mod's theme reaches the screen
        exactly as authored until a player decides otherwise.
        """
        if not palette or not self.colors:
            return palette
        resolved = dict(palette)
        for token, key in OVERRIDABLE.items():
            if key in self.colors and token in resolved:
                resolved[token] = self.colors[key]
        return resolved

    def piece_color(self, seat: int) -> str | None:
        """The colour chosen for the player in this seat, or None to leave the artwork alone."""
        if 0 <= seat < len(PIECE_KEYS):
            return self.colors.get(PIECE_KEYS[seat])
        return None

    def conflicts(self) -> list[str]:
        """Report colour pairs too close to tell apart, so the menu can refuse to save them."""
        chosen = {key: self.colors[key] for key in COLOR_CHOICES if key in self.colors}
        problems = []
        keys = sorted(chosen)
        for index, first in enumerate(keys):
            for second in keys[index + 1:]:
                if contrast(chosen[first], chosen[second]) < MIN_CONTRAST:
                    problems.append(f"{first.replace('_', ' ')} and {second.replace('_', ' ')} are too similar to tell apart")
        return problems
