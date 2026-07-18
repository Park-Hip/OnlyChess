# Manual Release Checklist

Run from a clean checkout after the automated suite passes.

1. Run the canonical test command from [status.md](status.md):
   `uv run python -m unittest @test_modules -q` after constructing `test_modules` with `rg`.
2. Start `python main.py`; the menu lists Standard Chess, Advanced Chess, and Prism Arena.
3. Open the Mods screen; verify installed metadata, the code-trust badge, and attributed startup errors.
4. Start Prism Arena; verify the 6x6 violet theme, Prism glyphs, bounded clicks, legal moves, status icon,
   HUD layout, sound cue, undo, and restart by returning to the menu.
5. Start Standard Chess; verify castling, en passant, promotion choice, ability targeting, sound, and undo.
6. Start Advanced Chess; verify resource display, fusion, event warning/execution, status marker, and complete-turn undo.
7. Temporarily introduce an invalid mod asset/reference and verify startup reports its mod, file, field, and correction.
