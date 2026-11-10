"""Full-content webpage scraper, image extractor, WebP optimizer, and multi-domain storage organizer."""

from __future__ import annotations

import datetime
import hashlib
import html as html_lib
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from bs4 import BeautifulSoup, Comment, Tag

from app.ingestion.image_downloader import (
    DEFAULT_USER_AGENT,
    DEFAULT_WEBP_QUALITY,
    STANDARD_HERO_HEIGHT,
    STANDARD_HERO_WIDTH,
    generate_svg_badge,
    optimize_image_to_webp,
)
from app.ingestion.sitemap_parser import SitemapEntry, extract_slug_from_url, parse_sitemap_entries
from app.ingestion.wp_client import (
    generate_default_checklist,
    generate_default_takeaways,
    infer_category_and_parent,
    strip_html,
)
from app.models import PostItem

logger = logging.getLogger(__name__)


def extract_subdomain(url: str) -> str:
    """Extracts clean alphanumeric subdomain identifier from URL string without protocol, www, or TLD extensions.

    Args:
        url: Raw URL string or domain name.

    Returns:
        Clean alphanumeric subdomain string (e.g. 'my-site', 'magazine', 'blog').
        Falls back to 'default' if input is empty or invalid.

    Permutations handled per Section 22.2:
        'https://mysite.com/sitemap_index.xml' -> 'mysite'
        'https://magazine.com/post-sitemap.xml' -> 'magazine'
        'https://blog.mysite.com/' -> 'blog'
        'https://mybrand.workers.dev' -> 'mybrand'
        'http://www.homedecor.com/page-1/' -> 'homedecor'
        'https://decor.studio.co.uk:8080/article/' -> 'decor'
        'https://minimalist-living.co.uk/feed/' -> 'minimalist-living'
        'myblog.net' -> 'myblog'
        '' or None -> 'default'
    """
    if not url:
        return "default"

    raw = str(url).strip()
    if not raw:
        return "default"

    if "://" not in raw:
        raw = f"https://{raw}"

    try:
        parsed = urllib.parse.urlsplit(raw)
        host = (parsed.hostname or parsed.netloc or "").lower().strip()
    except Exception:
        return "default"

    if "@" in host:
        host = host.split("@")[-1]
    if ":" in host:
        host = host.split(":")[0]

    if host.startswith("www."):
        host = host[4:]

    if not host:
        return "default"

    # Cloudflare Workers recognition: project_name.account_subdomain.workers.dev -> project_name
    if host.endswith(".workers.dev"):
        labels = [lbl for lbl in host.split(".") if lbl]
        if labels:
            token = labels[0]
            clean = re.sub(r"[^a-z0-9_-]", "", token.lower()).strip("_-")
            return clean or "default"

    labels = [lbl for lbl in host.split(".") if lbl]
    if not labels:
        return "default"

    # Multi-part ccTLD handling (e.g. .co.uk, .com.au, .org.uk, .co.jp, .co.nz, .com.br, etc.)
    cctld_slds = {"co", "com", "org", "net", "edu", "gov", "ac", "mil", "ne", "or", "gen"}
    is_two_part_cctld = (
        len(labels) >= 3
        and labels[-2] in cctld_slds
        and len(labels[-1]) == 2
    )

    if is_two_part_cctld:
        # Domain labels before the 2-part ccTLD
        domain_labels = labels[:-2]
        # decor.studio.co.uk -> domain_labels=['decor', 'studio'] -> token='decor'
        # minimalist-living.co.uk -> domain_labels=['minimalist-living'] -> token='minimalist-living'
        token = domain_labels[0]
    else:
        # Standard TLD (e.g. .com, .net, .org, .dev, etc.)
        # blog.stylesdays.com -> labels=['blog', 'stylesdays', 'com'] -> token='blog'
        # stylesdays.com -> labels=['stylesdays', 'com'] -> token='stylesdays'
        # stylesdays -> labels=['stylesdays'] -> token='stylesdays'
        token = labels[0]

    clean = re.sub(r"[^a-z0-9_-]", "", token.lower()).strip("_-")
    return clean or "default"


def extract_domain(url: str) -> str:
    """Extracts clean canonical domain name from URL string.

    Examples:
        'https://stylesdays.com/sitemap_index.xml' -> 'stylesdays.com'
        'http://sub.decor.co.uk:8080/path/' -> 'sub.decor.co.uk'
        'example.org' -> 'example.org'
    """
    if not url:
        return "default"

    raw = url.strip()
    if "://" not in raw:
        raw = f"https://{raw}"

    try:
        parsed = urllib.parse.urlparse(raw)
        host = (parsed.hostname or parsed.netloc or "").lower().strip()
        if host.startswith("www."):
            host = host[4:]
        return host or "default"
    except Exception:
        return "default"


