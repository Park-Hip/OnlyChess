# OnlyChess

Standard chess — until a capture fuses two pieces into something new, and a global event
turns the board upside down ten moves later.

![Full game window at the start of a match](docs/images/hero.png)

OnlyChess is a Python/Pygame chess variant built for an Object-Oriented Programming course
project. It keeps the base game fully standard-chess-legal, then layers on capture-triggered
**fusion**, resource-gated **active abilities**, and periodic **global events** that force both
players to adapt mid-game.

## What Makes It Different

- **Fusion:** capture the right piece with the right piece and the capturer transforms into a
  hybrid — an Archbishop, Chancellor, Warden, or Inquisitor — with the combined movement of both
  components. Fusion is automatic and permanent until the fused piece is captured.
- **Action Points & Abilities:** every player earns Action Points over time and can spend them
  on active skills — swap a Knight with an ally, snipe a piece with a Bishop without moving,
  shield a cluster of pieces, or sprint a Pawn three squares.
- **Global Events:** every 10 full turns, a random event resolves — meteor strikes, mass
  transformations, dice-roll piece removal, and more. A warning fires one turn ahead so players
  can brace for it.

See [`mode.md`](mode.md) for the full advanced-mode design document.

## Gameplay Showcase

<!-- screenshot: mid-game board with a fused piece (e.g. Archbishop) on it, e.g. docs/images/fusion.png -->
<!-- screenshot: event warning overlay / message log entry, e.g. docs/images/event-warning.png -->
<!-- screenshot: player panel showing Action Points and the ability menu open, e.g. docs/images/ability-menu.png -->

## Core Mechanics

### Fusion Pairs

| Capturing Piece | Captured Piece | Result | Movement |
|---|---|---|---|
| Knight | Bishop | **Archbishop** | Knight + Bishop |
| Rook | Knight | **Chancellor** | Rook + Knight |
| Rook | Bishop | **Warden** | Unlimited orthogonal + diagonal up to 3 |
| Bishop | Rook | **Inquisitor** | Unlimited diagonal + orthogonal up to 3 |

### Action Points & Abilities

Abilities cost Action Points (AP) and consume the player's entire turn. AP is gained
automatically over time (max 5), never from captures.

| Ability | Cost | Effect |
|---|---|---|
| Knight's Swap | 2 AP | Swap the Knight with any friendly piece, anywhere on the board |
| Bishop's Snipe | 3 AP | Remove an enemy piece along the Bishop's diagonal without moving |
| Rook's Shield | 3 AP | Grant the Rook and adjacent allies immunity to capture/destruction for one turn |
| Pawn's Sprint | 1 AP | Move a Pawn 3 squares forward, jumping over other pieces |

### A Few Global Events

Events trigger every 10 full turns, with a one-turn warning beforehand. A sample from the pool:

| Event | Effect |
|---|---|
| Umamusume | Every piece except Kings permanently becomes a Knight |
| Mỹ đánh Iran (Meteor Strike) | A random 2×2 zone is warned, then everything inside is destroyed |
| Tài Xỉu | A coin flip removes one random piece from a random side |
| Người Chồng Bất Lực | Both Kings are immobilized for a turn — check becomes deadly |

The full 10-event pool, triggers, and edge cases are documented in
[`mode.md`](mode.md#4-special-events-global-disruptions).

## Getting Started

Requires Python and [`uv`](https://github.com/astral-sh/uv).

```bash
uv run python run.py
```

Compatibility entrypoint (forwards to the same `src.main.main()`):

```bash
uv run python main.py
```

## Architecture & OOP Design

OnlyChess is organized around a central `GameState`, but `GameState` does not own every rule —
it coordinates focused collaborators instead:

| Package | Responsibility |
|---|---|
| `src/game/` | Board state, move legality, move execution, rollback, ordered post-move systems |
| `src/pieces/` | `Piece` base class plus standard and fused piece subclasses |
| `src/events/` | `ChessEvent` base class, concrete events, event registry, `EventManager` (timing) |
| `src/fusion/` | Capture-pair rule table and `FusionManager` (resolution) |
| `src/abilities/` | `Ability` base class, concrete abilities, ability registry |
| `src/ui/` | Pygame rendering, input handling, menus — reads game state, never decides rules |

**Inheritance** gives pieces, events, and abilities a shared contract (`Piece`, `ChessEvent`,
`Ability`) wherever the game naturally has one. **Composition** lets `GameState` delegate to
focused helpers — `EventManager`, `FusionManager`, `ActionPointTracker`, `CaptureTracker`,
`ShieldTracker` — instead of absorbing their logic. **Registries** create pieces, events, and
abilities from stable string keys, avoiding long conditional chains.

Move execution runs through an ordered list of post-move systems (capture tracking → fusion →
AP gain → shield expiry → event ticking), so new post-move mechanics slot in as one more system
rather than a new branch in `GameState`.

Full write-up: [`docs/system-overview.md`](docs/system-overview.md),
[`docs/oop-design.md`](docs/oop-design.md).

## Extensibility

The goal is that most new features are additive, not invasive:

- **New event** — add a `ChessEvent` subclass, register it, add it to the event pool.
- **New ability** — add an `Ability` subclass and register it.
- **New fusion pair** — add an entry to the fusion rule table.
- **New fused piece** — add a piece class, registry entry, fusion rule, and tests.
- **UI-only change** — edit `src/ui/` without touching gameplay rules.

Honest limits: new piece identities still need constants, new persistent state may need a
`GameState` field, and mechanics touching both moves and ability turns need care around
`GameState.finish_ability_turn()`. See
[`docs/extensibility-and-change-impact.md`](docs/extensibility-and-change-impact.md) for
worked examples.

## Testing

```bash
uv run python -m unittest discover -s tests/fusion -p "test_*.py" -v
uv run python -m unittest discover -s tests/abilities -p "test_*.py" -v
uv run python -m unittest discover -s tests/pieces -p "test_*.py" -v
uv run python -m unittest discover -s tests/game -p "test_*.py" -v
uv run python -m unittest discover -s tests/events -p "test_*event*.py" -v
uv run python -m unittest discover -s tests/ui -p "test_*.py" -v
```

Smoke test (boots the app headlessly via Pygame's dummy driver):

```bash
uv run python -c "import os; os.environ['SDL_VIDEODRIVER']='dummy'; import pygame as p; p.init(); p.event.post(p.event.Event(p.QUIT)); import run; run.main(); print('smoke-ok')"
```

## Documentation

- [docs/system-overview.md](docs/system-overview.md) — entry point, package structure, runtime flow
- [docs/oop-design.md](docs/oop-design.md) — OOP responsibilities and extension points
- [docs/extensibility-and-change-impact.md](docs/extensibility-and-change-impact.md) — concrete change scenarios
- [docs/file-map.md](docs/file-map.md) — source navigation guide
- [docs/game-domain.md](docs/game-domain.md) — core chess engine and move validation
- [docs/events-system.md](docs/events-system.md) — global special events
- [docs/fusion-system.md](docs/fusion-system.md) — capture-triggered fusion
- [docs/abilities-system.md](docs/abilities-system.md) — Action Points and active abilities
- [docs/ui-and-input.md](docs/ui-and-input.md) — UI and input boundaries
- [docs/presentation-summary.md](docs/presentation-summary.md) — slide-ready talking points
- [docs/architecture-current-baseline.md](docs/architecture-current-baseline.md) — verified baseline structure

## Tech Stack

Python, Pygame, `uv`.
