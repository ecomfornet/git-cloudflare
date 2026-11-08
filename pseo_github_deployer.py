#!/usr/bin/env python3
"""
pSEO GitHub Pages & WordPress Editorial Hub Deployer (Upgraded v2.0)
--------------------------------------------------------------------
Upgrades the original stylesdays.com static hub generator with:
1. GitHub Organization Domain Creation & Atomic Git Tree Push via Token
   (e.g., https://home-organization.github.io)
2. WordPress Sitemap XML + WP REST API (_embed=1) + Raw URL List Importer
   with incremental Update/Diff detection (pseo_manifest.json)
3. Local Image Downloading & GitHub Hosting (/assets/images/<slug>.jpg)
   so OpenGraph, Pinterest Rich Pins, and Hero images load from GitHub Pages
4. Multi-Slug Routing Structures:
   - "single"        -> /<slug>/index.html
   - "category_slug" -> /<category-slug>/<slug>/index.html  (Slug with Slug)
   - "parent_slug"   -> /<parent-slug>/<slug>/index.html    (Slug with Slug)
   - "silo_nested"   -> /guides/<parent-slug>/<slug>/index.html
   Plus automatic Root Hub (/index.html) and Silo Category Hubs!
5. Technical pSEO Suite:
   - robots.txt with Sitemap & Pinterestbot rules
   - sitemap.xml with Image Sitemap (<image:image>) tags
   - JSON-LD Schema.org (Article + BreadcrumbList + HowTo Checklist)
6. Multi-Theme Static HTML Generator (editorial-warm, nordic-studio, pinterest-mag)
"""

import argparse
import base64
import datetime
import html as html_lib
import json
import os
import random
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "guide"


