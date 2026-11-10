"""Static Site Builder for pSEO Static Site Generator.

Orchestrates multi-slug route resolution, Theme Engine post rendering,
recursive Category/Silo Index page generation (to eliminate 404s),
Root Organization Hub compilation, image asset synchronization,
and technical SEO generation (robots.txt & sitemap.xml with Google image extensions).
"""

from __future__ import annotations

import html as html_lib
import inspect
import json
import os
import re
import shutil
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Optional, Union

from app.config import AppConfig
from app.models import Manifest, PostItem
from app.routing.resolver import (
    IntermediateRoute,
    RouteResolver,
    RouteResult,
    get_intermediate_routes,
    normalize_base_path,
    normalize_routing_mode,
    resolve_all_routes,
    resolve_post_route,
    slugify,
)

# Dynamic theme integration with graceful fallback
try:
    from app.themes.engine import render_post as theme_render_post
except Exception:
    theme_render_post = None

try:
    from app.themes.templates import (
        render_category_index as template_render_category_index,
        render_hub as template_render_hub,
        render_post as template_render_post,
    )
except Exception:
    template_render_category_index = None
    template_render_hub = None
    template_render_post = None

# Dynamic SEO integration with graceful fallback
try:
    from app.seo.schema import generate_seo_head
except Exception:
    generate_seo_head = None

try:
    from app.seo.robots import generate_robots_txt
except Exception:
    generate_robots_txt = None

try:
    from app.seo.sitemap import generate_sitemap_xml, join_base_and_path
except Exception:
    generate_sitemap_xml = None
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


def _extract_path_prefix(base_url: str) -> str:
    """Extracts URL subpath prefix (e.g. '/repo' from 'https://org.github.io/repo').
    Returns '' for root domains (e.g. 'https://example.com' or 'https://org.github.io')."""
    if not base_url:
        return ""
    if "://" in base_url:
        parsed = urllib.parse.urlparse(base_url)
        path = parsed.path.rstrip("/")
        return path if path else ""
    path = str(base_url).strip().rstrip("/")
    return path if path.startswith("/") else ""


def _clean_source_domain(domain: str) -> str:
    """Strips protocol and trailing slashes so domain string never forms 'https://https://...'."""
    if not domain:
        return "stylesdays.com"
    clean = str(domain).strip()
    if clean.startswith("https://"):
        clean = clean[8:]
    elif clean.startswith("http://"):
        clean = clean[7:]
    return clean.rstrip("/")


def derive_brand_from_domain(domain: str, worker_name: str = "") -> str:
    """Intelligently derives a clean, human-readable Brand Name from a custom domain.
    Never returns worker names, infrastructure tokens, or raw URLs.
    """
    clean = re.sub(r"^https?://", "", str(domain or ""), flags=re.IGNORECASE).strip("/ ")
    if not clean or any(w in clean.lower() for w in ("workers.dev", "pages.dev", "github.io", "localhost", "127.0.0.1")):
        return "Styleire"
    host = clean.split("/")[0].split(":")[0]
    parts = host.split(".")
    if len(parts) >= 3 and parts[0].lower() in ("www", "decor", "blog", "shop", "store", "news", "hub", "mag", "magazine", "studio", "app", "web", "cdn"):
        main_token = parts[1]
    elif len(parts) >= 2:
        main_token = parts[0]
    else:
        main_token = host

    if worker_name and main_token.strip().lower() == worker_name.strip().lower():
        return "Styleire"
    if main_token.lower() in ("test", "demo"):
        return "Styleire"
    brand = main_token.replace("-", " ").replace("_", " ").strip().title()
    return brand or "Styleire"



THEME_PALETTES = {
    "editorial-warm": {
        "bg_body": "#FAF8F5",
        "text_body": "#1C1917",
        "accent": "#E60023",
        "header_bg": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "border": "#E7E5E4",
        "font_family": "'Plus Jakarta Sans', sans-serif",
        "font_heading": "'Playfair Display', Georgia, serif",
    },
    "nordic-studio": {
        "bg_body": "#F3F5F4",
        "text_body": "#0F172A",
        "accent": "#0F766E",
        "header_bg": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "border": "#E2E8F0",
        "font_family": "'Plus Jakarta Sans', sans-serif",
        "font_heading": "'Plus Jakarta Sans', sans-serif",
    },
    "pinterest-mag": {
        "bg_body": "#FFFFFF",
        "text_body": "#09090B",
        "accent": "#09090B",
        "header_bg": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "border": "#E4E4E7",
        "font_family": "'Plus Jakarta Sans', sans-serif",
        "font_heading": "'Playfair Display', Georgia, serif",
    },
    "styleire": {
        "bg_body": "#FFFFFF",
        "text_body": "#09090B",
        "accent": "#09090B",
        "header_bg": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "border": "#E4E4E7",
        "font_family": "'Plus Jakarta Sans', sans-serif",
        "font_heading": "'Playfair Display', Georgia, serif",
    },
}


@dataclass
class BuildSummary:
    """Detailed summary of the static site build execution."""

    status: str = "success"
    output_dir: str = ""
    theme: str = "editorial-warm"
    routing_mode: str = "single"
    total_posts: int = 0
    post_pages_generated: int = 0
    intermediate_pages_generated: int = 0
    total_pages_generated: int = 0
    images_copied: int = 0
    robots_generated: bool = False
    sitemap_generated: bool = False
    duration_seconds: float = 0.0
    files_created: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "output_dir": self.output_dir,
            "theme": self.theme,
            "routing_mode": self.routing_mode,
            "total_posts": self.total_posts,
            "post_pages_generated": self.post_pages_generated,
            "intermediate_pages_generated": self.intermediate_pages_generated,
            "total_pages_generated": self.total_pages_generated,
            "images_copied": self.images_copied,
            "robots_generated": self.robots_generated,
            "sitemap_generated": self.sitemap_generated,
            "duration_seconds": self.duration_seconds,
            "files_count": len(self.files_created),
            "errors": [str(e) for e in self.errors],
        }

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


def _generate_svg_fallback(title: str, category: str, theme_accent: str = "#E60023") -> str:
    """Generates an embedded SVG placeholder for posts missing local featured images."""
    safe_title = html_lib.escape(title[:45] + ("..." if len(title) > 45 else ""))
    safe_cat = html_lib.escape(category or "Home Organization")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" width="100%" height="100%">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1C1917" />
      <stop offset="100%" stop-color="#292524" />
    </linearGradient>
  </defs>
  <rect width="1200" height="675" fill="url(#bg)" />
  <rect x="60" y="60" width="1080" height="555" rx="16" fill="none" stroke="#44403C" stroke-width="2" />
  <rect x="100" y="100" width="160" height="36" rx="18" fill="{theme_accent}" />
  <text x="180" y="123" fill="#FFFFFF" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle">{safe_cat}</text>
  <text x="100" y="320" fill="#FFFFFF" font-family="serif" font-size="44" font-weight="bold">{safe_title}</text>
  <text x="100" y="380" fill="#A8A29E" font-family="sans-serif" font-size="20">StylesDays Editorial Architecture</text>
