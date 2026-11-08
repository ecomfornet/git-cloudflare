"""Static site generation module for pSEO.

Orchestrates post rendering, category/silo hub generation, root organization hub,
asset copying, robots.txt, and Google Image sitemaps into the output directory.
"""

from app.generator.site_builder import (
    BuildSummary,
    SiteBuilder,
    build_site,
    build_static_site,
    render_post_html,
)

__all__ = [
    "BuildSummary",
    "SiteBuilder",
    "build_site",
    "build_static_site",
    "render_post_html",
]
