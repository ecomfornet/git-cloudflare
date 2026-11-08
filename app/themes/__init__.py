"""Themes package: visual palettes, responsive templates, and interactive component engine."""

from app.themes.engine import ThemeEngine
from app.themes.templates import (
    THEMES,
    get_embedded_fallback_css,
    get_theme_tokens,
    render_category_index,
    render_checklist,
    render_hub,
    render_stitch_editorial_hub,
    render_post,
    render_related_guides,
    render_takeaways,
    render_taxonomy_pills,
)

__all__ = [
    "THEMES",
    "ThemeEngine",
    "render_post",
    "render_category_index",
    "render_hub",
    "render_stitch_editorial_hub",
    "render_checklist",
    "render_takeaways",
    "render_taxonomy_pills",
    "render_related_guides",
    "get_theme_tokens",
    "get_embedded_fallback_css",
]
