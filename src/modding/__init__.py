"""The loader — the seam between the engine and every mod, including the base game.

`CLAUDE.md`: *"The core is an engine. All content is a mod."* This package is where that
stops being a slogan. Nothing in here may name a piece, an event, or a mod — gate G2 checks
that mechanically, because a rule nobody can check is a rule that decays.

Start with `docs/refactor/wave-1-loader.md` for the implemented boundary, then read
`docs/modding/spec/loader-lifecycle.md` before changing lifecycle order. The ordering is
load-bearing and looks arbitrary until you know why.
"""

from .api import ModApi, ModApiError, MoveType
from .errors import ContentError, ModLoadError, did_you_mean
from .linking import LinkedBoard, LinkedContent, LinkedMode, Placement
from .loader import LoadResult, Manifest, activate, load
from .registries import CONTENT_TYPES, VERB_KINDS, Registries, Registry, namespace_of, qualify

__all__ = [
    "CONTENT_TYPES",
    "ContentError",
    "LoadResult",
    "LinkedBoard",
    "LinkedContent",
    "LinkedMode",
    "Manifest",
    "ModApi",
    "ModApiError",
    "ModLoadError",
    "MoveType",
    "Placement",
    "Registries",
    "Registry",
    "VERB_KINDS",
    "activate",
    "did_you_mean",
    "load",
    "namespace_of",
    "qualify",
]
