# Chess Fusion Phase 6 Advanced Events Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Advanced Mode global event pool from `mode.md` in a clean, student-friendly OOP style, using the current `events/` architecture with minimal core rewrites.

**Architecture:** Keep the existing simple event architecture: `ChessEvent` for lifecycle contract, `EventManager` for timing/orchestration, and one class per event for behavior. Use registry-based event creation and avoid hardcoded event branching in `GameState`.

**Tech Stack:** Python 3.12, Pygame, `unittest`, current `src/` package layout

---

## Planned File and Folder Structure After Phase 6

```text
src/
├── constants.py
├── game/
│   ├── board.py
│   ├── rules.py
│   └── ...
├── events/
│   ├── __init__.py
│   ├── base.py
│   ├── manager.py
│   ├── registry.py
│   ├── gia_xang_tang.py                  # Existing baseline event (kept and verified)
│   ├── umamusume.py                       # New
│   ├── my_danh_iran.py                   # New (My danh Iran)
│   ├── tai_xiu.py                         # New
│   ├── comeout.py                         # New
│   ├── viec_nhe_vol_cao.py                # New
│   ├── nguoi_chong_bat_luc.py             # New
│   ├── kho_ga_tron_ba_mia.py              # New
│   ├── long_toi_tan_nat_khi_nhan_ra_toi_la_gay.py  # New
│   └── mat_quyen_cong_dan.py                 # New (Mat quyen cong dan)
└── ...

tests/
└── events/
    ├── test_event_base_contract.py
    ├── test_event_manager_flow.py
    ├── test_gia_xang_tang_event.py        # Existing baseline tests (kept and extended if needed)
    ├── test_umamusume_event.py             # New
    ├── test_my_danh_iran_event.py         # New
    ├── test_tai_xiu_event.py               # New
    ├── test_comeout_event.py               # New
    ├── test_viec_nhe_vol_cao_event.py      # New
    ├── test_nguoi_chong_bat_luc_event.py  # New
    ├── test_kho_ga_tron_ba_mia_event.py   # New
    ├── test_long_toi_tan_nat_khi_nhan_ra_toi_la_gay_event.py  # New
    └── test_mat_quyen_cong_dan_event.py       # New
```

---

## Recommended Execution Order

1. **Phase A:** Lock baseline event behavior and include GiaXangTang in verification.
2. **Phase B:** Implement deterministic one-shot transformation/removal events.
3. **Phase C:** Implement random one-shot events with edge-case handling.
4. **Phase D:** Implement timed status events requiring turn tracking.
5. **Phase E:** Final event-pool wiring, docs, and full regression.

---

## Phase A: Baseline Lock and Contract Alignment

**Purpose:** Keep current event foundation stable before adding complexity.

### Task A1: Keep GiaXangTang as reference event in this phase

**Files:**
- Verify: `src/events/gia_xang_tang.py`
- Verify: `tests/events/test_gia_xang_tang_event.py`
- Verify: `tests/events/test_event_registry.py`

- [x] **Step 1: Confirm existing GiaXangTang behavior is unchanged and documented**
- [x] **Step 2: Confirm `gia_xang_tang` remains registry-registered**
- [x] **Step 3: Confirm warning/execute flow still works with manager timing**

### Task A2: Confirm reusable event contract for upcoming events

**Files:**
- Verify/Adjust: `src/events/base.py`
- Verify/Adjust: `src/events/manager.py`
- Verify: `tests/events/test_event_base_contract.py`
- Verify: `tests/events/test_event_manager_flow.py`

- [x] **Step 1: Keep lifecycle methods clear (`trigger_warning`, `execute`, `cleanup`, `tick`)**
- [x] **Step 2: Keep manager timing at warning turn and execution turn**
- [x] **Step 3: Add tiny helper methods only if they reduce duplication**

---

## Phase B: Deterministic One-Shot Events

**Purpose:** Add straightforward events first to stabilize event creation pattern.

### Task B1: Implement Umamusume

**Files:**
- Add: `src/events/umamusume.py`
- Add: `tests/events/test_umamusume_event.py`

- [x] **Step 1: Transform all non-king pieces to knights**
- [x] **Step 2: Preserve piece color and board position**
- [x] **Step 3: Confirm permanence in tests**

### Task B2: Implement Long Toi Tan Nat Khi Nhan Ra Toi La Gay

**Files:**
- Add: `src/events/long_toi_tan_nat_khi_nhan_ra_toi_la_gay.py`
- Add: `tests/events/test_long_toi_tan_nat_khi_nhan_ra_toi_la_gay_event.py`

- [x] **Step 1: Remove all queens (both colors)**
- [x] **Step 2: Keep no-op behavior when no queens exist**

### Task B3: Implement Comeout

**Files:**
- Add: `src/events/comeout.py`
- Add: `tests/events/test_comeout_event.py`

- [x] **Step 1: Randomly choose one pawn from all pawns**
- [x] **Step 2: Transform it into queen on same square**
- [x] **Step 3: Keep no-op behavior when no pawns exist**

---

## Phase C: Random One-Shot Elimination/Conversion Events

**Purpose:** Implement random events with strict edge-case checks.

### Task C1: Implement Tai Xiu