</svg>"""


def _build_standalone_seo_head(post: PostItem, route: RouteResult, base_url: str) -> str:
    """Generates comprehensive SEO head tags, OpenGraph, Pinterest, and JSON-LD schema."""
    clean_base = base_url.rstrip("/") if base_url else "https://home-organization.github.io"
    page_url = join_base_and_path(clean_base, route.web_path)

    image_rel = post.local_image_path or f"/assets/images/{post.slug}.jpg"
    image_rel_clean = "/" + image_rel.lstrip("/")
    image_url = join_base_and_path(clean_base, image_rel_clean)

    title_escaped = html_lib.escape(post.title or "Editorial Guide")
    clean_excerpt = (post.excerpt or "").strip()
    if not clean_excerpt or clean_excerpt.lower() in ("asqstyle", "asqstyle.com", "stylesdays", "stylesdays.com") or len(clean_excerpt) < 15:
        clean_excerpt = f"Discover inspiring {(post.title or 'home styling').lower()} with practical styling tips, curated palettes, and modern decor ideas."
    excerpt_escaped = html_lib.escape(clean_excerpt)

    # Breadcrumb list schema
    bc_items = []
    for idx, crumb in enumerate(route.breadcrumbs, start=1):
        crumb_url = crumb.get("url") or "/"
        full_crumb_url = crumb_url if crumb_url.startswith("http") else join_base_and_path(clean_base, crumb_url)
        bc_items.append({
            "@type": "ListItem",
            "position": idx,
            "name": crumb.get("name") or "Page",
            "item": full_crumb_url,
        })

    article_schema = {
        "@type": "Article",
        "headline": post.title or "Editorial Guide",
        "description": clean_excerpt,
        "image": image_url,
        "datePublished": post.date or "2026-01-01",
        "dateModified": post.modified or post.date or "2026-01-01",
        "author": {
            "@type": "Person",
            "name": "Sophia Bennett",
            "url": f"{clean_base}/author/sophia-bennett/",
        },
        "publisher": {
            "@type": "Organization",
            "name": "Styleire",
            "logo": {
                "@type": "ImageObject",
                "url": f"{clean_base}/assets/images/logo.png",
            },
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": page_url,
        },
    }

    breadcrumb_schema = {
        "@type": "BreadcrumbList",
        "itemListElement": bc_items,
    }

    # Extract FAQs if present in raw_meta or fallback
    raw_faqs = (post.raw_meta or {}).get("faq") if hasattr(post, "raw_meta") else None
    if not raw_faqs:
        raw_faqs = [
            {"q": f"What is the best way to get started with {post.title}?", "a": f"Begin with the core principles detailed in this guide: assess room dimensions, choose a cohesive palette, and prioritize functional layout."},
            {"q": "How long does a home styling project typically take?", "a": "Most focused room styling projects can be completed over a single weekend with proper planning and sourcing."}
        ]

    faq_schema = {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f.get("q", ""),
                "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}
            }
            for f in raw_faqs if f.get("q") and f.get("a")
        ]
    }

    graph_items = [article_schema, breadcrumb_schema]
    if faq_schema["mainEntity"]:
        graph_items.append(faq_schema)

    json_ld_graph = {
        "@context": "https://schema.org",
        "@graph": graph_items,
    }
    json_ld_str = json.dumps(json_ld_graph, indent=2)

    return f"""  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_escaped} | Styleire</title>
  <meta name="description" content="{excerpt_escaped}">
  <link rel="canonical" href="{page_url}">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">
  
  <!-- OpenGraph Metadata -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title_escaped}">
  <meta property="og:description" content="{excerpt_escaped}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:image" content="{image_url}">
  <meta property="og:site_name" content="Styleire">
  <meta name="twitter:site" content="@styleire">
  
  <!-- Pinterest Rich Pin Metadata -->
  <meta name="pinterest-rich-pin" content="true">
  <meta property="article:published_time" content="{post.date}">
  <meta property="article:modified_time" content="{post.modified or post.date}">
  <meta property="article:section" content="{html_lib.escape(post.category or 'Organization')}">
  
  <!-- JSON-LD Structured Data (@graph) -->
  <script type="application/ld+json">
{json_ld_str}
  </script>"""


def _build_standalone_post_html(
    post: PostItem,
    all_posts: list[PostItem],
    route: RouteResult,
    theme_key: str,
    base_url: str,
    seo_head: str,
    source_domain: str = "stylesdays.com",
    branding: Optional[Any] = None,
    categories: Optional[list[Any]] = None,
    routing_mode: str = "single",
) -> str:
    """Builds a complete post page containing all R4 interactive components and typography."""
    palette = THEME_PALETTES.get(theme_key, THEME_PALETTES["editorial-warm"])
    clean_base = base_url.rstrip("/") if base_url else ""
    path_prefix = _extract_path_prefix(base_url)
    clean_domain = _clean_source_domain(source_domain)
    brand_name = getattr(branding, "brand_name", "") or (branding.get("brand_name") if isinstance(branding, dict) else "") or (clean_domain.split(".")[0].title() if clean_domain else "StylesDays")
    logo_path = getattr(branding, "logo_path", "") or (branding.get("logo_path") if isinstance(branding, dict) else "") or ""
    home_link = f"{path_prefix}/" if path_prefix else "/"

    if logo_path:
        clean_logo = logo_path.lstrip("/")
        logo_url = f"{path_prefix}/{clean_logo}" if path_prefix else f"/{clean_logo}"
        brand_html = f'<a href="{home_link}" class="inline-block hover:opacity-90 transition"><img src="{logo_url}" alt="{html_lib.escape(brand_name)}" class="h-8 max-w-[180px] object-contain pseo-custom-logo"></a>'
    else:
        brand_html = f'<a href="{home_link}" class="flex items-center gap-2"><span class="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm" style="background-color: {palette["accent"]}">{brand_name[:1].upper()}</span><span class="font-serif-editorial text-xl font-bold tracking-tight text-stone-900">{html_lib.escape(brand_name)}</span></a>'

    nav_links_html = ""
    if categories:
        for c in categories[:6]:
            c_name = c.get("name") if isinstance(c, dict) else (getattr(c, "name", "") or str(c))
            c_slug = c.get("slug") if isinstance(c, dict) else (getattr(c, "slug", "") or slugify(c_name))
            if c_slug:
                c_url = f"{path_prefix}/{c_slug}/" if path_prefix else f"/{c_slug}/"
                nav_links_html += f'<a href="{c_url}" class="text-xs font-semibold text-stone-600 hover:text-stone-900 px-2 py-1 rounded transition">{html_lib.escape(c_name)}</a>'

    # Breadcrumb HTML
    crumbs_html = []
    for idx, c in enumerate(route.breadcrumbs):
        is_last = (idx == len(route.breadcrumbs) - 1)
        name = html_lib.escape(c.get("name") or "")
        url = c.get("url") or "/"
        if is_last:
            crumbs_html.append(f'<span class="text-stone-900 font-semibold truncate max-w-xs">{name}</span>')
        else:
            crumbs_html.append(f'<a href="{url}" class="hover:underline text-stone-500">{name}</a>')
            crumbs_html.append('<span class="text-stone-300 mx-1.5">/</span>')
    breadcrumbs_nav = "".join(crumbs_html)

    # Checklist HTML with localStorage persistence
    checklist_items_html = ""
    slug_safe = re.sub(r"[^a-zA-Z0-9_-]", "", post.slug)
    checklist = post.checklist or [
        {"id": "step-1", "text": "Measure target room and closet dimensions precisely."},
        {"id": "step-2", "text": "Gather modular storage bins, dividers, and mounting brackets."},
        {"id": "step-3", "text": "Label all containers and review spatial accessibility."},
    ]
    for item in checklist:
        item_id = item.get("id") or f"chk-{abs(hash(item.get('text', '')))}"
        item_text = html_lib.escape(item.get("text") or "")
        checklist_items_html += f"""
        <label class="flex items-start gap-3 p-3 rounded-xl hover:bg-stone-50 border border-stone-100 transition cursor-pointer select-none">
          <input type="checkbox" id="{slug_safe}_{item_id}" data-slug="{slug_safe}" data-item="{item_id}" class="diy-checkbox mt-1 w-4 h-4 rounded text-rose-600 focus:ring-rose-500 border-stone-300">
          <span class="text-sm text-stone-700 leading-relaxed">{item_text}</span>
        </label>"""

    # Takeaways HTML
    takeaways = post.takeaways or [
        "Consistent vertical storage doubles practical shelf capacity.",
        "Neutral palette bins create an editorial Scandinavian look.",
        "Anchor high storage units securely to wall studs.",
    ]
    takeaways_html = "".join([f'<li class="flex items-start gap-2.5 text-sm text-stone-700"><span class="text-rose-600 font-bold">✓</span><span>{html_lib.escape(t)}</span></li>' for t in takeaways])

    # Related Posts (Cards)
    related_posts = [p for p in all_posts if p.slug != post.slug][:3]
    related_cards_html = ""
    for rp in related_posts:
        rp_route = resolve_post_route(rp, mode="single")
        raw_rp_img = rp.local_image_path or f"assets/images/{rp.slug}.jpg"
        if raw_rp_img.startswith("http://") or raw_rp_img.startswith("https://"):
            rp_img = raw_rp_img
        else:
            clean_img = raw_rp_img.lstrip("/")
            rp_img = f"{path_prefix}/{clean_img}" if path_prefix else f"/{clean_img}"
        rp_fallback_svg = f"{path_prefix}/assets/images/placeholder.svg" if path_prefix else "/assets/images/placeholder.svg"
        rp_title = html_lib.escape(rp.title or rp.slug)
        rp_cat = html_lib.escape(rp.category or "Articles")
        related_cards_html += f"""
        <article class="bg-white rounded-2xl border border-stone-200 overflow-hidden shadow-xs hover:shadow-md transition flex flex-col justify-between group">
          <a href="{rp_route.web_path}" class="block">
            <div class="aspect-[16/10] bg-stone-100 overflow-hidden">
              <img src="{rp_img}" alt="{rp_title}" width="600" height="375" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" onerror="this.onerror=null; this.src='{rp_fallback_svg}'">
            </div>
            <div class="p-4">
              <span class="text-[10px] font-bold uppercase tracking-wider text-stone-400">{rp_cat}</span>
              <h3 class="font-serif text-base font-bold text-stone-900 mt-1 line-clamp-2">{rp_title}</h3>
            </div>
          </a>
        </article>"""

    raw_feat = post.local_image_path or f"assets/images/{post.slug}.jpg"
    if raw_feat.startswith("http://") or raw_feat.startswith("https://"):
        featured_image_path = raw_feat
    else:
        clean_img = raw_feat.lstrip("/")
        featured_image_path = f"{path_prefix}/{clean_img}" if path_prefix else f"/{clean_img}"
    feat_fallback_svg = f"{path_prefix}/assets/images/placeholder.svg" if path_prefix else "/assets/images/placeholder.svg"

    home_link = f"{path_prefix}/" if path_prefix else "/"

    # Post Body HTML
    raw_body = post.content_html or ""
    if raw_body:
        from app.themes.templates import clean_and_wrap_article_images
        body_html_rendered = clean_and_wrap_article_images(
            raw_body,
            canonical_url=join_base_and_path(clean_base, route.web_path),
            canonical_base=clean_base,
            page_title=post.title or "",
            path_prefix=path_prefix,
        )
    else:
        body_html_rendered = f'<p>{html_lib.escape(post.excerpt)}</p><p>Explore comprehensive DIY storage systems, modular shelving options, and minimalist organization tips crafted to elevate everyday spaces.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{seo_head}
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: {palette['font_family']};
      background-color: {palette['bg_body']};
      color: {palette['text_body']};
    }}
    .font-serif-editorial {{
      font-family: {palette['font_heading']};
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col antialiased">
  <!-- Top Navigation Header -->
  <header class="bg-white border-b border-stone-200/80 sticky top-0 z-40 backdrop-blur-md bg-white/95">
    <div class="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
      {brand_html}
      <nav class="hidden sm:flex items-center gap-3">
        {nav_links_html}
      </nav>
      <div class="flex items-center gap-2">
        <a href="{home_link}" class="text-xs font-semibold text-stone-600 hover:text-stone-900 px-3 py-1.5 rounded-lg hover:bg-stone-100 transition">Hub</a>
      </div>
    </div>
  </header>

  <!-- Breadcrumbs Bar -->
  <nav class="bg-white/50 border-b border-stone-200/60 py-3 px-4 text-xs">
    <div class="max-w-4xl mx-auto flex items-center flex-wrap">
      {breadcrumbs_nav}
    </div>
  </nav>

  <!-- Main Article Content -->
  <main class="max-w-4xl w-full mx-auto px-4 py-10 flex-grow">
    <!-- Category Header -->
    <div class="flex items-center gap-3 mb-4">
      <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider text-white" style="background-color: {palette['accent']}">
        {html_lib.escape(post.category or 'Home Organization')}
      </span>
    </div>

    <!-- Article Headline -->
    <h1 class="font-serif-editorial text-3xl sm:text-5xl font-bold tracking-tight text-stone-900 leading-tight mb-6">
      {html_lib.escape(post.title)}
    </h1>

    <!-- Excerpt / Subheading -->
    {f'<p class="text-lg sm:text-xl text-stone-600 leading-relaxed mb-8 font-light italic">{html_lib.escape(post.excerpt)}</p>' if post.excerpt else ''}

    <!-- Hero Featured Image -->
    <div class="aspect-[16/10] bg-stone-100 rounded-3xl overflow-hidden shadow-sm border border-stone-200/70 mb-10">
      <img src="{featured_image_path}" alt="{html_lib.escape(post.title)}" width="1200" height="750" fetchpriority="high" decoding="async" class="w-full h-full object-cover" onerror="this.onerror=null; this.src='{feat_fallback_svg}'">
    </div>

    <!-- Key Styling Takeaways Card -->
    <section class="bg-white rounded-2xl border border-stone-200 p-6 mb-10 shadow-xs">
      <div class="flex items-center gap-3 mb-4">
        <span class="w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs font-bold" style="background-color: {palette['accent']}">★</span>
        <h2 class="font-serif-editorial text-xl font-bold text-stone-900">Key Styling Takeaways</h2>
      </div>
      <ul class="space-y-3">
        {takeaways_html}
      </ul>
    </section>

    <!-- Post Body HTML -->
    <article class="prose prose-stone max-w-none text-stone-700 leading-relaxed mb-12 space-y-4">
      {body_html_rendered}
    </article>

    <!-- Interactive Room & DIY Checklist Component -->
    <section class="bg-white rounded-3xl border border-stone-200 p-6 sm:p-8 mb-12 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <span class="text-[11px] font-bold uppercase tracking-wider text-stone-400">Interactive Tool</span>
          <h2 class="font-serif-editorial text-2xl font-bold text-stone-900">Room & DIY Action Checklist</h2>
        </div>
        <span id="checklist-progress" class="text-xs font-bold text-stone-500 bg-stone-100 px-3 py-1.5 rounded-full">0 Completed</span>
      </div>
      <div class="space-y-2 mb-4">
        {checklist_items_html}
      </div>
      <p class="text-xs text-stone-400">Progress is automatically saved to your browser local storage.</p>
    </section>

    <!-- Related Articles Cards Section -->
    <section class="border-t border-stone-200/80 pt-10">
      <h2 class="font-serif-editorial text-2xl font-bold text-stone-900 mb-6">Related Articles &amp; Styling Ideas</h2>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {related_cards_html}
      </div>
    </section>
  </main>

  <!-- Footer -->
  <footer class="bg-white border-t border-stone-200 py-8 px-4 text-center text-xs text-stone-500 mt-16">
    <p>© 2026 StylesDays pSEO System. Static Edge Delivery.</p>
  </footer>

  <!-- Interactive Checklist Client-side Persistence -->
  <script>
    (function() {{
      const slug = "{slug_safe}";
      const storageKey = "pseo_checklist_" + slug;
      let state = {{}};
      try {{
        state = JSON.parse(localStorage.getItem(storageKey) || "{{}}");
      }} catch (e) {{}}

      const checkboxes = document.querySelectorAll('.diy-checkbox[data-slug="' + slug + '"]');
      function updateProgress() {{
        let checkedCount = 0;
        checkboxes.forEach(cb => {{
          const itemKey = cb.getAttribute('data-item');
          if (state[itemKey]) {{
            cb.checked = true;
            checkedCount++;
          }} else {{
            cb.checked = false;
          }}
        }});
        const badge = document.getElementById('checklist-progress');
        if (badge) {{
          badge.textContent = checkedCount + " of " + checkboxes.length + " Completed";
        }}
      }}

      checkboxes.forEach(cb => {{
        cb.addEventListener('change', function() {{
          const itemKey = this.getAttribute('data-item');
          state[itemKey] = this.checked;
          try {{
            localStorage.setItem(storageKey, JSON.stringify(state));
          }} catch (e) {{}}
          updateProgress();
        }});
      }});

      updateProgress();
    }})();
  </script>
  <script>
    (function() {{
      function syncPinterestButtons() {{
        document.querySelectorAll('a[title="Save to Pinterest"], a.pseo-pin-save-btn, a[href*="pinterest.com/pin/create/button"]').forEach(function(btn) {{
          var container = btn.closest('.pseo-photo-container, .group, .pseo-img-wrapper, figure, div');
          var img = container ? container.querySelector('img') : null;
          if (!img) img = document.querySelector('article img, main img');
          if (img) {{
            var liveSrc = img.currentSrc || img.src || img.getAttribute('src') || '';
            if (liveSrc && liveSrc.startsWith('/')) {{
              liveSrc = window.location.origin + liveSrc;
            }}
            if (liveSrc) {{
              try {{
                var u = new URL(btn.href, window.location.origin);
                u.searchParams.set('media', liveSrc);
                btn.href = u.toString();
              }} catch(e) {{}}
            }}
          }}
        }});
      }}
      if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', syncPinterestButtons);
      }} else {{
        syncPinterestButtons();
      }}
      document.addEventListener('click', function(e) {{
        var btn = e.target.closest('a[title="Save to Pinterest"], a.pseo-pin-save-btn, a[href*="pinterest.com/pin/create/button"]');
        if (!btn) return;
        var container = btn.closest('.pseo-photo-container, .group, .pseo-img-wrapper, figure, div');
        var img = container ? container.querySelector('img') : null;
        if (!img) img = document.querySelector('article img, main img');
        if (img) {{
          var liveSrc = img.currentSrc || img.src || img.getAttribute('src') || '';
          if (liveSrc && liveSrc.startsWith('/')) {{
            liveSrc = window.location.origin + liveSrc;
          }}
          if (liveSrc) {{
            try {{
              var u = new URL(btn.href, window.location.origin);
              u.searchParams.set('media', liveSrc);
              btn.href = u.toString();
            }} catch (err) {{}}
          }}
        }}
      }}, true);
    }})();
  </script>
</body>
</html>"""


