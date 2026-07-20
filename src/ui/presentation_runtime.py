"""Declarative Pygame presentation resolver; it owns no game state."""

from __future__ import annotations

from pathlib import Path
import pygame as p

from .mod_preview import sprite_path


class PresentationRuntime:
    def __init__(self, result, mode_id: str):
        self.result, self.mode_id = result, mode_id
        mode = result.registries.content["game_mode"].get(mode_id).value.tree
        self.config = mode.get("presentation", {})
        self.images = {}
        self.sounds = {}

    def palette(self):
        if not self.config: return None
        return self.result.registries.content["theme"].get(self.config["theme"]).value.tree["palette"]

    def hud_widgets(self):
        """Return the mode's declared HUD widget list (ordered), or [] when unthemed.

        The loader validates that every entry is a well-formed {type, slot, ...}, so the
        renderer can trust the shape without a use-site guard.
        """
        if not self.config: return []
        return self.result.registries.content["hud_layout"].get(self.config["hud_layout"]).value.tree["widgets"]

    def glyph(self, piece_id: str) -> str:
        entry = self.result.registries.content["piece"].get(piece_id)
        return entry.value.tree.get("presentation", {}).get("glyph", "?")

    def _load_sprite(self, entry, path: str, size: int):
        """Load and scale an owned PNG, cached by mod/path/output size."""
        key = (entry.mod_id, path, size)
        if key not in self.images:
            image = p.image.load(str(self.result.mod_roots[entry.mod_id] / path)).convert_alpha()
            self.images[key] = p.transform.smoothscale(image, (size, size))
        return self.images[key]

    def _lightest_base(self, entry, namespaced: str, root, sides):
        """The palest of a piece's side sprites, used as the canvas when a colour is applied.

        Dyeing works by multiplying, so it can darken but never lighten: tinting the black artwork
        red leaves it black. `development` sidestepped this by always dyeing the white sprite, which
        it could hardcode. Choosing the palest sprite by measurement gets the same result without
        core knowing which side is which — a mod whose sides are Amber and Violet works too.
        """
        key = ("__base__", namespaced)
        if key not in self.images:
            best, brightness = None, -1.0
            for side in sides:
                path = sprite_path(namespaced, side, root)
                if not path.is_file():
                    continue
                surface = p.image.load(str(path)).convert_alpha()
                value = sum(p.transform.average_color(surface)[:3])
                if value > brightness:
                    best, brightness = path, value
            self.images[key] = best
        return self.images[key]

    def image(self, piece_id: str, size: int, side_id: str | None = None, tint=None, sides=()):
        """The piece's artwork at this size, or None when it has only a glyph.

        Two declarations reach this, and both were already in use: `presentation.sprite` names one
        image for the piece, while a top-level `sprite:` names a per-side set laid out the way
        `mod_preview.sprite_path` resolves it. The second exists because most pieces need one
        picture per side and the first cannot express that — a white rook and a black rook would
        share an image. The menu preview already understood the per-side form; the board did not,
        which is why base chess rendered as letters.
        """
        entry = self.result.registries.content["piece"].get(piece_id)
        tree = entry.value.tree
        path = tree.get("presentation", {}).get("sprite")
        if path:
            return self._load_sprite(entry, path, size)
        namespaced = tree.get("sprite")
        if not namespaced or side_id is None:
            return None
        root = self.result.mod_roots[entry.mod_id]
        if tint is not None:
            base = self._lightest_base(entry, namespaced, root, sides or (side_id,))
            return self._dyed(entry, base, root, size, tint) if base else None
        resolved = sprite_path(namespaced, side_id, root)
        return self._load_sprite(entry, str(resolved.relative_to(root)), size) if resolved.is_file() else None

    def _dyed(self, entry, base_path, root, size: int, tint: str):
        """A sprite multiplied by the player's chosen colour, cached like any other image."""
        key = (entry.mod_id, str(base_path), size, tint)
        if key not in self.images:
            surface = self._load_sprite(entry, str(base_path.relative_to(root)), size).copy()
            surface.fill(p.Color(tint), special_flags=p.BLEND_RGBA_MULT)
            self.images[key] = surface
        return self.images[key]

    def status_presentation(self, status_id: str) -> dict:
        """The status's declared presentation block ({} when it declares none)."""
        return self.result.registries.content["status"].get(status_id).value.tree.get("presentation", {})

    def status_icon(self, status_id: str, size: int):
        """The status's owned icon sprite, or None when it declares only a glyph."""
        entry = self.result.registries.content["status"].get(status_id)
        path = entry.value.tree.get("presentation", {}).get("icon")
        return self._load_sprite(entry, path, size) if path else None

    def play(self, notices):
        if not self.config or not p.mixer.get_init(): return
        cues = self.result.registries.content["sound"].get(self.config["sound"]).value.tree.get("cues", {})
        sound_entry = self.result.registries.content["sound"].get(self.config["sound"])
        for notice in notices:
            path = cues.get(notice.kind)
            if path:
                key = (sound_entry.mod_id, path)
                if key not in self.sounds: self.sounds[key] = p.mixer.Sound(str(self.result.mod_roots[sound_entry.mod_id] / path))
                self.sounds[key].play()
