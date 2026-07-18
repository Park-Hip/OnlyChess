"""Resources loaded once at startup and shared across screens."""

class SharedResources:
    """Holds presentation resources shared by the active screens.

    The engine game screen currently needs fonts and the menu background. ``images`` and
    ``sound_player`` remain optional while the retired legacy screen is still present.
    """

    def __init__(self, images, fonts, menu_background, app_context, sound_player=None):
        self.images = images
        self.fonts = fonts
        self.menu_background = menu_background
        self.app_context = app_context
        self.sound_player = sound_player
