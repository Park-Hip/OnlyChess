# Manual Release Checklist

Run from a clean checkout after the automated suite passes.

1. Run the canonical test command in `tests/README.md`.
2. Start `python main.py`; the menu lists Standard Chess, Advanced Chess, and Prism Arena.
3. Start Prism Arena; verify the 6x6 violet theme, Prism glyphs, bounded clicks, legal moves, undo, and restart by returning to the menu.
4. Start Standard Chess; verify castling, en passant, promotion choice, ability targeting, and undo.
5. Start Advanced Chess; verify resource display, fusion, event warning/execution, status marker, and complete-turn undo.
6. Temporarily introduce an invalid mod asset/reference and verify startup reports its mod, file, field, and correction.
