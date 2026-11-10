"""XML Sitemap generator with Google Image extensions and multi-level hub prioritization."""

from __future__ import annotations

import datetime
import html
import re
from typing import Any, Iterable, Optional, Union
from xml.sax.saxutils import escape as xml_escape

import urllib.parse

try:
    from app.models import Manifest, PostItem
except ImportError:
    Manifest = Any  # type: ignore
    PostItem = Any  # type: ignore


def join_base_and_path(base_url: str, web_path: str) -> str:
    """Combines base_url and web_path without duplicating repository subpaths.

    Handles:
    - Base URL with repo: 'https://user.github.io/my-repo' + '/my-repo/slug/'
      -> 'https://user.github.io/my-repo/slug/'
    - Base URL with repo: 'https://user.github.io/my-repo' + '/slug/'
      -> 'https://user.github.io/my-repo/slug/'
    - Root domain: 'https://user.github.io' + '/slug/'
      -> 'https://user.github.io/slug/'
    """
    clean_base = (base_url or "").rstrip("/")
    if not clean_base:
        return str(web_path) if (web_path and str(web_path).startswith("/")) else f"/{web_path or ''}"

    parsed = urllib.parse.urlparse(clean_base)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
    repo_subpath = parsed.path.rstrip("/")  # e.g. "/my-repo" or ""

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


def _get_field(obj: Any, key: str, default: Any = "") -> Any:
    """Helper to extract field from PostItem or dict with raw_meta fallback."""
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


def _resolve_image_loc(post: Any, base_url: str) -> str:
    """Resolves image URL for sitemap pointing to native GitHub-hosted asset."""
    slug = _get_field(post, "slug", "")

    local_path = _get_field(post, "local_image_path") or _get_field(post, "local_image", "")
    if local_path:
        clean_local = str(local_path).lstrip("/")
        if clean_local.startswith("http://") or clean_local.startswith("https://"):
            return clean_local
        return join_base_and_path(base_url, f"/{clean_local}")

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


def _format_sitemap_date(raw_date: Any) -> str:
    """Normalizes date string to YYYY-MM-DD."""
    if not raw_date:
        return datetime.date.today().isoformat()
    s = str(raw_date).strip()
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", s)
    if match:
        return match.group(1)
    return datetime.date.today().isoformat()