def get_domain_storage_paths(subdomain: str, base_dir: str = ".") -> Dict[str, str]:
    """Resolves and creates isolated directory structures for a specific subdomain or domain project.

    Args:
        subdomain: Clean subdomain identifier or raw domain/URL string.
        base_dir: Root directory for relative path resolution.

    Returns:
        dict with absolute filesystem paths:
        {
            "subdomain": str,               # Clean subdomain identifier
            "domain": str,                  # Clean domain or subdomain identifier
            "html_dir": str,                # scraped_data/<subdomain>/html
            "images_dir": str,              # assets/<subdomain>/images
            "archive_images_dir": str,      # scraped_data/<subdomain>/assets/images
            "dist_dir": str,                # dist/<subdomain>
            "manifest_file": str,           # scraped_data/<subdomain>/manifest.json
            "html": str,                    # alias for html_dir
            "assets": str,                  # scraped_data/<subdomain>/assets
            "images": str,                  # alias for archive_images_dir
            "shared_images": str,           # alias for images_dir
            "manifest": str,                # alias for manifest_file
            "dist": str,                    # alias for dist_dir
        }
    """
    if not subdomain:
        subdomain = "default"

    raw_str = str(subdomain).strip()
    clean_sub = extract_subdomain(raw_str)
    clean_domain = extract_domain(raw_str)

    # Determine primary folder token
    # If explicitly passed a legacy domain with dot (e.g. "stylesdays.com") without scheme or workers.dev:
    if "." in raw_str and not ("://" in raw_str or raw_str.endswith(".workers.dev")):
        folder_token = clean_domain
    else:
        folder_token = clean_sub

    html_dir = os.path.abspath(os.path.join(base_dir, "scraped_data", folder_token, "html"))
    assets_dir = os.path.abspath(os.path.join(base_dir, "scraped_data", folder_token, "assets"))
    images_dir = os.path.abspath(os.path.join(base_dir, "assets", folder_token, "images"))
    archive_images_dir = os.path.abspath(os.path.join(base_dir, "scraped_data", folder_token, "assets", "images"))
    manifest_file = os.path.abspath(os.path.join(base_dir, "scraped_data", folder_token, "manifest.json"))
    dist_dir = os.path.abspath(os.path.join(base_dir, "dist", folder_token))

    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(archive_images_dir, exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)

    # If folder_token differs from clean_sub (e.g. legacy stylesdays.com vs clean stylesdays),
    # also ensure clean_sub directories are created so both are immediately ready.
    if clean_sub and clean_sub != folder_token:
        os.makedirs(os.path.abspath(os.path.join(base_dir, "scraped_data", clean_sub, "html")), exist_ok=True)
        os.makedirs(os.path.abspath(os.path.join(base_dir, "scraped_data", clean_sub, "assets")), exist_ok=True)
        os.makedirs(os.path.abspath(os.path.join(base_dir, "scraped_data", clean_sub, "assets", "images")), exist_ok=True)
        os.makedirs(os.path.abspath(os.path.join(base_dir, "assets", clean_sub, "images")), exist_ok=True)
        os.makedirs(os.path.abspath(os.path.join(base_dir, "dist", clean_sub)), exist_ok=True)

    domain_identifier = clean_domain if folder_token == clean_domain else clean_sub

    return {
        "subdomain": clean_sub,
        "domain": domain_identifier,
        "html_dir": html_dir,
        "images_dir": images_dir,
        "archive_images_dir": archive_images_dir,
        "dist_dir": dist_dir,
        "manifest_file": manifest_file,
        "html": html_dir,
        "assets": assets_dir,
        "images": archive_images_dir,
        "shared_images": images_dir,
        "manifest": manifest_file,
        "dist": dist_dir,
    }


def get_subdomain_storage_paths(subdomain: str, base_dir: str = ".") -> Dict[str, str]:
    """Resolves and creates isolated directory structures strictly keyed by clean subdomain."""
    clean_sub = extract_subdomain(subdomain)
    return get_domain_storage_paths(clean_sub, base_dir=base_dir)



