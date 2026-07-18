"""Milestone 2 catalog and viewport contracts."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.runtime import ApplicationContext, EngineSession
from src.ui.board_layout import BoardLayout
from src.ui.screens.engine_game_screen import EngineGameScreen

from .modding.builders import write_mod


class CatalogAndLayoutTests(unittest.TestCase):
    def test_independent_rectangular_mode_is_catalogued_and_builds_a_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_mod(root, "rectangular", manifest="""id: demo:rectangular
name: Rectangular Demo
version: 1.0.0
code: false
""", files={
                "piece.yaml": "type: piece\nid: demo:token\nname: Token\nproperties: { royal: true }\nmoves: []\n",
                "board.yaml": """type: board
id: demo:board
size: [3, 5]
sides:
  - { id: demo:north, name: North, forward: down, moves_first: true }
  - { id: demo:south, name: South, forward: up }
rows:
  - { row: 0, side: demo:north, fill: demo:token }
  - { row: 2, side: demo:south, fill: demo:token }
""",
                "mode.yaml": "type: game_mode\nid: demo:rectangular\nname: A Rectangular Mode\nboard: demo:board\npools: []\n",
            })
            context = ApplicationContext.load(root)

            self.assertEqual(("demo:rectangular",), tuple(mode.id for mode in context.modes))
            self.assertEqual((3, 5), (context.modes[0].rows, context.modes[0].columns))
            session = EngineSession(context.load_result, "demo:rectangular")
            self.assertEqual("North", session.state.board.sides[session.state.current_side].name)

    def test_layout_round_trips_squares_without_assuming_eight_by_eight(self):
        layout = BoardLayout.for_viewport((960, 640), 3, 5)
        self.assertEqual((3, 5), (layout.rows, layout.columns))
        self.assertEqual((2, 4), layout.square_at(layout.square_rect((2, 4)).center))
        self.assertIsNone(layout.square_at((layout.board.right + 1, layout.board.bottom + 1)))

    def test_catalog_order_is_display_name_then_id(self):
        context = ApplicationContext.load()
        self.assertEqual(tuple(sorted((mode.name.casefold(), mode.id) for mode in context.modes)), tuple((mode.name.casefold(), mode.id) for mode in context.modes))

    def test_ability_modal_lists_content_names_and_enters_target_mode(self):
        context = ApplicationContext.load()
        screen = EngineGameScreen(None, session=EngineSession(context.load_result, "base:vanilla"))
        screen.selected_square = (6, 0)
        screen.ability_choices = screen._choices()

        self.assertEqual(("Pawn Sprint",), tuple(choice.name for choice in screen.ability_choices))
        modal = screen._modal_rect()
        row = (modal.x + modal.width // 2, modal.y + 67)
        screen._choose_ability(row)
        self.assertEqual("base:pawn_sprint", screen.pending_ability)


if __name__ == "__main__":
    unittest.main()
