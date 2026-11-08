"""Schema.org structured data, OpenGraph, and Pinterest Rich Pin generators for pSEO static pages."""

from __future__ import annotations

import html
import json
import re
import urllib.parse
from typing import Any, Optional, Union

# Handle both PostItem/RouteResult objects and dictionary equivalents
try:
    from app.models import PostItem, RouteResult
except ImportError:
    PostItem = Any  # type: ignore
    RouteResult = Any  # type: ignore

try:
    from app.seo.sitemap import join_base_and_path
except Exception:
    def join_base_and_path(base_url: str, web_path: str) -> str:
        clean_base = (base_url or "").rstrip("/")
        if not clean_base:
            return str(web_path) if (web_path and str(web_path).startswith("/")) else f"/{web_path or ''}"
        parsed = urllib.parse.urlparse(clean_base)
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
        repo_subpath = parsed.path.rstrip("/")
        clean_path = str(web_path) if (web_path and str(web_path).startswith("/")) else f"/{web_path or ''}"
        if origin and repo_subpath:
            if clean_path.startswith(repo_subpath + "/"):
                return f"{origin}{clean_path}"
            elif clean_path == repo_subpath or clean_path == f"{repo_subpath}/":
                return f"{origin}{repo_subpath}/"
            elif clean_path == "/" or clean_path == "":
                return f"{clean_base}/"
            else:
                return f"{clean_base}{clean_path}"
        else:
            if clean_path == "" or clean_path == "/":
                return f"{clean_base}/"
            return f"{clean_base}{clean_path}"


def strip_html(text: str) -> str:
    """Removes HTML tags and decodes HTML entities into clean plain text."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", str(text))
    clean = html.unescape(clean)
    return " ".join(clean.split())


def _get_field(obj: Any, key: str, default: Any = "") -> Any:
    """Helper to extract field from PostItem, RouteResult, or dict, with raw_meta fallback."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        val = obj.get(key)
        if val is not None and val != "":
            return val
        raw_meta = obj.get("raw_meta")
        if isinstance(raw_meta, dict) and key in raw_meta:
            return raw_meta[key]
        return default

    val = getattr(obj, key, None)
    if val is not None and val != "":
        return val
    raw_meta = getattr(obj, "raw_meta", None)
    if isinstance(raw_meta, dict) and key in raw_meta:
        return raw_meta[key]
    return default


def resolve_image_url(post: Any, base_url: str) -> str:
    """
    Resolves the post featured image into an absolute native GitHub Pages URL.
    Follows: https://<org>.github.io/assets/images/<slug>.<ext>
    """
    slug = _get_field(post, "slug", "")

    # Check local_image_path first
    local_path = _get_field(post, "local_image_path") or _get_field(post, "local_image", "")
    if local_path:
        clean_local = str(local_path).lstrip("/")
        if clean_local.startswith("http://") or clean_local.startswith("https://"):
            return clean_local
        return join_base_and_path(base_url, f"/{clean_local}")

    # Determine extension from remote image_url if available
    remote_url = _get_field(post, "image_url") or _get_field(post, "image", "")
    ext = ".jpg"
    if remote_url:
        lower_url = remote_url.lower()
        for cand in (".jpg", ".jpeg", ".png", ".webp", ".svg"):
            if lower_url.endswith(cand):
                ext = cand
                break

    safe_slug = slug or "default"
    return join_base_and_path(base_url, f"/assets/images/{safe_slug}{ext}")


def _format_iso_date(raw_date: str) -> str:
    """Normalizes date string to ISO format."""
    if not raw_date:
        return "2026-10-29T00:00:00Z"
    s = str(raw_date).strip()
    if len(s) == 10 and re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return f"{s}T00:00:00Z"
    if s.endswith("Z") or "+" in s or re.search(r"-\d{2}:\d{2}$", s):
        return s
    if "T" in s:
        return f"{s}Z"
    return s


