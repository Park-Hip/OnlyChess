"""Base class for application screens (a basic Scene pattern).

main() only forwards pygame events to the current screen and swaps to
next_screen when a screen requests it. All game or menu rules live inside
the concrete screen subclasses, not in main().
"""


class Screen:
    """A self-contained application screen.

    Subclasses override handle_event(), update(), and draw() to implement
    their own behavior. A screen requests a transition by setting
    next_screen to another Screen instance, and requests application exit
    by setting should_quit to True.
    """

    def __init__(self):
        self.next_screen = None
        self.should_quit = False

    def handle_event(self, event):
        """Handle a single pygame event."""

    def update(self, dt):
        """Update per-frame logic (animations, ai)."""

    def draw(self, surface):
        """Draw the screen onto the given surface."""