def generate_sitemap_xml(
    posts: Union[Iterable[Any], Any],
    base_url: str = "https://home-organization.github.io",
    hub_urls: Optional[Iterable[str]] = None,
    extra_pages: Optional[Iterable[Union[dict[str, Any], str]]] = None,
) -> str:
    """
    Generates a production-ready sitemap.xml strictly following Sitemaps Protocol 0.9
    and Google Image Sitemap Extension 1.1.

    Hierarchy & Priorities:
    - Root organization hub (/): changefreq=daily, priority=1.0
    - Category and Silo hubs (/category/, /guides/...): changefreq=daily, priority=0.8
    - Editorial Posts (/blog/.../): changefreq=weekly, priority=0.8 with <image:image> tags
    - Author Profile (/author/.../): changefreq=monthly, priority=0.6
    - HTML Sitemap (/sitemap/): changefreq=weekly, priority=0.5
    - Trust & Legal Pages (/about/, /privacy-policy/, etc.): changefreq=monthly, priority=0.3 - 0.4
    """
    clean_base = base_url.rstrip("/")
    today = datetime.date.today().isoformat()

    # Extract posts if Manifest instance is passed
    post_list: list[Any] = []
    discovered_hubs: set[str] = set()

    if hasattr(posts, "posts") and isinstance(getattr(posts, "posts"), dict):
        post_list = list(getattr(posts, "posts").values())
        if hasattr(posts, "categories") and isinstance(getattr(posts, "categories"), list):
            for cat in getattr(posts, "categories"):
                cat_slug = cat.get("slug") if isinstance(cat, dict) else getattr(cat, "slug", "")
                if cat_slug:
                    discovered_hubs.add(f"/{cat_slug}/")
    elif isinstance(posts, dict):
        post_list = list(posts.values())
    elif isinstance(posts, (list, tuple, set)):
        post_list = list(posts)

    # Process and organize hub URLs
    normalized_hubs: list[str] = []
    seen_hubs: set[str] = set()

    # Always ensure root hub is included
    root_loc = join_base_and_path(base_url, "/")
    seen_hubs.add(root_loc)

    raw_hubs = list(hub_urls) if hub_urls is not None else list(discovered_hubs)

    for h in raw_hubs:
        if not h:
            continue
        h_str = str(h).strip()
        if h_str in ("/", ""):
            continue
        if h_str.startswith("http://") or h_str.startswith("https://"):
            full_hub_loc = h_str
        else:
            clean_path = h_str if h_str.startswith("/") else f"/{h_str}"
            if not clean_path.endswith("/"):
                clean_path = f"{clean_path}/"
            full_hub_loc = join_base_and_path(clean_base, clean_path)
        if full_hub_loc not in seen_hubs:
            seen_hubs.add(full_hub_loc)
            normalized_hubs.append(full_hub_loc)

    # Build XML lines
    url_entries: list[str] = []

    # 1. Root Hub (Priority 1.0, daily)
    url_entries.append(
        "  <url>\n"
        f"    <loc>{xml_escape(root_loc)}</loc>\n"
        f"    <lastmod>{today}</lastmod>\n"
        "    <changefreq>daily</changefreq>\n"
        "    <priority>1.0</priority>\n"
        "  </url>"
    )

    # 2. Category & Silo Hubs (Priority 0.8, daily)
    for hub_loc in normalized_hubs:
        url_entries.append(
            "  <url>\n"
            f"    <loc>{xml_escape(hub_loc)}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            "    <changefreq>daily</changefreq>\n"
            "    <priority>0.8</priority>\n"
            "  </url>"
        )

    # 3. Post URLs (Priority 0.8, weekly, with Google Image extension)
    seen_post_locs: set[str] = set()
    for p in post_list:
        slug = _get_field(p, "slug", "")
        if not slug:
            continue

        web_path = _get_field(p, "web_path") or f"/{slug}/"
        clean_path = str(web_path) if str(web_path).startswith("/") else f"/{web_path}"
        if not clean_path.endswith("/"):
            clean_path = f"{clean_path}/"
        post_loc = join_base_and_path(clean_base, clean_path)

        if post_loc in seen_post_locs or post_loc in seen_hubs:
            continue
        seen_post_locs.add(post_loc)

        raw_mod = _get_field(p, "modified") or _get_field(p, "lastmod") or _get_field(p, "date")
        post_lastmod = _format_sitemap_date(raw_mod)

        title = str(_get_field(p, "title") or slug).strip()
        clean_title = re.sub(r"<[^>]+>", " ", title)
        clean_title = html.unescape(clean_title)

        image_loc = _resolve_image_loc(p, base_url)

        entry_lines = [
            "  <url>",
            f"    <loc>{xml_escape(post_loc)}</loc>",
            f"    <lastmod>{post_lastmod}</lastmod>",
            "    <changefreq>weekly</changefreq>",
            "    <priority>0.8</priority>",
            "    <image:image>",
            f"      <image:loc>{xml_escape(image_loc)}</image:loc>",
            f"      <image:title>{xml_escape(clean_title)}</image:title>",
            "    </image:image>",
            "  </url>",
        ]
        url_entries.append("\n".join(entry_lines))

    # 4. Extra Pages: Author, Sitemap, and 9 Trust/Legal Compliance pages
    if extra_pages:
        for ep in extra_pages:
            if isinstance(ep, dict):
                ep_path = ep.get("path") or ep.get("web_path") or ""
                ep_prio = str(ep.get("priority", "0.4"))
                ep_freq = str(ep.get("changefreq", "monthly"))
                ep_mod = str(ep.get("lastmod", today))
            else:
                ep_path = str(ep)
                ep_prio = "0.4"
                ep_freq = "monthly"
                ep_mod = today

            if not ep_path:
                continue
            clean_ep = ep_path if ep_path.startswith("/") else f"/{ep_path}"
            if not clean_ep.endswith("/"):
                clean_ep = f"{clean_ep}/"
            ep_loc = join_base_and_path(clean_base, clean_ep)

            if ep_loc in seen_hubs or ep_loc in seen_post_locs:
                continue
            seen_post_locs.add(ep_loc)

            url_entries.append(
                "  <url>\n"
                f"    <loc>{xml_escape(ep_loc)}</loc>\n"
                f"    <lastmod>{ep_mod}</lastmod>\n"
                f"    <changefreq>{ep_freq}</changefreq>\n"
                f"    <priority>{ep_prio}</priority>\n"
                "  </url>"
            )

    # Assemble full XML document
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    urlset_open = (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
    )
    urlset_close = "\n</urlset>\n"

    return xml_header + urlset_open + "\n".join(url_entries) + urlset_close
