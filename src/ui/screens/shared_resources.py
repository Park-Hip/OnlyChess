"""Resources loaded once at startup and shared across screens."""


class SharedResources:
    """Holds piece images, fonts, and the menu background so each screen does not reload them."""

    def __init__(self, images, fonts, menu_background):
        self.images = images
        self.fonts = fonts
        self.menu_background = menu_background
