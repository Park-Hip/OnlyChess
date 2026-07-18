"""Resources loaded once at startup and shared across screens."""

from pathlib import Path

from ...settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[3]

class SharedResources:
    """Holds presentation resources shared by the active screens.

    The engine game screen currently needs fonts and the menu background. ``images`` and
    ``sound_player`` remain optional while the retired legacy screen is still present.
    """

    def __init__(self, images, fonts, menu_background, app_context, sound_player=None, settings=None, settings_root=None):
        self.images = images
        self.fonts = fonts
        self.menu_background = menu_background
        self.app_context = app_context
        self.sound_player = sound_player
        # Defaulted rather than required: a screen constructed without preferences behaves exactly
        # as it did before settings existed, which keeps every existing test honest.
        self.settings = settings if settings is not None else Settings()
        #: Where `save()` writes. Held here rather than inside Settings so a test can point it at a
        #: temporary directory without the settings object knowing anything about the filesystem.
        self.settings_root = settings_root if settings_root is not None else REPO_ROOT
