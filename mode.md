# OnlyChess: Advanced Mode Design Document

This document outlines the design and mechanics for the "Advanced Mode" in OnlyChess, introducing chaotic and strategic layers through Piece Fusions, Unique Abilities, and Global Events.

---

## Table of Contents
1. [Fusion Mechanics](#1-fusion-mechanics)
2. [Action Points (AP) System](#2-action-points-ap-system)
3. [Piece Abilities](#3-piece-abilities)
4. [Special Events](#4-special-events)
5. [Implementation Notes](#5-implementation-notes)

---

## 1. Fusion Mechanics

Players can fuse pieces through combat. When a piece captures an enemy piece, the player may optionally trigger a fusion — transforming the capturing piece into a powerful hybrid.

### How to Fuse

- Fusion triggers **automatically** when a **base piece** captures an **enemy base piece** that forms a valid fusion pair.
- Fusion is **forced** — the player cannot decline.
- A piece can only be part of **one fusion** at a time (no chaining fusions).
- Fusion cannot be triggered before **Turn 5** to prevent early-game exploits.
- When a fused piece is captured, **both component pieces are permanently removed** from the game.
- **Only standard captures trigger fusion.** Abilities (e.g., Bishop's Snipe), event damage (e.g., Meteor Strike, mines), and shield blocks do NOT trigger fusion.
- If a base piece captures an enemy fused piece, it checks fusion eligibility against the **original pre-fusion piece** of the target. If the pair is valid, fusion occurs. If not, no fusion occurs.
- Capturing a fused piece does NOT trigger fusion for the fused piece's own components.

### Valid Fusion Pairs

| Capturing Piece | Captured Piece | Result | Description |
|-----------------|----------------|--------|-------------|
| Knight | Bishop | **Archbishop** | Moves like both a Knight and a Bishop. Extremely deadly in closed positions. |
| Rook | Knight | **Chancellor** | Moves like both a Rook and a Knight. Excellent for mating nets. |
| Rook | Bishop | **Tempo Burst** | No permanent hybrid. The Rook gains a **one-time free extra move** immediately after the fusion capture, then remains a Rook. |

### Fused Piece Rules

- Fused pieces can use abilities from **both** of their component pieces, with their original AP costs.
- Fused pieces are still limited to **1 ability per turn** maximum (same as all pieces).
- Fused pieces share one AP pool with their owner (no separate pool).
- Fusion is permanent unless the piece is captured or transformed by an event.
- When a fused piece is affected by a transformation event (e.g., Umamusume, Giá Xăng Tăng), it follows the event's rules. If the event is temporary, the piece returns to its fused form when the event expires. If the event is permanent, the fused piece is permanently lost.

### Tempo Burst Details

- The Rook gains **one immediate extra move** after fusing via Tempo Burst.
- This extra move is a full standard move (or ability use if AP permits) and does not cost the player's normal turn.
- The Rook is **not** immune during this extra move and can be captured normally if it ends on a threatened square.
- After the extra move resolves, the Rook returns to being a standard Rook. No permanent hybrid is created.
- Tempo Burst is still considered a fusion for purposes of the "one fusion per piece" rule. A Rook that triggers Tempo Burst cannot fuse again later.

---

## 2. Action Points (AP) System

Standard pieces gain unique active abilities. Abilities are not free; they require a resource called **"Action Points" (AP)**.

### AP Rules

| Rule | Value |
|------|-------|
| Starting AP | 0 |
| AP Gain | +1 every 2 moves (tracked per player) |
| Maximum AP | 5 |
| AP on Capture | None (capturing an enemy piece does NOT grant AP) |
| AP Tracking | Each player has their own AP pool. AP gain is based on that player's move count. |

### AP Gain Timing

- White gains 1 AP after completing their 2nd, 4th, 6th, 8th, etc. move.
- Black gains 1 AP after completing their 2nd, 4th, 6th, 8th, etc. move.
- AP is awarded **at the end** of the player's turn.
- AP cannot exceed 5. Excess AP is lost.

---

## 3. Piece Abilities (Active Skills)

Standard pieces gain unique active abilities. Using an ability **consumes your entire turn** — it IS your move. You cannot move and use an ability in the same turn.

**Maximum 1 ability per turn** per player, even if a fused piece technically has access to multiple abilities.

**How to activate:** Right-click a friendly piece to open its "Ability Menu", select the ability, and target the appropriate square.

### Ability List

#### Knight's Swap
- **Cost:** 2 AP
- **Effect:** Instead of a normal move, the Knight targets a friendly piece anywhere on the board and swaps positions with it.
- **Target:** Any friendly piece, **including the King**.
- **Restrictions:** None. Both pieces occupy each other's previous squares.

#### Bishop's Snipe
- **Cost:** 3 AP
- **Effect:** The Bishop "shoots" an enemy piece in its line of sight, capturing it without moving to that square. The path must be clear (no pieces blocking).
- **Target:** Any enemy piece along the Bishop's diagonal lines of sight.
- **Result:** The target is removed from the board. The Bishop remains in place. **Does NOT trigger fusion.**
- **Restrictions:** Standard Bishop line-of-sight rules apply. Cannot snipe through pieces.

#### Rook's Shield
- **Cost:** 3 AP
- **Effect:** The Rook deploys a shield to **itself and all orthogonally adjacent friendly pieces** (up, down, left, right). Shielded pieces **cannot be captured or destroyed by ANY means** on the opponent's next turn.
- **Immunity includes:** Standard captures, ability damage (Snipe), event damage (Mỹ đánh Iran, Tài Xỉu, Mất Quyền Công Dân elimination), and any other form of removal.
- **Duration:** Opponent's next turn only. Shield expires after the opponent completes their turn.
- **Restrictions:** Does not protect against forced movement effects or transformation effects (Umamusume, Giá Xăng Tăng, Comeout, etc.). Only prevents capture/destruction.

#### Pawn's Sprint
- **Cost:** 1 AP
- **Effect:** A pawn can move exactly 3 squares forward, regardless of whether it is its first move or not.
- **Capture:** Cannot be used to capture. This is a movement-only ability.
- **Jumping:** The pawn **can jump over** pieces (both friendly and enemy) in its path. The intermediate squares do not need to be empty.
- **Obstruction:** The landing square must be empty (since it's not a capture).
- **Promotion:** If the pawn lands on rank 8 (for White) or rank 1 (for Black), it promotes immediately as per standard promotion rules.
- **Restrictions:** Cannot be used if the pawn is stunned (e.g., Việc Nhẹ Vol Cao). Requires a clear landing square.

---

## 4. Special Events (Global Disruptions)

To break the predictability of standard chess, "Global Events" occur periodically. Events introduce chaos that both players must adapt to.

### Event Triggers

- Events trigger exactly every **10 full turns** (Turn 10, Turn 20, Turn 30, etc.).
- Players receive a **"Warning"** 1 turn before the event happens (Turn 9, Turn 19, Turn 29, etc.) so they can brace for impact.
- The warning displays the **name of the upcoming event** and a brief description of what will happen.
- When triggered, the event resolves **at the start of the turn** before any player moves.

### Event Selection

- Events are chosen **randomly** from the pool.
- The same event can occur multiple times in a single game.
- All events resolve independently. If multiple events are active simultaneously (e.g., stunned pawns during an active Umamusume), they coexist and interact as specified.

---

### Event Pool

---

#### 1. Umamusume
> *Biến tất cả quân trừ Vua thành Mã.*

**Effect:**
- All pieces on the board **except Kings** are permanently transformed into Knights.
- This includes fused pieces (Archbishop, Chancellor, etc.).
- Transformed pieces lose access to their original abilities and fused movement. They move only as standard Knights.

**Duration:** **Permanent** for the remainder of the game. Pieces do not revert.

**Consequences:**
- Fused pieces (Archbishop, Chancellor) are **permanently lost** — they become standard Knights and never return to their fused form. Both original components are effectively gone.
- The board becomes an all-Knight army for both sides, fundamentally changing endgame strategy.
- Players lose access to all non-Knight abilities (Snipe, Shield, Sprint, Swap) for the rest of the game, unless a future event (e.g., Comeout) reintroduces a piece with ability access. Existing AP remains and can be used if ability-eligible pieces later appear.

**Note:** If a future event transforms pieces again (e.g., Giá Xăng Tăng would be moot since there are no Rooks anymore), apply the new transformation on top. Pieces are now Knights; further transformations treat them as Knights.

---

#### 2. Giá Xăng Tăng
> *Biến tất cả Xe thành Mã.*

**Effect:**
- All Rooks on the board are permanently transformed into Knights.
- **Chancellors (Rook + Knight fused):** Become standard Knights permanently. The Chancellor is lost forever — no reversion.
- Bishops, Queens, and other non-Rook pieces are unaffected.

**Duration:** Permanent for the remainder of the game.

**Note:** This event does NOT affect pieces that are already Knights.

---

#### 3. Mỹ đánh Iran (Meteor Strike)
> *Cảnh báo vùng 2×2 ngẫu nhiên (hàng 3–6). Đầu hiệp sau, mọi quân trong vùng bị tiêu diệt.*

**Warning Phase (Turn 9/19/29):**
- A random 2×2 area on the board is highlighted in red.
- The area only spawns within **ranks 3–6**, never on the starting ranks of either player (ranks 1, 2, 7, and 8).
- Both players can see the highlighted area and have one turn to move pieces out of (or into) the danger zone.

**Impact Phase (Turn 10/20/30):**
- **Any piece** (friend or foe) standing within the 2×2 area is **permanently destroyed**.
- Destroyed pieces are removed from the game. Fused pieces that are destroyed lose both components.
- Shielded pieces (from Rook's Shield) **are immune** and survive the strike.
- The event resolves before any player moves on that turn.

---

#### 4. Tài Xỉu
> *Tung xúc xắc. Tài thì Đen mất một quân ngẫu nhiên. Xỉu thì Trắng mất một quân ngẫu nhiên.*

**Effect:**
- A virtual dice is rolled (50/50 random — Tài or Xỉu).
- **Tài (Over):** One random **Black piece** on the board (excluding the King) is removed.
- **Xỉu (Under):** One random **White piece** on the board (excluding the King) is removed.
- The piece is selected truly randomly from all eligible pieces of that color currently on the board.

**Edge Cases:**
- If the affected side has **only a King** (no other pieces), that side loses nothing. The event still triggers but has no effect for them.
- Fused pieces count as one piece and can be selected. If removed, both components are lost.
- Shielded pieces (from Rook's Shield) **are immune** and cannot be selected. If all non-King pieces are shielded, the affected side loses nothing.

---

#### 5. Comeout
> *Biến một Tốt ngẫu nhiên thành Hậu.*

**Effect:**
- One **random Pawn on the board** (from either player) is selected.
- Selection is **truly random** across all Pawns of both colors.
- The selected Pawn is **immediately promoted to a Queen** on its current square.
- If the Pawn is stunned, poisoned, or affected by any other status effect, it retains those effects but is now a Queen.

**Edge Case:**
- If there are **no Pawns on the board** (from either player), the event has no effect. The warning still displays but nothing happens.

---

#### 6. Việc Nhẹ Vol Cao
> *Tất cả Tốt bị chích điện, không thể di chuyển trong 2 lượt.*

**Effect:**
- **All Pawns on the board** (both colors) are stunned.
- Stunned Pawns **cannot move** under any circumstances.
- **Can be captured:** Yes. Stunned Pawns can still be captured normally or targeted by abilities/events.
- **Cannot use Pawn Sprint:** Correct. Sprint is a movement ability and is blocked by stun.
- Promotion is impossible during the stun duration (since the Pawn cannot move to rank 8/1).

**Duration:** 2 turns per player (each player misses 2 opportunities to move their Pawns). After both players have made 2 moves each, all Pawns recover and move normally.

**Status Tracking:** The game tracks which Pawns are stunned and for how many remaining turns.

---

#### 7. Người Chồng Bất Lực
> *Vua không thể di chuyển trong 1 lượt.*

**Effect:**
- **Both Kings** (White and Black) are immobilized for 1 turn.
- Kings cannot move to any adjacent square. They cannot castle.
- Kings **can still** be part of other actions (e.g., a Knight can Swap with an immobilized King).
- Other pieces can still move normally, including blocking checks.

**Check and Checkmate:**
- If a King is in check, the player **must block with another piece** or capture the attacking piece — they cannot move the King away.
- If a King is in check and there is no legal block or capture, **it is checkmate.** The game ends. There are no mercy rules.
- This makes the event extremely high-stakes and forces defensive positioning before the event triggers.

**Duration:** 1 turn only. Both Kings regain mobility on the following turn.

---

#### 8. Khô Gà Trộn Bã Mía
> *Một quân Xe/Mã/Tượng ngẫu nhiên bị ngộ độc, chỉ có thể di chuyển 1 ô trong 3 lượt.*

**Effect:**
- **Each player** has one random piece selected from among their Rooks, Knights, or Bishops.
- The selected piece is **poisoned** and can only move a maximum of **1 square** per turn for 3 turns.
- The piece is chosen randomly and independently for each player. It's possible for both players to lose a Knight, or one loses a Rook and the other a Bishop, etc.

**Specific Piece Behavior:**
- **Rook (poisoned):** Can move 1 square orthogonally (up, down, left, right).
- **Bishop (poisoned):** Can move 1 square diagonally.
- **Knight (poisoned):** **Cannot move at all.** The Knight's L-shaped jump requires 2 squares of movement, which is impossible. The piece is effectively paralyzed for 3 turns.
- **Archbishop (poisoned):** Moves like a poisoned Bishop only (1 square diagonally). The Knight component is non-functional.
- **Chancellor (poisoned):** Moves like a poisoned Rook only (1 square orthogonally). The Knight component is non-functional.
- **Queen:** Cannot be selected (only Rook/Knight/Bishop are eligible).

**Duration:** 3 turns per player. Each player tracks their own poisoned piece independently. After 3 of their own moves, the poison wears off.

**Status Tracking:** The game tracks which piece is poisoned and how many turns remain per player.

**Edge Cases:**
- If a player has no Rooks, Knights, or Bishops (only Pawns, Queens, and King), that player is unaffected. The event still triggers for the other player if they have eligible pieces.
- Poisoned pieces can still be captured. Capturing a poisoned piece removes it (and the poison) from the game.

---

#### 9. Lòng Tôi Tan Nát Khi Nhận Ra Tôi Là Gay
> *Loại bỏ tất cả Hậu.*

**Effect:**
- **All Queens on the board** (both White and Black) are immediately removed.
- This includes **promoted Queens** (Pawns that previously promoted to Queen).
- Queens are permanently destroyed. They do not return.

**Edge Cases:**
- If there are no Queens on the board, the event has no effect. The warning still displays.
- Fused pieces that include a Queen component (currently none in the standard fusion list, but if added in future) would be destroyed.

**Strategic Note:** This event fundamentally alters the late-game power balance. Players with multiple promoted Queens lose all of them. Adapt accordingly.

---

#### 10. Mất Quyền Công Dân
> *Một Tốt Đen bị bắn chết. Một Tốt Trắng bị biến thành Tốt Đen.*

**Effect:**
1.  **One random Black Pawn** on the board is **eliminated** (removed from the game).
2.  **One random White Pawn** on the board is **transformed into a Black Pawn**.

**Transformation Details:**
- The transformed White Pawn becomes a **fully functional Black Pawn**.
- It remains on the **exact same square** where it stood. This can result in a Black Pawn deep in what was White's territory (e.g., on rank 2 or 3), or near promotion on rank 7.
- The new Black Pawn moves **toward White's starting side** (down the board) for promotion purposes (rank 1 for Black Pawns).
- It retains any status effects it had before transformation (stunned, poisoned, etc.).

**Edge Cases:**
- **If Black has no Pawns on the board:** The first effect (eliminating a Black Pawn) is skipped. Only the White Pawn transformation occurs.
- **If White has no Pawns on the board:** The second effect (transforming a White Pawn) is skipped. Only the Black Pawn elimination occurs.
- **If neither side has Pawns:** The event has no effect.

**Strategic Note:** This event can create instant promotion threats or remove critical defenders. Players should be aware of their Pawn positions before the event triggers.

---

## 5. Implementation Notes

### Game State Variables (Recommended)

```python
class AdvancedGameState:
    # AP System
    white_ap: int = 0
    black_ap: int = 0
    white_move_count: int = 0  # For AP gain tracking
    black_move_count: int = 0
    
    # Turn Tracking
    turn_counter: int = 0  # Increments after each full turn (White + Black)
    current_turn: str = "white"  # "white" or "black"
    
    # Event System
    pending_event: str = None  # Event name for the upcoming event turn
    event_warning_active: bool = False  # True on warning turns (9, 19, 29...)
    active_events: list = []  # Currently active event effects
    
    # Fusion Tracking
    fused_pieces: dict = {}  # {piece_id: {"components": [piece1, piece2], "type": "archbishop"|"chancellor"}}
    
    # Status Effects
    stunned_pawns: dict = {}  # {piece_id: turns_remaining}
    poisoned_pieces: dict = {}  # {piece_id: {"turns_remaining": int, "owner": "white"|"black"}}
    umamusume_active: bool = False
    impotent_kings_active: bool = False
    impotent_kings_turns_remaining: int = 0
    shielded_pieces: list = []  # piece_ids, clears after opponent's turn
    
    # Tempo Burst
    tempo_burst_pending: bool = False  # If a Rook just triggered Tempo Burst
    tempo_burst_rook_id: str = None