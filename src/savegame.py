"""Saving and loading a game in progress.

**A save is a state snapshot, not a list of moves to replay**, and that is not a preference —
`CLAUDE.md` already settled it for undo, and the reasoning transfers exactly:

> The alternative (replay from a captured RNG seed) forces every random effect to draw from an RNG
> core owns, and a code mod calling `random.random()` silently breaks it.

A replayed save would have the same hole, and worse: undo fails at the moment you press it, while a
replayed save fails silently, hours later, having reconstructed a game that never happened.

**What a snapshot costs, stated plainly:** the action log is not saved, so a loaded game cannot be
undone past the point it was loaded. Actions hold references to live pieces, and serialising them
would mean giving every action a portable form and a version — real work, for the ability to undo a
move made before lunch. Chess programs generally behave this way. It is recorded here so nobody
later mistakes it for an oversight.

**A save records the mod set it was played against and refuses to load against a different one.**
Content is data: a piece can gain a move, a fusion table can change shape, a status can change what
it modifies. Restoring a board into changed rules would produce a game that looks fine and is not
the one that was saved. Failing loudly with the mismatch named is the same contract the loader keeps
with modders.
"""

from __future__ import annotations

import json
from pathlib import Path

from .engine.fusion import compose_definition
from .engine.piece import Piece, StatusInstance
from .runtime import EngineSession

#: Bumped when the stored shape changes in a way older files cannot satisfy.
FORMAT_VERSION = 1

SAVE_FILE = "save_game.json"


class SaveError(Exception):
    """A save could not be read, or does not belong to the mods now installed."""


def fingerprint(load_result) -> list[list[str]]:
    """The mod set a game was played against: every loaded mod and its version."""
    return sorted([info.mod_id, info.version] for info in load_result.installed if info.mod_id in load_result.mods)


def capture(session: EngineSession) -> dict:
    """Everything needed to resume, and nothing that can be recomputed."""
    state = session.state
    return {
        "format": FORMAT_VERSION,
        "mods": fingerprint(session.load_result),
        "mode_id": session.mode_id,
        "current_side": state.current_side,
        "completed_turns": state.completed_turns,
        "move_counts": dict(state.move_counts),
        "resources": {side: dict(values) for side, values in state.resources.items()},
        "pool_turns": dict(state.pool_turns),
        "pending_events": dict(state.pending_events),
        # Bindings hold tuples, which JSON flattens to lists; restore turns them back.
        "pending_bindings": {pool: {name: list(value) for name, value in bindings.items()} for pool, bindings in state.pending_bindings.items()},
        "event_messages": list(state.event_messages),
        "captures": {side: list(taken) for side, taken in state.captures.items()},
        "pieces": [
            {
                "id": piece.definition.id,
                "components": list(piece.definition.components),
                "side": piece.side,
                "pos": list(piece.pos),
                "has_moved": piece.has_moved,
                "statuses": {status_id: instance.remaining for status_id, instance in piece.statuses.items()},
            }
            for piece in state.board.pieces()
        ],
        "time_limit": session.time_limit,
        "clocks": dict(session.clocks),
        "flagged": session.flagged,
    }


def write(session: EngineSession, root: Path) -> Path:
    path = Path(root) / SAVE_FILE
    path.write_text(json.dumps(capture(session), indent=2), encoding="utf-8")
    return path


def exists(root: Path) -> bool:
    return (Path(root) / SAVE_FILE).is_file()


def read(root: Path) -> dict:
    path = Path(root) / SAVE_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise SaveError(f"the saved game could not be read: {error}") from error
    except ValueError as error:
        raise SaveError(f"the saved game is not readable JSON: {error}") from error
    if not isinstance(data, dict) or data.get("format") != FORMAT_VERSION:
        raise SaveError(f"the saved game was written by a different version of this format (expected {FORMAT_VERSION})")
    return data


def restore(load_result, data: dict) -> EngineSession:
    """Rebuild a session from a snapshot, or refuse and say why."""
    installed = fingerprint(load_result)
    if data.get("mods") != installed:
        raise SaveError(
            "the saved game was played against a different mod set.\n"
            f"  saved with: {_describe(data.get('mods'))}\n"
            f"  installed:  {_describe(installed)}"
        )
    mode_id = data.get("mode_id")
    if load_result.linked is None or mode_id not in load_result.linked.modes:
        raise SaveError(f"the saved game's mode '{mode_id}' is not available")

    session = EngineSession(load_result, mode_id, time_limit=data.get("time_limit"))
    state = session.state
    for piece in list(state.board.pieces()):
        state.board.remove(piece.pos)

    for uid, stored in enumerate(data.get("pieces", []), start=1):
        definition = state.piece_defs.get(stored["id"])
        if definition is None:
            raise SaveError(f"the saved game contains '{stored['id']}', which no installed mod defines")
        # A fused piece is a composed definition rather than a registered one, so its components are
        # rebuilt here; a plain piece restores to exactly the definition content declared.
        components = tuple(stored.get("components") or definition.components)
        if components != definition.components:
            definition = compose_definition(state.piece_defs, definition, components)
        piece = Piece(uid, definition, stored["side"], tuple(stored["pos"]), stored.get("has_moved", False))
        for status_id, remaining in (stored.get("statuses") or {}).items():
            status = state.status_defs.get(status_id)
            if status is not None:
                piece.statuses[status_id] = StatusInstance(status, remaining)
        state.board.place(piece, piece.pos)

    state.current_side = data.get("current_side", state.current_side)
    state.completed_turns = data.get("completed_turns", 0)
    state.move_counts.update(data.get("move_counts", {}))
    for side, values in data.get("resources", {}).items():
        state.resources.setdefault(side, {}).update(values)
    state.pool_turns.update(data.get("pool_turns", {}))
    state.pending_events.update(data.get("pending_events", {}))
    state.pending_bindings.update({pool: {name: tuple(value) for name, value in bindings.items()} for pool, bindings in data.get("pending_bindings", {}).items()})
    state.event_messages[:] = data.get("event_messages", [])
    state.captures.update({side: list(taken) for side, taken in data.get("captures", {}).items()})

    session.clocks = {side: float(value) for side, value in data.get("clocks", {}).items()}
    session.flagged = data.get("flagged")
    return session


def _describe(mods) -> str:
    if not mods:
        return "nothing recorded"
    return ", ".join(f"{mod_id} {version}" for mod_id, version in mods)
