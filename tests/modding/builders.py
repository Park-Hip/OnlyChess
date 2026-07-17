"""Mod builders for tests.

Tests write mods to a temp directory rather than committing fixture mods under `mods/`.
Two reasons, and the second is the important one:

- A fixture in `mods/` loads in the real game.
- `migration-plan.md` is explicit that test content lives in `tests/`, and *"if a probe
  fixture ever moves out of `tests/`, something has gone badly wrong."* Same principle, one
  wave earlier.
"""

from __future__ import annotations

import textwrap
from pathlib import Path


def write_mod(
    root: Path,
    folder: str,
    *,
    manifest: str | None = None,
    files: dict[str, str] | None = None,
    code: str | None = None,
) -> Path:
    """Create one mod directory. Returns its path.

    `manifest=None` writes no manifest at all — which is how the "not a mod, ignore silently"
    case gets tested.
    """
    mod = root / folder
    mod.mkdir(parents=True, exist_ok=True)

    if manifest is not None:
        (mod / "manifest.yaml").write_text(textwrap.dedent(manifest).lstrip(), encoding="utf-8")

    for name, body in (files or {}).items():
        path = mod / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")

    if code is not None:
        code_dir = mod / "code"
        code_dir.mkdir(exist_ok=True)
        (code_dir / "__init__.py").write_text(textwrap.dedent(code).lstrip(), encoding="utf-8")

    return mod


def data_mod(root: Path, folder: str = "tinymod", mod_id: str = "tiny:mod", **files: str) -> Path:
    """A minimal, valid, code-free mod. Extra content files are passed by keyword."""
    return write_mod(
        root,
        folder,
        manifest=f"""
        id: {mod_id}
        name: Tiny Mod
        version: 1.0.0
        code: false
        """,
        files={name.replace("__", "/") + ".yaml": body for name, body in files.items()},
    )


def playable_mode(mod_id: str = "tiny:mod") -> str:
    """A game_mode file, in the namespace of the mod that will ship it.

    Parameterised rather than a constant because a mod may only define ids in its own
    namespace — a fixed `tiny:only_mode` would be a load error inside any other mod, which
    is the loader working, not a nuisance to route around.
    """
    namespace = mod_id.split(":", 1)[0]
    return f"""
    type: game_mode
    id: {namespace}:only_mode
    name: The Only Mode
    board: {namespace}:flat
    """
