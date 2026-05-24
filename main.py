"""Project entry point that forwards to the packaged Pygame app."""

from src.main import main as run_game


def main():
    """Run the packaged Chess Fusion application."""
    run_game()


if __name__ == "__main__":
    main()
