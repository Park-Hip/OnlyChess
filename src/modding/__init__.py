"""The loader — the seam between the engine and every mod, including the base game.

`CLAUDE.md`: *"The core is an engine. All content is a mod."* This package is where that
stops being a slogan. Nothing in here may name a piece, an event, or a mod — gate G2 checks
that mechanically, because a rule nobody can check is a rule that decays.

Read `docs/modding/spec/loader-lifecycle.md` before changing anything here; the stage
ordering in particular is load-bearing and looks arbitrary until you know why.
"""

from .api import ModApi, ModApiError, MoveType
from .errors import ContentError, ModLoadError, did_you_mean
from .loader import LoadResult, Manifest, activate, load
from .registries import CONTENT_TYPES, VERB_KINDS, Registries, Registry, namespace_of, qualify

__all__ = [
    "CONTENT_TYPES",
    "ContentError",
    "LoadResult",
    "Manifest",
    "ModApi",
    "ModApiError",
    "ModLoadError",
    "MoveType",
    "Registries",
    "Registry",
    "VERB_KINDS",
    "activate",
    "did_you_mean",
    "load",
    "namespace_of",
    "qualify",
]
