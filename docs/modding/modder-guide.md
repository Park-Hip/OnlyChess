# Making Mods for OnlyChess

**You do not need to know how to program to read this.** If you can edit a text file and count
squares on a chessboard, you can add pieces and events to this game.

By the end you will have written a mod that adds a new piece and a new event. Everything in the
game — the queen, the pawn, every event — is written exactly the way you are about to write yours.
There is no secret second way of doing it that the original authors used.

> ### Read this bit first: the game can run your mod
>
> The mod loader is part of the playable runtime. Once your mod is under `mods/` and enabled, the
> game parses, validates, links, and activates it through the same public path used by the shipped
> base mods. A malformed file is rejected with an attributed error before a game starts.
>
> The current runtime still renders glyphs rather than mod-provided sprites, sounds, themes, or HUD
> elements. Those presentation capabilities are planned work; pieces, rules, events, abilities,
> statuses, fusion, boards, resources, and game modes are loadable now.

---

## Contents

1. [What a mod is](#1-what-a-mod-is)
2. [Five rules that never change](#2-five-rules-that-never-change)
3. [Starting your mod: the manifest](#3-starting-your-mod-the-manifest)
4. [Task one: add a piece](#4-task-one-add-a-piece)
5. [Task two: add an event](#5-task-two-add-an-event)
6. [Making the event actually happen](#6-making-the-event-actually-happen)
7. [Reference cards](#7-reference-cards)
8. [Things you cannot do yet](#8-things-you-cannot-do-yet)
9. [When something is wrong](#9-when-something-is-wrong)
10. [Final checklist](#10-final-checklist)

---

## 1. What a mod is

A mod is **a folder with files in it**. The files are written in a format called YAML, which is
mostly just `name: value` lines.

Here is a whole mod:

```
mods/
  frostmod/
    manifest.yaml          ← who you are (every mod needs this one)
    pieces/
      griffin.yaml         ← a new piece
    events/
      cold_snap.yaml       ← a new event
```

**The folder names are for you, not for the game.** The game does not care that `griffin.yaml` sits
in a folder called `pieces/`. It knows it is a piece because the file says `type: piece` on the
first line. If you put everything in one folder called `stuff/`, your mod still works — it will
just be harder for you to find things later.

There are ten kinds of content you can write. This guide covers the two you asked about, plus the
one you need to make an event fire:

| `type:` | What it is |
|---|---|
| `piece` | A piece: how it moves, what it's worth |
| `event` | Something that happens to the whole board on a timer |
| `patch` | A small change to somebody else's file |
| `ability`, `status`, `fusion`, `board`, `event_pool`, `resource`, `game_mode` | The other seven — see the [reference cards](#7-reference-cards) |

---

## 2. Five rules that never change

### Rule 1 — Every file starts with `type:` and `id:`

```yaml
type: piece
id: frostmod:griffin
```

`type` tells the game which of the nine kinds this is. `id` is the name the game uses internally.

### Rule 2 — Every name has your mod's name in front of it

IDs look like `frostmod:griffin` — **your mod's name, a colon, then the thing's name.**

This is not bureaucracy. Two people will eventually both make a piece called "dragon". If both were
just called `dragon`, installing both mods would break. `frostmod:dragon` and `dragonmod:dragon` sit
side by side happily.

- Use **lowercase letters, numbers, and underscores only**. `frostmod:ice_golem` is fine.
  `FrostMod:IceGolem` is an error.
- **You may only invent IDs that start with your own mod's name.** You cannot write a file that says
  `id: base:queen` — that name belongs to somebody else. (There is a way to *replace* the queen; see
  the [reference cards](#7-reference-cards).)
- **When you refer to your own things, you can drop the prefix.** Inside your mod, `griffin` means
  `frostmod:griffin`. When you refer to *anybody else's* things, you must write it in full:
  `base:knight`, never `knight`.

### Rule 3 — A typo is an error, not a shrug

If you write `limt: 3` when you meant `limit: 3`, the game **refuses to load your mod and tells you
about the typo**. It does not quietly ignore the line and leave you wondering why your piece moves
wrong.

This is the single most useful thing the game does for you, and it is why the next rule exists.

### Rule 4 — Spaces, never tabs

YAML uses indentation to show what belongs inside what. **Use two spaces per level. Never press
Tab.** A tab character is invisible and breaks the file. Most text editors can be told to insert
spaces when you press Tab; it is worth doing before you start.

```yaml
moves:
  - type: leap          ← two spaces, then "- ", then the content
    offsets: [[1, 2]]   ← lines up under "type", because it's part of the same move
```

### Rule 5 — `#` starts a comment

Anything after a `#` is a note to yourself and is ignored by the game. Use them freely. The base
game's own files are full of them.

```yaml
material: 4    # worth a bit more than a knight
```

---

## 3. Starting your mod: the manifest

Every mod needs a file called exactly `manifest.yaml`, sitting at the top of your mod's folder. It
says who you are and what you need.

**`mods/frostmod/manifest.yaml`**

```yaml
id: frostmod:main             # your mod's own ID — this claims the name "frostmod"
name: Frost Mod               # what players see
version: 1.0.0                # three numbers, see below
authors: [Your Name Here]
description: >
  Adds the Griffin, and a Cold Snap event that freezes a piece on each side.

engine: "^1.0"                # which versions of the game this works with

dependencies:
  required:
    base:chess: "^1.0"        # I use base:knight and base:king, so I need this
    base:events: "^1.0"       # I use base:stun, which lives here

code: false                   # this mod is pure data — no Python
```

Three of these deserve a word.

**`version: 1.0.0`** — three numbers. The rule of thumb: change the last one for a fix, the middle
one when you add something, and the **first one only when you break something** other people were
relying on — like deleting a piece or renaming a field. Other mods can then say "I need frostmod
version 1-something" and be protected.

**`dependencies.required`** — a list of mods you cannot work without. If you name something that
isn't installed, your mod is switched off with a message saying which mod is missing. **You need one
line here for every mod whose IDs you mention.** Our griffin doesn't reference other pieces, but our
event uses `base:stun` and `base:king`, so we need both base mods.

**`code: false`** — this mod is pure data. It cannot run programs, so it is genuinely safe for
somebody to install. If you ever add a `code/` folder while this says `false`, the game refuses to
load the mod rather than trusting you. That honesty is the whole point of the field.

---

## 4. Task one: add a piece

We are making a **Griffin**: it leaps like a knight, and it can also glide up to two squares
diagonally.

**`mods/frostmod/pieces/griffin.yaml`**

```yaml
type: piece
id: frostmod:griffin
name: Griffin              # what players see
material: 4                # roughly what it's worth; a knight is 3, a rook 5

moves:
  # The knight's eight jumps.
  - type: leap
    offsets: [[1, 2], [2, 1], [2, -1], [1, -2], [-1, -2], [-2, -1], [-2, 1], [-1, 2]]

  # A short diagonal glide, up to two squares.
  - { type: slide, dirs: diagonal, limit: 2 }
```

That is a complete, working piece. Two things are worth understanding properly, because they are
where people go wrong.

### A piece's moves are a list, and it can do all of them

`moves:` is a list of **move parts**, each starting with `- `. The piece can do every part. The
Griffin has two parts, so it can leap *or* glide. If you want a piece that moves like a queen, you
give it two slides:

```yaml
moves:
  - { type: slide, dirs: orthogonal, limit: unlimited }
  - { type: slide, dirs: diagonal,   limit: unlimited }
```

There are only **two kinds of move part**, and they cover nearly everything:

| Kind | Meaning |
|---|---|
| `slide` | Travel in a direction until something stops you. Blocked by pieces in the way. |
| `leap` | Jump straight to a square. Ignores anything in between. |

A king is just a slide with `limit: 1`. There is no separate "step" move.

### Directions and offsets are from the piece's point of view

This is the one genuinely confusing idea in the whole guide, and it is worth getting straight now.

**`forward` means forward *for that piece*.** A white griffin's forward is up the board; a black
griffin's forward is down. You write the piece once and both colours work. You never write "up" or
"row 3".

Offsets follow the same idea. An offset is **`[forward, right]`**:

- `[1, 2]` means "one square forward, two squares to the right"
- `[-1, 2]` means "one square backward, two to the right"
- `[3, 0]` means "three squares straight forward"

Again — forward and right **from the piece's own view**, so black's `[1, 0]` and white's `[1, 0]`
go opposite ways on the screen. That is what you want. It is also why you must never think in board
rows and columns here.

For `slide`, you name a direction instead:

| `dirs:` | Meaning |
|---|---|
| `orthogonal` | The four straight lines (rook-style) |
| `diagonal` | The four diagonals (bishop-style) |
| `all` | All eight |
| `forward` `backward` `left` `right` | One direction only |
| `forward_diagonal` | The two forward diagonals (how a pawn captures) |

And `limit:` is **how many squares**, counted normally. `limit: 2` means two squares. `limit:
unlimited` means as far as it can go.

### Presentation runtime is not available yet

The declarative presentation contract is specified in [presentation.md](spec/presentation.md), and
its data validates at load time. The current playable runtime still renders glyphs and does not yet
draw themes/HUDs or play cues; that runtime work is Milestone 4.

### Optional extras

```yaml

capture: false     # on a move part: this move can never capture (a pawn's forward step)
capture: only      # on a move part: this move can ONLY capture (a pawn's diagonal)
                   # leave it out and the move can do both — which is normal
```

### Your piece is poison-aware for free

You never write anything about poison, stun, or shields on a piece. Those rules live in one place,
and they apply to your Griffin automatically. A poisoned Griffin is slowed without you lifting a
finger.

### Checklist for a piece

- [ ] `type: piece` and an `id:` starting with your mod name
- [ ] Every ID lowercase, with `:` between the two halves
- [ ] `moves:` is a list — each part starts with `- `
- [ ] Offsets are `[forward, right]`, not board coordinates
- [ ] `limit:` counts squares
- [ ] Two spaces for indenting, no tabs

---

## 5. Task two: add an event

An **event** is something that happens to the whole board on a timer. Every ten turns, the game
picks one event at random, warns everybody one turn ahead, and then fires it.

We are making **Cold Snap**: one random piece on each side gets frozen for two turns.

**`mods/frostmod/events/cold_snap.yaml`**

```yaml
type: event
id: frostmod:cold_snap
name: Cold Snap

warning:
  message: "COLD SNAP INCOMING! ONE PIECE ON EACH SIDE WILL FREEZE."

execute:
  - select:
      scope: board                    # look at the whole board
      filter:
        not: base:king                # ...but never the king
        not_status: [base:shield]     # ...and skip shielded pieces
      pick: { random: 1, per: color } # one at random from each side
    effect: { type: apply_status, status: base:stun, duration: 2 }
    message: { each: "[frz] {piece}@{square}" }

empty_message: "0x"
```

That's the whole event. Read it as a sentence: *out of every piece on the board, ignoring kings and
shielded pieces, pick one per side at random, and freeze it for two turns.*

### Every event has two phases

- **`warning:`** — one turn before it fires, this message appears. Players get a chance to react.
- **`execute:`** — what actually happens.

### `execute:` is a list of steps, and every step is the same three things

Each step is **select** (which pieces) → **effect** (what happens to them) → **message** (what to
tell the player). Most events have one step. You can have more if your event does two unrelated
things.

### Choosing pieces: `select:`

This is where most of the thinking goes. It has three parts, and **all three have defaults**, so you
only write what you need.

```yaml
select:
  scope: board        # WHERE to look    — default: the whole board
  filter: { ... }     # WHICH ones count — default: all of them
  pick: all           # HOW MANY         — default: all of them
```

**Filters stack.** Everything in `filter:` must be true at once. Our event's filter means "not a
king **and** not shielded".

The filters you will use most:

| Filter | Means |
|---|---|
| `is: base:queen` | Exactly this piece. `is: [base:rook, base:knight]` means either. |
| `not: base:king` | Anything except this |
| `color: white` / `color: black` | One fixed side |
| `color: random_one` | One side, chosen by a coin flip |
| `tag_any: [base:rook]` | **Contains** a rook (see the box below) |
| `primary: base:rook` | **Is mainly** a rook (see the box below) |
| `not_status: [base:shield]` | Doesn't have this status |
| `empty: true` | An empty square |

> #### `tag_any` versus `primary` — the one you must not get wrong
>
> Pieces in this game **fuse**. A Warden is a rook and a bishop stuck together. So "a rook" is
> suddenly two different questions, and the game needs both:
>
> - **`tag_any: [base:rook]`** — *does it contain a rook?* Catches the Rook, the Chancellor, the
>   Warden, **and the Inquisitor**.
> - **`primary: base:rook`** — *is it mainly a rook?* Catches the Rook, Chancellor and Warden, but
>   **not the Inquisitor**, which is mainly a bishop.
>
> If your event is about rook-ness in spirit ("all rooks turn into knights"), you want `primary`.
> If it's about what a piece can do ("anything with a bishop in it can snipe"), you want `tag_any`.
> Picking the wrong one gives you a rule that works for months and then does something baffling the
> first time a fused piece is involved.
>
> Your own pieces work here automatically. A Griffin is `primary: frostmod:griffin` and
> `tag_any: [frostmod:griffin]` without you writing anything.

**`pick:`** decides how many of the matches actually get hit:

| `pick:` | Means |
|---|---|
| `all` | Every match (the default) |
| `{ random: 1 }` | One at random, out of all matches |
| `{ random: 1, per: color }` | One at random **from each side** |

### Doing something: `effect:`

There are six things an effect can do:

| Effect | Does | Extra fields |
|---|---|---|
| `destroy` | Removes the piece | — |
| `transform` | Turns it into another piece | `into:`, `preserve:` |
| `apply_status` | Poisons/stuns/shields it | `status:`, `duration:` |
| `set_color` | Switches which side it's on | `to:` |
| `move` | Moves it | `to:` |
| `swap` | Swaps two pieces | `with:` |

They act on whatever your `select:` chose — you don't have to say so again.

**If you use `transform`, you must say `preserve:`.** There is no default, on purpose, because the
two options genuinely disagree and somebody has to choose:

```yaml
- { type: transform, into: base:knight, preserve: [has_moved] }        # statuses are LOST
- { type: transform, into: base:queen,  preserve: all_except_identity } # statuses are KEPT
```

**If you use `apply_status`, `duration:` is only for statuses that count down.** `base:stun` and
`base:poison` count down, so they take one. `base:shield` doesn't work that way — it lasts until
your opponent finishes their turn — so giving it a `duration:` is an error rather than a number
that quietly does nothing.

### Telling the player: `message:`

Every event prints a short code to the game log. There are two shapes, and the difference is real:

```yaml
message: "(All) R=N"                  # ONE line for the step, however many pieces matched
message: { each: "[frz] {piece}@{square}" }   # one line PER piece
```

You have exactly two things you can drop into a message:

- **`{piece}`** — the piece, like `wN` (white knight) or `bP` (black pawn). The colour is already
  in there; don't try to add it separately.
- **`{square}`** — where it is, like `e4`.

`empty_message: "0x"` sits at the **bottom of the file, not inside a step**. It's what gets printed
if the event fired and nothing at all happened — every piece was shielded, or there were no matches.
`"0x"` is what the rest of the game uses; stick with it unless you have a reason.

### Checklist for an event

- [ ] `type: event` and an `id:` starting with your mod name
- [ ] A `warning:` with a `message:`
- [ ] `execute:` is a list — each step starts with `- `
- [ ] Chose between `tag_any` and `primary` deliberately
- [ ] `transform` has a `preserve:`; `apply_status` has a `duration:` only if it counts down
- [ ] `empty_message:` at the bottom, not inside a step
- [ ] Every `base:` thing you named is covered by a line in `dependencies.required`

---

## 6. Making the event actually happen

**Writing an event file is not enough. Nothing will ever fire it.**

Events don't have their own timers. There is one schedule for the whole game — a **pool** — that
picks one event at random every ten turns. The base game's pool lists its ten events by name, and
your event is not in that list.

So you need to add it. You cannot edit `base:events`'s file (it isn't yours, and it would be
overwritten next time the game updates), so instead you write a **patch**: a small file that says
"change this one thing in somebody else's content".

**`mods/frostmod/patches/pool.yaml`**

```yaml
type: patch
id: frostmod:pool_entry
patches:
  - { target: base:main_pool, op: add, path: members, value: frostmod:cold_snap }
```

Read it as: *in `base:main_pool`, add `frostmod:cold_snap` to the list called `members`.*

That is the whole patch system. Three operations, no more:

| `op:` | Does |
|---|---|
| `add` | Adds an item to a list |
| `set` | Changes a value |
| `remove` | Deletes something |

`path:` points at the thing you're changing, using the same field names you'd see if you opened the
file yourself. A couple of examples from other mods:

```yaml
- { target: base:queen,      op: set,    path: moves[0].limit, value: 3 }   # nerf the queen
- { target: base:bishop_snipe, op: set,  path: cost.base:ap,   value: 2 }   # cheaper snipe
```

`moves[0]` means "the first move part" — lists are counted from zero, which is a programmer habit
you unfortunately have to know here.

**If two mods patch the same thing, the one that loads later wins, and the game says so out loud.**
It won't silently pick one behind your back.

---

## 7. Reference cards

Everything above, plus the parts this guide didn't walk through. Keep this section; skim the rest.

### The ten content types

| `type:` | What it does | Covered above? |
|---|---|---|
| `piece` | A piece and its moves | [yes](#4-task-one-add-a-piece) |
| `event` | A board-wide happening | [yes](#5-task-two-add-an-event) |
| `patch` | Change somebody else's content | [yes](#6-making-the-event-actually-happen) |
| `event_pool` | The schedule that fires events | below |
| `ability` | A thing a piece can do, paid for with points | below |
| `status` | Poison, stun, shield, and your own | below |
| `fusion` | Which pieces combine into what | below |
| `board` | Board size, layout, and the two sides | below |
| `resource` | The points abilities are paid with | below |
| `game_mode` | A playable entry in the menu: a board plus its events | below |

### Ability

An ability is something a player spends Action Points to do.

```yaml
type: ability
id: frostmod:griffin_dive
name: Griffin Dive
owner: { tag_any: [frostmod:griffin] }   # which pieces get it — the "contains" axis
cost: { base:ap: 2 }                     # 2 Action Points
target:                                  # what the player clicks — a selector, same as an event's
  scope: { of: self, ray: diagonal }     # along unblocked diagonals from this piece
  filter: { friendly: false }
effect: { type: destroy, credit: self }
```

`target: self` (instead of the block above) means the ability needs no target and acts on its own
piece.

The scopes that only make sense from a piece:

| `scope:` | Means |
|---|---|
| `{ of: self, adjacent: orthogonal }` | The four squares beside it |
| `{ of: self, ray: diagonal }` | Outward along the diagonals, stopping at the first piece |
| `{ of: self, offset: [3, 0] }` | One specific square, three forward |

**The acting piece is never included by default.** Add `include_self: true` if you want it — that's
how Rook Shield covers the rook as well as its neighbours.

### Status

```yaml
type: status
id: frostmod:frostbite
expiry: { turns: 3 }         # counts down
modifies:
  movement:
    slide: { limit: 1 }      # can only slide one square
    leap: { disable: true }  # can't leap at all
on_expire:                   # optional
  effect: { type: destroy }
```

Two ways for a status to end, and only two:

| `expiry:` | Means | Used by |
|---|---|---|
| `{ turns: 3 }` | Counts down full turns | poison, stun |
| `after_opponent_turn` | Survives your turn, dies at the end of your opponent's | shield |

Four things a status can change, and only four:

| Modifier | Effect |
|---|---|
| `movement.slide.limit: 1` | Sliding capped at one square |
| `movement.leap.disable: true` | No leaping |
| `movement.disable: true` | Can't move at all |
| `capturable: false` | Can't be captured |

**Note what stun does not do:** a stunned piece can't *move*, but it can still use *abilities*. That
is deliberate — it's how the game behaves today.

### Resource

```yaml
type: resource
id: frostmod:mana
name: Mana
starting: 0
max: 5
gain: { amount: 1, every_moves: 2 }
```

Your abilities can then cost `{ frostmod:mana: 2 }`. The game has no idea what mana is; it just
counts it. `base:ap` is defined in exactly this way and gets no special treatment.

### Board

```yaml
type: board
id: frostmod:tiny
size: [8, 8]
sides:
  - { id: base:white, name: White, forward: up,   promotes_at: 0, moves_first: true }
  - { id: base:black, name: Black, forward: down, promotes_at: 7 }
rows:
  - { row: 0, side: base:black, pieces: [base:rook, base:knight, ...] }   # positional
  - { row: 1, side: base:black, fill: base:pawn }                          # whole row
```

Rows you don't list are empty. `forward:` is what makes every piece's "forward" mean something.

### Fusion

```yaml
type: fusion
id: frostmod:my_table
match: { capturer: exact, captured: primary }
fuses_on: displacing_captures
rules:
  - { capturer: base:rook, captured: base:bishop, into: base:warden }
```

**Order matters and is not a mistake:** rook-takes-bishop and bishop-takes-rook give different
pieces. A piece that appears in no row simply never fuses — that's how kings and queens are excluded,
without a field saying so.

### Event pool

```yaml
type: event_pool
id: frostmod:my_pool
every: 10              # turns between events
warn_before: 1         # warn this many turns ahead
pick: { random: 1 }
members: [frostmod:cold_snap, base:tai_xiu]
```

Most mods should [patch the existing pool](#6-making-the-event-actually-happen) rather than define
their own. Define your own if you want a **separate menu entry** with its own event set — then you
need a `game_mode` to point at it.

### Game mode

A mode is what the player picks from the menu: a board, plus which event pools run on it.

```yaml
type: game_mode
id: frostmod:frozen_chess
name: Frozen Chess
board: base:standard
pools: [frostmod:my_pool]      # `pools: []` means a game with no events at all
```

This is how you ship a whole alternative game rather than adding to the existing one. Your mode
appears in the menu next to the built-in ones — which are written exactly like this, in
`base:chess` and `base:events`.

### Replacing something outright

If patching isn't enough and you want to *replace* a piece everywhere:

```yaml
type: piece
id: frostmod:queen        # your namespace — always
replaces: base:queen      # and it stands in for the real one everywhere
```

This is a blunt instrument, meant for total conversions. Prefer a patch.

### Conditions

A `when:` can hang off a move part, an ability, or an effect. There are four things you can ask:

| Condition | Asks |
|---|---|
| `at_promotion_rank: true` | Is it on its promotion row? |
| `has_moved: false` | Has it never moved? |
| `empty: true` | Is the destination empty? |
| `not_status: [base:stun]` | Is it free of this status? |

You can combine them with `all_of: [...]`, `any_of: [...]` and `not: {...}`.

**A condition never says who it's about** — it's always about the thing it's attached to. A `when:`
on a move part is about the moving piece; on an ability, the piece that owns it. There is no way to
ask about a *different* piece, and that is on purpose.

### Reacting to a move

A piece can react to things with `on:`. Today there is exactly one trigger — `moved` — and this is
how pawn promotion works:

```yaml
on:
  - trigger: moved
    when: { at_promotion_rank: true }
    effect:
      type: transform
      into: [base:queen, base:rook, base:bishop, base:knight]
      choose: mover          # the player picks
      preserve: [has_moved]
```

---

## 8. Things you cannot do yet

Honesty is cheaper than a wasted afternoon. These are the walls you will hit.

**Your event cannot decide when it fires.** There is no way to write "when a queen is captured" or
"when a piece reaches the far side". Events fire from the pool's timer, at random, and that is all.
This is the most likely thing you will want and not find. It is a known gap, deliberately left for
later.

**Pieces only react to `moved`.** That's the only trigger there is.

**No arithmetic, no variables, no counting.** You cannot write "if this piece has captured three
times" or "costs 1 point per enemy nearby". The format asks questions and does things; it does not
calculate. This is a firm line, not an oversight — the moment it does arithmetic, it becomes a
programming language with no debugger and you would be better off writing Python.

**No hit points, no health, no damage.** Not built in, and not planned. It is the sort of thing a
programmer adds by writing a small code mod, which then lets *you* use hit points as ordinary data.

**Statuses can only do the four things in the table.** Want a status that doubles a piece's range?
That needs a code mod to add the ability first.

**If you need something that isn't here**, that's worth reporting rather than working around. The
whole design is built on the idea that new abilities get added as *vocabulary everybody can use*,
not as one-off special cases. Your "I couldn't do X" is the input that decides what gets added.

---

## 9. When something is wrong

Once the game exists, a mistake looks like this:

```
ERROR  frostmod  events/cold_snap.yaml:12:5
  field:     execute[0].filter.not_stat
  problem:   unknown key 'not_stat'
  expected:  one of is, not, color, friendly, tag_any, primary,
             has_status, not_status, empty
  did you mean 'not_status'?
```

You get told the file, the line, the exact field, and what was expected. Things worth knowing:

- **You'll be shown every error at once**, not one per run. Six typos, one list, one fix session.
- **A mod with any error is switched off entirely**, not half-loaded. A mod that loaded everything
  except your queen would look like it was working, and that's worse than an honest refusal.
- **The message points at the real cause.** If your mod is off because a mod you depend on is off,
  it says that — it doesn't leave you staring at your own perfectly fine file.

---

## 10. Final checklist

Your mod, end to end:

- [ ] A folder under `mods/` with your mod's name
- [ ] `manifest.yaml` at the top of it, with `id:`, `name:`, `version:`, `engine:`, `code: false`
- [ ] `dependencies.required` lists **every mod whose IDs you mention** (`base:chess` for pieces,
      `base:events` for poison and stun)
- [ ] Every file starts with `type:` and `id:`
- [ ] Every ID you invented starts with your own mod's name and is lowercase
- [ ] Every ID you borrowed is written in full, with its owner's name (`base:knight`)
- [ ] Indented with spaces, never tabs
- [ ] **Your event is added to a pool**, or it will never fire
- [ ] Checklists in [section 4](#checklist-for-a-piece) and [section 5](#checklist-for-an-event) done

If you got here and the two files make sense to you, the design has done its job. If any part of it
made you feel stupid, that is a bug in this guide — please say which part. That reaction is the most
valuable thing you can report, and it is genuinely what this document is being tested for.
