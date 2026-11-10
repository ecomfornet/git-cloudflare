"""Copies pre-built static pages and assets from static-site/ to dist/ with rebased links."""
from __future__ import annotations

import os
import re
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)

STATIC_PAGES = [
    "about",
    "contact",
    "privacy-policy",
    "terms",
    "cookie-policy",
    "disclaimer",
    "copyright",
    "editorial-policy",
    "fact-checking-policy",
    "sitemap",
]

AUTHOR_PAGES = [
    "sophia-bennett",
]

CATEGORY_PAGES = [
    "bedroom",
    "diy-decor",
    "kitchen-dining",
    "living-room",
    "outdoor-spaces",
    "seasonal-trends",
]


def _rebase_links(html: str, path_prefix: str = "") -> str:
    """Rewrites relative asset and page links to work from dist/ root."""
    base = path_prefix.rstrip("/") if path_prefix else ""

    # Replace relative asset references like ../../assets/ or ./assets/ or /assets/
    html = re.sub(
        r'(href|src)="(?:\./|(?:\.\./)+)assets/',
        lambda m: f'{m.group(1)}="{base}/assets/' if base else f'{m.group(1)}="/assets/',
        html,
    )

    # Fix internal page links like href="../../about/index.html" or href="../about/" or href="./about/index.html"
    page_names = STATIC_PAGES + ["category", "author"]
    for page in page_names:
        escaped = re.escape(page)
        html = re.sub(
            rf'href="(?:\./|(?:\.\./)+){escaped}(?:/index\.html|/)?(?=["\?#])',
            f'href="{base}/{page}/"' if base else f'href="/{page}/"',
            html,
        )

    # Category subpages
    for cat in CATEGORY_PAGES:
        html = re.sub(
            rf'href="(?:\./|(?:\.\./)+)category/{cat}(?:/index\.html|/)?(?=["\?#])',
            f'href="{base}/category/{cat}/"' if base else f'href="/category/{cat}/"',
            html,
        )

    # Author subpages
    for author in AUTHOR_PAGES:
        html = re.sub(
            rf'href="(?:\./|(?:\.\./)+)author/{author}(?:/index\.html|/)?(?=["\?#])',
            f'href="{base}/author/{author}/"' if base else f'href="/author/{author}/"',
            html,
        )

    # Blog post links: href="../../blog/cozy-bedroom-ideas/index.html" -> href="{base}/cozy-bedroom-ideas/"
    html = re.sub(
        r'href="(?:\./|(?:\.\./)+)blog/([^/\"]+)(?:/index\.html|/)?(?=["\?#])',
        lambda m: f'href="{base}/{m.group(1)}/"' if base else f'href="/{m.group(1)}/"',
        html,
    )

    # Root / Home links
    html = re.sub(
        r'href="(?:\./|(?:\.\./)+)(?:index\.html)?(?=["\?#])',
        f'href="{base}/"' if base else 'href="/"',
        html,
    )

    # Favicon
    html = re.sub(
        r'href="(?:\./|(?:\.\./)+)favicon\.ico"',
        f'href="{base}/favicon.ico"' if base else 'href="/favicon.ico"',
        html,
    )

    return html


def copy_static_pages(
    source_site_dir: str,
    output_dir: str,
    path_prefix: str = "",
    favicon_src: Optional[str] = None,
    overwrite_existing: bool = False,
    copy_categories: bool = False,
) -> int:
    """Copies static pages, authors, and essential assets from source_site_dir to output_dir without overwriting dynamic pages or injecting supplemental categories."""
    copied = 0

    # 1. Copy top-level static legal/about pages (only if missing or overwrite requested)
    for page in STATIC_PAGES:
        src_path = os.path.join(source_site_dir, page, "index.html")
        dst_dir = os.path.join(output_dir, page)
        dst_path = os.path.join(dst_dir, "index.html")

        if not os.path.exists(src_path):
            continue
        if os.path.exists(dst_path) and not overwrite_existing:
            continue

        os.makedirs(dst_dir, exist_ok=True)
        with open(src_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()

        html = _rebase_links(html, path_prefix=path_prefix)
        with open(dst_path, "w", encoding="utf-8") as f:
            f.write(html)

        copied += 1

    # 2. Copy author pages (only if missing or overwrite requested)
    for author_slug in AUTHOR_PAGES:
        src_path = os.path.join(source_site_dir, "author", author_slug, "index.html")
        dst_dir = os.path.join(output_dir, "author", author_slug)
        dst_path = os.path.join(dst_dir, "index.html")

        if not os.path.exists(src_path):
            continue
        if os.path.exists(dst_path) and not overwrite_existing:
            continue

        os.makedirs(dst_dir, exist_ok=True)
        with open(src_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()

        html = _rebase_links(html, path_prefix=path_prefix)
        with open(dst_path, "w", encoding="utf-8") as f:
            f.write(html)

        copied += 1

    # 3. Copy category pages only if explicitly requested (strictly respects ingested data)
    if copy_categories:
        for cat_slug in CATEGORY_PAGES:
            src_path = os.path.join(source_site_dir, "category", cat_slug, "index.html")
            dst_dir = os.path.join(output_dir, "category", cat_slug)
            dst_path = os.path.join(dst_dir, "index.html")

            if not os.path.exists(src_path):
                continue
            if os.path.exists(dst_path) and not overwrite_existing:
                continue

            os.makedirs(dst_dir, exist_ok=True)
            with open(src_path, "r", encoding="utf-8", errors="replace") as f:
                html = f.read()

            html = _rebase_links(html, path_prefix=path_prefix)
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(html)

            copied += 1

    # 4. Copy favicon and ads.txt
    favicon_src_path = favicon_src or os.path.join(source_site_dir, "favicon.ico")
    favicon_dst = os.path.join(output_dir, "favicon.ico")
    if os.path.exists(favicon_src_path):
        shutil.copy2(favicon_src_path, favicon_dst)

    ads_src = os.path.join(source_site_dir, "ads.txt")
    ads_dst = os.path.join(output_dir, "ads.txt")
    if os.path.exists(ads_src):
        shutil.copy2(ads_src, ads_dst)

    # 5. Copy static-site assets into output_dir/assets and ensure author image is in images/
    src_assets = os.path.join(source_site_dir, "assets")
    dst_assets = os.path.join(output_dir, "assets")
    dst_images = os.path.join(output_dir, "assets", "images")
    os.makedirs(dst_images, exist_ok=True)

    if os.path.exists(src_assets):
        os.makedirs(dst_assets, exist_ok=True)
        for item in os.listdir(src_assets):
            s_item = os.path.join(src_assets, item)
            d_item = os.path.join(dst_assets, item)
            if os.path.isfile(s_item) and not os.path.exists(d_item):
                shutil.copy2(s_item, d_item)

            # Copy author-sophia into images/author-sophia.jpg
            if "author-sophia" in item.lower() and item.lower().endswith((".jpg", ".png", ".webp")):
                sophia_target = os.path.join(dst_images, "author-sophia.jpg")
                if not os.path.exists(sophia_target):
                    shutil.copy2(s_item, sophia_target)

    return copied
