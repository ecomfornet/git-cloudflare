"""Routing module for pSEO static site generation.

Provides multi-slug URL resolution, base URL subpath resolution,
breadcrumb generation, and recursive intermediate silo index routing.
"""

from app.routing.resolver import (
    IntermediateRoute,
    RouteResolver,
    RouteResult,
    get_intermediate_routes,
    normalize_base_path,
    normalize_routing_mode,
    resolve_all_routes,
    resolve_intermediate_routes,
    resolve_post_route,
    slugify,
)

__all__ = [
    "slugify",
    "normalize_base_path",
    "normalize_routing_mode",
    "RouteResult",
    "IntermediateRoute",
    "resolve_post_route",
    "resolve_all_routes",
    "get_intermediate_routes",
    "resolve_intermediate_routes",
    "RouteResolver",
]
