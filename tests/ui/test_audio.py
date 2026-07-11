"""Tests for UI sound-effect helpers."""

import unittest

from src.ui.audio import (
    CAPTURE,
    MOVE,
    SoundPlayer,
    build_sound_path,
    load_sounds,
    move_sound_key,
)


class _FakeMove:
    """Minimal stand-in for Move carrying only the capture flag we read."""

    def __init__(self, piece_captured):
        self.piece_captured = piece_captured


class _RecordingSound:
    """Records how many times it was played."""

    def __init__(self):
        self.play_count = 0

    def play(self):
        self.play_count += 1


class SoundPathTests(unittest.TestCase):
    def test_build_sound_path_uses_sfx_dir_and_filename(self):
        self.assertEqual(build_sound_path(MOVE), "sfx/move-self.mp3")
        self.assertEqual(build_sound_path(CAPTURE), "sfx/capture.mp3")


class LoadSoundsTests(unittest.TestCase):
    def test_load_sounds_uses_loader_hook(self):
        loaded_paths = []

        def fake_loader(path):
            loaded_paths.append(path)
            return path

        sounds = load_sounds(sound_loader=fake_loader)

        self.assertEqual(set(loaded_paths), {"sfx/move-self.mp3", "sfx/capture.mp3"})
        self.assertEqual(sounds[MOVE], "sfx/move-self.mp3")
        self.assertEqual(sounds[CAPTURE], "sfx/capture.mp3")

    def test_load_sounds_skips_files_that_fail_to_load(self):
        def failing_loader(path):
            raise OSError("no such file")

        sounds = load_sounds(sound_loader=failing_loader)

        self.assertEqual(sounds, {})


class MoveSoundKeyTests(unittest.TestCase):
    def test_capture_move_uses_capture_sound(self):
        self.assertEqual(move_sound_key(_FakeMove(piece_captured="bp")), CAPTURE)

    def test_quiet_move_uses_move_sound(self):
        self.assertEqual(move_sound_key(_FakeMove(piece_captured=None)), MOVE)


class SoundPlayerTests(unittest.TestCase):
    def test_play_plays_known_sound(self):
        sound = _RecordingSound()
        player = SoundPlayer(sounds={MOVE: sound})

        player.play(MOVE)

        self.assertEqual(sound.play_count, 1)

    def test_play_ignores_unknown_key(self):
        player = SoundPlayer(sounds={})
        # Should not raise.
        player.play(MOVE)

    def test_muted_player_does_not_play(self):
        sound = _RecordingSound()
        player = SoundPlayer(sounds={MOVE: sound}, muted=True)

        player.play(MOVE)

        self.assertEqual(sound.play_count, 0)


if __name__ == "__main__":
    unittest.main()
