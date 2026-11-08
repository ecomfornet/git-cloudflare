"""Multi-slug route resolver and intermediate hierarchy builder for pSEO.

Supports 4 routing modes:
- single:        /<slug>/index.html
- category_slug: /<category-slug>/<slug>/index.html
- parent_slug:   /<parent-slug>/<slug>/index.html
- silo_nested:   /guides/<parent-slug>/<slug>/index.html

Handles subpaths (e.g. /<repo>/ for GitHub project pages), builds exact-depth
breadcrumbs, and discovers all intermediate directory index pages to prevent 404s.
"""

from __future__ import annotations

import os
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Optional, Union

from app.models import PostItem, RouteResult as BaseRouteResult


def slugify(text: str) -> str:
    """Converts arbitrary text into a clean URL slug (lowercase alphanumeric with dashes)."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "guide"


def normalize_base_path(base_path: str = "", base_url: str = "") -> str:
    """Normalizes base path into a single leading slash without trailing slash.

    Examples:
        normalize_base_path("my-repo") -> "/my-repo"
        normalize_base_path("/my-repo/") -> "/my-repo"
        normalize_base_path(base_url="https://org.github.io/my-repo/") -> "/my-repo"
        normalize_base_path(base_url="https://org.github.io/") -> ""
    """
    if base_path:
        cleaned = base_path.strip()
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            parsed = urllib.parse.urlparse(cleaned)
            cleaned = parsed.path
        cleaned = cleaned.strip("/")
        return f"/{cleaned}" if cleaned else ""
    elif base_url:
        parsed = urllib.parse.urlparse(base_url.strip())
        path = parsed.path.strip("/")
        return f"/{path}" if path else ""
    return ""


def normalize_routing_mode(mode: Optional[str] = None) -> str:
    """Normalizes route mode string into one of the 4 canonical modes."""
    clean = (mode or "single").lower().strip()
    if clean in ("category", "category_slug", "category-slug", "catslug"):
        return "category_slug"
    elif clean in ("parent", "parent_slug", "parent-slug"):
        return "parent_slug"
    elif clean in ("silo", "silo_nested", "silo-nested", "nested"):
        return "silo_nested"
    return "single"


@dataclass
class RouteResult(BaseRouteResult):
    """Route resolution result supporting both attribute and dict-subscript access."""

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def __setitem__(self, item: str, value: Any) -> None:
        setattr(self, item, value)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "web_path": self.web_path,
            "file_path": self.file_path,
            "depth": self.depth,
            "breadcrumbs": [dict(b) for b in self.breadcrumbs],
        }


@dataclass
class IntermediateRoute:
    """Represents an intermediate directory hub requiring an index.html (to prevent 404s)."""

    web_path: str = ""
    file_path: str = ""
    title: str = ""
    slug: str = ""
    parent_slug: str = ""
    depth: int = 1
    breadcrumbs: list[dict[str, str]] = field(default_factory=list)
    posts: list[Any] = field(default_factory=list)

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def __setitem__(self, item: str, value: Any) -> None:
        setattr(self, item, value)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "web_path": self.web_path,
            "file_path": self.file_path,
            "title": self.title,
            "slug": self.slug,
            "parent_slug": self.parent_slug,
            "depth": self.depth,
            "breadcrumbs": [dict(b) for b in self.breadcrumbs],
            "posts_count": len(self.posts),
        }


def _extract_post_fields(post: Union[PostItem, dict[str, Any], Any]) -> tuple[str, str, str, str, str]:
    """Extracts (slug, title, category, category_slug, parent_slug) safely from post."""
    if hasattr(post, "slug"):
        slug = str(post.slug or "")
        title = str(post.title or "")
        category = str(post.category or "")
        cat_slug = str(post.category_slug or "")
        parent = str(post.parent_slug or "")
    elif isinstance(post, dict):
        slug = str(post.get("slug") or "")
        title = str(post.get("title") or "")
        category = str(post.get("category") or "")
        cat_slug = str(post.get("category_slug") or "")
        parent = str(post.get("parent_slug") or "")
    else:
        slug = str(getattr(post, "slug", "") or "")
        title = str(getattr(post, "title", "") or "")
        category = str(getattr(post, "category", "") or "")
        cat_slug = str(getattr(post, "category_slug", "") or "")
        parent = str(getattr(post, "parent_slug", "") or "")

    return slug, title, category, cat_slug, parent


def resolve_post_route(
    post: Union[PostItem, dict[str, Any], Any],
    mode: str = "single",
    routing_mode: Optional[str] = None,
    base_path: str = "",
    base_url: str = "",
) -> RouteResult:
    """Resolves web URL path, relative output disk path, depth, and breadcrumbs for a post.

    Args:
        post: PostItem instance or dictionary.
        mode: Routing structure ('single', 'category_slug', 'parent_slug', 'silo_nested').
        routing_mode: Alias for mode.
        base_path: Subpath for repository (e.g. '/<repo>').
        base_url: Base deployment URL for subpath extraction.

    Returns:
        RouteResult with web_path, file_path, depth, and breadcrumbs.
    """
    raw_slug, raw_title, category, raw_cat_slug, raw_parent_slug = _extract_post_fields(post)

    slug = slugify(raw_slug or "post")
    title = raw_title or slug.replace("-", " ").title()

    cat_slug = slugify(raw_cat_slug or category or "guides")
    parent_slug = slugify(raw_parent_slug or raw_cat_slug or category or "home-organization")

    cat_name = category or cat_slug.replace("-", " ").title()
    parent_name = raw_parent_slug.replace("-", " ").title() if raw_parent_slug else (category or parent_slug.replace("-", " ").title())

    active_mode = normalize_routing_mode(routing_mode or mode)
    base_prefix = normalize_base_path(base_path, base_url)
    home_url = f"{base_prefix}/" if base_prefix else "/"

    if active_mode == "category_slug":
        web_path = f"{base_prefix}/{cat_slug}/{slug}/"
        file_path = f"{cat_slug}/{slug}/index.html"
        depth = 2
        breadcrumbs = [
            {"name": "Home", "url": home_url},
            {"name": cat_name, "url": f"{base_prefix}/{cat_slug}/"},
            {"name": title, "url": web_path},
        ]
    elif active_mode == "parent_slug":
        web_path = f"{base_prefix}/{parent_slug}/{slug}/"
        file_path = f"{parent_slug}/{slug}/index.html"
        depth = 2
        breadcrumbs = [
            {"name": "Home", "url": home_url},
            {"name": parent_name, "url": f"{base_prefix}/{parent_slug}/"},
            {"name": title, "url": web_path},
        ]
    elif active_mode == "silo_nested":
        web_path = f"{base_prefix}/guides/{parent_slug}/{slug}/"
        file_path = f"guides/{parent_slug}/{slug}/index.html"
        depth = 3
        breadcrumbs = [
            {"name": "Home", "url": home_url},
            {"name": "Guides", "url": f"{base_prefix}/guides/"},
            {"name": parent_name, "url": f"{base_prefix}/guides/{parent_slug}/"},
            {"name": title, "url": web_path},
        ]
    else:  # single
        web_path = f"{base_prefix}/{slug}/"
        file_path = f"{slug}/index.html"
        depth = 1
        breadcrumbs = [
            {"name": "Home", "url": home_url},
            {"name": title, "url": web_path},
        ]

    return RouteResult(
        web_path=web_path,
        file_path=file_path,
        depth=depth,
        breadcrumbs=breadcrumbs,
    )


def resolve_all_routes(
    posts: list[Union[PostItem, dict[str, Any], Any]],
    mode: str = "single",
    routing_mode: Optional[str] = None,
    base_path: str = "",
    base_url: str = "",
) -> dict[str, RouteResult]:
    """Resolves routes for a list of posts, returning a dictionary keyed by post slug."""
    routes: dict[str, RouteResult] = {}
    for post in posts:
        route = resolve_post_route(
            post,
            mode=mode,
            routing_mode=routing_mode,
            base_path=base_path,
            base_url=base_url,
        )
        slug, _, _, _, _ = _extract_post_fields(post)
        key = slugify(slug or "post")
        routes[key] = route
    return routes


def get_intermediate_routes(
    posts: list[Union[PostItem, dict[str, Any], Any]],
    mode: str = "single",
    routing_mode: Optional[str] = None,
    base_path: str = "",
    base_url: str = "",
) -> list[IntermediateRoute]:
    """Discovers all intermediate directory index pages required so no parent path ever 404s.

    In 'single' & 'category_slug' modes: returns /<category-slug>/index.html for each category
    so that category navigation pills, breadcrumbs, and tags never 404.
    In 'parent_slug' mode: returns /<parent-slug>/index.html for each parent.
    In 'silo_nested' mode: returns BOTH /guides/index.html AND /guides/<parent-slug>/index.html
    for each unique parent category.
    """
    active_mode = normalize_routing_mode(routing_mode or mode)
    base_prefix = normalize_base_path(base_path, base_url)
    home_url = f"{base_prefix}/" if base_prefix else "/"

    intermediate_routes: list[IntermediateRoute] = []

    if active_mode in ("single", "category_slug"):
        categories: dict[str, list[Any]] = {}
        cat_names: dict[str, str] = {}
        for post in posts:
            _, _, category, cat_slug_raw, _ = _extract_post_fields(post)
            cat_slug = slugify(cat_slug_raw or category or "guides")
            categories.setdefault(cat_slug, []).append(post)
            if cat_slug not in cat_names:
                cat_names[cat_slug] = category or cat_slug.replace("-", " ").title()

        for cat_slug, child_posts in categories.items():
            name = cat_names.get(cat_slug) or cat_slug.replace("-", " ").title()
            web_path = f"{base_prefix}/{cat_slug}/"
            file_path = f"{cat_slug}/index.html"
            breadcrumbs = [
                {"name": "Home", "url": home_url},
                {"name": name, "url": web_path},
            ]
            intermediate_routes.append(
                IntermediateRoute(
                    web_path=web_path,
                    file_path=file_path,
                    title=f"{name} Guides",
                    slug=cat_slug,
                    parent_slug="",
                    depth=1,
                    breadcrumbs=breadcrumbs,
                    posts=child_posts,
                )
            )

    elif active_mode == "parent_slug":
        parents: dict[str, list[Any]] = {}
        parent_names: dict[str, str] = {}
        for post in posts:
            _, _, category, cat_slug_raw, parent_raw = _extract_post_fields(post)
            p_slug = slugify(parent_raw or cat_slug_raw or category or "home-organization")
            parents.setdefault(p_slug, []).append(post)
            if p_slug not in parent_names:
                parent_names[p_slug] = parent_raw.replace("-", " ").title() if parent_raw else (category or p_slug.replace("-", " ").title())

        for p_slug, child_posts in parents.items():
            name = parent_names.get(p_slug) or p_slug.replace("-", " ").title()
            web_path = f"{base_prefix}/{p_slug}/"
            file_path = f"{p_slug}/index.html"
            breadcrumbs = [
                {"name": "Home", "url": home_url},
                {"name": name, "url": web_path},
            ]
            intermediate_routes.append(
                IntermediateRoute(
                    web_path=web_path,
                    file_path=file_path,
                    title=f"{name} Guides",
                    slug=p_slug,
                    parent_slug=p_slug,
                    depth=1,
                    breadcrumbs=breadcrumbs,
                    posts=child_posts,
                )
            )

    elif active_mode == "silo_nested":
        # 1. Top-level /guides/ hub
        guides_web_path = f"{base_prefix}/guides/"
        guides_file_path = "guides/index.html"
        guides_breadcrumbs = [
            {"name": "Home", "url": home_url},
            {"name": "Guides", "url": guides_web_path},
        ]
        intermediate_routes.append(
            IntermediateRoute(
                web_path=guides_web_path,
                file_path=guides_file_path,
                title="Curated Guides Hub",
                slug="guides",
                parent_slug="",
                depth=1,
                breadcrumbs=guides_breadcrumbs,
                posts=list(posts),
            )
        )

        # 2. Intermediate /guides/<parent-slug>/ silo category pages
        parents = {}
        parent_names = {}
        for post in posts:
            _, _, category, cat_slug_raw, parent_raw = _extract_post_fields(post)
            p_slug = slugify(parent_raw or cat_slug_raw or category or "home-organization")
            parents.setdefault(p_slug, []).append(post)
            if p_slug not in parent_names:
                parent_names[p_slug] = parent_raw.replace("-", " ").title() if parent_raw else (category or p_slug.replace("-", " ").title())

        for p_slug, child_posts in parents.items():
            name = parent_names.get(p_slug) or p_slug.replace("-", " ").title()
            web_path = f"{base_prefix}/guides/{p_slug}/"
            file_path = f"guides/{p_slug}/index.html"
            breadcrumbs = [
                {"name": "Home", "url": home_url},
                {"name": "Guides", "url": guides_web_path},
                {"name": name, "url": web_path},
            ]
            intermediate_routes.append(
                IntermediateRoute(
                    web_path=web_path,
                    file_path=file_path,
                    title=f"{name} Guides",
                    slug=p_slug,
                    parent_slug=p_slug,
                    depth=2,
                    breadcrumbs=breadcrumbs,
                    posts=child_posts,
                )
            )

    return intermediate_routes


# Backward-compatible alias
resolve_intermediate_routes = get_intermediate_routes


class RouteResolver:
    """Convenience class providing unified route resolution for site building."""

    def __init__(
        self,
        mode: str = "single",
        routing_mode: Optional[str] = None,
        base_path: str = "",
        base_url: str = "",
    ) -> None:
        self.mode = normalize_routing_mode(routing_mode or mode)
        self.base_path = base_path
        self.base_url = base_url

    def resolve_post(self, post: Union[PostItem, dict[str, Any], Any]) -> RouteResult:
        """Resolves route for a single post."""
        return resolve_post_route(
            post,
            mode=self.mode,
            base_path=self.base_path,
            base_url=self.base_url,
        )

    def resolve_all(
        self, posts: list[Union[PostItem, dict[str, Any], Any]]
    ) -> dict[str, RouteResult]:
        """Resolves routes for all posts in a list."""
        return resolve_all_routes(
            posts,
            mode=self.mode,
            base_path=self.base_path,
            base_url=self.base_url,
        )

    def get_intermediate_routes(
        self, posts: list[Union[PostItem, dict[str, Any], Any]]
    ) -> list[IntermediateRoute]:
        """Discovers intermediate hubs for the configured routing mode."""
        return get_intermediate_routes(
            posts,
            mode=self.mode,
            base_path=self.base_path,
            base_url=self.base_url,
        )