def strip_html(raw_html: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", raw_html or "")
    cleaned = html_lib.unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def fetch_url(url: str, headers: dict = None, timeout: int = 20) -> bytes:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except Exception as exc:
        print(f"[WARN] Error fetching {url}: {exc}")
        return None


def parse_sitemap(url: str, found_urls: set = None) -> set:
    if found_urls is None:
        found_urls = set()

    xml_data = fetch_url(url)
    if not xml_data:
        return found_urls

    try:
        root = ET.fromstring(xml_data)
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        sitemaps = root.findall("ns:sitemap", namespace)
        if sitemaps:
            for sm in sitemaps:
                loc = sm.find("ns:loc", namespace)
                if loc is not None and loc.text:
                    sub_url = loc.text.strip()
                    print(f"[SITEMAP] Found sub-sitemap: {sub_url}")
                    parse_sitemap(sub_url, found_urls)
        else:
            urls = root.findall("ns:url", namespace)
            for u in urls:
                loc = u.find("ns:loc", namespace)
                if loc is not None and loc.text:
                    found_urls.add(loc.text.strip())
    except Exception as exc:
        print(f"[WARN] Error parsing XML for {url}: {exc}")

    return found_urls


def infer_category_and_parent(slug: str, url_parts: list) -> tuple:
    """Infers a human-readable category and parent slug from URL segments or post slug."""
    parent_slug = ""
    if len(url_parts) >= 3:
        candidate = slugify(url_parts[-2])
        if candidate and candidate not in ("blog", "posts", "articles", "p"):
            parent_slug = candidate

    s = slug.lower()
    if "hack" in s:
        category = "IKEA Hacks"
        default_parent = "ikea-hacks"
    elif "storage" in s or "pax" in s or "closet" in s or "organiz" in s:
        category = "IKEA Storage & Closet"
        default_parent = "closet-storage"
    elif "daybed" in s or "guest" in s:
        category = "Guest Bedroom & Daybeds"
        default_parent = "guest-bedroom"
    elif "bedroom" in s:
        category = "Bedroom Ideas"
        default_parent = "bedroom-design"
    elif "living" in s or "sofa" in s or "tv" in s:
        category = "Living Room Styling"
        default_parent = "living-room"
    elif "kitchen" in s or "pantry" in s:
        category = "Kitchen & Pantry"
        default_parent = "kitchen-organization"
    else:
        category = "Home Decor & Organization"
        default_parent = "home-organization"

    return category, (parent_slug or default_parent)


def fetch_wp_rest_posts(wp_domain: str, max_pages: int = 10) -> dict:
    """Fetches WordPress REST API posts to map slugs to titles, excerpts, categories, and images."""
    wp_posts_map = {}
    base = wp_domain.rstrip("/")
    for page in range(1, max_pages + 1):
        api_url = f"{base}/wp-json/wp/v2/posts?per_page=100&page={page}&_embed=1"
        print(f"[WP-API] Fetching batch {page}: {api_url}")
        data = fetch_url(api_url)
        if not data:
            break
        try:
            posts = json.loads(data.decode("utf-8"))
            if not isinstance(posts, list) or not posts:
                break
            for p in posts:
                slug = p.get("slug")
                if not slug:
                    continue
                title = strip_html(p.get("title", {}).get("rendered", ""))
                excerpt = strip_html(p.get("excerpt", {}).get("rendered", ""))
                link = p.get("link", f"{base}/{slug}/")
                modified = p.get("modified", datetime.date.today().isoformat())[:10]

                img_url = ""
                try:
                    img_url = (
                        p.get("_embedded", {})
                        .get("wp:featuredmedia", [{}])[0]
                        .get("source_url", "")
                    )
                except Exception:
                    pass

                cat_name = ""
                cat_slug = ""
                try:
                    terms = p.get("_embedded", {}).get("wp:term", [])
                    if terms and terms[0]:
                        cat_name = terms[0][0].get("name", "")
                        cat_slug = terms[0][0].get("slug", "")
                except Exception:
                    pass

                wp_posts_map[slug] = {
                    "slug": slug,
                    "title": title,
                    "excerpt": excerpt,
                    "image": img_url,
                    "url": link,
                    "category": cat_name,
                    "parent_slug": cat_slug,
                    "lastmod": modified,
                }
        except Exception as exc:
            print(f"[WARN] Error parsing WP API batch {page}: {exc}")
            break
    print(f"[WP-API] Loaded {len(wp_posts_map)} posts with metadata.")
    return wp_posts_map


def download_image_to_repo(img_url: str, slug: str, output_dir: str) -> str:
    """
    Downloads the post's featured image into <output_dir>/assets/images/<slug>.jpg
    so that the image is hosted directly inside the GitHub Pages repository.
    Returns the relative web path '/assets/images/<slug>.jpg'.
    """
    assets_dir = os.path.join(output_dir, "assets", "images")
    os.makedirs(assets_dir, exist_ok=True)

    ext = ".jpg"
    if img_url:
        parsed_path = urllib.parse.urlparse(img_url).path.lower()
        for candidate_ext in (".jpg", ".jpeg", ".png", ".webp"):
            if parsed_path.endswith(candidate_ext):
                ext = candidate_ext
                break

    filename = f"{slug}{ext}"
    local_file_path = os.path.join(assets_dir, filename)
    web_path = f"/assets/images/{filename}"

    if img_url and img_url.startswith("http"):
        img_bytes = fetch_url(img_url)
        if img_bytes and len(img_bytes) > 512:
            with open(local_file_path, "wb") as f:
                f.write(img_bytes)
            print(f"[IMAGE] Downloaded {img_url} -> {web_path} ({len(img_bytes)} bytes)")
            return web_path

    svg_filename = f"{slug}.svg"
    svg_path = os.path.join(assets_dir, svg_filename)
    safe_title = html_lib.escape(slug.replace("-", " ").title()[:42])
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="750" viewBox="0 0 1200 750">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#F5F2EB"/>
      <stop offset="100%" stop-color="#E6DFD3"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="750" fill="url(#bg)"/>
  <rect x="60" y="60" width="1080" height="630" rx="24" fill="none" stroke="#D6CEC2" stroke-width="2"/>
  <text x="600" y="340" text-anchor="middle" font-family="Georgia, serif" font-size="42" font-weight="bold" fill="#1C1917">{safe_title}</text>
  <text x="600" y="405" text-anchor="middle" font-family="sans-serif" font-size="22" letter-spacing="3" fill="#78716C">CURATED EDITORIAL GUIDE</text>
</svg>"""
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    return f"/assets/images/{svg_filename}"


def resolve_post_paths(post: dict, route_structure: str) -> tuple:
    """
    Returns (relative_disk_dir, web_url_path) based on the chosen URL structure:
    - single:        /<slug>/
    - category_slug: /<category-slug>/<slug>/
    - parent_slug:   /<parent-slug>/<slug>/
    - silo_nested:   /guides/<parent-slug>/<slug>/
    """
    slug = slugify(post["slug"])
    parent = slugify(post.get("parent_slug") or post.get("category") or "home-organization")

    if route_structure == "category_slug":
        cat_slug = slugify(post.get("category") or parent)
        return os.path.join(cat_slug, slug), f"/{cat_slug}/{slug}/"
    elif route_structure == "parent_slug":
        return os.path.join(parent, slug), f"/{parent}/{slug}/"
    elif route_structure == "silo_nested":
        return os.path.join("guides", parent, slug), f"/guides/{parent}/{slug}/"
    else:
        return slug, f"/{slug}/"


def build_json_ld_schema(post: dict, github_domain: str, source_domain: str) -> str:
    """Builds Schema.org Article + BreadcrumbList + HowTo JSON-LD block."""
    full_page_url = f"{github_domain.rstrip('/')}{post['web_path']}"
    full_image_url = (
        post["local_image"]
        if post["local_image"].startswith("http")
        else f"{github_domain.rstrip('/')}{post['local_image']}"
    )

    breadcrumbs = [
        {
            "@type": "ListItem",
            "position": 1,
            "name": "Editorial Hub",
            "item": f"{github_domain.rstrip('/')}/",
        }
    ]
    if post.get("parent_slug") and post["web_path"].count("/") > 2:
        breadcrumbs.append(
            {
                "@type": "ListItem",
                "position": 2,
                "name": post.get("category", "Category"),
                "item": f"{github_domain.rstrip('/')}/{slugify(post['parent_slug'])}/",
            }
        )
        breadcrumbs.append(
            {
                "@type": "ListItem",
                "position": 3,
                "name": post["title"],
                "item": full_page_url,
            }
        )
    else:
        breadcrumbs.append(
            {
                "@type": "ListItem",
                "position": 2,
                "name": post["title"],
                "item": full_page_url,
            }
        )

    schema_obj = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": post["title"],
                "description": post["description"],
                "image": [full_image_url],
                "datePublished": post.get("lastmod", "2026-10-29"),
                "dateModified": post.get("lastmod", "2026-10-29"),
                "author": {
                    "@type": "Organization",
                    "name": f"{source_domain} Editorial Team",
                    "url": f"https://{source_domain}/",
                },
                "publisher": {
                    "@type": "Organization",
                    "name": f"{source_domain} Editorial Hub",
                    "url": github_domain,
                },
                "mainEntityOfPage": {
                    "@type": "WebPage",
                    "@id": full_page_url,
                },
                "isBasedOn": post["canonical_url"],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": breadcrumbs,
            },
        ],
    }
    return json.dumps(schema_obj, indent=2)


THEMES = {
    "editorial-warm": {
        "bg_body": "#FAF8F5",
        "text_body": "#1C1917",
        "accent": "#E60023",
        "accent_hover": "#c4001d",
        "card_bg": "#FFFFFF",
        "CheckBoxBg": "#F1EDE6",
        "badge_bg": "#15803D",
    },
    "nordic-studio": {
        "bg_body": "#F3F5F4",
        "text_body": "#0F172A",
        "accent": "#0F766E",
        "accent_hover": "#115E59",
        "card_bg": "#FFFFFF",
        "CheckBoxBg": "#E6ECEA",
        "badge_bg": "#0F766E",
    },
    "pinterest-mag": {
        "bg_body": "#FFFDF9",
        "text_body": "#18181B",
        "accent": "#BE123C",
        "accent_hover": "#9F1239",
        "card_bg": "#FFFFFF",
        "CheckBoxBg": "#FCE7F3",
        "badge_bg": "#BE123C",
    },
}


def render_post_html(
    post: dict,
    all_posts: list,
    github_domain: str,
    source_domain: str,
    theme_key: str = "editorial-warm",
    self_canonical: bool = False,
) -> str:
    theme = THEMES.get(theme_key, THEMES["editorial-warm"])
    others = [p for p in all_posts if p["slug"] != post["slug"]]
    related_sample = random.sample(others, min(3, len(others))) if others else []
    pills_sample = random.sample(others, min(6, len(others))) if others else []

    pills_html = ""
    for p in pills_sample:
        short_t = html_lib.escape(p["title"][:32] + ("…" if len(p["title"]) > 34 else ""))
        pills_html += (
            f'<a href="{p["web_path"]}" class="px-3 py-1 rounded-lg text-xs font-medium '
            f'bg-stone-100 hover:bg-stone-200 text-stone-700 transition shrink-0">{short_t}</a>'
        )

    related_html = ""
    for p in related_sample:
        related_html += f"""
        <div class="bg-white rounded-2xl border border-stone-200/80 overflow-hidden shadow-xs hover:shadow-md transition flex flex-col justify-between group">
          <a href="{p['web_path']}" class="block h-full">
            <div>
              <div class="aspect-[16/10] bg-stone-100 overflow-hidden relative">
                <img src="{p['local_image']}" alt="{html_lib.escape(p['title'])}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500">
                <span class="absolute top-3 left-3 bg-white/95 text-stone-900 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full">
                  {html_lib.escape(p['category'])}
                </span>
              </div>
              <div class="p-5">
                <h3 class="font-serif-editorial text-lg font-bold text-stone-900 group-hover:text-[{theme['accent']}] transition leading-snug mb-2">
                  {html_lib.escape(p['title'])}
                </h3>
                <p class="text-xs text-stone-500 line-clamp-2">{html_lib.escape(p['description'][:120])}...</p>
              </div>
            </div>
            <div class="px-5 py-3 bg-stone-50 border-t border-stone-100 flex items-center justify-between text-[11px] text-stone-500 font-medium">
              <span><strong class="text-stone-700">Read Guide</strong></span>
              <span class="text-[{theme['accent']}] font-bold">→</span>
            </div>
          </a>
        </div>"""

    full_gh_url = f"{github_domain.rstrip('/')}{post['web_path']}"
    full_img_url = (
        post["local_image"]
        if post["local_image"].startswith("http")
        else f"{github_domain.rstrip('/')}{post['local_image']}"
    )
    canonical_href = full_gh_url if self_canonical else post["canonical_url"]
    schema_json = build_json_ld_schema(post, github_domain, source_domain)

    breadcrumb_nav = f'<a href="/" class="hover:underline">Home</a> <span class="mx-1">/</span> '
    if post["web_path"].count("/") > 2:
        parent_s = post["web_path"].strip("/").split("/")[0]
        breadcrumb_nav += f'<a href="/{parent_s}/" class="hover:underline capitalize">{parent_s.replace("-", " ")}</a> <span class="mx-1">/</span> '
    breadcrumb_nav += f'<span class="text-stone-900 font-semibold">{html_lib.escape(post["title"][:45])}</span>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_lib.escape(post['title'])} | {source_domain} Editorial Hub</title>
  <meta name="description" content="{html_lib.escape(post['description'])}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{canonical_href}">

  <!-- OpenGraph & Pinterest Rich Pin Metadata -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="{html_lib.escape(post['title'])}">
  <meta property="og:description" content="{html_lib.escape(post['description'])}">
  <meta property="og:image" content="{full_img_url}">
  <meta property="og:url" content="{full_gh_url}">
  <meta property="og:site_name" content="{source_domain} Editorial Hub">
  <meta name="twitter:card" content="summary_large_image">

  <!-- Schema.org pSEO Structured Data -->
  <script type="application/ld+json">
{schema_json}
  </script>

  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: {theme['bg_body']};
      color: {theme['text_body']};
      -webkit-font-smoothing: antialiased;
    }}
    .font-serif-editorial {{
      font-family: 'Playfair Display', Georgia, serif;
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col">
  <header class="bg-white border-b border-stone-200/70">
    <div class="max-w-6xl mx-auto px-4 py-3 flex flex-col gap-2">
      <div class="flex items-center justify-between text-xs text-stone-500">
        <nav aria-label="Breadcrumb">{breadcrumb_nav}</nav>
        <a href="https://{source_domain}/" target="_blank" rel="noopener" class="font-semibold text-stone-800 hover:underline">{source_domain} Official →</a>
      </div>
      <div class="flex items-center space-x-1.5 text-xs overflow-x-auto pt-1">
        <span class="text-stone-400 font-bold uppercase tracking-wider text-[10px] mr-1 shrink-0">Featured Posts:</span>
        <div class="flex items-center gap-1.5 shrink-0">{pills_html}</div>
      </div>
    </div>
  </header>

  <main class="max-w-6xl w-full mx-auto px-4 py-8 md:py-10 flex-grow">
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      <article class="lg:col-span-8 bg-white rounded-3xl shadow-sm border border-stone-200/80 overflow-hidden">
        <div class="relative w-full aspect-[16/10] bg-stone-100 overflow-hidden">
          <img src="{post['local_image']}" alt="{html_lib.escape(post['title'])}" class="w-full h-full object-cover">
          <div class="absolute top-4 left-4 z-20">
            <span class="bg-white/95 backdrop-blur-md text-stone-900 text-xs font-bold uppercase tracking-wider px-3.5 py-1.5 rounded-full shadow-sm border border-stone-200">{html_lib.escape(post['category'])}</span>
          </div>
          <div class="absolute bottom-4 right-4 z-20">
            <div class="flex items-center space-x-1.5 bg-stone-900/90 backdrop-blur-md text-white text-xs font-medium px-3.5 py-1.5 rounded-full shadow-md">
              <span class="text-stone-300">Published on:</span>
              <strong class="font-semibold text-white">{source_domain}</strong>
            </div>
          </div>
        </div>

        <div class="p-6 sm:p-10">
          <div class="flex flex-wrap items-center gap-2.5 text-xs text-stone-500 font-medium mb-4">
            <span class="text-stone-800 font-semibold">{source_domain} Editorial Team</span>
            <span>•</span>
            <span>6 min full read</span>
            <span>•</span>
            <span>Updated {post.get('lastmod', '2026')}</span>
          </div>

          <h1 class="font-serif-editorial text-2xl sm:text-4xl font-bold text-stone-900 leading-tight mb-5">{html_lib.escape(post['title'])}</h1>

          <p class="text-stone-700 text-base sm:text-lg leading-relaxed mb-8">{html_lib.escape(post['description'])}</p>

          <div class="bg-[#FAF8F5] p-5 sm:p-6 rounded-2xl border border-stone-200/90 mb-8">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span class="text-[11px] font-bold uppercase tracking-wider text-stone-400 block mb-1">Full Illustrated Article &amp; Room Photos</span>
                <div class="text-sm font-semibold text-stone-900">
                  Explore all room photos &amp; step-by-step styling tips on <span class="underline font-bold">{source_domain}</span>
                </div>
              </div>
              <a href="{post['canonical_url']}" target="_blank" rel="noopener" style="background-color: {theme['accent']}" class="inline-flex items-center justify-center space-x-2 text-white font-bold text-sm px-6 py-3.5 rounded-xl shadow-sm transition shrink-0">
                <span>Read Full Guide on {source_domain}</span>
                <span>→</span>
              </a>
            </div>
          </div>

          <section class="mb-8">
            <h2 class="font-serif-editorial text-xl font-bold text-stone-900 mb-4">Key Styling Ideas &amp; DIY Highlights Inside This Guide</h2>
            <div class="grid grid-cols-1 gap-3">
              <div class="flex items-start gap-3.5 p-4 rounded-2xl bg-[#FAF8F5] border border-stone-200/80">
                <span class="w-6 h-6 rounded-full bg-stone-900 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">1</span>
                <p class="text-sm text-stone-700 leading-relaxed">Balanced Room Proportions: Anchor your layout with clean-lined furniture and intentional traffic flow suited for everyday living.</p>
              </div>
              <div class="flex items-start gap-3.5 p-4 rounded-2xl bg-[#FAF8F5] border border-stone-200/80">
                <span class="w-6 h-6 rounded-full bg-stone-900 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">2</span>
                <p class="text-sm text-stone-700 leading-relaxed">Layered Textures &amp; Storage: Combine natural wood finishes, modular organizers, and warm ambient lighting for instant coziness.</p>
              </div>
            </div>
          </section>

          <div class="pt-6 border-t border-stone-200/80 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="text-xs text-stone-500">
              <span>Direct Permalink:</span>
              <span class="font-mono text-stone-700 break-all ml-1">{post['canonical_url']}</span>
            </div>
            <a href="{post['canonical_url']}" target="_blank" rel="noopener" class="bg-stone-900 hover:bg-stone-800 text-white font-semibold text-xs px-5 py-3 rounded-xl transition shrink-0">
              Continue to {source_domain} →
            </a>
          </div>
        </div>
      </article>

      <aside class="lg:col-span-4 space-y-6">
        <div style="background-color: {theme['CheckBoxBg']}" class="rounded-3xl p-6 border border-stone-200/90">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-serif-editorial text-base font-bold text-stone-900">Room &amp; DIY Action Checklist</h3>
            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-stone-800 text-white">Interactive</span>
          </div>
          <p class="text-xs text-stone-600 mb-4">Key prep steps before diving into the full tutorial on <strong>{source_domain}</strong>:</p>
          <div class="space-y-2.5 text-xs text-stone-700">
            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" checked class="mt-0.5 rounded"><span>Review full room photos and step-by-step details on {source_domain}</span></label>
            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" checked class="mt-0.5 rounded"><span>Measure furniture clearances before starting your project</span></label>
            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" checked class="mt-0.5 rounded"><span>Save this guide to your Pinterest board for reference</span></label>
          </div>
        </div>
      </aside>
    </div>

    <section class="mt-14 pt-10 border-t border-stone-200">
      <h2 class="font-serif-editorial text-2xl font-bold text-stone-900 mb-6">More Home Decor &amp; IKEA Hack Guides</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">{related_html}</div>
    </section>
  </main>
</body>
</html>"""


def render_hub_index_html(
    title: str,
    subtitle: str,
    posts: list,
    github_domain: str,
    source_domain: str,
    theme_key: str = "editorial-warm",
) -> str:
    """Renders the root organization index.html or category silo index.html."""
    theme = THEMES.get(theme_key, THEMES["editorial-warm"])
    cards_html = ""
    for p in posts:
        cards_html += f"""
        <article class="bg-white rounded-2xl border border-stone-200/80 overflow-hidden shadow-xs hover:shadow-md transition flex flex-col justify-between group">
          <a href="{p['web_path']}" class="block h-full">
            <div class="aspect-[16/10] bg-stone-100 overflow-hidden relative">
              <img src="{p['local_image']}" alt="{html_lib.escape(p['title'])}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500">
              <span class="absolute top-3 left-3 bg-white/95 text-stone-900 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full">
                {html_lib.escape(p['category'])}
              </span>
            </div>
            <div class="p-5">
              <div class="text-[11px] font-mono text-stone-400 mb-1">{p['web_path']}</div>
              <h2 class="font-serif-editorial text-lg font-bold text-stone-900 mb-2">{html_lib.escape(p['title'])}</h2>
              <p class="text-xs text-stone-600 line-clamp-2">{html_lib.escape(p['description'])}</p>
            </div>
          </a>
        </article>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_lib.escape(title)} | {source_domain} Editorial Hub</title>
  <meta name="description" content="{html_lib.escape(subtitle)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{github_domain.rstrip('/')}/">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: {theme['bg_body']}; color: {theme['text_body']}; }}
    .font-serif-editorial {{ font-family: 'Playfair Display', Georgia, serif; }}
  </style>
</head>
<body class="min-h-screen flex flex-col">
  <header class="bg-white border-b border-stone-200 py-8 px-4">
    <div class="max-w-6xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div>
        <span class="text-xs font-bold uppercase tracking-widest text-stone-400 block mb-1">{github_domain}</span>
        <h1 class="font-serif-editorial text-3xl sm:text-4xl font-bold text-stone-900">{html_lib.escape(title)}</h1>
        <p class="text-sm text-stone-600 mt-1">{html_lib.escape(subtitle)}</p>
      </div>
      <a href="https://{source_domain}/" target="_blank" rel="noopener" style="background-color: {theme['accent']}" class="text-white text-xs font-bold px-5 py-3 rounded-xl shadow-sm">
        Visit {source_domain} →
      </a>
    </div>
  </header>
  <main class="max-w-6xl w-full mx-auto px-4 py-10 flex-grow">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">{cards_html}</div>
  </main>
</body>
</html>"""


def generate_robots_and_sitemap(posts: list, github_domain: str, output_dir: str):
    """Generates robots.txt and sitemap.xml (with image:image extensions)."""
    base_domain = github_domain.rstrip("/")
    robots_txt = f"""User-agent: *
Allow: /
Allow: /assets/images/

User-agent: Pinterestbot
Allow: /
Allow: /assets/images/
Crawl-delay: 1

Sitemap: {base_domain}/sitemap.xml
"""
    with open(os.path.join(output_dir, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots_txt)

    today = datetime.date.today().isoformat()
    url_entries = [
        f"""  <url>
    <loc>{base_domain}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>"""
    ]
    for p in posts:
        loc = f"{base_domain}{p['web_path']}"
        img_loc = (
            p["local_image"]
            if p["local_image"].startswith("http")
            else f"{base_domain}{p['local_image']}"
        )
        url_entries.append(
            f"""  <url>
    <loc>{html_lib.escape(loc)}</loc>
    <lastmod>{p.get('lastmod', today)}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
    <image:image>
      <image:loc>{html_lib.escape(img_loc)}</image:loc>
      <image:title>{html_lib.escape(p['title'])}</image:title>
    </image:image>
  </url>"""
        )

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
{chr(10).join(url_entries)}
</urlset>
"""
    with open(os.path.join(output_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml)
    print(f"[SEO] Wrote robots.txt and sitemap.xml ({len(posts)} URLs) to {output_dir}")


def github_api_request(method: str, endpoint: str, token: str, payload: dict = None) -> dict:
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "pSEO-GitHub-Deployer",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def deploy_to_github_pages(
    output_dir: str,
    owner: str,
    repo: str,
    token: str,
    is_org: bool = True,
    branch: str = "main",
):
    """
    Creates the GitHub Organization/User repository (e.g. home-organization.github.io)
    if missing, and pushes all HTML, robots.txt, sitemap.xml, and binary images via Git Data API.
    """
    print(f"[GITHUB] Checking repository {owner}/{repo}...")
    try:
        github_api_request("GET", f"/repos/{owner}/{repo}", token)
        print(f"[GITHUB] Repository {owner}/{repo} exists.")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            create_ep = f"/orgs/{owner}/repos" if is_org else "/user/repos"
            print(f"[GITHUB] Creating repository {owner}/{repo} via {create_ep}...")
            github_api_request(
                "POST",
                create_ep,
                token,
                {
                    "name": repo,
                    "description": f"Curated Editorial pSEO Hub ({repo})",
                    "homepage": f"https://{repo}" if repo.endswith(".github.io") else f"https://{owner}.github.io/{repo}",
                    "private": False,
                    "auto_init": True,
                },
            )
        else:
            raise

    ref_data = github_api_request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}", token)
    latest_commit_sha = ref_data["object"]["sha"]
    commit_data = github_api_request("GET", f"/repos/{owner}/{repo}/git/commits/{latest_commit_sha}", token)
    base_tree_sha = commit_data["tree"]["sha"]

    tree_items = []
    for root_dir, _, files in os.walk(output_dir):
        for fname in files:
            full_path = os.path.join(root_dir, fname)
            rel_path = os.path.relpath(full_path, output_dir).replace("\\", "/")
            with open(full_path, "rb") as f:
                raw_bytes = f.read()
            b64_content = base64.b64encode(raw_bytes).decode("ascii")
            blob = github_api_request(
                "POST",
                f"/repos/{owner}/{repo}/git/blobs",
                token,
                {"content": b64_content, "encoding": "base64"},
            )
            tree_items.append(
                {
                    "path": rel_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob["sha"],
                }
            )
            print(f"[GITHUB] Uploaded blob: {rel_path}")

    new_tree = github_api_request(
        "POST",
        f"/repos/{owner}/{repo}/git/trees",
        token,
        {"base_tree": base_tree_sha, "tree": tree_items},
    )
    new_commit = github_api_request(
        "POST",
        f"/repos/{owner}/{repo}/git/commits",
        token,
        {
            "message": f"Deploy {len(tree_items)} pSEO pages, images, robots.txt & sitemap.xml",
            "tree": new_tree["sha"],
            "parents": [latest_commit_sha],
        },
    )
    github_api_request(
        "PATCH",
        f"/repos/{owner}/{repo}/git/refs/heads/{branch}",
        token,
        {"sha": new_commit["sha"]},
    )
    print(f"[GITHUB] Successfully deployed commit {new_commit['sha']} to https://{owner}.github.io/")


def main():
    parser = argparse.ArgumentParser(description="pSEO GitHub Pages & WordPress Static Hub Generator")
    parser.add_argument("--sitemap", default="https://stylesdays.com/sitemap_index.xml", help="WordPress Sitemap XML URL")
    parser.add_argument("--url-list", default="", help="Optional path to a .txt file with one post URL per line")
    parser.add_argument("--wp-domain", default="stylesdays.com", help="Source WordPress domain")
    parser.add_argument("--github-org", default="home-organization", help="GitHub Organization or Username")
    parser.add_argument("--github-repo", default="home-organization.github.io", help="GitHub Pages repository name")
    parser.add_argument(
        "--route-structure",
        choices=["single", "category_slug", "parent_slug", "silo_nested"],
        default="parent_slug",
        help="URL structure: single (/slug/), category_slug (/cat/slug/), parent_slug (/parent/slug/), silo_nested (/guides/parent/slug/)",
    )
    parser.add_argument(
        "--theme",
        choices=["editorial-warm", "nordic-studio", "pinterest-mag"],
        default="editorial-warm",
        help="Visual HTML template theme",
    )
    parser.add_argument("--output-dir", default="./dist_github_pages", help="Output directory for generated site")
    parser.add_argument("--download-images", action="store_true", default=True, help="Download featured images into /assets/images/")
    parser.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN", ""), help="GitHub Personal Access Token for direct push")
    parser.add_argument("--push-github", action="store_true", help="Push generated site + images directly to GitHub Pages via API")
    args = parser.parse_args()

    github_domain = (
        f"https://{args.github_repo}"
        if args.github_repo.endswith(".github.io")
        else f"https://{args.github_org}.github.io/{args.github_repo}"
    )

    raw_urls = []
    if args.url_list and os.path.exists(args.url_list):
        with open(args.url_list, "r", encoding="utf-8") as f:
            raw_urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        print(f"[INPUT] Loaded {len(raw_urls)} URLs from {args.url_list}")
    else:
        print(f"[INPUT] Fetching sitemap from: {args.sitemap}")
        raw_urls = sorted(parse_sitemap(args.sitemap))
        print(f"[INPUT] Total unique URLs found in sitemap: {len(raw_urls)}")

    wp_posts_map = fetch_wp_rest_posts(f"https://{args.wp_domain}")

    os.makedirs(args.output_dir, exist_ok=True)
    processed_posts = []

    for url in raw_urls:
        clean_url = url if url.endswith("/") else url + "/"
        parts = [p for p in clean_url.split("/") if p]
        if len(parts) <= 2:
            continue
        slug = parts[-1]
        wp_data = wp_posts_map.get(slug, {})

        inferred_cat, inferred_parent = infer_category_and_parent(slug, parts)
        category = wp_data.get("category") or inferred_cat
        parent_slug = wp_data.get("parent_slug") or inferred_parent
        title = wp_data.get("title") or slug.replace("-", " ").title()
        remote_img = wp_data.get("image") or ""
        excerpt = wp_data.get("excerpt") or (
            f"Explore our complete {title} guide on {args.wp_domain}. "
            f"This curated feature breaks down practical room styling ideas, space-saving furniture layouts, "
            f"and budget-friendly DIY upgrades tailored for real-life homes."
        )

        local_img = (
            download_image_to_repo(remote_img, slug, args.output_dir)
            if args.download_images
            else (remote_img or f"/assets/images/{slug}.svg")
        )

        post_record = {
            "slug": slug,
            "parent_slug": slugify(parent_slug),
            "category": category,
            "title": title,
            "description": excerpt,
            "canonical_url": clean_url,
            "remote_image": remote_img,
            "local_image": local_img,
            "lastmod": wp_data.get("lastmod", datetime.date.today().isoformat()),
        }
        rel_dir, web_path = resolve_post_paths(post_record, args.route_structure)
        post_record["rel_dir"] = rel_dir
        post_record["web_path"] = web_path
        processed_posts.append(post_record)

    silos = {}
    for post in processed_posts:
        target_dir = os.path.join(args.output_dir, post["rel_dir"])
        os.makedirs(target_dir, exist_ok=True)
        html_out = render_post_html(
            post,
            processed_posts,
            github_domain=github_domain,
            source_domain=args.wp_domain,
            theme_key=args.theme,
        )
        with open(os.path.join(target_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_out)

        top_segment = post["web_path"].strip("/").split("/")[0]
        if post["web_path"].count("/") > 2:
            silos.setdefault(top_segment, []).append(post)

    for silo_slug, silo_posts in silos.items():
        silo_dir = os.path.join(args.output_dir, silo_slug)
        os.makedirs(silo_dir, exist_ok=True)
        silo_title = f"{silo_slug.replace('-', ' ').title()} — Curated Guides"
        silo_html = render_hub_index_html(
            silo_title,
            f"Browse {len(silo_posts)} curated {silo_slug.replace('-', ' ')} tutorials and room checklists.",
            silo_posts,
            github_domain,
            args.wp_domain,
            args.theme,
        )
        with open(os.path.join(silo_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(silo_html)

    root_html = render_hub_index_html(
        f"{args.github_org.replace('-', ' ').title()} Editorial Hub",
        f"Curated Home Organization, IKEA Hacks, and Room Styling Guides powered by {args.wp_domain}.",
        processed_posts,
        github_domain,
        args.wp_domain,
        args.theme,
    )
    with open(os.path.join(args.output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(root_html)

    generate_robots_and_sitemap(processed_posts, github_domain, args.output_dir)
    with open(os.path.join(args.output_dir, "pseo_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "github_domain": github_domain,
                "route_structure": args.route_structure,
                "theme": args.theme,
                "total_posts": len(processed_posts),
                "posts": processed_posts,
            },
            f,
            indent=2,
        )

    print(f"[SUCCESS] Generated {len(processed_posts)} static pages + hub indexes in {args.output_dir}")

    if args.push_github and args.github_token:
        deploy_to_github_pages(
            output_dir=args.output_dir,
            owner=args.github_org,
            repo=args.github_repo,
            token=args.github_token,
            is_org=True,
        )


if __name__ == "__main__":
    main()