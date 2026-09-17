"""Extractor package — YouTube, podcast, Aparat, education, routing registry."""

from smart_dl.extractors.registry import (
    ROUTES,
    ExtractorKind,
    ExtractorRoute,
    describe_routes,
    resolve_extractor_kind,
    resolve_route,
)

__all__ = [
    "ROUTES",
    "ExtractorKind",
    "ExtractorRoute",
    "describe_routes",
    "resolve_extractor_kind",
    "resolve_route",
]