def _fetch_html(url: str, timeout: int = 20, user_agent: str = DEFAULT_USER_AGENT) -> str:
    """Fetches decoded HTML string from a remote URL with standard User-Agent header."""
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw_bytes = resp.read()
        # Decode using response charset or fallback to utf-8
        charset = resp.headers.get_content_charset() or "utf-8"
        try:
            return raw_bytes.decode(charset, errors="replace")
        except Exception:
            return raw_bytes.decode("utf-8", errors="replace")


def _fetch_html_with_retry(
    url: str,
    timeout: int = 20,
    user_agent: str = DEFAULT_USER_AGENT,
    max_retries: int = 3,
    base_delay: float = 0.25,
    max_delay: float = 6.0,
    fetcher: Optional[Callable[[str], bytes]] = None,
) -> str:
    """Fetches HTML with exponential backoff and jitter protection on HTTP 429/503 or transient network errors."""
    import random
    import time

    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            if fetcher:
                raw_bytes = fetcher(url)
                if isinstance(raw_bytes, str):
                    return raw_bytes
                return raw_bytes.decode("utf-8", errors="replace")
            return _fetch_html(url, timeout=timeout, user_agent=user_agent)
        except urllib.error.HTTPError as http_err:
            last_exc = http_err
            # Retry on rate limiting (429) or temporary server errors (502, 503, 504)
            if http_err.code in (429, 502, 503, 504) and attempt < max_retries:
                jitter = random.uniform(0.05, 0.2)
                delay = min(max_delay, base_delay * (2 ** attempt) + jitter)
                logger.warning("HTTP %d for %s; retrying in %.2fs (attempt %d/%d)", http_err.code, url, delay, attempt + 1, max_retries)
                time.sleep(delay)
                continue
            raise http_err
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as net_err:
            last_exc = net_err
            if attempt < max_retries:
                jitter = random.uniform(0.05, 0.2)
                delay = min(max_delay, base_delay * (2 ** attempt) + jitter)
                logger.warning("Network error for %s: %s; retrying in %.2fs (attempt %d/%d)", url, net_err, delay, attempt + 1, max_retries)
                time.sleep(delay)
                continue
            raise net_err
        except Exception as exc:
            raise exc

    if last_exc:
        raise last_exc
    return ""



def _clean_title(raw_title: str) -> str:
    """Cleans site branding, pipe, or dash suffixes from an extracted title."""
    if not raw_title:
        return ""
    title = strip_html(raw_title)
    # Remove common patterns like " - StylesDays", " | Home Decor Magazine"
    for sep in (" | ", " - ", " – ", " — ", " :: "):
        if sep in title:
            parts = title.split(sep)
            if len(parts[0].strip()) > 8:
                title = parts[0].strip()
                break
    return title.strip()


def _extract_meta_content(soup: BeautifulSoup, *property_or_names: str) -> str:
    """Extracts first matching meta tag content attribute."""
    for prop in property_or_names:
        tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    return ""


def clean_article_container(container: Tag, base_url: str) -> str:
    """Extracts semantic article elements, removes noisy widgets, and returns clean HTML."""
    # Remove unwanted tags
    for unwanted in container.find_all(
        ["script", "style", "noscript", "iframe", "form", "button", "svg", "nav", "header", "footer", "aside"]
    ):
        unwanted.decompose()

    # Remove HTML comments
    for comment in container.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    # Remove noisy widgets by class or id
    noisy_patterns = re.compile(
        r"comment|share|social|advert|promo|sidebar|newsletter|author-box|related-posts|breadcrumb|widget|jp-relatedposts",
        re.I,
    )
    for tag in container.find_all(True):
        classes = " ".join(tag.get("class", [])) if isinstance(tag.get("class"), list) else str(tag.get("class") or "")
        tag_id = str(tag.get("id") or "")
        if noisy_patterns.search(classes) or noisy_patterns.search(tag_id):
            tag.decompose()

    # Clean attributes on surviving tags
    allowed_tags = {
        "p", "h1", "h2", "h3", "h4", "h5", "h6",
        "ul", "ol", "li", "blockquote", "figure", "figcaption",
        "table", "thead", "tbody", "tr", "th", "td",
        "strong", "b", "em", "i", "a", "img", "code", "pre", "hr", "div", "span"
    }

    for tag in list(container.find_all(True)):
        if tag.name not in allowed_tags:
            tag.unwrap()
            continue

        # Strip inline style, onclick, and junk attributes
        attrs_to_remove = [attr for attr in tag.attrs if attr.startswith("on") or attr in ("style", "data-reactid")]
        for attr in attrs_to_remove:
            del tag[attr]

        if tag.name == "a":
            href = tag.get("href", "")
            if href and not href.startswith(("#", "mailto:", "tel:")):
                tag["href"] = urllib.parse.urljoin(base_url, href)
            tag["target"] = "_blank"
            tag["rel"] = "noopener"

    return str(container).strip()


