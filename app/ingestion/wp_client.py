"""WordPress REST API client for fetching posts, categories, and embedded media."""

from __future__ import annotations

import html as html_lib
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from app.models import PostItem

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def strip_html(raw_html: str) -> str:
    """Strips HTML tags, unescapes HTML entities, and normalizes whitespace."""
    if not raw_html:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", raw_html)
    cleaned = html_lib.unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def infer_category_and_parent(slug: str) -> Tuple[str, str]:
    """Infers taxonomy name and parent slug from slug keywords when categories are missing."""
    s = slug.lower()
    if "hack" in s:
        return "IKEA Hacks", "ikea-hacks"
    elif any(k in s for k in ("storage", "pax", "closet", "organiz")):
        return "IKEA Storage & Closet", "closet-storage"
    elif any(k in s for k in ("daybed", "guest")):
        return "Guest Bedroom & Daybeds", "guest-bedroom"
    elif "bedroom" in s:
        return "Bedroom Ideas", "bedroom-design"
    elif any(k in s for k in ("living", "sofa", "tv")):
        return "Living Room Styling", "living-room"
    elif any(k in s for k in ("kitchen", "pantry")):
        return "Kitchen & Pantry", "kitchen-organization"
    else:
        return "Home Decor & Organization", "home-organization"


def extract_featured_image(post_dict: Dict[str, Any]) -> str:
    """Extracts high-resolution featured image URL from WordPress _embedded payload."""
    embedded = post_dict.get("_embedded") or {}
    media_list = embedded.get("wp:featuredmedia") or []
    if media_list and isinstance(media_list, list) and len(media_list) > 0:
        media = media_list[0]
        if isinstance(media, dict):
            # Check direct source_url
            source_url = media.get("source_url")
            if source_url:
                return str(source_url).strip()

            # Check media_details sizes fallbacks
            details = media.get("media_details") or {}
            sizes = details.get("sizes") or {}
            for size_key in ("full", "large", "medium_large", "medium"):
                size_obj = sizes.get(size_key) or {}
                size_url = size_obj.get("source_url")
                if size_url:
                    return str(size_url).strip()

    return ""


def extract_category_and_slug(post_dict: Dict[str, Any], slug: str) -> Tuple[str, str]:
    """Extracts category name and slug from _embedded['wp:term'][0] with fallback to inference."""
    embedded = post_dict.get("_embedded") or {}
    terms_outer = embedded.get("wp:term") or []
    if terms_outer and isinstance(terms_outer, list) and len(terms_outer) > 0:
        categories = terms_outer[0]
        if categories and isinstance(categories, list) and len(categories) > 0:
            first_cat = categories[0]
            if isinstance(first_cat, dict):
                name = str(first_cat.get("name", "")).strip()
                cat_slug = str(first_cat.get("slug", "")).strip()
                if name and cat_slug:
                    return html_lib.unescape(name), cat_slug
                elif name:
                    clean_slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                    return html_lib.unescape(name), clean_slug

    return infer_category_and_parent(slug)


def generate_default_checklist(title: str) -> List[Dict[str, str]]:
    """Generates standard interactive checklist steps for room styling / DIY posts."""
    return [
        {"id": "step-1", "text": "Measure room footprint and review natural light layout"},
        {"id": "step-2", "text": "Select coordinating foundational furniture pieces and color palette"},
        {"id": "step-3", "text": "Assemble key storage elements and anchor securely to wall studs"},
        {"id": "step-4", "text": "Incorporate layered ambient lighting, textured textiles, and greenery"},
    ]


def generate_default_takeaways(title: str, category: str) -> List[str]:
    """Generates structured key styling takeaways."""
    return [
        f"Optimized layout approach tailored for {title}",
        f"Practical space-saving and organizational solutions for {category}",
        "High-impact, budget-friendly decor materials and accents",
    ]