def _build_standalone_hub_html(
    title: str,
    subtitle: str,
    posts: list[PostItem],
    categories: list[dict[str, Any]],
    theme_key: str,
    base_url: str,
    post_routes: dict[str, RouteResult],
    intermediate_routes: list[IntermediateRoute],
    source_domain: str = "stylesdays.com",
    branding: Optional[Any] = None,
) -> str:
    """Builds the Root Organization Hub (/index.html) with search/filter bar and category directory."""
    if theme_key == "editorial-warm":
        try:
            from app.themes.templates import render_stitch_editorial_hub
            path_prefix = _extract_path_prefix(base_url)
            return render_stitch_editorial_hub(
                posts=posts,
                categories=categories,
                title=title,
                subtitle=subtitle,
                base_url=base_url,
                theme=theme_key,
                source_domain=source_domain,
                branding=branding,
                path_prefix=path_prefix,
                post_routes=post_routes,
                intermediate_routes=intermediate_routes,
            )
        except Exception as e:
            logger.warning(f"Failed rendering stitch editorial hub, falling back: {e}")

    palette = THEME_PALETTES.get(theme_key, THEME_PALETTES["editorial-warm"])
    clean_base = base_url.rstrip("/") if base_url else ""
    path_prefix = _extract_path_prefix(base_url)
    clean_domain = _clean_source_domain(source_domain)
    canonical_hub_url = join_base_and_path(base_url, "/")

    # Category Pills
    cat_pills_html = [
        '<button class="filter-pill active px-4 py-2 rounded-xl text-xs font-bold transition bg-stone-900 text-white" data-cat="all" onclick="filterByCat(\'all\', this)">All Articles</button>'
    ]
    seen_cats = set()
    for c in categories:
        c_slug = c.get("slug")
        c_name = c.get("name")
        if c_slug and c_slug not in seen_cats:
            seen_cats.add(c_slug)
            cat_pills_html.append(
                f'<button class="filter-pill px-4 py-2 rounded-xl text-xs font-bold transition bg-white text-stone-700 border border-stone-200 hover:bg-stone-50" data-cat="{c_slug}" onclick="filterByCat(\'{c_slug}\', this)">{html_lib.escape(c_name)}</button>'
            )
    filter_pills_markup = "".join(cat_pills_html)

    # Category Index List (Links to intermediate category index hubs)
    category_links_html = ""
    for ir in intermediate_routes:
        category_links_html += f"""
        <a href="{ir.web_path}" class="p-4 bg-white rounded-2xl border border-stone-200 hover:border-stone-400 hover:shadow-xs transition block group">
          <div class="text-[11px] font-mono text-stone-400 mb-1">{ir.web_path}</div>
          <h3 class="font-serif-editorial text-lg font-bold text-stone-900 group-hover:text-rose-600 transition">{html_lib.escape(ir.title)}</h3>
          <p class="text-xs text-stone-500 mt-1">{len(ir.posts)} curated articles available</p>
        </a>"""

    # Post Cards HTML
    cards_html = ""
    for p in posts:
        route = post_routes.get(p.slug) or resolve_post_route(p, mode="single")
        raw_img = p.local_image_path or f"assets/images/{p.slug}.jpg"
        if raw_img.startswith("http://") or raw_img.startswith("https://"):
            img_src = raw_img
        else:
            clean_img = raw_img.lstrip("/")
            img_src = f"{path_prefix}/{clean_img}" if path_prefix else f"/{clean_img}"
        card_fallback = f"{path_prefix}/assets/images/placeholder.svg" if path_prefix else "/assets/images/placeholder.svg"
        p_title = html_lib.escape(p.title or p.slug)
        clean_rp = (p.excerpt or "").strip()
        if not clean_rp or clean_rp.lower() in ("asqstyle", "asqstyle.com", "stylesdays", "stylesdays.com") or len(clean_rp) < 15:
            clean_rp = f"Discover inspiring {(p.title or 'decor').lower()} with practical styling tips."
        p_excerpt = html_lib.escape(clean_rp)
        p_cat = html_lib.escape(p.category or "Home Organization")
        p_cat_slug = p.category_slug or slugify(p.category)

        cards_html += f"""
        <article class="post-card bg-white rounded-3xl border border-stone-200/90 overflow-hidden shadow-xs hover:shadow-md transition flex flex-col justify-between group" data-title="{p.title.lower()}" data-category="{p_cat_slug}">
          <a href="{route.web_path}" class="block h-full">
            <div class="aspect-[16/10] bg-stone-100 overflow-hidden relative">
              <img src="{img_src}" alt="{p_title}" width="600" height="375" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" onerror="this.onerror=null; this.src='{card_fallback}'">
              <span class="absolute top-3 left-3 bg-white/95 backdrop-blur-sm text-stone-900 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full shadow-xs">
                {p_cat}
              </span>
            </div>
            <div class="p-6">
              <span class="text-[11px] font-mono text-stone-400 block mb-1">{route.web_path}</span>
              <h2 class="font-serif-editorial text-xl font-bold text-stone-900 mb-2 leading-snug group-hover:text-rose-600 transition">{p_title}</h2>
              <p class="text-xs text-stone-600 line-clamp-2 leading-relaxed">{p_excerpt}</p>
            </div>
          </a>
        </article>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_lib.escape(title)}</title>
  <meta name="description" content="{html_lib.escape(subtitle)}">
  <link rel="canonical" href="{canonical_hub_url}">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: {palette['font_family']};
      background-color: {palette['bg_body']};
      color: {palette['text_body']};
    }}
    .font-serif-editorial {{
      font-family: {palette['font_heading']};
    }}
    .filter-pill.active {{
      background-color: {palette['accent']} !important;
      color: #FFFFFF !important;
      border-color: {palette['accent']} !important;
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col antialiased">
  <!-- Header Banner -->
  <header class="bg-white border-b border-stone-200 py-12 px-4 shadow-xs">
    <div class="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-6">
      <div>
        <div class="flex items-center gap-2 mb-2">
          <span class="w-6 h-6 rounded-md flex items-center justify-center text-white font-bold text-xs" style="background-color: {palette['accent']}">S</span>
          <span class="text-xs font-bold uppercase tracking-widest text-stone-400">Editorial Organization Hub</span>
        </div>
        <h1 class="font-serif-editorial text-4xl sm:text-5xl font-bold text-stone-900 tracking-tight">{html_lib.escape(title)}</h1>
        <p class="text-sm sm:text-base text-stone-600 mt-2 max-w-2xl leading-relaxed">{html_lib.escape(subtitle)}</p>
      </div>
      <div class="flex items-center gap-3">
        <a href="https://{source_domain}/" target="_blank" rel="noopener" class="text-xs font-bold text-white px-5 py-3 rounded-2xl shadow-sm hover:opacity-90 transition" style="background-color: {palette['accent']}">
          Visit {source_domain} ↗
        </a>
      </div>
    </div>
  </header>

  <!-- Hub Directory & Search Bar -->
  <div class="bg-stone-50 border-b border-stone-200/80 py-8 px-4">
    <div class="max-w-6xl mx-auto space-y-6">
      <!-- Search & Filter Controls -->
      <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div class="relative flex-grow max-w-md">
          <input type="text" id="hub-search" placeholder="Search articles, decor ideas, room inspiration..." oninput="handleSearch()" class="w-full pl-10 pr-4 py-2.5 rounded-2xl bg-white border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500 shadow-xs">
          <span class="absolute left-3.5 top-3 text-stone-400 text-sm">🔍</span>
        </div>
        <div class="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          {filter_pills_markup}
        </div>
      </div>

      <!-- Intermediate Category Hubs List -->
      {f'''
      <div>
        <h2 class="text-xs font-bold uppercase tracking-wider text-stone-400 mb-3">Topic Silos & Categories</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {category_links_html}
        </div>
      </div>''' if intermediate_routes else ''}
    </div>
  </div>

  <!-- Main Posts Catalog Grid -->
  <main class="max-w-6xl w-full mx-auto px-4 py-12 flex-grow">
    <div class="flex items-center justify-between mb-8">
      <h2 class="font-serif-editorial text-2xl font-bold text-stone-900">All Published Articles</h2>
      <span id="posts-count-badge" class="text-xs font-bold text-stone-500 bg-stone-100 px-3 py-1 rounded-full">{len(posts)} Articles</span>
    </div>
    <div id="posts-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {cards_html}
    </div>
    <div id="empty-state" class="hidden text-center py-16">
      <p class="text-stone-400 text-sm">No articles match your search or filter.</p>
    </div>
  </main>

  <!-- Footer -->
  <footer class="bg-white border-t border-stone-200 py-10 px-4 text-center text-xs text-stone-500">
    <div class="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
      <p>© 2026 StylesDays pSEO System. Built for GitHub Organization Pages.</p>
      <div class="flex items-center gap-4 text-stone-400">
        <a href="{path_prefix}/sitemap.xml" class="hover:underline">Sitemap XML</a>
        <span>•</span>
        <a href="{path_prefix}/robots.txt" class="hover:underline">Robots.txt</a>
      </div>
    </div>
  </footer>

  <!-- Search & Filter JS -->
  <script>
    let activeCat = 'all';
    function filterByCat(cat, btn) {{
      activeCat = cat;
      document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      handleSearch();
    }}

    function handleSearch() {{
      const q = (document.getElementById('hub-search').value || '').toLowerCase().trim();
      const cards = document.querySelectorAll('.post-card');
      let visibleCount = 0;

      cards.forEach(card => {{
        const title = card.getAttribute('data-title') || '';
        const cat = card.getAttribute('data-category') || '';
        const matchesCat = (activeCat === 'all' || cat === activeCat);
        const matchesQuery = (!q || title.includes(q));

        if (matchesCat && matchesQuery) {{
          card.style.display = '';
          visibleCount++;
        }} else {{
          card.style.display = 'none';
        }}
      }});

      const empty = document.getElementById('empty-state');
      if (empty) empty.style.display = (visibleCount === 0) ? 'block' : 'none';

      const badge = document.getElementById('posts-count-badge');
      if (badge) badge.textContent = visibleCount + ' Articles';
    }}
  </script>
</body>
</html>"""


