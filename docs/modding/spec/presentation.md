# Spec — Declarative Presentation

**Status:** current data and loader contract; normal Pygame rendering lands in Milestone 4.

Presentation is content. Mods never receive a surface, mixer, font object, or mutable game state.
They declare data; core renders it from immutable snapshots and plays cues from immutable notices.

## Content types

Three reusable types extend the content vocabulary: `theme`, `hud_layout`, and `sound`.

```yaml
type: theme
id: mymod:night
name: Night
palette: { background: "#111111", panel: "#222222", board_light: "#dddddd", board_dark: "#555555", text: "#ffffff", accent: "#ffaa00", warning: "#ff4444", selection: "#44aaff", target: "#66cc66" }
typography: { scale: 1, weight: normal }
```

`palette` contains exactly the nine tokens above. Typography uses a core system font only; custom
font assets are not a v1 capability.

```yaml
type: hud_layout
id: mymod:standard_hud
name: Standard HUD
widgets:
  - { type: turn, slot: top }
  - { type: resources, slot: side }
  - { type: log, slot: side, max_lines: 12 }
  - { type: prompt, slot: bottom }
```

Widget types are exactly `turn`, `resources`, `log`, and `prompt`; slots are `top`, `side`, or
`bottom`. A widget may occur once.

```yaml
type: sound
id: mymod:sounds
name: Sounds
cues: { move_completed: assets/sounds/move.ogg }
```

The cue names are `move_completed`, `capture_completed`, `ability_used`, `promotion_chosen`,
`event_warning`, `event_executed`, `status_applied`, `status_expired`, `outcome_reached`, and
`undo_completed`.

## References and assets

`game_mode.presentation` references `theme`, `hud_layout`, and `sound`. Piece `presentation`
requires `glyph` and may name `sprite`; status `presentation` may set `visible`, `glyph`, and `icon`.
There is no inferred glyph or asset fallback.

Every asset path is relative to the defining mod and begins with `assets/`. Images are PNG; audio is
WAV or OGG. Paths may not be absolute or traverse with `..`; missing files and bad extensions are
load errors. Core caches images by mod/path/output size and audio by mod/path.

## Observation boundary

`PresentationSnapshot` is read-only state for drawing. `PresentationNotification` is an immutable
record emitted after a completed engine action. Neither exposes a mutation path. Rendering and audio
subscribe to the documented notifications; rules never call Pygame or audio directly.
