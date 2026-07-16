"""Xref resolution.

The corpus-wide resolution index + cascade now live in
``britannica.xrefs.resolver`` — one owner, shared by every caller (pipeline,
single-pass export, vol29 topic, reader's guide, and the contributor linkers).
This module re-exports them under their historical names so existing importers
(``assemble``, ``export.article_json``, the diagnostics) keep working
unchanged.  See [[project_resolver_consolidation]].
"""
from britannica.xrefs.resolver import (  # noqa: F401
    ResolutionIndex,
    build_index as build_resolution_index,
    resolve as resolve_one,
)

__all__ = ["ResolutionIndex", "build_resolution_index", "resolve_one"]