def _build_standalone_category_index_html(
    route: IntermediateRoute,
    theme_key: str,
    base_url: str,
    post_routes: dict[str, RouteResult],
    source_domain: str = "stylesdays.com",
) -> str:
    """Builds a Category / Silo intermediate index page (/<category>/ or /guides/<parent>/) to prevent 404s."""
    palette = THEME_PALETTES.get(theme_key, THEME_PALETTES["editorial-warm"])
    clean_base = base_url.rstrip("/") if base_url else ""
    path_prefix = _extract_path_prefix(base_url)
    clean_domain = _clean_source_domain(source_domain)

    # Breadcrumbs HTML
    crumbs_html = []
    for idx, c in enumerate(route.breadcrumbs):
        is_last = (idx == len(route.breadcrumbs) - 1)
        name = html_lib.escape(c.get("name") or "")
        url = c.get("url") or "/"
        if is_last:
            crumbs_html.append(f'<span class="text-stone-900 font-semibold">{name}</span>')
        else:
            crumbs_html.append(f'<a href="{url}" class="hover:underline text-stone-500">{name}</a>')
            crumbs_html.append('<span class="text-stone-300 mx-1.5">/</span>')
    breadcrumbs_nav = "".join(crumbs_html)

    # Child Post Cards
    cards_html = ""
    for p in route.posts:
        slug = getattr(p, "slug", "") or (p.get("slug") if isinstance(p, dict) else "")
        p_route = post_routes.get(slug) or resolve_post_route(p, mode="single")
        raw_img = getattr(p, "local_image_path", "") or f"assets/images/{slug}.jpg"
        if raw_img.startswith("http://") or raw_img.startswith("https://"):
            img_src = raw_img
        else:
            clean_img = raw_img.lstrip("/")
            img_src = f"{path_prefix}/{clean_img}" if path_prefix else f"/{clean_img}"
        cat_fallback = f"{path_prefix}/assets/images/placeholder.svg" if path_prefix else "/assets/images/placeholder.svg"
        p_title = html_lib.escape(getattr(p, "title", "") or slug)
        p_excerpt = html_lib.escape(getattr(p, "excerpt", "") or "")
        p_cat = html_lib.escape(getattr(p, "category", "") or "Articles")

        cards_html += f"""
        <article class="bg-white rounded-3xl border border-stone-200/90 overflow-hidden shadow-xs hover:shadow-md transition flex flex-col justify-between group">
          <a href="{p_route.web_path}" class="block h-full">
            <div class="aspect-[16/10] bg-stone-100 overflow-hidden relative">
              <img src="{img_src}" alt="{p_title}" width="600" height="375" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" onerror="this.onerror=null; this.src='{cat_fallback}'">
              <span class="absolute top-3 left-3 bg-white/95 text-stone-900 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full shadow-xs">
                {p_cat}
              </span>
            </div>
            <div class="p-6">
              <span class="text-[11px] font-mono text-stone-400 block mb-1">{p_route.web_path}</span>
              <h2 class="font-serif-editorial text-xl font-bold text-stone-900 mb-2 group-hover:text-rose-600 transition">{p_title}</h2>
              <p class="text-xs text-stone-600 line-clamp-2 leading-relaxed">{p_excerpt}</p>
            </div>
          </a>
        </article>"""

    home_link = f"{path_prefix}/" if path_prefix else "/"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_lib.escape(route.title)} | Home Organization</title>
  <meta name="description" content="Browse curated {html_lib.escape(route.title.lower())} tutorials, room checklists, and styling ideas.">
  <link rel="canonical" href="{clean_base}{route.web_path}">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: {palette['font_family']};
      background-color: {palette['bg_body']};
      color: {palette['text_body']};
    }}
    .font-serif-editorial {{
      font-family: {palette['font_heading']};
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col antialiased">
  <header class="bg-white border-b border-stone-200 sticky top-0 z-40">
    <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
      <a href="{home_link}" class="flex items-center gap-2">
        <span class="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm" style="background-color: {palette['accent']}">S</span>
        <span class="font-serif-editorial text-xl font-bold text-stone-900">StylesDays Hub</span>
      </a>
      <a href="{home_link}" class="text-xs font-semibold text-stone-600 hover:text-stone-900 px-3 py-1.5 rounded-lg hover:bg-stone-100 transition">← All Articles</a>
    </div>
  </header>

  <nav class="bg-white/60 border-b border-stone-200/60 py-3 px-4 text-xs">
    <div class="max-w-6xl mx-auto flex items-center flex-wrap">
      {breadcrumbs_nav}
    </div>
  </nav>

  <section class="bg-white border-b border-stone-200 py-10 px-4">
    <div class="max-w-6xl mx-auto">
      <span class="text-xs font-bold uppercase tracking-widest text-stone-400 block mb-1">Topic Hub</span>
      <h1 class="font-serif-editorial text-3xl sm:text-4xl font-bold text-stone-900">{html_lib.escape(route.title)}</h1>
      <p class="text-sm text-stone-600 mt-2">Curated collection of {len(route.posts)} articles under this category.</p>
    </div>
  </section>

  <main class="max-w-6xl w-full mx-auto px-4 py-12 flex-grow">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {cards_html}
    </div>
  </main>

  <footer class="bg-white border-t border-stone-200 py-8 px-4 text-center text-xs text-stone-500">
    <p>© 2026 StylesDays pSEO System. Non-404 Intermediate Silo Hub.</p>
  </footer>
</body>
</html>"""


class SiteBuilder:
    """Production static site generator for pSEO."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        output_dir: Optional[str] = None,
        theme: Optional[str] = None,
        routing_mode: Optional[str] = None,
        base_url: Optional[str] = None,
        base_path: Optional[str] = None,
        source_domain: str = "stylesdays.com",
        subdomain: Optional[str] = None,
    ) -> None:
        self.config = config or AppConfig()
        self._explicit_output_dir = bool(output_dir)
        self._explicit_subdomain = bool(subdomain and subdomain.strip())
        self.subdomain = subdomain.strip() if subdomain else ""
        raw_output_dir = output_dir or self.config.build.output_dir or "dist"
        if os.path.basename(os.path.normpath(raw_output_dir)).lower() == "distooso":
            raw_output_dir = "dist"

        if self.subdomain:
            norm_out = os.path.normpath(raw_output_dir)
            if os.path.basename(norm_out).lower() != self.subdomain.lower():
                self.output_dir = os.path.join(raw_output_dir, self.subdomain)
            else:
                self.output_dir = raw_output_dir
        else:
            self.output_dir = raw_output_dir

        self.theme = theme or self.config.build.theme or "editorial-warm"
        self.routing_mode = normalize_routing_mode(routing_mode or self.config.build.routing_mode or "single")
        self._explicit_base_url = bool(base_url)
        self.base_url = (base_url or "").rstrip("/")
        self.base_path = base_path or self.config.github.base_path or ""
        self.branding = getattr(self.config, "branding", None)
        if self.subdomain and hasattr(self.config, "projects"):
            proj_data = self.config.projects.get(self.subdomain)
            if proj_data and isinstance(proj_data, dict) and proj_data.get("branding"):
                try:
                    from app.config import BrandingConfig
                    self.branding = BrandingConfig.from_dict(proj_data["branding"])
                except Exception:
                    pass

        # Check for configured Custom Domain (from active project or cloudflare config)
        effective_custom_domain = ""
        if self.subdomain and hasattr(self.config, "projects"):
            proj_data = self.config.projects.get(self.subdomain)
            if isinstance(proj_data, dict):
                effective_custom_domain = (proj_data.get("cf_custom_domain") or proj_data.get("custom_domain") or "").strip()
            elif hasattr(proj_data, "cf_custom_domain"):
                effective_custom_domain = (getattr(proj_data, "cf_custom_domain", "") or getattr(proj_data, "custom_domain", "") or "").strip()
        if not effective_custom_domain and hasattr(self.config, "cloudflare") and self.config.cloudflare.custom_domain:
            effective_custom_domain = self.config.cloudflare.custom_domain.strip()

        if effective_custom_domain:
            clean_dom = re.sub(r"^https?://", "", effective_custom_domain, flags=re.IGNORECASE).strip("/ ")
            derived_brand = derive_brand_from_domain(clean_dom, worker_name=self.subdomain)
            if not self.branding:
                from app.config import BrandingConfig
                self.branding = BrandingConfig(brand_name=derived_brand)
            else:
                self.branding.brand_name = derived_brand
            if not self.base_url or "workers.dev" in self.base_url.lower():
                self.base_url = f"https://{clean_dom}"
            self.source_domain = clean_dom or "styleire.com"
        else:
            if not self.branding:
                from app.config import BrandingConfig
                self.branding = BrandingConfig(brand_name="Styleire")
            elif not getattr(self.branding, "brand_name", "") or (self.subdomain and self.branding.brand_name.strip().lower() == self.subdomain.lower()):
                self.branding.brand_name = "Editorial"
            raw_domain = source_domain or self.config.ingestion.wp_api_url or "styleire.com"
            self.source_domain = raw_domain.replace("https://", "").replace("http://", "").strip("/")
            if self.subdomain and (self.source_domain in ("stylesdays.com", "asqstyle.com") or not self.source_domain):
                self.source_domain = "styleire.com"

        # If base_url was not provided, derive canonical from Cloudflare or GitHub config if available
        if not self.base_url:
            active_plat = getattr(getattr(self.config, "build", None), "active_platform", None) or getattr(self.config, "active_platform", None) or "cloudflare"
            if effective_custom_domain:
                clean_dom = re.sub(r"^https?://", "", effective_custom_domain, flags=re.IGNORECASE).strip("/ ")
                self.base_url = f"https://{clean_dom}"
            elif self.subdomain:
                if self.config.cloudflare.account_subdomain:
                    self.base_url = f"https://{self.subdomain}.{self.config.cloudflare.account_subdomain}.workers.dev"
                elif self.config.cloudflare.project_name == self.subdomain:
                    self.base_url = self.config.cloudflare.get_live_url()
                else:
                    self.base_url = f"https://{self.subdomain}.workers.dev"
            elif self.config.cloudflare.custom_domain:
                self.base_url = f"https://{self.config.cloudflare.custom_domain.strip('/')}"
            elif self.config.cloudflare.project_name and (active_plat in ("cloudflare", "cf") or not self.config.github.owner):
                self.base_url = self.config.cloudflare.get_live_url()
            elif self.config.github.owner and active_plat in ("github", "gh"):
                if self.config.github.repo.endswith(".github.io"):
                    self.base_url = f"https://{self.config.github.repo}"
                elif self.config.github.is_org and (not self.config.github.repo or self.config.github.repo == f"{self.config.github.owner}.github.io"):
                    self.base_url = f"https://{self.config.github.owner}.github.io"
                else:
                    self.base_url = f"https://{self.config.github.owner}.github.io/{self.config.github.repo}"
            elif self.config.cloudflare.project_name:
                self.base_url = self.config.cloudflare.get_live_url()
            elif self.config.github.owner:
                if self.config.github.repo.endswith(".github.io"):
                    self.base_url = f"https://{self.config.github.repo}"
                elif self.config.github.is_org and (not self.config.github.repo or self.config.github.repo == f"{self.config.github.owner}.github.io"):
                    self.base_url = f"https://{self.config.github.owner}.github.io"
                else:
                    self.base_url = f"https://{self.config.github.owner}.github.io/{self.config.github.repo}"

        if not self.base_url:
            self.base_url = "https://home-organization.github.io"

    def _normalize_posts(
        self, manifest_or_posts: Union[Manifest, list[PostItem], list[dict[str, Any]], str, None]
    ) -> tuple[list[PostItem], list[dict[str, Any]]]:
        """Converts diverse manifest inputs into a canonical list of PostItem objects and categories."""
        if manifest_or_posts is None:
            manifest_path = "pseo_manifest.json"
            if os.path.exists(manifest_path):
                manifest = Manifest.load_from_json(manifest_path)
                return list(manifest.posts.values()), manifest.categories
            return [], []

        if isinstance(manifest_or_posts, Manifest):
            return list(manifest_or_posts.posts.values()), manifest_or_posts.categories

        if isinstance(manifest_or_posts, str):
            if os.path.exists(manifest_or_posts):
                manifest = Manifest.load_from_json(manifest_or_posts)
                return list(manifest.posts.values()), manifest.categories
            return [], []

        if isinstance(manifest_or_posts, dict):
            if "posts" in manifest_or_posts and isinstance(manifest_or_posts["posts"], (dict, list)):
                manifest = Manifest.from_dict(manifest_or_posts)
                return list(manifest.posts.values()), manifest.categories
            posts_input = list(manifest_or_posts.values())
            posts = []
            categories_dict = {}
            for item in posts_input:
                if isinstance(item, PostItem):
                    posts.append(item)
                    if item.category and item.category_slug:
                        categories_dict[item.category_slug] = item.category
                elif isinstance(item, dict):
                    p = PostItem.from_dict(item)
                    posts.append(p)
                    if p.category and p.category_slug:
                        categories_dict[p.category_slug] = p.category
            categories = [{"slug": s, "name": n} for s, n in categories_dict.items()]
            return posts, categories

        if isinstance(manifest_or_posts, list):
            posts: list[PostItem] = []
            categories_dict: dict[str, str] = {}
            for item in manifest_or_posts:
                if isinstance(item, PostItem):
                    posts.append(item)
                    if item.category and item.category_slug:
                        categories_dict[item.category_slug] = item.category
                elif isinstance(item, dict):
                    p = PostItem.from_dict(item)
                    posts.append(p)
                    if p.category and p.category_slug:
                        categories_dict[p.category_slug] = p.category
            categories = [{"slug": s, "name": n} for s, n in categories_dict.items()]
            return posts, categories

        return [], []

    def copy_image_assets(self, posts: list[PostItem], target_assets_dir: str) -> int:
        """Copies local images from assets/images/ and subdomain assets to output directory, creating SVG fallbacks as needed."""
        os.makedirs(target_assets_dir, exist_ok=True)
        copied_count = 0

        # Determine active subdomains from builder or posts
        subdomains = set()
        if self.subdomain:
            subdomains.add(self.subdomain)
        for post in posts:
            if getattr(post, "domain", None):
                subdomains.add(post.domain)

        # target_assets_dir is typically <output_dir>/assets/images
        # dist_assets_parent is typically <output_dir>/assets
        dist_assets_parent = os.path.abspath(os.path.dirname(target_assets_dir))

        # Destination directories to mirror assets into:
        # 1. target_assets_dir (<output_dir>/assets/images) - for backward compatibility
        # 2. per-subdomain dirs (<output_dir>/assets/<subdomain>/images)
        dest_images_dirs = [target_assets_dir]
        for sub in subdomains:
            sub_target = os.path.join(dist_assets_parent, sub, "images")
            os.makedirs(sub_target, exist_ok=True)
            if sub_target not in dest_images_dirs:
                dest_images_dirs.append(sub_target)

        # Write generic fallback placeholder in all target directories
        palette = THEME_PALETTES.get(self.theme, THEME_PALETTES["editorial-warm"])
        svg_placeholder = _generate_svg_fallback("Editorial Organization Guide", "StylesDays", palette["accent"])
        for d_dir in dest_images_dirs:
            p_path = os.path.join(d_dir, "placeholder.svg")
            if not os.path.exists(p_path):
                with open(p_path, "w", encoding="utf-8") as f:
                    f.write(svg_placeholder)
                copied_count += 1

        source_assets_dir = os.path.abspath(os.path.join("assets", "images"))

        # Synchronize brand logos and custom logo files to all target assets directories
        if os.path.exists(source_assets_dir):
            for logo_file in ("logo.svg", "logo-badge.svg", "custom-logo.webp", "custom-logo.png", "custom-logo.jpg", "custom-logo.jpeg", "custom-logo.svg"):
                src_logo = os.path.join(source_assets_dir, logo_file)
                if os.path.exists(src_logo):
                    for d_dir in dest_images_dirs:
                        dst_logo = os.path.join(d_dir, logo_file)
                        try:
                            if not os.path.exists(dst_logo) or os.path.getsize(src_logo) != os.path.getsize(dst_logo):
                                shutil.copy2(src_logo, dst_logo)
                                copied_count += 1
                        except Exception:
                            pass

        # Synchronize from assets/<subdomain>/images/ and scraped_data/<subdomain>/assets/images/
        for sub in subdomains:
            sub_src1 = os.path.abspath(os.path.join("assets", sub, "images"))
            sub_src2 = os.path.abspath(os.path.join("scraped_data", sub, "assets", "images"))
            for s_src in (sub_src1, sub_src2):
                if os.path.exists(s_src):
                    for fname in os.listdir(s_src):
                        fpath = os.path.join(s_src, fname)
                        if os.path.isfile(fpath):
                            for d_dir in dest_images_dirs:
                                dst_path = os.path.join(d_dir, fname)
                                try:
                                    if not os.path.exists(dst_path) or os.path.getsize(fpath) != os.path.getsize(dst_path):
                                        shutil.copy2(fpath, dst_path)
                                        copied_count += 1
                                except Exception:
                                    pass

        # Synchronize any other domain-specific assets/ folders (e.g. assets/<domain>/images/)
        root_assets_dir = os.path.abspath("assets")
        if os.path.exists(root_assets_dir):
            for item in os.listdir(root_assets_dir):
                item_path = os.path.join(root_assets_dir, item)
                if os.path.isdir(item_path) and item != "images":
                    target_domain_dir = os.path.join(dist_assets_parent, item)
                    try:
                        shutil.copytree(item_path, target_domain_dir, dirs_exist_ok=True)
                        copied_count += 1
                    except Exception:
                        pass

        for post in posts:
            slug = post.slug
            # Check if source exists in post.local_image_path or subdomain assets or source_assets_dir
            found_src = None
            if post.local_image_path and os.path.exists(post.local_image_path):
                found_src = post.local_image_path
            elif getattr(post, "domain", None):
                dom_cands = [
                    os.path.join("assets", post.domain, "images", f"{slug}.webp"),
                    os.path.join("scraped_data", post.domain, "assets", "images", f"{slug}.webp"),
                    os.path.join("assets", post.domain, "images", f"{slug}.jpg"),
                ]
                for dc in dom_cands:
                    if os.path.exists(dc):
                        found_src = dc
                        break
            if not found_src and self.subdomain:
                dom_cands = [
                    os.path.join("assets", self.subdomain, "images", f"{slug}.webp"),
                    os.path.join("scraped_data", self.subdomain, "assets", "images", f"{slug}.webp"),
                ]
                for dc in dom_cands:
                    if os.path.exists(dc):
                        found_src = dc
                        break
            if not found_src and os.path.exists(source_assets_dir):
                for ext in (".webp", ".jpg", ".jpeg", ".png", ".svg"):
                    cand = os.path.join(source_assets_dir, f"{slug}{ext}")
                    if os.path.exists(cand):
                        found_src = cand
                        break

            if found_src:
                _, ext = os.path.splitext(found_src)
                for d_dir in dest_images_dirs:
                    target_dest = os.path.join(d_dir, f"{slug}{ext}")
                    if not os.path.exists(target_dest) or os.path.getsize(found_src) != os.path.getsize(target_dest):
                        shutil.copy2(found_src, target_dest)
                        copied_count += 1
            else:
                # Check if target already has an image
                has_any = any(
                    os.path.exists(os.path.join(d_dir, f"{slug}.webp"))
                    or os.path.exists(os.path.join(d_dir, f"{slug}.jpg"))
                    or os.path.exists(os.path.join(d_dir, f"{slug}.svg"))
                    for d_dir in dest_images_dirs
                )
                if not has_any:
                    svg_content = _generate_svg_fallback(post.title, post.category, palette["accent"])
                    for d_dir in dest_images_dirs:
                        target_svg = os.path.join(d_dir, f"{slug}.svg")
                        with open(target_svg, "w", encoding="utf-8") as f:
                            f.write(svg_content)
                        copied_count += 1
                    if os.path.exists(source_assets_dir):
                        proj_svg = os.path.join(source_assets_dir, f"{slug}.svg")
                        if not os.path.exists(proj_svg):
                            try:
                                with open(proj_svg, "w", encoding="utf-8") as pf:
                                    pf.write(svg_content)
                            except Exception:
                                pass

        return copied_count

    def render_post_page(
        self,
        post: PostItem,
        all_posts: list[PostItem],
        route: RouteResult,
        categories: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        """Renders post HTML using Theme Engine if available, with robust fallback."""
        clean_base = self.base_url.rstrip("/") if (self.base_url and "://" in self.base_url) else "https://styleire.com"
        clean_post_url = f"{clean_base}/{post.slug}/"
        if getattr(post, "content_html", None) and ("asqstyle.com" in post.content_html or "asqstyle" in post.content_html):
            post.content_html = re.sub(r"https?://(?:www\.)?asqstyle\.com/[^\s\"'&<>]*", clean_post_url, post.content_html)
            post.content_html = re.sub(r"https?://(?:www\.)?asqstyle\.com", clean_base, post.content_html)
        # Generate SEO Head
        seo_head = ""
        if generate_seo_head is not None:
            try:
                sig = inspect.signature(generate_seo_head)
                kwargs = {}
                for name in sig.parameters:
                    if name in ("post", "post_item"):
                        kwargs[name] = post
                    elif name in ("route", "route_result"):
                        kwargs[name] = route
                    elif name in ("base_url", "github_domain", "domain"):
                        kwargs[name] = self.base_url
                seo_head = generate_seo_head(**kwargs)
            except Exception:
                seo_head = _build_standalone_seo_head(post, route, self.base_url)
        else:
            seo_head = _build_standalone_seo_head(post, route, self.base_url)

        # Render HTML through theme engine
        if theme_render_post is not None:
            try:
                sig = inspect.signature(theme_render_post)
                kwargs = {}
                for name in sig.parameters:
                    if name in ("post", "post_item"):
                        kwargs[name] = post
                    elif name in ("all_posts", "posts", "processed_posts"):
                        kwargs[name] = all_posts
                    elif name in ("theme", "theme_key", "theme_name"):
                        kwargs[name] = self.theme
                    elif name in ("base_url", "github_domain", "domain"):
                        kwargs[name] = self.base_url
                    elif name in ("seo_head", "head_tags", "meta_tags"):
                        kwargs[name] = seo_head
                    elif name == "route":
                        kwargs[name] = route
                    elif name in ("source_domain", "wp_domain"):
                        kwargs[name] = self.source_domain
                    elif name == "branding":
                        kwargs[name] = getattr(self, "branding", None)
                    elif name == "categories":
                        kwargs[name] = categories
                    elif name == "routing_mode":
                        kwargs[name] = self.routing_mode
                if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
                    kwargs.setdefault("branding", getattr(self, "branding", None))
                    kwargs.setdefault("categories", categories)
                    kwargs.setdefault("routing_mode", self.routing_mode)
                    kwargs.setdefault("route", route)
                    kwargs.setdefault("seo_head", seo_head)
                return theme_render_post(**kwargs)
            except Exception:
                pass

        if template_render_post is not None:
            try:
                return template_render_post(
                    post=post,
                    all_posts=all_posts,
                    theme=self.theme,
                    base_url=self.base_url,
                    seo_head=seo_head,
                    route=route,
                    branding=getattr(self, "branding", None),
                    categories=categories,
                    routing_mode=self.routing_mode,
                )
            except Exception:
                pass

        return _build_standalone_post_html(
            post=post,
            all_posts=all_posts,
            route=route,
            theme_key=self.theme,
            base_url=self.base_url,
            seo_head=seo_head,
            source_domain=self.source_domain,
            branding=getattr(self, "branding", None),
            categories=categories,
            routing_mode=self.routing_mode,
        )

    def render_category_page(
        self,
        route: IntermediateRoute,
        post_routes: dict[str, RouteResult],
        all_categories: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        """Renders category/silo index page containing links to child posts."""
        if template_render_category_index is not None:
            try:
                cat_slug = getattr(route, "slug", "") or (route.web_path.strip("/").split("/")[-1] if hasattr(route, "web_path") else "")
                raw_cat_title = getattr(route, "title", "") or ""
                clean_cat_title = re.sub(r'\s+guides?$', '', raw_cat_title, flags=re.IGNORECASE).strip() or raw_cat_title
                return template_render_category_index(
                    category_name=clean_cat_title,
                    category_slug=cat_slug,
                    posts=route.posts,
                    base_url=self.base_url,
                    theme=self.theme,
                    source_domain=self.source_domain,
                    branding=getattr(self, "branding", None),
                    post_routes=post_routes,
                    routing_mode=self.routing_mode,
                    all_categories=all_categories,
                )
            except Exception:
                pass
        return _build_standalone_category_index_html(
            route=route,
            theme_key=self.theme,
            base_url=self.base_url,
            post_routes=post_routes,
            source_domain=self.source_domain,
        )

    def render_root_hub(
        self,
        posts: list[PostItem],
        categories: list[dict[str, Any]],
        post_routes: dict[str, RouteResult],
        intermediate_routes: list[IntermediateRoute],
    ) -> str:
        """Renders the root organization hub index.html with search/filter section and category directory."""
        if template_render_hub is not None and self.theme in ("styleire", "pinterest-mag", "nordic-studio"):
            try:
                brand = getattr(getattr(self, "branding", None), "brand_name", None) or getattr(getattr(self.config, "branding", None), "brand_name", None) or "Styleire"
                title = f"{brand} - Home decor ideas, articles, and inspiration"
                subtitle = f"{brand} is an independent home decor publication with practical articles, expert styling advice, and inspiration for every room of your home."
                return template_render_hub(
                    posts=posts,
                    categories=categories,
                    title=title,
                    subtitle=subtitle,
                    base_url=self.base_url,
                    theme=self.theme,
                    source_domain=self.source_domain,
                    branding=getattr(self, "branding", None),
                    post_routes=post_routes,
                    intermediate_routes=intermediate_routes,
                    routing_mode=self.routing_mode,
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Failed to render hub via template_render_hub: %s", e, exc_info=True)
        if self.base_url and ("workers.dev" in self.base_url or "pages.dev" in self.base_url):
            brand = self.config.cloudflare.project_name or self.source_domain or "StylesDays"
        elif self.config.cloudflare.project_name and not self.config.github.owner:
            brand = self.config.cloudflare.project_name
        elif self.config.github.owner:
            brand = self.config.github.owner
        else:
            brand = self.source_domain or "StylesDays"
        brand_clean = (
            brand.replace("https://", "")
            .replace("http://", "")
            .replace(".com", "")
            .replace(".github.io", "")
            .replace("-", " ")
            .title()
        )
        title = f"{brand_clean} Editorial Hub"
        subtitle = "Curated Home Organization, Room Styling Inspiration, and Modern Living Articles."

        return _build_standalone_hub_html(
            title=title,
            subtitle=subtitle,
            posts=posts,
            categories=categories,
            theme_key=self.theme,
            base_url=self.base_url,
            post_routes=post_routes,
            intermediate_routes=intermediate_routes,
            source_domain=self.source_domain,
            branding=getattr(self, "branding", None),
        )

    def generate_robots_and_sitemap(
        self,
        posts: list[PostItem],
        post_routes: dict[str, RouteResult],
        intermediate_routes: list[IntermediateRoute],
        extra_pages: Optional[list[dict[str, Any]]] = None,
    ) -> tuple[str, str]:
        """Generates robots.txt and sitemap.xml adhering strictly to R5."""
        clean_base = self.base_url.rstrip("/")
        sitemap_url = join_base_and_path(clean_base, "/sitemap.xml")

        # 1. Robots.txt
        if generate_robots_txt is not None:
            try:
                robots_txt = generate_robots_txt(sitemap_url=sitemap_url)
            except Exception:
                robots_txt = f"""User-agent: *
Allow: /
Allow: /assets/images/

User-agent: Pinterestbot
Allow: /
Allow: /assets/images/

Sitemap: {sitemap_url}
"""
        else:
            robots_txt = f"""User-agent: *
Allow: /
Allow: /assets/images/

User-agent: Pinterestbot
Allow: /
Allow: /assets/images/

Sitemap: {sitemap_url}
"""

        # 2. Sitemap.xml
        # Ensure post objects have web_path populated from resolved routes
        for p in posts:
            r = post_routes.get(p.slug)
            if r:
                try:
                    setattr(p, "web_path", r.web_path)
                except Exception:
                    pass
                if hasattr(p, "raw_meta") and isinstance(p.raw_meta, dict):
                    p.raw_meta["web_path"] = r.web_path

        hub_urls = ["/"] + [ir.web_path for ir in intermediate_routes]
        if generate_sitemap_xml is not None:
            try:
                sitemap_xml = generate_sitemap_xml(
                    posts=posts,
                    base_url=clean_base,
                    hub_urls=hub_urls,
                    extra_pages=extra_pages,
                )
            except Exception:
                sitemap_xml = self._build_standalone_sitemap_xml(posts, post_routes, intermediate_routes)
        else:
            sitemap_xml = self._build_standalone_sitemap_xml(posts, post_routes, intermediate_routes)

        return robots_txt, sitemap_xml

    def _build_standalone_sitemap_xml(
        self,
        posts: list[PostItem],
        post_routes: dict[str, RouteResult],
        intermediate_routes: list[IntermediateRoute],
    ) -> str:
        """Constructs valid XML sitemap with Google <image:image> tags for every post."""
        clean_base = self.base_url.rstrip("/")
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
        ]

        # Root hub entry
        root_url = join_base_and_path(clean_base, "/")
        lines.append("  <url>")
        lines.append(f"    <loc>{root_url}</loc>")
        lines.append("    <changefreq>daily</changefreq>")
        lines.append("    <priority>1.0</priority>")
        lines.append("  </url>")

        # Intermediate Category & Silo Hub entries
        for ir in intermediate_routes:
            hub_url = join_base_and_path(clean_base, ir.web_path)
            lines.append("  <url>")
            lines.append(f"    <loc>{hub_url}</loc>")
            lines.append("    <changefreq>daily</changefreq>")
            lines.append("    <priority>0.8</priority>")
            lines.append("  </url>")

        # Post entries with image:image
        for post in posts:
            route = post_routes.get(post.slug) or resolve_post_route(post, mode=self.routing_mode)
            post_url = join_base_and_path(clean_base, route.web_path)
            img_path = post.local_image_path or f"/assets/images/{post.slug}.jpg"
            img_clean = "/" + img_path.lstrip("/")
            full_img_url = join_base_and_path(clean_base, img_clean)
            escaped_title = html_lib.escape(post.title or post.slug)
            lastmod = post.modified or post.date or "2026-10-29"

            lines.append("  <url>")
            lines.append(f"    <loc>{post_url}</loc>")
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
            lines.append("    <changefreq>weekly</changefreq>")
            lines.append("    <priority>0.7</priority>")
            lines.append("    <image:image>")
            lines.append(f"      <image:loc>{full_img_url}</image:loc>")
            lines.append(f"      <image:title>{escaped_title}</image:title>")
            lines.append("    </image:image>")
            lines.append("  </url>")

        lines.append("</urlset>")
        return "\n".join(lines)

    def build(
        self,
        manifest_or_posts: Union[Manifest, list[PostItem], list[dict[str, Any]], str, None] = None,
        subdomain: Optional[str] = None,
    ) -> BuildSummary:
        """Executes the complete static site build pipeline into self.output_dir."""
        start_time = time.time()

        # 1. Normalize posts and categories
        posts, categories = self._normalize_posts(manifest_or_posts)

        # Detect subdomain if specified or inferred
        sub = (subdomain or (self.subdomain if getattr(self, "_explicit_subdomain", True) else "") or "").strip()
        if not sub:
            if hasattr(manifest_or_posts, "subdomain") and getattr(manifest_or_posts, "subdomain", None):
                sub = str(getattr(manifest_or_posts, "subdomain")).strip()
            elif isinstance(manifest_or_posts, dict) and manifest_or_posts.get("subdomain"):
                sub = str(manifest_or_posts.get("subdomain")).strip()
            elif posts:
                doms = [p.domain for p in posts if getattr(p, "domain", None)]
                if doms:
                    sub = doms[0].strip()
        if not sub and not getattr(self, "_explicit_output_dir", False):
            sub = (
                (self.config.cloudflare.project_name.strip() if getattr(self.config.cloudflare, "project_name", None) else None)
                or (self.config.github.owner.strip() if getattr(self.config.github, "owner", None) else None)
                or ""
            )

        if sub:
            self.subdomain = sub
            if not getattr(self, "_explicit_output_dir", False):
                norm_out = os.path.normpath(self.output_dir)
                if os.path.basename(norm_out) != self.subdomain:
                    self.output_dir = os.path.join(self.output_dir, self.subdomain)
            if not getattr(self, "_explicit_base_url", False):
                eff_cd = ""
                if self.subdomain and hasattr(self.config, "projects"):
                    proj_d = self.config.projects.get(self.subdomain)
                    if isinstance(proj_d, dict):
                        eff_cd = (proj_d.get("cf_custom_domain") or proj_d.get("custom_domain") or "").strip()
                    elif hasattr(proj_d, "cf_custom_domain"):
                        eff_cd = (getattr(proj_d, "cf_custom_domain", "") or getattr(proj_d, "custom_domain", "") or "").strip()
                if not eff_cd and hasattr(self.config, "cloudflare") and self.config.cloudflare.custom_domain:
                    eff_cd = self.config.cloudflare.custom_domain.strip()

                if eff_cd:
                    clean_dom = re.sub(r"^https?://", "", eff_cd, flags=re.IGNORECASE).strip("/ ")
                    self.base_url = f"https://{clean_dom}"
                    self.source_domain = clean_dom
                    derived_brand = derive_brand_from_domain(clean_dom, worker_name=self.subdomain)
                    if not self.branding:
                        from app.config import BrandingConfig
                        self.branding = BrandingConfig(brand_name=derived_brand)
                    elif not getattr(self.branding, "brand_name", "") or (self.subdomain and self.branding.brand_name.strip().lower() == self.subdomain.lower()):
                        self.branding.brand_name = derived_brand
                elif self.config.cloudflare.account_subdomain:
                    self.base_url = f"https://{self.subdomain}.{self.config.cloudflare.account_subdomain}.workers.dev"
                elif self.config.cloudflare.project_name == self.subdomain:
                    self.base_url = self.config.cloudflare.get_live_url()
                else:
                    self.base_url = f"https://{self.subdomain}.workers.dev"

        abs_output_dir = os.path.abspath(self.output_dir)
        os.makedirs(abs_output_dir, exist_ok=True)

        # Clean stale generated HTML files and route directories (preserve assets/, images/, _worker.js, .git)
        for entry in os.listdir(abs_output_dir):
            if entry in ("assets", "images", "_worker.js", ".git"):
                continue
            entry_path = os.path.join(abs_output_dir, entry)
            if os.path.isdir(entry_path):
                shutil.rmtree(entry_path, ignore_errors=True)
            elif entry.endswith((".html", ".xml", ".txt")):
                try:
                    os.remove(entry_path)
                except OSError:
                    pass

        files_created: list[str] = []
        errors: list[str] = []

        # 2. Resolve post routes and intermediate category/silo routes
        resolver = RouteResolver(
            mode=self.routing_mode,
            base_path=self.base_path,
            base_url=self.base_url,
        )
        post_routes: dict[str, RouteResult] = resolver.resolve_all(posts)
        intermediate_routes: list[IntermediateRoute] = resolver.get_intermediate_routes(posts)

        # 3. Synchronize assets/images/
        target_assets_dir = os.path.join(abs_output_dir, "assets", "images")
        images_copied = self.copy_image_assets(posts, target_assets_dir)

        # Normalize post local_image_path to eliminate any /assets/<worker>/images/ leakage in HTML
        for post in posts:
            lip = getattr(post, "local_image_path", "") or ""
            if lip and not lip.startswith("http"):
                clean_lip = lip.replace("\\", "/").lstrip("/")
                if "/images/" in clean_lip:
                    img_filename = clean_lip.split("/images/")[-1]
                    post.local_image_path = f"assets/images/{img_filename}"

        # 4. Render Post Pages
        post_pages_count = 0
        for post in posts:
            route = post_routes.get(post.slug)
            if not route:
                continue

            target_file = os.path.join(abs_output_dir, route.file_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            try:
                html_content = self.render_post_page(post, posts, route, categories=categories)
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                files_created.append(route.file_path)
                post_pages_count += 1
            except Exception as e:
                errors.append(f"Error rendering post {post.slug}: {e}")

        # 5. Render Intermediate Category / Silo Pages (Prevent 404s!)
        intermediate_count = 0
        for ir in intermediate_routes:
            target_file = os.path.join(abs_output_dir, ir.file_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            try:
                html_content = self.render_category_page(ir, post_routes, all_categories=categories)
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                files_created.append(ir.file_path)
                intermediate_count += 1

                # Dual alias support: ensure both /{slug}/ and /category/{slug}/ exist on disk
                if ir.file_path.startswith("category/"):
                    alias_file = os.path.join(abs_output_dir, ir.file_path[len("category/"):].replace("/", os.sep))
                else:
                    alias_file = os.path.join(abs_output_dir, "category", ir.file_path.replace("/", os.sep))
                os.makedirs(os.path.dirname(alias_file), exist_ok=True)
                with open(alias_file, "w", encoding="utf-8") as af:
                    af.write(html_content)
            except Exception as e:
                errors.append(f"Error rendering intermediate route {ir.web_path}: {e}")

        # 6. Render Root Organization Hub (/index.html)
        root_file = os.path.join(abs_output_dir, "index.html")
        try:
            root_html = self.render_root_hub(posts, categories, post_routes, intermediate_routes)
            with open(root_file, "w", encoding="utf-8") as f:
                f.write(root_html)
            files_created.append("index.html")
        except Exception as e:
            errors.append(f"Error rendering root hub: {e}")

        # 7. Generate robots.txt and sitemap.xml
        # 6b. Render E-E-A-T Author Page (/author/sophia-bennett/index.html)
        author_file = os.path.join(abs_output_dir, "author", "sophia-bennett", "index.html")
        os.makedirs(os.path.dirname(author_file), exist_ok=True)
        try:
            from app.themes.templates import render_author_page
            author_html = render_author_page(
                author_name="Sophia Bennett",
                posts=posts,
                theme=self.theme,
                base_url=self.base_url,
                source_domain=self.source_domain,
                branding=getattr(self, "branding", None),
                post_routes=post_routes,
                routing_mode=self.routing_mode,
                categories=categories,
            )
            with open(author_file, "w", encoding="utf-8") as f:
                f.write(author_html)
            files_created.append("author/sophia-bennett/index.html")
        except Exception as e:
            errors.append(f"Error rendering author page: {e}")

        # 6c. Render 9 Trust & Compliance Pages
        trust_slugs = [
            "about", "contact", "editorial-policy", "fact-checking-policy",
            "privacy-policy", "cookie-policy", "terms", "disclaimer", "copyright"
        ]
        try:
            from app.themes.templates import render_trust_page
            for t_slug in trust_slugs:
                t_file = os.path.join(abs_output_dir, t_slug, "index.html")
                os.makedirs(os.path.dirname(t_file), exist_ok=True)
                t_html = render_trust_page(
                    slug=t_slug,
                    theme=self.theme,
                    base_url=self.base_url,
                    source_domain=self.source_domain,
                    branding=getattr(self, "branding", None),
                    categories=categories,
                    all_posts=posts,
                    routing_mode=self.routing_mode,
                )
                with open(t_file, "w", encoding="utf-8") as f:
                    f.write(t_html)
                files_created.append(f"{t_slug}/index.html")
        except Exception as e:
            errors.append(f"Error rendering trust pages: {e}")

        # 6d. Render HTML Sitemap Directory (/sitemap/index.html)
        sitemap_html_file = os.path.join(abs_output_dir, "sitemap", "index.html")
        os.makedirs(os.path.dirname(sitemap_html_file), exist_ok=True)
        try:
            from app.themes.templates import render_html_sitemap
            sitemap_html = render_html_sitemap(
                posts=posts,
                categories=categories,
                theme=self.theme,
                base_url=self.base_url,
                source_domain=self.source_domain,
                branding=getattr(self, "branding", None),
                routing_mode=self.routing_mode,
            )
            with open(sitemap_html_file, "w", encoding="utf-8") as f:
                f.write(sitemap_html)
            files_created.append("sitemap/index.html")
        except Exception as e:
            errors.append(f"Error rendering HTML sitemap: {e}")

        # 6e. Deploy ads.txt
        ads_file = os.path.join(abs_output_dir, "ads.txt")
        ref_ads = os.path.join("static-site", "ads.txt")
        if os.path.exists(ref_ads):
            shutil.copy2(ref_ads, ads_file)
        else:
            with open(ads_file, "w", encoding="utf-8") as f:
                f.write("google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0\n")
        files_created.append("ads.txt")

        # 7. Generate robots.txt and sitemap.xml with full 78-URL priority index
        extra_sitemap_pages = [
            {"path": "/author/sophia-bennett/", "priority": "0.6", "changefreq": "monthly"},
            {"path": "/sitemap/", "priority": "0.5", "changefreq": "weekly"},
        ]
        for t_slug in trust_slugs:
            extra_sitemap_pages.append({"path": f"/{t_slug}/", "priority": "0.4", "changefreq": "monthly"})

        robots_content, sitemap_content = self.generate_robots_and_sitemap(
            posts, post_routes, intermediate_routes, extra_pages=extra_sitemap_pages
        )
        robots_file = os.path.join(abs_output_dir, "robots.txt")
        with open(robots_file, "w", encoding="utf-8") as f:
            f.write(robots_content)
        files_created.append("robots.txt")

        sitemap_file = os.path.join(abs_output_dir, "sitemap.xml")
        with open(sitemap_file, "w", encoding="utf-8") as f:
            f.write(sitemap_content)
        files_created.append("sitemap.xml")

        # Copy static pages & assets from static-site/ to ensure 100% compliance
        try:
            from app.generator.static_pages import copy_static_pages
            source_site = "static-site"
            if os.path.exists(source_site):
                path_prefix = _extract_path_prefix(self.base_url)
                copy_static_pages(
                    source_site_dir=source_site,
                    output_dir=abs_output_dir,
                    path_prefix=path_prefix,
                )
        except Exception as e:
            errors.append(f"Error copying static pages: {e}")

        # 8. Dump Manifest to output directory for portability
        manifest_dest = os.path.join(abs_output_dir, "pseo_manifest.json")
        try:
            manifest_obj = Manifest(
                posts={p.slug: p for p in posts},
                categories=categories,
            )
            manifest_obj.save_to_json(manifest_dest)
            files_created.append("pseo_manifest.json")
        except Exception as e:
            errors.append(f"Error saving manifest to output: {e}")

        # 9. Universal post-compilation guard rail: sanitize any leaked worker names
        self._sanitize_output_files(abs_output_dir)

        duration = round(time.time() - start_time, 4)
        total_pages = 1 + intermediate_count + post_pages_count + 1 + len(trust_slugs) + 1

        return BuildSummary(
            status="success" if not errors else "partial_success",
            output_dir=abs_output_dir,
            theme=self.theme,
            routing_mode=self.routing_mode,
            total_posts=len(posts),
            post_pages_generated=post_pages_count,
            intermediate_pages_generated=intermediate_count,
            total_pages_generated=total_pages,
            images_copied=images_copied,
            robots_generated=True,
            sitemap_generated=True,
            duration_seconds=duration,
            files_created=files_created,
            errors=errors,
        )

    @classmethod
    def sanitize_directory(
        cls,
        output_dir: str,
        worker_names: Optional[list[str]] = None,
        base_url: Optional[str] = None,
        brand_name: Optional[str] = None,
        config: Optional[AppConfig] = None,
    ) -> None:
        """Universal audit and sanitization pass: purges any leaked worker names in static files."""
        if not output_dir or not os.path.exists(output_dir):
            return

        worker_patterns = list(worker_names or [])
        if config and hasattr(config, "cloudflare") and config.cloudflare.project_name:
            worker_patterns.append(config.cloudflare.project_name.strip())

        unique_workers = [w.strip() for w in set(worker_patterns) if w and len(w.strip()) >= 3]
        if not unique_workers:
            return

        # Check config for configured custom domain
        effective_cd = ""
        if config and hasattr(config, "cloudflare") and config.cloudflare.custom_domain:
            effective_cd = config.cloudflare.custom_domain.strip()
        if not effective_cd and base_url and "workers.dev" not in base_url.lower():
            effective_cd = base_url

        replacement_domain = ""
        if effective_cd:
            replacement_domain = re.sub(r"^https?://", "", effective_cd, flags=re.IGNORECASE).strip("/ ")
        elif base_url:
            replacement_domain = re.sub(r"^https?://", "", base_url, flags=re.IGNORECASE).strip("/ ")

        target_brand = (brand_name or (getattr(config.branding, "brand_name", "") if config and getattr(config, "branding", None) else "") or "").strip()
        if not target_brand or target_brand.lower() in [w.lower() for w in unique_workers]:
            if replacement_domain and "workers.dev" not in replacement_domain.lower():
                target_brand = derive_brand_from_domain(replacement_domain, worker_name=unique_workers[0])
            elif base_url:
                target_brand = derive_brand_from_domain(base_url, worker_name=unique_workers[0])
            else:
                target_brand = "Styleire"

        for root, _, files in os.walk(output_dir):
            for fname in files:
                if fname.endswith((".html", ".xml", ".txt", ".json")):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            content = f.read()

                        modified = content

                        # 1. Clean worker domain URLs only when replacing with an external domain
                        if replacement_domain and "workers.dev" not in replacement_domain.lower():
                            for w in unique_workers:
                                w_lower = w.lower()
                                modified = re.sub(
                                    rf"https?://{re.escape(w_lower)}\.[a-zA-Z0-9_\-\.]*workers\.dev",
                                    f"https://{replacement_domain}",
                                    modified,
                                    flags=re.IGNORECASE,
                                )
                                modified = re.sub(
                                    rf"https?://{re.escape(w_lower)}\.workers\.dev",
                                    f"https://{replacement_domain}",
                                    modified,
                                    flags=re.IGNORECASE,
                                )
                            # Universal worker URL catch-all for any leftover *.workers.dev
                            modified = re.sub(
                                r"https?://[a-zA-Z0-9_\-\.]*workers\.dev",
                                f"https://{replacement_domain}",
                                modified,
                                flags=re.IGNORECASE,
                            )
                            # If custom domain is a subdomain (e.g. decohome.homeandrecipe.com), align apex domain references
                            if replacement_domain.count(".") >= 2:
                                apex = ".".join(replacement_domain.split(".")[-2:])
                                modified = re.sub(
                                    rf"https?://(?:www\.)?{re.escape(apex)}(?=[/'\"])",
                                    f"https://{replacement_domain}",
                                    modified,
                                    flags=re.IGNORECASE,
                                )
                                modified = re.sub(
                                    rf"https?%3A%2F%2F(?:www\.)?{re.escape(apex)}(?=%2F|&|\"|'|%22)",
                                    f"https%3A%2F%2F{replacement_domain}",
                                    modified,
                                    flags=re.IGNORECASE,
                                )

                        for w in unique_workers:
                            w_title = w.title()
                            w_lower = w.lower()

                            # 2. Clean asset paths (raw and URL-encoded): /assets/<worker>/images/ -> /assets/images/
                            modified = re.sub(
                                rf"assets/{re.escape(w_lower)}/images/",
                                "assets/images/",
                                modified,
                                flags=re.IGNORECASE,
                            )
                            modified = re.sub(
                                rf"assets/{re.escape(w_lower)}/",
                                "assets/",
                                modified,
                                flags=re.IGNORECASE,
                            )
                            modified = re.sub(
                                rf"assets%2F{re.escape(w_lower)}%2Fimages%2F",
                                "assets%2Fimages%2F",
                                modified,
                                flags=re.IGNORECASE,
                            )
                            modified = re.sub(
                                rf"assets%2F{re.escape(w_lower)}%2F",
                                "assets%2F",
                                modified,
                                flags=re.IGNORECASE,
                            )

                            # 3. Clean titles and meta og:title / twitter:title: " | <WorkerTitle>" -> " | <TargetBrand>"
                            modified = re.sub(
                                rf"\|\s*{re.escape(w_title)}(?=[<\s\"])",
                                f"| {target_brand}",
                                modified,
                            )
                            modified = re.sub(
                                rf"\|\s*{re.escape(w)}(?=[<\s\"])",
                                f"| {target_brand}",
                                modified,
                            )

                            # 4. Clean og:site_name and schema publisher name
                            modified = re.sub(
                                rf'(property="og:site_name"\s+content="){re.escape(w_title)}(")',
                                rf"\g<1>{target_brand}\2",
                                modified,
                            )
                            modified = re.sub(
                                rf'(property="og:site_name"\s+content="){re.escape(w)}(")',
                                rf"\g<1>{target_brand}\2",
                                modified,
                            )
                            modified = re.sub(
                                rf'("publisher":\s*\{{[^}}]*"name":\s*"){re.escape(w_title)}(")',
                                rf"\g<1>{target_brand}\2",
                                modified,
                            )
                            modified = re.sub(
                                rf'("publisher":\s*\{{[^}}]*"name":\s*"){re.escape(w)}(")',
                                rf"\g<1>{target_brand}\2",
                                modified,
                            )

                            # 5. Clean trust pages (About <Worker>, <Worker> is an independent)
                            modified = re.sub(
                                rf"About\s+{re.escape(w_title)}",
                                f"About {target_brand}",
                                modified,
                            )
                            modified = re.sub(
                                rf"About\s+{re.escape(w)}",
                                f"About {target_brand}",
                                modified,
                            )
                            modified = re.sub(
                                rf"{re.escape(w_title)}\s+is\s+an\s+independent",
                                f"{target_brand} is an independent",
                                modified,
                            )
                            modified = re.sub(
                                rf"{re.escape(w)}\s+is\s+an\s+independent",
                                f"{target_brand} is an independent",
                                modified,
                            )
                            modified = re.sub(
                                rf"&copy;\s*2026\s+{re.escape(w_title)}\.",
                                f"&copy; 2026 {target_brand}.",
                                modified,
                            )
                            modified = re.sub(
                                rf"&copy;\s*2026\s+{re.escape(w)}\.",
                                f"&copy; 2026 {target_brand}.",
                                modified,
                            )

                        # 6. Universal purge of "Last updated" and "Updated [date]" text nodes
                        modified = re.sub(
                            r'<p\s+class="mt-4 text-lg text-stone-600 leading-relaxed">\s*Last updated:?[^<]*</p>',
                            '',
                            modified,
                            flags=re.IGNORECASE,
                        )
                        modified = re.sub(
                            r'<meta\s+name="description"\s+content="Last updated:?[^"]*">',
                            f'<meta name="description" content="Official editorial policies and guidance for {target_brand}.">',
                            modified,
                            flags=re.IGNORECASE,
                        )
                        modified = re.sub(
                            r'<span\s+class="text-xs text-stone-400 font-medium">\s*Updated:?\s*[^<]*</span>',
                            '',
                            modified,
                            flags=re.IGNORECASE,
                        )
                        modified = re.sub(
                            r'<span\s+class="text-xs text-stone-500 font-medium">\s*Updated Regularly\s*</span>',
                            '',
                            modified,
                            flags=re.IGNORECASE,
                        )
                        modified = re.sub(
                            r'<span>Updated\s+[^<]+</span>\s*<span>&middot;</span>',
                            '',
                            modified,
                            flags=re.IGNORECASE,
                        )
                        modified = re.sub(
                            r'&nbsp;&middot;&nbsp;\s*Updated\s*\d{4}-\d{2}-\d{2}',
                            '',
                            modified,
                            flags=re.IGNORECASE,
                        )
                        modified = re.sub(
                            r'•\s*UPDATED\s*\d{4}',
                            '',
                            modified,
                            flags=re.IGNORECASE,
                        )
                        modified = re.sub(
                            r'Updated\s+(?:\d{4}-\d{2}-\d{2}|Recently)\s*•\s*',
                            '',
                            modified,
                            flags=re.IGNORECASE,
                        )

                        # 7. Universal purge of foreign scraped Pinterest Save buttons & wrappers
                        modified = re.sub(r'<a\s+[^>]*class="[^"]*(?:pinsave|pin-it-button|ss-pin-button)[^"]*"[^>]*>.*?</a>', '', modified, flags=re.DOTALL | re.IGNORECASE)
                        modified = re.sub(r'<div\s+[^>]*class="[^"]*ss-on-media-wrapper[^"]*"[^>]*>.*?</div>', '', modified, flags=re.DOTALL | re.IGNORECASE)
                        modified = re.sub(r'</?(?:div|span)\s+[^>]*class="[^"]*(?:ss-on-media-container|ss-on-media-image-wrap|pin-it-container)[^"]*"[^>]*>', '', modified, flags=re.IGNORECASE)

                        if modified != content:
                            with open(fpath, "w", encoding="utf-8") as f:
                                f.write(modified)
                    except Exception:
                        pass

    def _sanitize_output_files(self, output_dir: str) -> None:
        """Universal post-compilation guard rail: audits and removes any leaked worker names in generated static files."""
        sub = (self.subdomain or "").strip()
        worker_patterns = []
        if sub:
            worker_patterns.append(sub)
        if hasattr(self.config, "cloudflare") and self.config.cloudflare.project_name:
            worker_patterns.append(self.config.cloudflare.project_name.strip())

        target_brand = (getattr(self.branding, "brand_name", "") if self.branding else "") or ""
        self.sanitize_directory(
            output_dir=output_dir,
            worker_names=worker_patterns,
            base_url=self.base_url,
            brand_name=target_brand,
            config=self.config,
        )

    # Convenience method alias
    build_site = build


def build_site(
    manifest_or_posts: Union[Manifest, list[PostItem], list[dict[str, Any]], str, None] = None,
    config: Optional[AppConfig] = None,
    output_dir: str = "dist",
    theme: str = "editorial-warm",
    routing_mode: str = "single",
    base_url: str = "",
    base_path: str = "",
    source_domain: str = "stylesdays.com",
    subdomain: Optional[str] = None,
) -> BuildSummary:
    """Convenience function to build the static site."""
    builder = SiteBuilder(
        config=config,
        output_dir=output_dir,
        theme=theme,
        routing_mode=routing_mode,
        base_url=base_url,
        base_path=base_path,
        source_domain=source_domain,
        subdomain=subdomain,
    )
    return builder.build(manifest_or_posts, subdomain=subdomain)


# Backward-compatibility alias
build_static_site = build_site


def render_post_html(
    post: Any,
    all_posts: Optional[list[Any]] = None,
    github_domain: str = "",
    source_domain: str = "stylesdays.com",
    theme_key: str = "editorial-warm",
    **kwargs: Any,
) -> str:
    """Convenience function matching reference deployer render_post_html signature."""
    builder = SiteBuilder(theme=theme_key, base_url=github_domain, source_domain=source_domain)
    p_item = post if isinstance(post, PostItem) else PostItem.from_dict(post)
    posts_list = [p if isinstance(p, PostItem) else PostItem.from_dict(p) for p in (all_posts or [post])]
    route = resolve_post_route(p_item, mode=builder.routing_mode, base_url=github_domain)
    return builder.render_post_page(p_item, posts_list, route)

