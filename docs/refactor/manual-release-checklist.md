# Manual Release Checklist

Run from a clean checkout after dependencies have been installed by the documented project setup.
Do not treat an old successful run as current release evidence.

1. Confirm the clean checkout can import the declared dependencies and run the canonical test command
   from [status.md](status.md):
   `uv run python -m unittest @test_modules -q` after constructing `test_modules` with `rg`.
2. Temporarily add a mod whose `engine:` range excludes `ENGINE_VERSION`; verify it is rejected with an
   attributed compatibility error. Remove the fixture before continuing.
3. Start `python main.py`; the menu lists Standard Chess, Advanced Chess, and Prism Arena.
4. Open the Mods screen; verify installed metadata, the code-trust badge, and attributed startup errors.
5. Start Prism Arena; verify the 6x6 violet theme, Prism glyphs, bounded clicks, legal moves, status icon,
   HUD layout, sound cue, undo, and restart by returning to the menu.
6. Start Standard Chess; verify castling, en passant, promotion choice, ability targeting, sound, and undo.
7. Start Advanced Chess; verify resource display, fusion, event warning/execution, status marker, and complete-turn undo.
8. Temporarily introduce an invalid mod asset/reference and verify startup reports its mod, file, field, and correction.