def scrape_post_from_html(
    html: str,
    url: str,
    domain: Optional[str] = None,
    subdomain: Optional[str] = None,
    download_images: bool = True,
    base_dir: str = ".",
    fetcher: Optional[Callable[[str], bytes]] = None,
    timeout: int = 15,
) -> PostItem:
    """Parses raw HTML, extracts full article content, downloads/optimizes images, and archives to subdomain folder."""
    clean_target = subdomain or domain or extract_subdomain(url)
    storage = get_domain_storage_paths(clean_target, base_dir=base_dir)
    sub_token = storage.get("subdomain") or extract_subdomain(clean_target)
    slug = extract_slug_from_url(url) or "scraped-guide"

    soup = BeautifulSoup(html, "html.parser")

    # 1. Title Extraction
    meta_title = _extract_meta_content(soup, "og:title", "twitter:title")
    h1_tag = soup.find("h1")
    title_tag = soup.find("title")
    raw_title = meta_title or (h1_tag.get_text() if h1_tag else "") or (title_tag.get_text() if title_tag else "")
    title = _clean_title(raw_title) or slug.replace("-", " ").title()

    # 2. Excerpt / Description Extraction
    excerpt = _extract_meta_content(soup, "og:description", "description", "twitter:description")
    if not excerpt:
        first_p = soup.find("p")
        if first_p:
            excerpt = strip_html(first_p.get_text())[:280]

    # 3. Dates Extraction
    date_str = _extract_meta_content(soup, "article:published_time", "og:published_time")
    modified_str = _extract_meta_content(soup, "article:modified_time", "og:updated_time")
    if not date_str:
        time_tag = soup.find("time", attrs={"datetime": True})
        if time_tag:
            date_str = str(time_tag["datetime"]).strip()
    if not date_str:
        date_str = datetime.date.today().isoformat()
    if not modified_str:
        modified_str = date_str

    # Normalize dates to YYYY-MM-DD
    date_iso = date_str[:10] if len(date_str) >= 10 else datetime.date.today().isoformat()
    modified_iso = modified_str[:10] if len(modified_str) >= 10 else date_iso

    # 4. Category and Tags Extraction
    category = _extract_meta_content(soup, "article:section")
    category_slug = ""
    parent_slug = ""
    if not category:
        category, parent_slug = infer_category_and_parent(slug)
        category_slug = parent_slug
    else:
        category = strip_html(category)
        category_slug = re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")
        parent_slug = category_slug

    extracted_tags: List[str] = []
    for tag_meta in soup.find_all("meta", attrs={"property": "article:tag"}):
        content_val = str(tag_meta.get("content") or "").strip()
        if content_val and content_val not in extracted_tags:
            extracted_tags.append(content_val)
    if not extracted_tags:
        for a_tag in soup.find_all("a", attrs={"rel": lambda r: r and "tag" in r}):
            text_val = a_tag.get_text().strip()
            if text_val and text_val not in extracted_tags:
                extracted_tags.append(text_val)

    # 5. Locate Article Content Container
    article_container = (
        soup.find("article")
        or soup.find(class_=re.compile(r"entry-content|post-content|article-body|story-content", re.I))
        or soup.find("main")
        or soup.find(id=re.compile(r"content|main", re.I))
        or soup.body
    )

    content_soup = BeautifulSoup(str(article_container), "html.parser") if article_container else BeautifulSoup("", "html.parser")

    # 6. Featured Image Discovery
    featured_img_url = _extract_meta_content(soup, "og:image", "twitter:image")
    if not featured_img_url:
        first_img = content_soup.find("img")
        if first_img:
            featured_img_url = first_img.get("src") or first_img.get("data-src") or ""

    if featured_img_url and "://" not in featured_img_url:
        featured_img_url = urllib.parse.urljoin(url, featured_img_url)

    # 7. In-Content Image Extraction, Download & WebP Optimization
    downloaded_image_count = 0
    hero_local_image_path = f"assets/{sub_token}/images/{slug}.webp"
    hero_target_file = os.path.join(storage["images_dir"], f"{slug}.webp")
    hero_archive_file = os.path.join(storage["archive_images_dir"], f"{slug}.webp")

    # Download featured hero image
    if download_images and featured_img_url:
        try:
            raw_data = fetcher(featured_img_url) if fetcher else _fetch_raw_bytes(featured_img_url, timeout=timeout)
            if raw_data and len(raw_data) > 64:
                optimize_image_to_webp(raw_data, hero_target_file, quality=DEFAULT_WEBP_QUALITY)
                if not os.path.exists(hero_archive_file):
                    optimize_image_to_webp(raw_data, hero_archive_file, quality=DEFAULT_WEBP_QUALITY)
                downloaded_image_count += 1
        except Exception as exc:
            logger.warning("Could not download hero image for %s: %s", slug, exc)

    # If hero image is missing or failed, generate clean SVG badge
    if not os.path.exists(hero_target_file):
        generate_svg_badge(title=title, slug=slug, output_path=hero_target_file, subtitle=category)
    if not os.path.exists(hero_archive_file):
        generate_svg_badge(title=title, slug=slug, output_path=hero_archive_file, subtitle=category)

    # Process all inline <img> tags in content
    img_tags = content_soup.find_all("img")
    for idx, img in enumerate(img_tags):
        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-lazy-src")
            or img.get("data-orig-file")
            or img.get("data-original")
            or ""
        )
        if not src and img.get("srcset"):
            srcset_parts = str(img["srcset"]).split(",")
            if srcset_parts:
                src = srcset_parts[0].strip().split()[0]
        if not src:
            continue
        full_src = urllib.parse.urljoin(url, src)

        # Hash image URL for unique, clean naming
        url_hash = hashlib.md5(full_src.encode("utf-8")).hexdigest()[:8]
        img_filename = f"{slug}-img-{idx + 1}-{url_hash}.webp"
        target_img_path = os.path.join(storage["images_dir"], img_filename)
        archive_img_path = os.path.join(storage["archive_images_dir"], img_filename)
        web_asset_src = f"/assets/{sub_token}/images/{img_filename}"

        if download_images:
            try:
                if not os.path.exists(target_img_path):
                    raw_data = fetcher(full_src) if fetcher else _fetch_raw_bytes(full_src, timeout=timeout)
                    if raw_data and len(raw_data) > 64:
                        optimize_image_to_webp(raw_data, target_img_path, quality=DEFAULT_WEBP_QUALITY)
                        optimize_image_to_webp(raw_data, archive_img_path, quality=DEFAULT_WEBP_QUALITY)
                        downloaded_image_count += 1
                    else:
                        generate_svg_badge(title=f"{slug} Photo {idx + 1}", slug=slug, output_path=target_img_path)
                        generate_svg_badge(title=f"{slug} Photo {idx + 1}", slug=slug, output_path=archive_img_path)
                img["src"] = web_asset_src
            except Exception as exc:
                logger.warning("Failed downloading inline image %s: %s; falling back to SVG", full_src, exc)
                generate_svg_badge(title=f"{slug} Photo {idx + 1}", slug=slug, output_path=target_img_path)
                generate_svg_badge(title=f"{slug} Photo {idx + 1}", slug=slug, output_path=archive_img_path)
                img["src"] = web_asset_src
        else:
            img["src"] = full_src

        # Clean attributes for responsive display
        img["loading"] = "lazy"
        img["decoding"] = "async"
        for attr in ("srcset", "sizes", "data-src", "data-lazy-src", "data-orig-file", "data-original", "style"):
            if img.has_attr(attr):
                del img[attr]

    # Clean HTML body
    cleaned_html = clean_article_container(content_soup, url)

    # 8. Archive Scraped HTML File to Domain/Subdomain Folder
    saved_html_path = os.path.join(storage["html_dir"], f"{slug}.html")
    with open(saved_html_path, "w", encoding="utf-8") as f:
        f.write(cleaned_html)

    # If storage folder differs from clean_sub, also ensure archived HTML exists under clean_sub
    if sub_token and sub_token != clean_target and os.path.isdir(os.path.join(base_dir, "scraped_data", sub_token, "html")):
        sub_html_path = os.path.join(base_dir, "scraped_data", sub_token, "html", f"{slug}.html")
        if not os.path.exists(sub_html_path):
            with open(sub_html_path, "w", encoding="utf-8") as f:
                f.write(cleaned_html)

    # 9. Generate Checklists and Key Takeaways
    checklist = generate_default_checklist(title)
    takeaways = generate_default_takeaways(title, category)

    # Preserve explicit domain if caller passed one, otherwise use clean subdomain
    post_domain = domain if domain else sub_token

    post = PostItem(
        slug=slug,
        title=title,
        excerpt=excerpt,
        content_html=cleaned_html,
        category=category,
        category_slug=category_slug,
        parent_slug=parent_slug,
        date=date_iso,
        modified=modified_iso,
        image_url=featured_img_url,
        local_image_path=hero_local_image_path,
        image_width=STANDARD_HERO_WIDTH,
        image_height=STANDARD_HERO_HEIGHT,
        checklist=checklist,
        takeaways=takeaways,
        domain=post_domain,
        raw_meta={
            "source_url": url,
            "domain": post_domain,
            "subdomain": sub_token,
            "scraped_html_path": saved_html_path,
            "images_extracted": len(img_tags),
            "images_downloaded": downloaded_image_count,
            "tags": extracted_tags,
        },
    )

    logger.info("Successfully scraped full content for '%s' (domain=%s, images=%d)", slug, post_domain, downloaded_image_count)
    return post


