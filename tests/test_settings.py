"""Preferences are the one layer allowed to overrule a mod, so the override stays narrow."""

import json
import tempfile
import unittest
from pathlib import Path

from src.settings import COLOR_CHOICES, MIN_CONTRAST, Settings, contrast


class SettingsTests(unittest.TestCase):
    def test_defaults_change_nothing(self):
        """An unconfigured install must behave exactly as it did before settings existed."""
        palette = {"board_light": "#AAAAAA", "board_dark": "#111111", "text": "#FFFFFF"}
        settings = Settings()

        self.assertIsNone(settings.time_limit)
        self.assertEqual(palette, settings.apply(palette))
        self.assertEqual([], settings.conflicts())

    def test_only_declared_tokens_are_overridden(self):
        palette = {"board_light": "#AAAAAA", "board_dark": "#111111", "accent": "#FF0000"}
        settings = Settings(colors={"light_square": "#EEEED2"})

        resolved = settings.apply(palette)

        self.assertEqual("#EEEED2", resolved["board_light"])
        self.assertEqual("#111111", resolved["board_dark"])
        self.assertEqual("#FF0000", resolved["accent"], "settings must not touch tokens they do not name")

    def test_a_setting_cannot_invent_a_token_the_theme_lacks(self):
        settings = Settings(colors={"light_square": "#EEEED2"})

        self.assertEqual({"accent": "#FF0000"}, settings.apply({"accent": "#FF0000"}))

    def test_a_mode_with_no_palette_is_left_alone(self):
        self.assertIsNone(Settings(colors={"light_square": "#EEEED2"}).apply(None))

    def test_clock_minutes_become_seconds_and_none_means_no_clock(self):
        self.assertEqual(600, Settings(clock_minutes=10).time_limit)
        self.assertIsNone(Settings(clock_minutes=None).time_limit)

    def test_colours_too_close_to_tell_apart_are_reported(self):
        settings = Settings(colors={"light_square": "#E8D5B5", "dark_square": "#E8D5B7"})

        problems = settings.conflicts()

        self.assertEqual(1, len(problems))
        self.assertIn("too similar", problems[0])

    def test_the_shipped_presets_never_conflict_within_a_pair(self):
        """A curated list should not let a player build an unreadable board by accident."""
        for light in COLOR_CHOICES["light_square"]:
            for dark in COLOR_CHOICES["dark_square"]:
                self.assertGreaterEqual(
                    contrast(light, dark), MIN_CONTRAST,
                    f"preset pair {light}/{dark} is below the contrast floor",
                )

    def test_piece_colours_are_addressed_by_seat_not_by_side_name(self):
        """Side ids belong to content, so a preference must not name one. Seat 0 is whoever moves
        first, which works for a mod whose players are Amber and Violet."""
        settings = Settings(colors={"piece_first": "#98D8A0", "piece_second": "#8B3A3A"})

        self.assertEqual("#98D8A0", settings.piece_color(0))
        self.assertEqual("#8B3A3A", settings.piece_color(1))
        self.assertIsNone(settings.piece_color(2), "a third seat has no preference to apply")
        self.assertIsNone(Settings().piece_color(0), "unset leaves the artwork as the mod shipped it")

    def test_piece_colours_are_not_palette_tokens(self):
        """A piece is drawn from artwork, so its colour dyes the sprite rather than replacing a
        colour name. Applying settings must leave the palette's own text colour alone."""
        palette = {"text": "#FFFFFF", "board_light": "#AAAAAA"}

        resolved = Settings(colors={"piece_first": "#98D8A0"}).apply(palette)

        self.assertEqual("#FFFFFF", resolved["text"])

    def test_settings_round_trip_through_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            Settings(clock_minutes=15, colors={"dark_square": "#769656"}).save(Path(directory))

            restored = Settings.load(Path(directory))

            self.assertEqual(15, restored.clock_minutes)
            self.assertEqual({"dark_square": "#769656"}, restored.colors)

    def test_a_missing_file_gives_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(Settings(), Settings.load(Path(directory)))

    def test_a_corrupt_file_gives_defaults_rather_than_stopping_startup(self):
        """Unlike mod content, which fails loudly because a modder needs to know, a preferences
        file whose worst case is default colours must never stop the game starting."""
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "config.json").write_text("{not json at all", encoding="utf-8")

            self.assertEqual(Settings(), Settings.load(Path(directory)))

    def test_unknown_keys_and_out_of_range_values_are_discarded(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "config.json").write_text(
                json.dumps({"clock_minutes": 999, "colors": {"light_square": "#EEEED2", "nonsense": "#000000"}}),
                encoding="utf-8",
            )

            restored = Settings.load(Path(directory))

            self.assertIsNone(restored.clock_minutes)
            self.assertEqual({"light_square": "#EEEED2"}, restored.colors)


if __name__ == "__main__":
    unittest.main()