**Files:**
- Add: `src/events/tai_xiu.py`
- Add: `tests/events/test_tai_xiu_event.py`

- [x] **Step 1: Randomly pick side outcome**
- [x] **Step 2: Remove one random non-king piece on affected side**
- [x] **Step 3: Enforce no-op when side has only king or no eligible piece**

### Task C2: Implement Mat Quyen Cong Dan

**Files:**
- Add: `src/events/mat_quyen_cong_dan.py`
- Add: `tests/events/test_mat_quyen_cong_dan_event.py`

- [x] **Step 1: Remove one random black pawn if available**
- [x] **Step 2: Convert one random white pawn to black pawn if available**
- [x] **Step 3: Preserve square and handle one-sided/empty edge cases**

---

## Phase D: Timed Status and Warning-Area Events

**Purpose:** Add multi-turn event effects after one-shot events are stable.

### Task D1: Implement My Danh Iran (Meteor Strike)

**Files:**
- Add: `src/events/my_danh_iran.py`
- Add: `tests/events/test_my_danh_iran_event.py`

- [x] **Step 1: Warning marks random 2x2 zone in ranks 3-6**
- [x] **Step 2: Execute removes pieces in zone on impact turn**
- [x] **Step 3: Keep selection and warning state testable**

### Task D2: Implement Viec Nhe Vol Cao

**Files:**
- Add: `src/events/viec_nhe_vol_cao.py`
- Add: `tests/events/test_viec_nhe_vol_cao_event.py`
- Update: `src/game/board.py` (minimal status state if needed)

- [x] **Step 1: Apply stunned status to all pawns**
- [x] **Step 2: Block pawn movement during stun duration**
- [x] **Step 3: Clear status after required turns**

### Task D3: Implement Nguoi Chong Bat Luc

**Files:**
- Add: `src/events/nguoi_chong_bat_luc.py`
- Add: `tests/events/test_nguoi_chong_bat_luc_event.py`
- Update: `src/game/board.py` (minimal king-mobility status if needed)

- [x] **Step 1: Immobilize both kings for one turn**
- [x] **Step 2: Confirm castling disabled during effect**
- [x] **Step 3: Confirm mobility restoration after effect**

### Task D4: Implement Kho Ga Tron Ba Mia

**Files:**
- Add: `src/events/kho_ga_tron_ba_mia.py`
- Add: `tests/events/test_kho_ga_tron_ba_mia_event.py`
- Update: `src/pieces/standard.py` (minimal movement-cap handling)

- [x] **Step 1: Select one eligible piece per side (R/N/B)**
- [x] **Step 2: Restrict movement per event rule for 3 turns**
- [x] **Step 3: Confirm automatic expiry and edge cases**

---

## Phase E: Event Pool Wiring and Final Verification

**Purpose:** Integrate all events into runtime pool and lock correctness.

### Task E1: Register all new events and expose package surface

**Files:**
- Update: `src/events/__init__.py`
- Update: `src/events/registry.py` (registration through decorators)
- Add/Update: `tests/events/test_event_registry.py`

- [x] **Step 1: Ensure all event keys are unique and stable**
- [x] **Step 2: Ensure manager can choose from complete pool**

### Task E2: Configure default event pool behavior

**Files:**
- Update: `src/events/manager.py`
- Update: `src/game/board.py` (only if constructor wiring is needed)
- Add/Update: `tests/events/test_event_manager_flow.py`

- [x] **Step 1: Keep deterministic behavior testable via injectable pools**
- [x] **Step 2: Keep empty-pool support**

### Task E3: Final documentation and regression run

**Files:**
- Update: `docs/architecture-current-baseline.md` (or follow-up architecture note)
- Update: `README.md` (if event-run note is needed)

- [ ] **Step 1: Document event pool and lifecycle briefly**
- [x] **Step 2: Run full regression suite and event subset suite**

---

## Final Verification Checklist

- [x] GiaXangTang remains implemented and verified in this phase plan.
- [x] All planned event classes from this phase are registry-wired and test-covered.
- [x] Warning/execute timing remains consistent with turn-based event flow.
- [x] Random events handle empty/edge cases safely.
- [x] Timed status events expire correctly.
- [x] Full regression suite passes.

---

## Progress Notes

- Implemented and verified baseline event: `gia_xang_tang`.
- Implemented and verified event: `umamusume`.
- Implemented and verified queen-removal event with mode-aligned naming:
  - File: `src/events/long_toi_tan_nat_khi_nhan_ra_toi_la_gay.py`
  - Event key: `long_toi_tan_nat_khi_nhan_ra_toi_la_gay`
- Implemented and verified event: `comeout`.
- Implemented and verified event: `tai_xiu`.
- Implemented and verified event: `mat_quyen_cong_dan`.
- Implemented and verified event: `my_danh_iran`.
- Implemented and verified timed status event: `viec_nhe_vol_cao`.
- Implemented and verified timed status event: `nguoi_chong_bat_luc`.
- Implemented and verified timed status event: `kho_ga_tron_ba_mia`.
- Updated default event pool so gameplay can choose from all 10 implemented events.
- Verified event subset suite: 51 tests passing.
- Verified game, piece, and UI regression suites: 66 tests passing.



