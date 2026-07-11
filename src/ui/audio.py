"""Sound-effect loading and playback for the game's UI layer.

Audio lives entirely in the UI layer: game logic decides *what* happened
(a move, a capture) and the UI decides how to *present* it. This mirrors
``assets.py`` for images, and degrades gracefully so the game still runs
when no sound files or audio device are available (e.g. headless tests).
"""

import pygame as p


# Sound keys — used instead of raw strings so callers never hardcode filenames.
MOVE = "move"
CAPTURE = "capture"

# Maps a stable sound key to its file inside the sfx directory.
SOUND_FILES = {
    MOVE: "move-self.mp3",
    CAPTURE: "capture.mp3",
}


def build_sound_path(sound_key, sfx_dir="sfx"):
    """Build the filesystem path for a sound-effect file."""
    return f"{sfx_dir}/{SOUND_FILES[sound_key]}"


def load_sounds(sound_loader=None, sound_keys=None, sfx_dir="sfx"):
    """Load sound effects keyed by their stable sound identifiers.

    A file that fails to load is skipped with a warning rather than
    crashing, so a missing asset or audio device never breaks the game.
    """
    if sound_loader is None:
        sound_loader = p.mixer.Sound
    if sound_keys is None:
        sound_keys = list(SOUND_FILES.keys())

    sounds = {}
    for sound_key in sound_keys:
        path = build_sound_path(sound_key, sfx_dir)
        try:
            sounds[sound_key] = sound_loader(path)
        except Exception as e:
            print(f"Warning: could not load {path} ({e}). Sound '{sound_key}' disabled.")
    return sounds


def move_sound_key(move):
    """Pick which sound a completed move should play.

    This is the single extension seam for move audio: to add a castle,
    promotion, check, or fusion sound later, add a key above and one
    branch here — no other code needs to change.
    """
    if move.piece_captured is not None:
        return CAPTURE
    return MOVE


class SoundPlayer:
    """Plays loaded sound effects, tolerating missing sounds and muting.

    ``play`` never raises: an unknown key, a sound that failed to load,
    or a playback error is silently ignored so audio can never interrupt
    gameplay.
    """

    def __init__(self, sounds=None, muted=False):
        self.sounds = sounds or {}
        self.muted = muted

    def play(self, sound_key):
        """Play the sound for ``sound_key`` if available and not muted."""
        if self.muted:
            return
        sound = self.sounds.get(sound_key)
        if sound is None:
            return
        try:
            sound.play()
        except Exception:
            pass
