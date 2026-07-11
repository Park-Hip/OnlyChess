"""Resources loaded once at startup and shared across screens."""

from ..audio import SoundPlayer


class SharedResources:
    """Holds piece images, fonts, menu background, and sound player so each screen does not reload them."""

    def __init__(self, images, fonts, menu_background, sound_player=None):
        self.images = images
        self.fonts = fonts
        self.menu_background = menu_background
        # Default to a silent player so screens always have a usable audio hook.
        self.sound_player = sound_player if sound_player is not None else SoundPlayer()