def build_breadcrumb_list(
    post: Any,
    route: Any,
    base_url: str,
    root_name: str = "Editorial Hub",
) -> dict[str, Any]:
    """
    Constructs a Schema.org BreadcrumbList matching 1-level, 2-level, or 3-level slug hierarchy.
    Utilizes route.breadcrumbs if provided, or synthesizes based on web_path/taxonomy.
    """
    clean_base = base_url.rstrip("/")
    post_title = strip_html(_get_field(post, "title") or _get_field(post, "slug", "Article"))
    slug = _get_field(post, "slug", "")
    web_path = _get_field(route, "web_path") or f"/{slug}/"
    full_page_url = join_base_and_path(base_url, web_path)

    route_breadcrumbs = _get_field(route, "breadcrumbs", [])

    items: list[dict[str, Any]] = []

    if route_breadcrumbs and len(route_breadcrumbs) >= 2:
        for idx, crumb in enumerate(route_breadcrumbs):
            crumb_name = crumb.get("name", "")
            crumb_url = crumb.get("url", "")

            # Normalize root crumb name
            if idx == 0 or crumb_url in ("/", ""):
                item_name = root_name
                item_url = join_base_and_path(base_url, "/")
            elif idx == len(route_breadcrumbs) - 1:
                item_name = post_title
                item_url = full_page_url
            else:
                item_name = crumb_name or "Category"
                if crumb_url.startswith("http://") or crumb_url.startswith("https://"):
                    item_url = crumb_url
                else:
                    item_url = join_base_and_path(base_url, crumb_url)

            items.append({
                "@type": "ListItem",
                "position": idx + 1,
                "name": item_name,
                "item": item_url,
            })
    else:
        # Synthesize from category/parent slug or path hierarchy
        items.append({
            "@type": "ListItem",
            "position": 1,
            "name": root_name,
            "item": join_base_and_path(base_url, "/"),
        })

        category = _get_field(post, "category", "")
        category_slug = _get_field(post, "category_slug", "")
        parent_slug = _get_field(post, "parent_slug", "")
        cat_seg = category_slug or parent_slug

        # Detect 3-level (silo_nested)
        if "/guides/" in web_path or _get_field(route, "depth", 1) == 3:
            items.append({
                "@type": "ListItem",
                "position": 2,
                "name": "Guides",
                "item": join_base_and_path(base_url, "/guides/"),
            })
            if cat_seg:
                items.append({
                    "@type": "ListItem",
                    "position": 3,
                    "name": category or cat_seg.replace("-", " ").title(),
                    "item": join_base_and_path(base_url, f"/guides/{cat_seg}/"),
                })
        elif cat_seg:
            items.append({
                "@type": "ListItem",
                "position": 2,
                "name": category or cat_seg.replace("-", " ").title(),
                "item": join_base_and_path(base_url, f"/{cat_seg}/"),
            })

        items.append({
            "@type": "ListItem",
            "position": len(items) + 1,
            "name": post_title,
            "item": full_page_url,
        })

    return {
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def build_article_schema(
    post: Any,
    route: Any,
    base_url: str,
    source_domain: str = "stylesdays.com",
) -> dict[str, Any]:
    """Constructs Schema.org Article block with native GitHub image and canonical reference."""
    clean_base = base_url.rstrip("/")
    slug = _get_field(post, "slug", "")
    title = strip_html(_get_field(post, "title") or slug)
    excerpt = strip_html(_get_field(post, "excerpt") or _get_field(post, "description", ""))

    web_path = _get_field(route, "web_path") or f"/{slug}/"
    full_page_url = join_base_and_path(base_url, web_path)

    image_url = resolve_image_url(post, base_url)

    raw_date = _get_field(post, "date") or _get_field(post, "published", "")
    raw_modified = _get_field(post, "modified") or _get_field(post, "lastmod", raw_date)
    date_published = _format_iso_date(raw_date or raw_modified)
    date_modified = _format_iso_date(raw_modified or raw_date)

    raw_meta = _get_field(post, "raw_meta", {})
    canonical_source = (
        _get_field(post, "link", "")
        or (raw_meta.get("link") if isinstance(raw_meta, dict) else "")
        or f"https://{source_domain}/{slug}/"
    )

    return {
        "@type": "Article",
        "headline": title,
        "description": excerpt,
        "image": [image_url],
        "datePublished": date_published,
        "dateModified": date_modified,
        "author": {
            "@type": "Organization",
            "name": f"{source_domain} Editorial Team",
            "url": f"https://{source_domain}/",
        },
        "publisher": {
            "@type": "Organization",
            "name": f"{source_domain} Editorial Hub",
            "url": clean_base,
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": full_page_url,
        },
        "isBasedOn": canonical_source,
    }


def generate_json_ld(
    post: Any,
    route: Any,
    base_url: str = "https://home-organization.github.io",
    source_domain: str = "stylesdays.com",
) -> dict[str, Any]:
    """
    Interface Contract 3:
    Returns valid JSON-LD @graph structure containing Article and BreadcrumbList.
    """
    article = build_article_schema(post, route, base_url, source_domain)
    breadcrumbs = build_breadcrumb_list(post, route, base_url)

    return {
        "@context": "https://schema.org",
        "@graph": [
            article,
            breadcrumbs,
        ],
    }


def generate_json_ld_script(
    post: Any,
    route: Any,
    base_url: str = "https://home-organization.github.io",
    source_domain: str = "stylesdays.com",
    indent: int = 2,
) -> str:
    """Returns formatted JSON-LD embedded within a <script type="application/ld+json"> tag."""
    schema = generate_json_ld(post, route, base_url, source_domain)
    json_str = json.dumps(schema, indent=indent, ensure_ascii=False)
    return f'<script type="application/ld+json">\n{json_str}\n</script>'


def generate_opengraph_tags(
    post: Any,
    route: Any,
    base_url: str = "https://home-organization.github.io",
    source_domain: str = "stylesdays.com",
) -> list[str]:
    """Generates standard OpenGraph metadata tags referencing native GitHub-hosted assets."""
    clean_base = base_url.rstrip("/")
    slug = _get_field(post, "slug", "")
    title = strip_html(_get_field(post, "title") or slug)
    excerpt = strip_html(_get_field(post, "excerpt") or _get_field(post, "description", ""))

    web_path = _get_field(route, "web_path") or f"/{slug}/"
    full_page_url = join_base_and_path(base_url, web_path)
    image_url = resolve_image_url(post, base_url)
    site_name = f"{source_domain} Editorial Hub"

    return [
        '<meta property="og:type" content="article">',
        f'<meta property="og:title" content="{html.escape(title, quote=True)}">',
        f'<meta property="og:description" content="{html.escape(excerpt, quote=True)}">',
        f'<meta property="og:image" content="{html.escape(image_url, quote=True)}">',
        f'<meta property="og:url" content="{html.escape(full_page_url, quote=True)}">',
        f'<meta property="og:site_name" content="{html.escape(site_name, quote=True)}">',
    ]


def generate_pinterest_tags(
    post: Any,
    source_domain: str = "stylesdays.com",
) -> list[str]:
    """Generates Pinterest Rich Pin verification metadata tags."""
    raw_date = _get_field(post, "date") or _get_field(post, "published", "")
    raw_modified = _get_field(post, "modified") or _get_field(post, "lastmod", raw_date)
    date_published = _format_iso_date(raw_date or raw_modified)
    date_modified = _format_iso_date(raw_modified or raw_date)
    author_name = f"{source_domain} Editorial Team"

    return [
        '<meta name="pinterest-rich-pin" content="true">',
        f'<meta property="article:published_time" content="{html.escape(date_published, quote=True)}">',
        f'<meta property="article:modified_time" content="{html.escape(date_modified, quote=True)}">',
        f'<meta property="article:author" content="{html.escape(author_name, quote=True)}">',
    ]


def generate_twitter_tags(
    post: Any,
    base_url: str = "https://home-organization.github.io",
) -> list[str]:
    """Generates Twitter Card metadata tags."""
    slug = _get_field(post, "slug", "")
    title = strip_html(_get_field(post, "title") or slug)
    excerpt = strip_html(_get_field(post, "excerpt") or _get_field(post, "description", ""))
    image_url = resolve_image_url(post, base_url)

    return [
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{html.escape(title, quote=True)}">',
        f'<meta name="twitter:description" content="{html.escape(excerpt, quote=True)}">',
        f'<meta name="twitter:image" content="{html.escape(image_url, quote=True)}">',
    ]


def generate_seo_head(
    post: Any,
    route: Any,
    base_url: str = "https://home-organization.github.io",
    source_domain: str = "stylesdays.com",
) -> str:
    """
    Helper function returning complete SEO and social metadata tags to inject into HTML <head>.
    Includes canonical link, meta description, OpenGraph, Pinterest Rich Pins, Twitter Cards,
    and JSON-LD structured data.
    """
    clean_base = base_url.rstrip("/")
    slug = _get_field(post, "slug", "")
    excerpt = strip_html(_get_field(post, "excerpt") or _get_field(post, "description", ""))

    web_path = _get_field(route, "web_path") or f"/{slug}/"
    full_page_url = join_base_and_path(base_url, web_path)

    raw_meta = _get_field(post, "raw_meta", {})
    canonical_source = (
        _get_field(post, "link", "")
        or (raw_meta.get("link") if isinstance(raw_meta, dict) else "")
        or full_page_url
    )

    tags: list[str] = [
        f'<meta name="description" content="{html.escape(excerpt, quote=True)}">',
        f'<link rel="canonical" href="{html.escape(canonical_source, quote=True)}">',
        '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 100 100\'><text y=\'.9em\' font-size=\'90\'>🏠</text></svg>">',
    ]

    tags.extend(generate_opengraph_tags(post, route, base_url, source_domain))
    tags.extend(generate_pinterest_tags(post, source_domain))
    tags.extend(generate_twitter_tags(post, base_url))

    script_tag = generate_json_ld_script(post, route, base_url, source_domain)
    tags.append(script_tag)

    return "\n  ".join(tags)
