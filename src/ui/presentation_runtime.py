"""Declarative Pygame presentation resolver; it owns no game state."""

from __future__ import annotations

from pathlib import Path
import pygame as p


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

    def glyph(self, piece_id: str) -> str:
        entry = self.result.registries.content["piece"].get(piece_id)
        return entry.value.tree.get("presentation", {}).get("glyph", "?")

    def image(self, piece_id: str, size: int):
        entry = self.result.registries.content["piece"].get(piece_id)
        path = entry.value.tree.get("presentation", {}).get("sprite")
        if not path: return None
        key = (entry.mod_id, path, size)
        if key not in self.images:
            image = p.image.load(str(self.result.mod_roots[entry.mod_id] / path)).convert_alpha()
            self.images[key] = p.transform.smoothscale(image, (size, size))
        return self.images[key]

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