def _fetch_raw_bytes(url: str, timeout: int = 15) -> bytes:
    """Helper to download binary content (images) with User-Agent."""
    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "image/webp,image/avif,image/*,*/*;q=0.8"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def discover_sitemap_urls(
    sitemap_url: str,
    max_urls: Optional[int] = None,
    max_depth: int = 5,
    timeout: int = 15,
    fetcher: Optional[Callable[[str], bytes]] = None,
    user_agent: str = DEFAULT_USER_AGENT,
) -> List[str]:
    """Recursively discovers all post/article URLs from an XML sitemap or sitemap index."""
    from app.ingestion.sitemap_parser import discover_sitemap_urls as _discover
    return _discover(
        sitemap_url=sitemap_url,
        max_urls=max_urls,
        max_depth=max_depth,
        timeout=timeout,
        fetcher=fetcher,
        user_agent=user_agent,
    )


def scrape_sitemap(
    sitemap_url: str,
    max_posts: int = 100,
    download_images: bool = True,
    base_dir: str = ".",
    timeout: int = 15,
    fetcher: Optional[Callable[[str], bytes]] = None,
    progress_callback: Optional[Callable[..., None]] = None,
    batch_size: int = 20,
    inter_batch_delay: float = 0.0,
    max_retries: int = 3,
    project_id: Optional[str] = None,
) -> List[PostItem]:
    """Recursively parses XML sitemap, fetches every article page in batches, extracts full content and WebP images."""
    subdomain = (project_id or "").strip() or extract_subdomain(sitemap_url)
    storage = get_domain_storage_paths(subdomain, base_dir=base_dir)

    def _report_progress(level: str, msg: str, processed: int = 0, total: int = 0, current_url: str = "") -> None:
        if not progress_callback:
            return
        try:
            import inspect
            sig = inspect.signature(progress_callback)
            params = len(sig.parameters)
            if params >= 5:
                progress_callback(level, msg, processed, total, current_url)
            elif params == 3:
                progress_callback(processed, total, current_url)
            else:
                progress_callback(level, msg)
        except Exception:
            try:
                progress_callback(level, msg)
            except Exception:
                pass

    _report_progress("info", f"Parsing sitemap XML: {sitemap_url} (target subdomain: {subdomain})")

    entries: List[SitemapEntry] = parse_sitemap_entries(sitemap_url, timeout=timeout, fetcher=fetcher)
    if not entries:
        _report_progress("warning", f"No sitemap entries found for {sitemap_url}")
        return []

    # Filter out homepage / non-slug root URLs and deduplicate
    valid_entries = [e for e in entries if e.loc and (e.slug or extract_slug_from_url(e.loc))]
    seen_locs: Set[str] = set()
    deduped_entries: List[SitemapEntry] = []
    for e in valid_entries:
        if e.loc not in seen_locs:
            seen_locs.add(e.loc)
            deduped_entries.append(e)

    target_entries = deduped_entries[:max_posts]
    total_targets = len(target_entries)
    _report_progress("info", f"Discovered {len(entries)} URLs ({len(deduped_entries)} post articles); scraping top {total_targets}...")

    scraped_posts: List[PostItem] = []
    batch_size = max(1, batch_size)

    for chunk_start in range(0, total_targets, batch_size):
        chunk = target_entries[chunk_start : chunk_start + batch_size]
        for idx_in_chunk, entry in enumerate(chunk):
            global_idx = chunk_start + idx_in_chunk
            post_url = entry.loc
            if not post_url:
                continue

            slug = entry.slug or extract_slug_from_url(post_url)
            if not slug:
                continue

            _report_progress(
                "info",
                f"[{global_idx + 1}/{total_targets}] Scraping full article: {slug} ({post_url})",
                processed=global_idx + 1,
                total=total_targets,
                current_url=post_url,
            )

            try:
                html = _fetch_html_with_retry(
                    post_url,
                    timeout=timeout,
                    fetcher=fetcher,
                    max_retries=max_retries,
                )
                post = scrape_post_from_html(
                    html=html,
                    url=post_url,
                    domain=subdomain,
                    subdomain=subdomain,
                    download_images=download_images,
                    base_dir=base_dir,
                    fetcher=fetcher,
                    timeout=timeout,
                )
                if entry.image_urls:
                    post.raw_meta["sitemap_image_urls"] = entry.image_urls
                    if not post.image_url and entry.image_urls:
                        post.image_url = entry.image_urls[0]

                scraped_posts.append(post)
            except Exception as exc:
                logger.warning("Network scraping failed for %s: %s; falling back to sitemap entry model", post_url, exc)
                _report_progress("warning", f"Scrape failed for {slug} ({exc}); generating fallback entry.")

                fallback_hero = f"assets/{subdomain}/images/{slug}.webp"
                fallback_target = os.path.join(storage["images_dir"], f"{slug}.webp")
                fallback_archive = os.path.join(storage["archive_images_dir"], f"{slug}.webp")
                if not os.path.exists(fallback_target):
                    generate_svg_badge(title=slug.replace("-", " ").title(), slug=slug, output_path=fallback_target)
                if not os.path.exists(fallback_archive):
                    generate_svg_badge(title=slug.replace("-", " ").title(), slug=slug, output_path=fallback_archive)

                fallback_post = PostItem(
                    slug=slug,
                    title=slug.replace("-", " ").title(),
                    excerpt=f"Editorial styling and room layout guide for {slug.replace('-', ' ')}.",
                    content_html=f"<p>Comprehensive interior layout, sourcing notes, and styling instructions for {slug.replace('-', ' ')}.</p>",
                    category="Home Organization",
                    category_slug="home-organization",
                    parent_slug="home-organization",
                    date=entry.lastmod[:10] if entry.lastmod else datetime.date.today().isoformat(),
                    modified=entry.lastmod[:10] if entry.lastmod else datetime.date.today().isoformat(),
                    image_url=entry.image_urls[0] if entry.image_urls else "",
                    local_image_path=fallback_hero,
                    domain=subdomain,
                    checklist=generate_default_checklist(slug.replace("-", " ").title()),
                    takeaways=generate_default_takeaways(slug.replace("-", " ").title(), "Home Organization"),
                    raw_meta={"source_url": post_url, "sitemap_lastmod": entry.lastmod},
                )
                scraped_posts.append(fallback_post)

        # Batch persistence of PostManifest
        try:
            seen_cats: set[str] = set()
            derived_categories: list[dict[str, str]] = []
            for p in scraped_posts:
                c_name = (p.category or "").strip()
                c_slug = (p.category_slug or "").strip()
                if c_name and c_slug and c_slug not in seen_cats:
                    seen_cats.add(c_slug)
                    derived_categories.append({"name": c_name, "slug": c_slug})

            manifest_data = {
                "version": "2.0",
                "subdomain": subdomain,
                "domain": subdomain,
                "source_url": sitemap_url,
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "total_posts": len(scraped_posts),
                "posts": {p.slug: p.to_dict() for p in scraped_posts},
                "categories": derived_categories,
            }
            with open(storage["manifest_file"], "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("Could not write interim domain manifest: %s", exc)

        if inter_batch_delay > 0 and (chunk_start + batch_size) < total_targets:
            import time
            time.sleep(inter_batch_delay)

    _report_progress("success", f"Saved domain manifest with {len(scraped_posts)} posts to {storage['manifest_file']}")
    return scraped_posts


def scrape_url_list(
    urls: List[str],
    max_posts: int = 100,
    download_images: bool = True,
    base_dir: str = ".",
    timeout: int = 15,
    fetcher: Optional[Callable[[str], bytes]] = None,
    progress_callback: Optional[Callable[..., None]] = None,
    batch_size: int = 20,
    inter_batch_delay: float = 0.0,
    max_retries: int = 3,
) -> List[PostItem]:
    """Scrapes full content for an arbitrary list of URLs, isolating output into per-subdomain folders."""
    valid_urls = [u for u in urls if u and extract_slug_from_url(u)]
    target_urls = valid_urls[:max_posts] if valid_urls else urls[:max_posts]
    scraped_posts: List[PostItem] = []
    subdomain_posts: Dict[str, List[PostItem]] = {}
    batch_size = max(1, batch_size)

    def _report_progress(level: str, msg: str, processed: int = 0, total: int = 0, current_url: str = "") -> None:
        if not progress_callback:
            return
        try:
            import inspect
            sig = inspect.signature(progress_callback)
            params = len(sig.parameters)
            if params >= 5:
                progress_callback(level, msg, processed, total, current_url)
            elif params == 3:
                progress_callback(processed, total, current_url)
            else:
                progress_callback(level, msg)
        except Exception:
            try:
                progress_callback(level, msg)
            except Exception:
                pass

    total_targets = len(target_urls)

    for chunk_start in range(0, total_targets, batch_size):
        chunk = target_urls[chunk_start : chunk_start + batch_size]
        for idx_in_chunk, post_url in enumerate(chunk):
            global_idx = chunk_start + idx_in_chunk
            sub = extract_subdomain(post_url)
            slug = extract_slug_from_url(post_url) or f"post-{global_idx + 1}"
            storage = get_domain_storage_paths(sub, base_dir=base_dir)

            _report_progress(
                "info",
                f"[{global_idx + 1}/{total_targets}] Scraping {slug} (subdomain: {sub})...",
                processed=global_idx + 1,
                total=total_targets,
                current_url=post_url,
            )

            try:
                html = _fetch_html_with_retry(
                    post_url,
                    timeout=timeout,
                    fetcher=fetcher,
                    max_retries=max_retries,
                )
                post = scrape_post_from_html(
                    html=html,
                    url=post_url,
                    domain=sub,
                    subdomain=sub,
                    download_images=download_images,
                    base_dir=base_dir,
                    fetcher=fetcher,
                    timeout=timeout,
                )
                scraped_posts.append(post)
                subdomain_posts.setdefault(sub, []).append(post)
            except Exception as exc:
                logger.warning("Failed scraping %s: %s", post_url, exc)
                _report_progress("warning", f"Failed scraping {post_url}: {exc}")

                fallback_hero = f"assets/{sub}/images/{slug}.webp"
                fallback_target = os.path.join(storage["images_dir"], f"{slug}.webp")
                fallback_archive = os.path.join(storage["archive_images_dir"], f"{slug}.webp")
                if not os.path.exists(fallback_target):
                    generate_svg_badge(title=slug.replace("-", " ").title(), slug=slug, output_path=fallback_target)
                if not os.path.exists(fallback_archive):
                    generate_svg_badge(title=slug.replace("-", " ").title(), slug=slug, output_path=fallback_archive)

                fallback_post = PostItem(
                    slug=slug,
                    title=slug.replace("-", " ").title(),
                    excerpt=f"Editorial styling and room layout guide for {slug.replace('-', ' ')}.",
                    content_html=f"<p>Comprehensive interior layout, sourcing notes, and styling instructions for {slug.replace('-', ' ')}.</p>",
                    category="Home Organization",
                    category_slug="home-organization",
                    parent_slug="home-organization",
                    date=datetime.date.today().isoformat(),
                    modified=datetime.date.today().isoformat(),
                    local_image_path=fallback_hero,
                    domain=sub,
                    checklist=generate_default_checklist(slug.replace("-", " ").title()),
                    takeaways=generate_default_takeaways(slug.replace("-", " ").title(), "Home Organization"),
                    raw_meta={"source_url": post_url},
                )
                scraped_posts.append(fallback_post)
                subdomain_posts.setdefault(sub, []).append(fallback_post)

        if inter_batch_delay > 0 and (chunk_start + batch_size) < total_targets:
            import time
            time.sleep(inter_batch_delay)

    # Persist manifests for every affected subdomain
    for sub, posts_list in subdomain_posts.items():
        try:
            sub_storage = get_domain_storage_paths(sub, base_dir=base_dir)
            seen_cats: set[str] = set()
            derived_categories: list[dict[str, str]] = []
            for p in posts_list:
                c_name = (p.category or "").strip()
                c_slug = (p.category_slug or "").strip()
                if c_name and c_slug and c_slug not in seen_cats:
                    seen_cats.add(c_slug)
                    derived_categories.append({"name": c_name, "slug": c_slug})

            manifest_data = {
                "version": "2.0",
                "subdomain": sub,
                "domain": sub,
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "total_posts": len(posts_list),
                "posts": {p.slug: p.to_dict() for p in posts_list},
                "categories": derived_categories,
            }
            with open(sub_storage["manifest_file"], "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("Could not persist manifest for subdomain %s: %s", sub, exc)

    return scraped_posts

