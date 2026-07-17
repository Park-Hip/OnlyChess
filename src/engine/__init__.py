"""The data-defined engine introduced in Wave 3; it never imports legacy gameplay code."""

from .factory import build_state
from .pipeline import Pipeline

__all__ = ["Pipeline", "build_state"]