class WordPressClient:
    """Client for WordPress REST API with embedded resource extraction and pagination handling."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 20,
        user_agent: str = DEFAULT_USER_AGENT,
        fetcher: Optional[Callable[[str], Tuple[bytes, Dict[str, str]]]] = None,
    ):
        clean_url = base_url.strip().rstrip("/")
        if not clean_url.startswith(("http://", "https://")):
            clean_url = f"https://{clean_url}"
        self.base_url = clean_url
        self.timeout = timeout
        self.user_agent = user_agent
        self._fetcher = fetcher or self._default_fetcher

    def _default_fetcher(self, url: str) -> Tuple[bytes, Dict[str, str]]:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, */*",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            content = resp.read()
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            return content, resp_headers

    def post_from_wp_dict(self, p: Dict[str, Any]) -> PostItem:
        """Transforms a raw WordPress REST API post dictionary into a canonical PostItem model."""
        slug = str(p.get("slug") or "").strip()
        raw_title = p.get("title", {})
        title_text = raw_title.get("rendered", "") if isinstance(raw_title, dict) else str(raw_title or "")
        title = strip_html(title_text) or slug.replace("-", " ").title()

        raw_excerpt = p.get("excerpt", {})
        excerpt_text = raw_excerpt.get("rendered", "") if isinstance(raw_excerpt, dict) else str(raw_excerpt or "")
        excerpt = strip_html(excerpt_text)

        raw_content = p.get("content", {})
        content_html = raw_content.get("rendered", "") if isinstance(raw_content, dict) else str(raw_content or "")

        cat_name, cat_slug = extract_category_and_slug(p, slug)
        _, parent_slug = infer_category_and_parent(slug)
        if not parent_slug:
            parent_slug = cat_slug

        date_str = str(p.get("date") or "")
        modified_str = str(p.get("modified") or date_str)

        image_url = extract_featured_image(p)

        raw_meta = {
            "wp_id": p.get("id"),
            "wp_link": p.get("link"),
            "status": p.get("status"),
            "author_id": p.get("author"),
        }

        checklist = generate_default_checklist(title)
        takeaways = generate_default_takeaways(title, cat_name)

        return PostItem(
            slug=slug,
            title=title,
            excerpt=excerpt,
            content_html=content_html,
            category=cat_name,
            category_slug=cat_slug,
            parent_slug=parent_slug,
            date=date_str,
            modified=modified_str,
            image_url=image_url,
            local_image_path=f"assets/images/{slug}.jpg" if slug else "",
            custom_edited=False,
            checklist=checklist,
            takeaways=takeaways,
            raw_meta=raw_meta,
        )

    def fetch_posts(self, max_posts: Optional[int] = None, page_size: int = 100) -> List[PostItem]:
        """Fetches posts in paginated batches until exhausted or max_posts is reached.

        Handles HTTP 400 'rest_post_invalid_page_number' as normal pagination termination.
        """
        all_posts: List[PostItem] = []
        page = 1
        per_page = max(1, min(page_size, 100))

        while True:
            if max_posts is not None and len(all_posts) >= max_posts:
                break

            api_url = f"{self.base_url}/wp-json/wp/v2/posts?per_page={per_page}&page={page}&_embed=1"
            logger.info("Fetching WordPress posts page %d: %s", page, api_url)

            try:
                body_bytes, resp_headers = self._fetcher(api_url)
            except urllib.error.HTTPError as exc:
                if exc.code == 400:
                    # Check for WordPress invalid page number termination code
                    try:
                        err_data = json.loads(exc.read().decode("utf-8"))
                        if err_data.get("code") == "rest_post_invalid_page_number":
                            logger.info("Reached end of WordPress posts pagination at page %d", page)
                            break
                    except Exception:
                        pass
                    # If 400 on page > 1, treat as termination
                    if page > 1:
                        logger.info("HTTP 400 on page %d; terminating pagination", page)
                        break
                logger.warning("HTTP error %d fetching posts page %d: %s", exc.code, page, exc)
                break
            except Exception as exc:
                logger.warning("Error fetching posts page %d: %s", page, exc)
                break

            try:
                text = body_bytes.decode("utf-8").lstrip()
                try:
                    posts_raw = json.loads(text)
                except Exception:
                    posts_raw, _ = json.JSONDecoder().raw_decode(text)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                logger.warning("Failed to decode JSON from %s: %s", api_url, exc)
                break

            if not isinstance(posts_raw, list) or not posts_raw:
                logger.info("Empty posts list received at page %d; terminating", page)
                break

            for p_dict in posts_raw:
                if isinstance(p_dict, dict) and p_dict.get("slug"):
                    item = self.post_from_wp_dict(p_dict)
                    all_posts.append(item)
                    if max_posts is not None and len(all_posts) >= max_posts:
                        break

            # Inspect X-WP-TotalPages header if present
            total_pages_hdr = resp_headers.get("x-wp-totalpages")
            if total_pages_hdr:
                try:
                    total_pages = int(total_pages_hdr)
                    if page >= total_pages:
                        logger.info("Reached declared total pages (%d); terminating", total_pages)
                        break
                except ValueError:
                    pass

            page += 1

        return all_posts

    def fetch_post_by_slug(self, slug: str) -> Optional[PostItem]:
        """Fetches a single post by slug via ?slug=<slug>&_embed=1."""
        if not slug:
            return None

        safe_slug = urllib.parse.quote(slug.strip())
        api_url = f"{self.base_url}/wp-json/wp/v2/posts?slug={safe_slug}&_embed=1"

        try:
            body_bytes, _ = self._fetcher(api_url)
            text = body_bytes.decode("utf-8").lstrip()
            try:
                posts_raw = json.loads(text)
            except Exception:
                posts_raw, _ = json.JSONDecoder().raw_decode(text)

            if isinstance(posts_raw, list) and len(posts_raw) > 0:
                first = posts_raw[0]
                if isinstance(first, dict):
                    return self.post_from_wp_dict(first)
        except Exception as exc:
            logger.warning("Error fetching post slug '%s': %s", slug, exc)

        return None

    def fetch_posts_by_slugs(self, slugs: List[str]) -> List[PostItem]:
        """Fetches posts matching a list of slugs."""
        results: List[PostItem] = []
        for s in slugs:
            post = self.fetch_post_by_slug(s)
            if post:
                results.append(post)
        return results


def fetch_wp_posts(base_url: str, max_posts: int = 100, page_size: int = 100) -> List[PostItem]:
    """Convenience functional interface to fetch WordPress posts."""
    client = WordPressClient(base_url=base_url)
    return client.fetch_posts(max_posts=max_posts, page_size=page_size)


def fetch_wp_post_by_slug(base_url: str, slug: str) -> Optional[PostItem]:
    """Convenience functional interface to fetch a single WordPress post by slug."""
    client = WordPressClient(base_url=base_url)
    return client.fetch_post_by_slug(slug)


def fetch_wp_rest_posts(wp_domain: str, max_pages: int = 10) -> Dict[str, Dict[str, Any]]:
    """Fetches WordPress REST API posts to map slugs to titles, excerpts, categories, and images.

    Compatible with legacy and integration test signatures expecting a dict mapping slug -> post dict.
    """
    clean_domain = wp_domain.strip().rstrip("/")
    if not clean_domain.startswith(("http://", "https://")):
        clean_domain = f"https://{clean_domain}"

    client = WordPressClient(base_url=clean_domain)
    posts = client.fetch_posts(max_posts=max_pages * 100, page_size=100)

    result_map: Dict[str, Dict[str, Any]] = {}
    for p in posts:
        if not p.slug:
            continue
        result_map[p.slug] = {
            "slug": p.slug,
            "title": p.title,
            "excerpt": p.excerpt,
            "image": p.image_url,
            "url": (p.raw_meta or {}).get("wp_link", f"{clean_domain}/{p.slug}/"),
            "category": p.category,
            "parent_slug": p.category_slug or p.parent_slug,
            "lastmod": p.modified[:10] if p.modified else "",
        }

    return result_map
