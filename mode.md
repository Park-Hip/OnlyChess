# OnlyChess: Advanced Mode Design Document

This document outlines the design and mechanics for the "Advanced Mode" in OnlyChess, introducing chaotic and strategic layers through Piece Fusions, Unique Abilities, and Global Events.

---

## 1. Fusion Mechanics

Players can fuse pieces through combat. When a piece captures an enemy piece, the player may optionally trigger a fusion — transforming the capturing piece into a powerful hybrid.

**How to Fuse:**
- Fusion is triggered when a friendly piece captures an enemy piece.
- After the capture, the player is prompted: **Fuse** or **Normal Capture?**
- Fusion is optional — the player can always decline.
- A piece can only be part of one fusion at a time (no chaining fusions).
- Fusion cannot be performed before **Turn 5** to prevent early-game exploits.
- When a fused piece is captured, **both component pieces are permanently removed** from the game.

**Possible Fusions:**
*   **Knight captures Bishop = Archbishop**: Moves like both a Knight and a Bishop. Extremely deadly in closed positions.
*   **Rook captures Knight = Chancellor**: Moves like both a Rook and a Knight. Excellent for mating nets.
*   **Rook captures Bishop = Tempo Burst**: No permanent hybrid. The Rook gains a **one-time free extra move** immediately after the fusion capture, then remains a Rook.

---

## 2. Piece Abilities (Active Skills)

Standard pieces gain unique active abilities. Abilities are not free; they require a resource called **"Action Points" (AP)**.

**Action Points (AP) System:**
*   Each player starts with 0 AP.
*   Players gain **+1 AP every 2 moves**.
*   Maximum AP capacity is **5**.
*   Capturing an enemy piece does **not** grant AP.

**Abilities:**
*   **Knight's Swap (Cost: 2 AP)**: Instead of a normal move, the Knight targets a friendly piece on the board and swaps positions with it.
*   **Bishop's Snipe (Cost: 3 AP)**: The Bishop "shoots" an enemy piece in its line of sight, capturing it without moving to that square. The path must be clear.
*   **Rook's Shield (Cost: 3 AP)**: The Rook deploys a shield to itself and all adjacent friendly pieces (horizontal/vertical). Shielded pieces cannot be captured on the opponent's next turn.
*   **Pawn's Sprint (Cost: 1 AP)**: A pawn can move 3 squares forward (if unobstructed), regardless of whether it is its first move or not.

**How to activate:** Right-click a friendly piece to open its "Ability Menu", select the ability, and target the appropriate square.

---

## 3. Special Events (Global Disruptions)

To break the predictability of standard chess, "Global Events" occur periodically.

**Event Triggers:**
*   Events trigger exactly every 10 full turns (Turn 10, Turn 20, etc.).
*   Players receive a "Warning" 1 turn before the event happens so they can brace for impact.

**Event Pool (Chosen randomly):**
1.  **Meteor Strike**: A random 2x2 area on the board is highlighted in red. At the start of the next turn, any piece (friend or foe) in that area is destroyed. The 2x2 area will only spawn within **ranks 3–6**, never on the starting ranks of either player (ranks 1, 2, 7, and 8).
2.  **Hidden Minefield**: 3 invisible landmines are spawned randomly on empty squares. They are invisible to BOTH players (so no screen-cheating). The first piece to step on a mined square is instantly destroyed. Mines expire after **4 turns**. If a new Minefield event occurs while mines are still active, the old mines are replaced and the timer resets. Any other event resolves normally alongside the active Minefield.
3.  **Tectonic Shift**: Two random adjacent columns on the board slide vertically by 1 square. Pieces pushed off the edge of the board wrap around to the other side.
4.  **Necromancy**: Both players may choose to revive one captured minor piece (Knight/Bishop). The player chooses **which** piece to revive, but the square is randomly assigned from available empty squares on their starting rank. This event only activates if the player has **at least 3 captured pieces** at the time of the event.
5.  **Ice Storm**: All empty squares become "slippery" for **1 turn only**. Pieces like Rooks, Bishops, and Queens must move to the absolute end of their path (until they hit another piece or the edge of the board) — they cannot stop midway.

---

## Next Steps for Implementation
To implement this mode in Pygame, the following architecture changes will be required:
1.  **State Tracking**: `GameState` will need new variables for `white_ap`, `black_ap`, `turn_counter`, `active_mines[]`, `mine_expiry_turn`, and `fused_pieces[]`.
2.  **UI Overlays**: We will need a right-click context menu for abilities, AP display per player in the sidebar, and a "Turn Counter / Next Event" countdown display.
3.  **Custom Piece Classes**: Creating classes like `Archbishop(Piece)` and `Chancellor(Piece)` with combined move validation logic.
4.  **Fusion Prompt**: A post-capture modal asking the player to choose Fuse or Normal Capture, triggered only when a valid fusion pair is detected.
5.  **Event System**: Event queue resolved at the end of every 10th turn. Warning flag triggers on turns 9, 19, 29, etc.