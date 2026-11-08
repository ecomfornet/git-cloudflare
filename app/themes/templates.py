"""HTML layout templates and responsive components for the pSEO static site generator."""

from __future__ import annotations

import html as html_lib
import json
import os
import random
import urllib.parse
from typing import Any, Optional
import re


def slugify(text: str) -> str:
    """Converts arbitrary text into a clean URL slug (lowercase alphanumeric with dashes)."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "guide"


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


def _resolve_fallback_svg(slug: str, path_prefix: str = "") -> str:
    """Returns /assets/images/{slug}.svg if exists on disk, otherwise /assets/images/placeholder.svg."""
    prefix = path_prefix.rstrip("/") if path_prefix else ""
    candidate = os.path.join("assets", "images", f"{slug}.svg")
    if os.path.exists(candidate):
        return f"{prefix}/assets/images/{slug}.svg" if prefix else f"/assets/images/{slug}.svg"
    return f"{prefix}/assets/images/placeholder.svg" if prefix else "/assets/images/placeholder.svg"


THEMES: dict[str, dict[str, str]] = {
    "editorial-warm": {
        "id": "editorial-warm",
        "name": "Editorial Warm (Stylesdays Signature)",
        "bg_body": "#FAF8F5",
        "text_body": "#1C1917",
        "accent": "#E60023",
        "accent_hover": "#C4001D",
        "card_bg": "#FFFFFF",
        "card_border": "#E7E2DA",
        "CheckBoxBg": "#F1EDE6",
        "badge_bg": "#15803D",
        "font_headline": "'Playfair Display', Georgia, serif",
        "font_body": "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "header_bg": "#FFFFFF",
        "muted_text": "#78716C",
        "tag_bg": "#F5F5F4",
    },
    "nordic-studio": {
        "id": "nordic-studio",
        "name": "The Nordroom (Scandinavian Minimalist)",
        "bg_body": "#FBFBFA",
        "text_body": "#1C1C1C",
        "accent": "#8C6D53",
        "accent_hover": "#6E523B",
        "card_bg": "#FFFFFF",
        "card_border": "#EBEBEA",
        "CheckBoxBg": "#F4F3F0",
        "badge_bg": "#8C6D53",
        "font_headline": "'Cormorant Garamond', 'Playfair Display', Georgia, serif",
        "font_body": "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "header_bg": "#FFFFFF",
        "muted_text": "#686866",
        "tag_bg": "#F4F3F0",
    },
    "pinterest-mag": {
        "id": "pinterest-mag",
        "name": "Model 3 · Styleire Magazine (Editorial & Trust Suite)",
        "bg_body": "#FFFFFF",
        "text_body": "#09090B",
        "accent": "#09090B",
        "accent_hover": "#27272A",
        "card_bg": "#FFFFFF",
        "card_border": "#E4E4E7",
        "CheckBoxBg": "#F4F4F5",
        "badge_bg": "#09090B",
        "font_headline": "'Playfair Display', Georgia, serif",
        "font_body": "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "header_bg": "#FFFFFF",
        "muted_text": "#71717A",
        "tag_bg": "#F4F4F5",
    },
    "styleire": {
        "id": "pinterest-mag",
        "name": "Model 3 · Styleire Magazine (Editorial & Trust Suite)",
        "bg_body": "#FFFFFF",
        "text_body": "#09090B",
        "accent": "#09090B",
        "accent_hover": "#27272A",
        "card_bg": "#FFFFFF",
        "card_border": "#E4E4E7",
        "CheckBoxBg": "#F4F4F5",
        "badge_bg": "#09090B",
        "font_headline": "'Playfair Display', Georgia, serif",
        "font_body": "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "header_bg": "#FFFFFF",
        "muted_text": "#71717A",
        "tag_bg": "#F4F4F5",
    },
}


def get_theme_tokens(theme_key: str = "editorial-warm") -> dict[str, str]:
    """Retrieves palette and styling tokens for a given theme name."""
    return THEMES.get(theme_key, THEMES["editorial-warm"]).copy()


def get_embedded_fallback_css(theme: dict[str, str]) -> str:
    """Generates an embedded responsive CSS stylesheet guaranteeing beautiful layout offline."""
    return f"""
    /* --- Embedded Responsive CSS Fallback (Offline Guaranteed) --- */
    :root {{
      --pseo-bg: {theme['bg_body']};
      --pseo-text: {theme['text_body']};
      --pseo-accent: {theme['accent']};
      --pseo-accent-hover: {theme['accent_hover']};
      --pseo-card-bg: {theme['card_bg']};
      --pseo-card-border: {theme['card_border']};
      --pseo-checkbox-bg: {theme['CheckBoxBg']};
      --pseo-badge-bg: {theme['badge_bg']};
      --pseo-font-headline: {theme['font_headline']};
      --pseo-font-body: {theme['font_body']};
    }}

    *, *::before, *::after {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--pseo-bg);
      color: var(--pseo-text);
      font-family: var(--pseo-font-body);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }}

    h1, h2, h3, h4, .font-serif-editorial {{
      font-family: var(--pseo-font-headline);
      color: var(--pseo-text);
      line-height: 1.25;
    }}

    a {{
      color: inherit;
      text-decoration: none;
    }}

    img {{
      max-width: 100%;
      height: auto;
      display: block;
    }}

    .pseo-container {{
      width: 100%;
      max-width: 1152px;
      margin-left: auto;
      margin-right: auto;
      padding-left: 1rem;
      padding-right: 1rem;
    }}

    .pseo-header {{
      background-color: #FFFFFF;
      border-bottom: 1px solid var(--pseo-card-border);
      padding: 0.75rem 0;
    }}

    .pseo-main {{
      flex: 1 0 auto;
      padding-top: 2rem;
      padding-bottom: 2.5rem;
    }}

    .pseo-grid-layout {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 2rem;
    }}

    @media (min-width: 1024px) {{
      .pseo-grid-layout {{
        grid-template-columns: 8fr 4fr;
      }}
    }}

    .pseo-article-card {{
      background-color: var(--pseo-card-bg);
      border: 1px solid var(--pseo-card-border);
      border-radius: 1.5rem;
      overflow: hidden;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }}

    .pseo-hero-media {{
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 10;
      background-color: #F5F5F4;
      overflow: hidden;
    }}

    .pseo-hero-media img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.5s ease;
    }}

    .pseo-hero-media:hover img {{
      transform: scale(1.03);
    }}

    .pseo-badge {{
      display: inline-flex;
      align-items: center;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .pseo-article-body {{
      padding: 1.5rem;
    }}

    @media (min-width: 640px) {{
      .pseo-article-body {{
        padding: 2.5rem;
      }}
    }}

    .pseo-btn-primary {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      background-color: var(--pseo-accent);
      color: #FFFFFF !important;
      font-weight: 700;
      font-size: 0.875rem;
      padding: 0.875rem 1.5rem;
      border-radius: 0.75rem;
      transition: background-color 0.2s ease, transform 0.1s ease;
      cursor: pointer;
    }}

    .pseo-btn-primary:hover {{
      background-color: var(--pseo-accent-hover);
      transform: translateY(-1px);
    }}

    /* Article Body Typography & Responsive Elements */
    .pseo-article-body {{
      margin: 2rem 0;
      font-size: 1.05rem;
      line-height: 1.8;
      color: inherit;
    }}
    .pseo-article-body p {{
      margin-bottom: 1.5rem;
    }}
    .pseo-article-body h2 {{
      font-size: 1.75rem;
      font-weight: 700;
      margin-top: 2.5rem;
      margin-bottom: 1rem;
      color: var(--pseo-text);
      line-height: 1.3;
    }}
    .pseo-article-body h3 {{
      font-size: 1.35rem;
      font-weight: 600;
      margin-top: 2rem;
      margin-bottom: 0.75rem;
      color: var(--pseo-text);
      line-height: 1.35;
    }}
    .pseo-article-body h4 {{
      font-size: 1.15rem;
      font-weight: 600;
      margin-top: 1.5rem;
      margin-bottom: 0.5rem;
    }}
    .pseo-article-body ul, .pseo-article-body ol {{
      margin: 1.25rem 0 1.5rem 1.75rem;
    }}
    .pseo-article-body li {{
      margin-bottom: 0.5rem;
    }}
    .pseo-article-body blockquote {{
      border-left: 3px solid var(--pseo-accent);
      padding: 0.75rem 1.25rem;
      margin: 1.75rem 0;
      background: rgba(0, 0, 0, 0.02);
      border-radius: 0 0.5rem 0.5rem 0;
      font-style: italic;
    }}
    .pseo-article-body figure {{
      margin: 2rem 0;
    }}
    .pseo-article-body figure img, .pseo-article-body img {{
      width: 100%;
      height: auto;
      border-radius: 0.75rem;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    }}
    .pseo-article-body figcaption {{
      font-size: 0.8rem;
      color: #78716C;
      margin-top: 0.5rem;
      text-align: center;
    }}

    .pseo-takeaways-card {{
      background-color: var(--pseo-card-bg);
      border: 1px solid var(--pseo-card-border);
      border-radius: 1rem;
      padding: 1.5rem;
      margin-bottom: 2rem;
    }}

    .pseo-checklist-container {{
      background-color: var(--pseo-checkbox-bg);
      border: 1px solid var(--pseo-card-border);
      border-radius: 1.5rem;
      padding: 1.5rem;
    }}

    .pseo-checklist-item {{
      display: flex;
      align-items: flex-start;
      gap: 0.625rem;
      padding: 0.5rem;
      border-radius: 0.5rem;
      transition: background-color 0.15s ease;
      cursor: pointer;
    }}

    .pseo-checklist-item:hover {{
      background-color: rgba(0, 0, 0, 0.04);
    }}

    .pseo-checklist-item.completed .checklist-label {{
      text-decoration: line-through;
      color: #A8A29E;
    }}

    .pseo-pin-save-btn {{
      position: absolute;
      top: 14px;
      right: 14px;
      z-index: 30;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background-color: #E60023 !important;
      color: #FFFFFF !important;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 13px;
      font-weight: 700;
      line-height: 1;
      padding: 8px 16px;
      border-radius: 9999px;
      text-decoration: none !important;
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.32);
      cursor: pointer;
      transition: transform 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
    }}
    .pseo-pin-save-btn:hover {{
      background-color: #BD081C !important;
      transform: scale(1.05);
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
      color: #FFFFFF !important;
    }}
    .pseo-img-wrapper {{
      position: relative;
      display: block;
      margin: 1.5rem 0;
    }}
    .pseo-img-wrapper img {{
      display: block;
      width: 100%;
      height: auto;
      border-radius: 0.75rem;
    }}

    .pseo-related-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }}

    @media (min-width: 768px) {{
      .pseo-related-grid {{
        grid-template-columns: repeat(3, 1fr);
      }}
    }}

    .pseo-card {{
      background-color: var(--pseo-card-bg);
      border: 1px solid var(--pseo-card-border);
      border-radius: 1rem;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: box-shadow 0.2s ease, transform 0.2s ease;
    }}

    .pseo-card:hover {{
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.06);
      transform: translateY(-2px);
    }}

    .pseo-pills-bar {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      overflow-x: auto;
      padding: 0.25rem 0;
      scrollbar-width: none;
    }}
    .pseo-pills-bar::-webkit-scrollbar {{
      display: none;
    }}

    .pseo-pill {{
      display: inline-block;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 500;
      background-color: #F5F5F4;
      color: #44403C;
      white-space: nowrap;
      transition: background-color 0.15s ease, color 0.15s ease;
    }}

    .pseo-pill:hover {{
      background-color: #E7E5E4;
      color: #1C1917;
    }}

    .pseo-footer {{
      background-color: #FFFFFF;
      border-top: 1px solid var(--pseo-card-border);
      padding: 2rem 0;
      margin-top: auto;
      text-align: center;
      font-size: 0.875rem;
      color: #78716C;
    }}

    /* --- Programmatic SEO Styling --- */
    .pseo-toc-box {{
      scroll-margin-top: 5rem;
    }}
    .pseo-toc-link:hover {{
      background: #FFFFFF !important;
      border-color: var(--pseo-accent) !important;
      color: var(--pseo-accent) !important;
      transform: translateY(-1px);
    }}
    .pseo-faq-item[open] .pseo-faq-toggle {{
      transform: rotate(45deg);
    }}
    .pseo-faq-item[open] {{
      border-color: var(--pseo-accent) !important;
      box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }}
    .pseo-custom-logo {{
      transition: opacity 0.2s ease, transform 0.2s ease;
    }}
    .pseo-custom-logo:hover {{
      opacity: 0.92;
      transform: scale(1.02);
    }}

    /* --- Blogger Header, Sticky Nav & Mobile Optimization --- */
    .pseo-blogger-header {{
      position: sticky;
      top: 0;
      z-index: 50;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--pseo-card-border);
      transition: box-shadow 0.2s ease;
    }}

    .pseo-announcement-bar {{
      background: #FAF8F5;
      border-bottom: 1px solid rgba(0, 0, 0, 0.05);
      padding: 0.4rem 0;
      font-size: 0.72rem;
      color: #78716C;
    }}

    .pseo-brand-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.85rem 0 0.5rem 0;
      gap: 1rem;
    }}

    .pseo-brand-link {{
      display: inline-flex;
      align-items: center;
      gap: 0.75rem;
      text-decoration: none;
      color: inherit;
    }}

    .pseo-breadcrumb-nav {{
      font-size: 0.72rem;
      color: #78716C;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .pseo-byline {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.85rem;
      padding: 0.85rem 1.15rem;
      background: #FFFFFF;
      border: 1px solid var(--pseo-card-border);
      border-radius: 0.85rem;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
    }}

    .pseo-byline-avatar {{
      width: 2.25rem;
      height: 2.25rem;
      border-radius: 9999px;
      background: var(--pseo-accent);
      color: #FFFFFF;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 0.8rem;
      flex-shrink: 0;
      border: 2px solid #FAF8F5;
      box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    }}

    /* --- Multi-Column Rich Blogger Footer --- */
    .pseo-blogger-footer {{
      background: #FFFFFF;
      border-top: 1px solid var(--pseo-card-border);
      padding: 3.5rem 0 2rem 0;
      margin-top: auto;
      font-size: 0.85rem;
      color: #64748B;
    }}

    .pseo-footer-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 2.5rem;
      margin-bottom: 2.5rem;
    }}

    @media (min-width: 640px) {{
      .pseo-footer-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
    }}

    @media (min-width: 1024px) {{
      .pseo-footer-grid {{
        grid-template-columns: 1.4fr 1fr 1fr 1.4fr;
      }}
    }}

    .pseo-footer-col {{
      display: flex;
      flex-direction: column;
    }}

    .pseo-footer-bio {{
      font-size: 0.8rem;
      line-height: 1.6;
      color: #64748B;
      margin-bottom: 1rem;
    }}

    .pseo-footer-social {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}

    .pseo-social-chip {{
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      font-size: 0.72rem;
      font-weight: 600;
      color: #475569;
      background: #F1F5F9;
      padding: 0.3rem 0.65rem;
      border-radius: 0.375rem;
      text-decoration: none;
      transition: background 0.15s ease, color 0.15s ease;
    }}
    .pseo-social-chip:hover {{
      background: #E2E8F0;
      color: #0F172A;
    }}

    .pseo-footer-title {{
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--pseo-text);
      margin-bottom: 0.85rem;
    }}

    .pseo-footer-links {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }}

    .pseo-footer-links a {{
      color: #64748B;
      text-decoration: none;
      font-size: 0.82rem;
      transition: color 0.15s ease;
    }}

    .pseo-footer-links a:hover {{
      color: var(--pseo-accent);
    }}

    .pseo-footer-newsletter-desc {{
      font-size: 0.8rem;
      line-height: 1.5;
      color: #64748B;
      margin-bottom: 0.75rem;
    }}

    .pseo-newsletter-form {{
      display: flex;
      gap: 0.5rem;
      align-items: stretch;
      width: 100%;
    }}

    .pseo-newsletter-input {{
      flex: 1;
      min-width: 0;
      padding: 0.6rem 0.75rem;
      border: 1px solid var(--pseo-card-border);
      border-radius: 0.5rem;
      font-size: 0.8rem;
      background: #FAF8F5;
      color: var(--pseo-text);
      outline: none;
    }}
    .pseo-newsletter-input:focus {{
      border-color: var(--pseo-accent);
      background: #FFFFFF;
    }}

    .pseo-newsletter-btn {{
      background: var(--pseo-accent);
      color: #FFFFFF;
      border: none;
      border-radius: 0.5rem;
      padding: 0.6rem 0.95rem;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      transition: opacity 0.2s;
    }}
    .pseo-newsletter-btn:hover {{
      opacity: 0.9;
    }}

    .pseo-footer-bottom {{
      border-top: 1px solid var(--pseo-card-border);
      padding-top: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      font-size: 0.75rem;
      color: #94A3B8;
    }}

    @media (min-width: 768px) {{
      .pseo-footer-bottom {{
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
      }}
    }}

    .pseo-footer-disclosure {{
      font-size: 0.72rem;
      color: #94A3B8;
      margin-top: 0.25rem;
      max-width: 640px;
      line-height: 1.5;
    }}

    .pseo-back-to-top {{
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      font-size: 0.75rem;
      font-weight: 600;
      color: #64748B;
      text-decoration: none;
      padding: 0.4rem 0.75rem;
      border: 1px solid var(--pseo-card-border);
      border-radius: 0.375rem;
      background: #FAFAFA;
      transition: background 0.15s ease;
    }}
    .pseo-back-to-top:hover {{
      background: #F4F4F5;
      color: var(--pseo-text);
    }}

    """



def _detect_custom_logo(path_prefix: str = "") -> tuple[str, bool]:
    """Checks if a user-uploaded custom logo exists in assets/images/."""
    assets_dir = os.path.abspath(os.path.join("assets", "images"))
    if os.path.exists(assets_dir):
        for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
            filename = f"custom-logo{ext}"
            full_p = os.path.join(assets_dir, filename)
            if os.path.exists(full_p) and os.path.getsize(full_p) > 64:
                prefix = path_prefix.rstrip("/") if path_prefix else ""
                return (f"{prefix}/assets/images/{filename}" if prefix else f"/assets/images/{filename}"), True
    return "", False


def render_blogger_logo(
    brand_name: str = "ANNADECO",
    theme_tokens: Optional[dict[str, str]] = None,
    compact: bool = False,
    path_prefix: str = "",
    custom_logo_url: str = "",
    tagline: str = "",
) -> str:
    """Renders a responsive, razor-sharp logo brand mark: custom uploaded image if available, else vector SVG emblem."""
    theme = theme_tokens or {}
    accent = theme.get("accent", "#D97706")
    text_color = theme.get("text_body", "#1C1917")
    home_url = f"{path_prefix}/" if path_prefix else "/"
    initials = html_lib.escape(brand_name[:2].upper() if brand_name else "AD")
    clean_brand = brand_name.strip() if brand_name else "ANNADECO"
    clean_tagline = tagline.strip() if tagline else ("Interiors Journal" if compact else "Home · Interiors · Living")

    if not custom_logo_url:
        detected_url, has_custom = _detect_custom_logo(path_prefix)
        if has_custom:
            custom_logo_url = detected_url

    if custom_logo_url:
        img_h = "32" if compact else "38"
        font_sz = "1.15rem" if compact else "1.35rem"
        return f"""<a href="{home_url}" class="pseo-brand-link" aria-label="{html_lib.escape(clean_brand)} Home">
          <img src="{custom_logo_url}" alt="{html_lib.escape(clean_brand)}" class="pseo-custom-logo" style="max-height:{img_h}px;width:auto;max-width:180px;object-fit:contain;flex-shrink:0;" loading="eager">
          <div style="display:flex;flex-direction:column;line-height:1.1;">
            <div style="display:flex;flex-direction:column;line-height:1.15;">
              <span style="font-family:'Playfair Display',Georgia,serif;font-weight:700;font-size:{font_sz};letter-spacing:0.12em;color:{text_color};text-transform:uppercase;">{html_lib.escape(clean_brand)}</span>
            </div>
            <span style="font-size:0.6rem;font-weight:700;letter-spacing:0.18em;color:#78716C;text-transform:uppercase;margin-top:0.15rem;">{html_lib.escape(clean_tagline)}</span>
          </div>
        </a>"""

    if compact:
        return f"""<a href="{home_url}" class="pseo-brand-link" aria-label="{html_lib.escape(clean_brand)} Home">
          <svg width="34" height="34" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
            <circle cx="50" cy="50" r="46" fill="#FAF8F5" stroke="{text_color}" stroke-width="3"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke="{accent}" stroke-width="1.5" stroke-dasharray="3 3"/>
            <path d="M 32 68 L 32 44 C 32 30, 68 30, 68 44 L 68 68 Z" stroke="{text_color}" stroke-width="2.5" fill="none"/>
            <text x="50" y="58" font-family="'Playfair Display', Georgia, serif" font-size="22" font-weight="700" fill="{text_color}" text-anchor="middle">{initials}</text>
            <circle cx="50" cy="24" r="3" fill="{accent}"/>
          </svg>
          <div style="display:flex;flex-direction:column;line-height:1.1;">
            <span style="font-family:'Playfair Display',Georgia,serif;font-weight:700;font-size:1.15rem;letter-spacing:0.12em;color:{text_color};">{html_lib.escape(clean_brand)}</span>
            <span style="font-size:0.6rem;font-weight:700;letter-spacing:0.18em;color:#78716C;text-transform:uppercase;">{html_lib.escape(clean_tagline)}</span>
          </div>
        </a>"""

    return f"""<a href="{home_url}" class="pseo-brand-link" aria-label="{html_lib.escape(clean_brand)} Home">
      <svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
        <circle cx="50" cy="50" r="46" fill="#FAF8F5" stroke="{text_color}" stroke-width="3"/>
        <circle cx="50" cy="50" r="40" fill="none" stroke="{accent}" stroke-width="1.5" stroke-dasharray="3 3"/>
        <path d="M 32 68 L 32 44 C 32 30, 68 30, 68 44 L 68 68 Z" stroke="{text_color}" stroke-width="2.5" fill="none"/>
        <path d="M 50 64 C 50 48, 50 36, 50 28" stroke="{text_color}" stroke-width="2" stroke-linecap="round"/>
        <circle cx="50" cy="24" r="3" fill="{accent}"/>
        <text x="50" y="58" font-family="'Playfair Display', Georgia, serif" font-size="20" font-weight="700" fill="{text_color}" text-anchor="middle">{initials}</text>
      </svg>
      <div style="display:flex;flex-direction:column;line-height:1.1;">
        <div style="display:flex;flex-direction:column;line-height:1.15;">
          <span style="font-family:'Playfair Display',Georgia,serif;font-weight:700;font-size:1.35rem;letter-spacing:0.14em;color:{text_color};text-transform:uppercase;">{html_lib.escape(clean_brand)}</span>
        </div>
        <span style="font-size:0.62rem;font-weight:700;letter-spacing:0.2em;color:#78716C;text-transform:uppercase;margin-top:0.15rem;">{html_lib.escape(clean_tagline)}</span>
      </div>
    </a>"""

    return f"""<a href="{home_url}" class="pseo-brand-link" aria-label="{html_lib.escape(brand_name)} Home">
      <svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
        <circle cx="50" cy="50" r="46" fill="#FAF8F5" stroke="{text_color}" stroke-width="3"/>
        <circle cx="50" cy="50" r="40" fill="none" stroke="{accent}" stroke-width="1.5" stroke-dasharray="3 3"/>
        <path d="M 32 68 L 32 44 C 32 30, 68 30, 68 44 L 68 68 Z" stroke="{text_color}" stroke-width="2.5" fill="none"/>
        <path d="M 50 64 C 50 48, 50 36, 50 28" stroke="{text_color}" stroke-width="2" stroke-linecap="round"/>
        <circle cx="50" cy="24" r="3" fill="{accent}"/>
        <text x="50" y="58" font-family="'Playfair Display', Georgia, serif" font-size="20" font-weight="700" fill="{text_color}" text-anchor="middle">{initials}</text>
      </svg>
      <div style="display:flex;flex-direction:column;line-height:1.1;">
        <div style="display:flex;align-items:center;gap:0.4rem;">
          <span style="font-family:'Playfair Display',Georgia,serif;font-weight:700;font-size:1.35rem;letter-spacing:0.14em;color:{text_color};">{html_lib.escape(brand_name)}</span>
          <span style="background:{accent};color:#FFFFFF;font-size:0.55rem;font-weight:700;padding:0.15rem 0.45rem;border-radius:9999px;letter-spacing:0.06em;text-transform:uppercase;">Journal</span>
        </div>
        <span style="font-size:0.62rem;font-weight:700;letter-spacing:0.2em;color:#78716C;text-transform:uppercase;margin-top:0.15rem;">Home &middot; Interiors &middot; Living</span>
      </div>
    </a>"""


def render_blogger_header(
    clean_domain: str,
    breadcrumb_html: str,
    pills_html: str,
    theme_tokens: dict[str, str],
    path_prefix: str = "",
    canonical_url: str = "",
    branding: Optional[Any] = None,
) -> str:
    """Renders a modern, responsive Blogger & Magazine header with sticky blur and logo."""
    brand_name = getattr(branding, "brand_name", None) or (clean_domain.split(".")[0].upper() if clean_domain else "ANNADECO")
    if brand_name in ("ANNA", "ANNADECO", "HOMESTYLESDECO", "STYLEDAYS", "STYLESDAYS"):
        brand_name = getattr(branding, "brand_name", None) or "ANNADECO"
    tagline = getattr(branding, "tagline", "") or ""
    logo_path = getattr(branding, "logo_path", "") or ""
    if logo_path and path_prefix and not logo_path.startswith(path_prefix) and not logo_path.startswith("http"):
        custom_logo_url = f"{path_prefix}/{logo_path.lstrip('/')}"
    else:
        custom_logo_url = logo_path
    accent = theme_tokens.get("accent", "#E60023")
    logo_html = render_blogger_logo(brand_name, theme_tokens, compact=False, path_prefix=path_prefix, custom_logo_url=custom_logo_url, tagline=tagline)
    home_link = f"{path_prefix}/" if path_prefix else "/"

    return f"""
  <header class="pseo-header pseo-blogger-header">
    <div class="pseo-announcement-bar">
      <div class="pseo-container" style="display:flex;align-items:center;justify-content:space-between;gap:1rem;">
        <nav aria-label="Breadcrumb" class="pseo-breadcrumb-nav">{breadcrumb_html}</nav>
        <div style="font-size:0.68rem;letter-spacing:0.08em;text-transform:uppercase;color:#A8A29E;font-weight:600;" class="hidden sm:inline">
          Editorial Architecture &amp; Interiors
        </div>
      </div>
    </div>

    <div class="pseo-container">
      <div class="pseo-brand-row">
        {logo_html}
        <nav class="pseo-nav-links hidden md:flex" style="display:flex;align-items:center;gap:1.5rem;font-size:0.8rem;font-weight:600;letter-spacing:0.02em;">
          <a href="{home_link}" style="color:#1C1917;text-decoration:none;" class="hover:opacity-75">All Guides</a>
          <a href="{home_link}#overview" style="color:#57534E;text-decoration:none;" class="hover:opacity-75">Sanctuary Edits</a>
          
          <a href="{home_link}#sourcing" style="color:#57534E;text-decoration:none;" class="hover:opacity-75">Sourcing Notes</a>
        </nav>
        <div style="display:flex;align-items:center;gap:0.6rem;">
          <a href="https://pinterest.com/" target="_blank" rel="noopener" class="pseo-header-action-btn" style="border:1px solid #E7E2DA;background:#FAF8F5;color:#1C1917;padding:0.4rem 0.95rem;border-radius:9999px;font-size:0.72rem;font-weight:700;display:inline-flex;align-items:center;gap:0.35rem;text-decoration:none;">
            <span>&#x1F4CC; Save Ideas</span>
          </a>
        </div>
      </div>

      {pills_html}
    </div>
  </header>
  """


def render_blogger_byline(
    clean_domain: str,
    lastmod: str,
    category: str,
    theme_tokens: dict[str, str],
    canonical_url: str = "",
    author_name: str = "",
    branding: Optional[Any] = None,
) -> str:
    """Renders the top author byline & reading meta block for authentic blogger aesthetics."""
    brand_name = getattr(branding, "brand_name", "") or "AnnaDeco"
    if brand_name in ("ANNA", "HOMESTYLESDECO", "STYLEDAYS", "STYLESDAYS"):
        brand_name = "AnnaDeco"
    display_author = author_name.strip() if author_name else (getattr(branding, "author_name", "") or f"{brand_name} Studio")
    accent = theme_tokens.get("accent", "#E60023")
    formatted_date = (lastmod or "2026-11-02")[:10]
    pin_url = f"https://pinterest.com/pin/create/button/?url={urllib.parse.quote(canonical_url)}" if canonical_url else "https://pinterest.com/"
    initials = html_lib.escape(brand_name[:2].upper() if brand_name else "AD")

    return f"""
    <div class="pseo-byline">
      <div style="display:flex;align-items:center;gap:0.75rem;">
        <div class="pseo-byline-avatar">{initials}</div>
        <div>
          <div style="font-size:0.82rem;font-weight:700;color:#1C1917;">
            Curated by <span style="text-decoration:underline;text-decoration-color:{accent};">{html_lib.escape(display_author)}</span>
          </div>
          <div style="font-size:0.7rem;color:#78716C;display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;margin-top:0.15rem;">
            <span>&#x23F1; 6 min read</span>
            <span>&middot;</span>
            <span>Updated {formatted_date}</span>
            <span>&middot;</span>
            <span style="color:#15803D;font-weight:600;">&#x2713; Editorial Verified</span>
          </div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:0.5rem;">
        <a href="{pin_url}" target="_blank" rel="noopener" class="pseo-byline-pin-btn" style="background:#FFF1F2;color:{accent};border:1px solid #FECDD3;padding:0.35rem 0.75rem;border-radius:9999px;font-size:0.72rem;font-weight:700;display:inline-flex;align-items:center;gap:0.3rem;text-decoration:none;">
          <span>&#x1F4CC; Save Idea</span>
        </a>
      </div>
    </div>
    """


def render_blogger_footer(
    clean_domain: str,
    theme_tokens: dict[str, str],
    path_prefix: str = "",
    branding: Optional[Any] = None,
) -> str:
    """Renders a rich multi-column blogger footer with brand manifesto, categories, and newsletter."""
    brand_name = getattr(branding, "brand_name", "") or "ANNADECO"
    if brand_name in ("ANNA", "HOMESTYLESDECO", "STYLEDAYS", "STYLESDAYS"):
        brand_name = "ANNADECO"
    tagline = getattr(branding, "tagline", "") or "Home · Interiors · Living"
    clean_brand = brand_name.strip()
    accent = theme_tokens.get("accent", "#E60023")
    logo_compact = render_blogger_logo(brand_name, theme_tokens, compact=True, path_prefix=path_prefix, tagline=tagline)
    home_link = f"{path_prefix}/" if path_prefix else "/"

    return f"""
  <footer class="pseo-footer pseo-blogger-footer">
    <div class="pseo-container">
      <div class="pseo-footer-grid">
        <!-- Col 1: Brand & Manifesto -->
        <div class="pseo-footer-col pseo-footer-brand-col">
          <div style="margin-bottom:1rem;">
            {logo_compact}
          </div>
          <p class="pseo-footer-bio">
            An independent visual archive and curated design journal exploring modern bedroom refreshes, Scandinavian minimalism, and intentional interior styling.
          </p>
          <div class="pseo-footer-social">
            <a href="https://pinterest.com/" target="_blank" rel="noopener" class="pseo-social-chip">&#x1F4CC; Pinterest</a>
            <a href="https://instagram.com/" target="_blank" rel="noopener" class="pseo-social-chip">&#x1F4F7; Instagram</a>
            <a href="{home_link}" class="pseo-social-chip">&#x1F3DB;&#xFE0F; Curated Studio</a>
          </div>
        </div>

        <!-- Col 2: Curated Editorial Hubs -->
        <div class="pseo-footer-col">
          <div class="pseo-footer-title">Curated Spaces</div>
          <ul class="pseo-footer-links">
            <li><a href="{home_link}">Sanctuary Hub Overview</a></li>
            <li><a href="{home_link}#overview">Bedroom Styling &amp; Linens</a></li>
            <li><a href="{home_link}#sourcing">Material Sourcing Notes</a></li>
            
            <li><a href="{home_link}#faq">Editorial Q&amp;A</a></li>
          </ul>
        </div>

        <!-- Col 3: Editorial Studio -->
        <div class="pseo-footer-col">
          <div class="pseo-footer-title">Editorial Studio</div>
          <ul class="pseo-footer-links">
            
            
            <li><a href="{home_link}">Architectural Spec Guides</a></li>
            <li><a href="{home_link}">Material Sourcing Standards</a></li>
            <li><a href="{home_link}">Curatorial Standards</a></li>
          </ul>
        </div>

        <!-- Col 4: The Weekly Room Edit (Newsletter) -->
        <div class="pseo-footer-col pseo-footer-newsletter-col">
          <div class="pseo-footer-title">The Weekly Room Edit</div>
          <p class="pseo-footer-newsletter-desc">
            Get handpicked bedroom makeovers, material swatches, and weekend styling guides delivered to your inbox every Friday.
          </p>
          <form class="pseo-newsletter-form" onsubmit="event.preventDefault(); var btn=this.querySelector('button'); btn.innerText='Subscribed! ✨'; btn.style.background='#15803D'; this.querySelector('input').disabled=true;">
            <input type="email" placeholder="Your email address..." required class="pseo-newsletter-input" aria-label="Email address for weekly room edit">
            <button type="submit" class="pseo-newsletter-btn">Join Edit</button>
          </form>
          <div style="font-size:0.68rem;color:#9CA3AF;margin-top:0.4rem;">Zero spam. Curated interior inspiration only.</div>
        </div>
      </div>

      <!-- Bottom Bar -->
      <div class="pseo-footer-bottom">
        <div class="pseo-footer-legal">
          <p>&copy; 2026 {html_lib.escape(clean_brand)} Lifestyle Journal. All rights reserved.</p>
          <p class="pseo-footer-disclosure">
            {html_lib.escape(clean_brand)} is an independently curated decor publication. When you purchase through our links, we may earn an affiliate commission at no extra cost to you.
          </p>
        </div>
        <div class="pseo-footer-actions">
          <a href="#" class="pseo-back-to-top" onclick="window.scrollTo({{top:0, behavior:'smooth'}}); return false;">Back to Top &#8593;</a>
        </div>
      </div>
    </div>
  </footer>
  """


def render_checklist(checklist: list[Any], slug: str, theme: dict[str, str], source_domain: str = "stylesdays.com") -> str:
    """Checklist items eliminated per Section 24 specification."""
    return ""

def render_takeaways(takeaways: list[str], theme: dict[str, str], title: str = "", category: str = "") -> str:
    """Takeaways eliminated per Section 24 specification."""
    return ""

def render_taxonomy_pills(posts: list[Any], current_slug: str, theme: dict[str, str], base_url: str = "") -> str:
    """Renders horizontal Taxonomy Switcher Pills for quick navigation."""
    candidates = []
    for p in (posts or []):
        slug = getattr(p, "slug", None) or (p.get("slug") if isinstance(p, dict) else "")
        if slug and slug != current_slug:
            title = getattr(p, "title", None) or (p.get("title") if isinstance(p, dict) else slug.replace("-", " ").title())
            web_path = getattr(p, "web_path", None) or (p.get("web_path") if isinstance(p, dict) else f"/{slug}/")
            candidates.append({"slug": slug, "title": title, "web_path": web_path})

    # If no sibling posts are present, provide default curated taxonomy navigation pills
    if not candidates:
        default_topics = [
            ("ikea-hacks", "IKEA Hacks & DIY"),
            ("closet-storage", "Closet & PAX Storage"),
            ("bedroom-design", "Bedroom Styling"),
            ("living-room", "Living Room Layouts"),
            ("guest-bedroom", "Guest Room Daybeds"),
            ("kitchen-organization", "Kitchen Organization"),
        ]
        for s, t in default_topics:
            candidates.append({"slug": s, "title": t, "web_path": f"/{s}/"})

    sample_size = min(6, len(candidates))
    selected = candidates[:sample_size]

    path_prefix = _extract_path_prefix(base_url)
    pills_html = ""
    for item in selected:
        short_title = item["title"][:28] + ("…" if len(item["title"]) > 30 else "")
        link = f"{path_prefix}{item['web_path']}" if path_prefix else item["web_path"]
        pills_html += f"""
        <a href="{link}" class="pseo-pill">{html_lib.escape(short_title)}</a>
        """

    return f"""
    <div class="pseo-pills-bar">
      <span style="font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #A8A29E; margin-right: 0.25rem; flex-shrink: 0;">Featured Guides:</span>
      {pills_html}
    </div>
    """


def render_related_guides(posts: list[Any], current_slug: str, theme: dict[str, str], base_url: str = "") -> str:
    """Renders 3-column Related Guides cards with thumbnail, title, excerpt, and link."""
    candidates = []
    for p in (posts or []):
        slug = getattr(p, "slug", None) or (p.get("slug") if isinstance(p, dict) else "")
        if slug and slug != current_slug:
            title = getattr(p, "title", None) or (p.get("title") if isinstance(p, dict) else slug.replace("-", " ").title())
            excerpt = getattr(p, "excerpt", None) or (p.get("excerpt") if isinstance(p, dict) else (p.get("description", "") if isinstance(p, dict) else ""))
            category = getattr(p, "category", None) or (p.get("category") if isinstance(p, dict) else "Home Decor")
            local_img = getattr(p, "local_image_path", None) or (p.get("local_image_path") if isinstance(p, dict) else (p.get("local_image", "") if isinstance(p, dict) else ""))
            web_path = getattr(p, "web_path", None) or (p.get("web_path") if isinstance(p, dict) else f"/{slug}/")
            candidates.append({
                "slug": slug,
                "title": title,
                "excerpt": excerpt,
                "category": category or "Home Decor",
                "image": local_img or f"/assets/images/{slug}.svg",
                "web_path": web_path,
            })

    # If no sibling posts available, provide curated fallback cards
    if not candidates:
        sample_guides = [
            ("small-walk-in-closet-ideas", "Small Walk-In Closet Ideas for Maximum Storage", "IKEA Storage", "Transform compact closets with modular shelving and lighting."),
            ("ikea-kallax-nursery-storage", "IKEA Kallax Nursery Storage Transformations", "IKEA Hacks", "Smart bin organizers and wooden top additions for baby nurseries."),
            ("minimalist-bedroom-styling", "Minimalist Scandinavian Bedroom Styling Tips", "Bedroom Ideas", "Clean lines, breathable linen bedding, and calming neutral palettes."),
        ]
        for s, t, cat, exc in sample_guides:
            candidates.append({
                "slug": s,
                "title": t,
                "excerpt": exc,
                "category": cat,
                "image": f"/assets/images/{s}.svg",
                "web_path": f"/{s}/",
            })

    sample_size = min(3, len(candidates))
    selected = candidates[:sample_size]

    path_prefix = _extract_path_prefix(base_url)
    cards_html = ""
    for c in selected:
        link = f"{path_prefix}{c['web_path']}" if path_prefix else c["web_path"]
        img_src = c["image"]
        if not img_src.startswith("http"):
            clean_rel_img = img_src.lstrip("/")
            img_src = f"{path_prefix}/{clean_rel_img}" if path_prefix else f"/{clean_rel_img}"
        fallback_svg = _resolve_fallback_svg(c["slug"], path_prefix)

        cards_html += f"""
        <article class="pseo-card group">
          <a href="{link}" style="display: flex; flex-direction: column; height: 100%;">
            <div class="pseo-hero-media">
              <img src="{img_src}" alt="{html_lib.escape(c['title'])}" width="600" height="375" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='{fallback_svg}';">
              <span class="pseo-badge" style="position: absolute; top: 0.75rem; left: 0.75rem; background-color: rgba(255, 255, 255, 0.95); color: #1C1917; font-size: 0.625rem;">
                {html_lib.escape(c['category'])}
              </span>
            </div>
            <div style="padding: 1.25rem; flex: 1 0 auto;">
              <h3 class="font-serif-editorial text-base sm:text-lg font-bold text-stone-900 group-hover:text-[{theme['accent']}]" style="margin-bottom: 0.5rem; transition: color 0.15s ease;">
                {html_lib.escape(c['title'])}
              </h3>
              <p class="text-xs text-stone-500" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                {html_lib.escape(c['excerpt'][:120])}...
              </p>
            </div>
            <div style="padding: 0.75rem 1.25rem; background-color: #FAFAFA; border-top: 1px solid var(--pseo-card-border); display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem; font-weight: 500; color: #78716C;">
              <span>Read Guide</span>
              <span style="color: {theme['accent']}; font-weight: 700;">→</span>
            </div>
          </a>
        </article>
        """

    return f"""
    <section style="margin-top: 3.5rem; padding-top: 2.5rem; border-top: 1px solid var(--pseo-card-border);">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
        <h2 class="font-serif-editorial text-2xl font-bold text-stone-900">Related Guides &amp; Inspiration</h2>
      </div>
      <div class="pseo-related-grid">
        {cards_html}
      </div>
    </section>
    """


def build_fallback_schema(post: Any, base_url: str, source_domain: str) -> str:
    """Builds valid JSON-LD schema with Article and BreadcrumbList if app.seo is not available."""
    slug = getattr(post, "slug", None) or (post.get("slug") if isinstance(post, dict) else "")
    title = getattr(post, "title", None) or (post.get("title") if isinstance(post, dict) else slug.replace("-", " ").title())
    excerpt = getattr(post, "excerpt", None) or (post.get("excerpt") if isinstance(post, dict) else (post.get("description", "") if isinstance(post, dict) else ""))
    web_path = getattr(post, "web_path", None) or (post.get("web_path") if isinstance(post, dict) else f"/{slug}/")
    img = getattr(post, "local_image_path", None) or (post.get("local_image_path") if isinstance(post, dict) else (post.get("local_image", "") if isinstance(post, dict) else ""))
    category = getattr(post, "category", None) or (post.get("category") if isinstance(post, dict) else "Home Decor")
    lastmod = getattr(post, "modified", None) or getattr(post, "date", None) or (post.get("modified") if isinstance(post, dict) else (post.get("lastmod", "2026-10-29") if isinstance(post, dict) else "2026-10-29"))

    base = base_url.rstrip("/") if base_url else "https://home-organization.github.io"
    full_url = f"{base}{web_path}"
    full_img = img if img.startswith("http") else f"{base}{img if img.startswith('/') else '/' + img}"

    breadcrumbs = [
        {"@type": "ListItem", "position": 1, "name": "Editorial Hub", "item": f"{base}/"},
    ]
    if category and web_path.count("/") > 2:
        parent_seg = web_path.strip("/").split("/")[0]
        breadcrumbs.append({
            "@type": "ListItem",
            "position": 2,
            "name": category,
            "item": f"{base}/{parent_seg}/",
        })
        breadcrumbs.append({
            "@type": "ListItem",
            "position": 3,
            "name": title,
            "item": full_url,
        })
    else:
        breadcrumbs.append({
            "@type": "ListItem",
            "position": 2,
            "name": title,
            "item": full_url,
        })

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": title,
                "description": excerpt,
                "image": [full_img],
                "datePublished": (lastmod or "2026-10-29")[:10],
                "dateModified": (lastmod or "2026-10-29")[:10],
                "author": {
                    "@type": "Organization",
                    "name": f"{source_domain} Editorial Team",
                    "url": f"https://{source_domain}/",
                },
                "publisher": {
                    "@type": "Organization",
                    "name": f"{source_domain} Editorial Hub",
                    "url": base,
                },
                "mainEntityOfPage": {
                    "@type": "WebPage",
                    "@id": full_url,
                },
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": breadcrumbs,
            },
        ],
    }
    return json.dumps(schema, indent=2)




# =============================================================================
def render_toc(slug: str, theme_tokens: dict[str, str], layout_theme: str = "editorial-warm") -> str:
    """Table of Contents eliminated per Section 25 specification."""
    return ""

def render_faq_section(
    title: str,
    category: str,
    clean_domain: str,
    theme_tokens: dict[str, str],
    canonical_url: str = "",
) -> str:
    """Renders 4 high-value semantic Q&As with companion Schema.org FAQPage structured data."""
    accent = theme_tokens.get("accent", "#E60023")
    cat_clean = category or "Interior Decor"
    title_clean = title or "Room Refresh"

    faqs = [
        {
            "q": f"How can I recreate this {cat_clean} look in a small space?",
            "a": f"When adapting {title_clean} for compact rooms, prioritize multi-functional modular pieces, open floor sightlines, and vertical wall storage. Incorporating 2700K warm neutral lighting and floor-to-ceiling linen drapery will instantly create the illusion of heightened volume.",
        },
        {
            "q": f"What materials and textures define this style?",
            "a": f"This aesthetic combines breathable, tactile textures such as washed Belgian linen, raw white oak, matte ceramics, and ribbed bouclé with minimalist hardware. Avoid high-gloss synthetics in favor of natural, organic surfaces.",
        },
        {
            "q": f"Where can I find direct furniture sourcing and material specs?",
            "a": f"All specific room dimensions, paint swatch codes, and furniture sourcing references are detailed directly in our editorial notes above with recommended suppliers and artisan makers.",
        },
        {
            "q": f"Are the styling moodboards and guides printable or saveable to Pinterest?",
            "a": f"Yes! Every room image is high-resolution Pinterest-optimized (16:10 format). You can click our 'Save to Board' badge to pin immediately, and browse through our curated design guides in real time.",
        },
    ]

    faq_items_html = ""
    for idx, item in enumerate(faqs):
        q_esc = html_lib.escape(item["q"])
        a_esc = html_lib.escape(item["a"])
        faq_items_html += f"""
        <details class="pseo-faq-item" style="border:1px solid var(--pseo-card-border);border-radius:0.75rem;background:#FFFFFF;margin-bottom:0.75rem;overflow:hidden;" {"open" if idx == 0 else ""}>
          <summary class="pseo-faq-summary" style="display:flex;align-items:center;justify-content:space-between;padding:1rem 1.25rem;font-size:0.9rem;font-weight:700;color:#1C1917;cursor:pointer;list-style:none;user-select:none;">
            <span>{q_esc}</span>
            <span class="pseo-faq-toggle" style="color:{accent};font-size:1.1rem;font-weight:700;transition:transform 0.2s;">+</span>
          </summary>
          <div class="pseo-faq-answer" style="padding:0 1.25rem 1.15rem 1.25rem;font-size:0.82rem;line-height:1.65;color:#475569;border-top:1px solid rgba(0,0,0,0.04);">
            <p>{a_esc}</p>
          </div>
        </details>
        """

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["q"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["a"],
                },
            }
            for item in faqs
        ],
    }
    faq_schema_json = json.dumps(faq_schema, indent=2)

    return f"""
    <section class="pseo-faq-section" id="faq" style="margin:2.5rem 0;">
      <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;">
        <span style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:{accent};background:rgba(0,0,0,0.04);padding:0.25rem 0.6rem;border-radius:9999px;">Got Questions?</span>
      </div>
      <h2 style="font-family:var(--pseo-font-headline);font-size:1.35rem;font-weight:700;color:#1C1917;margin-bottom:1.25rem;">
        Frequently Asked Styling &amp; Sourcing Questions
      </h2>
      <div class="pseo-faq-list">
        {faq_items_html}
      </div>
      <script type="application/ld+json">
{faq_schema_json}
      </script>
    </section>
    """


def render_eeat_box(
    author_name: str = "Anna Lindqvist",
    author_bio: str = "Senior Interior Architect & Kinfolk Stylist",
    clean_domain: str = "stylesdays.com",
    theme_tokens: Optional[dict[str, str]] = None,
    lastmod: str = "",
) -> str:
    """Renders an authoritative Google E-E-A-T editorial trust card."""
    theme = theme_tokens or {}
    accent = theme.get("accent", "#E60023")
    author_clean = author_name.strip() if author_name else "Anna Lindqvist"
    bio_clean = author_bio.strip() if author_bio else "Senior Interior Architect & Kinfolk Stylist with 12+ years in curated Scandinavian living."
    initials = "".join([p[0].upper() for p in author_clean.split()[:2]]) if author_clean else "AL"
    rev_date = (lastmod or "2026-11-02")[:10]

    return f"""
    <aside class="pseo-eeat-box" style="background:#FAF8F5;border:1px solid var(--pseo-card-border);border-radius:1rem;padding:1.35rem;margin:2rem 0;box-shadow:0 2px 6px rgba(0,0,0,0.02);">
      <div style="display:flex;align-items:flex-start;gap:1rem;flex-wrap:wrap;">
        <div style="width:3rem;height:3rem;border-radius:9999px;background:{accent};color:#FFFFFF;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.05rem;flex-shrink:0;box-shadow:0 2px 6px rgba(0,0,0,0.1);">
          {initials}
        </div>
        <div style="flex:1;min-width:240px;">
          <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.25rem;">
            <span style="font-weight:700;font-size:0.95rem;color:#1C1917;">{html_lib.escape(author_clean)}</span>
            <span style="background:#15803D;color:#FFFFFF;font-size:0.6rem;font-weight:700;padding:0.15rem 0.5rem;border-radius:9999px;letter-spacing:0.04em;">&#x2713; Verified Expert</span>
          </div>
          <div style="font-size:0.75rem;color:#78716C;margin-bottom:0.5rem;">{html_lib.escape(bio_clean)}</div>
          <div style="display:flex;align-items:center;gap:0.75rem;font-size:0.7rem;color:#64748B;flex-wrap:wrap;border-top:1px solid rgba(0,0,0,0.06);padding-top:0.5rem;">
            <span>Reviewed &amp; Fact-Checked: <strong>{rev_date}</strong></span>
            <span>&middot;</span>
            <span>Editorial Standards: <strong>Independent Curatorial Review</strong></span>
            <span>&middot;</span>
            <span>Independent Curation</span>
          </div>
        </div>
      </div>
    </aside>
    """

# THEME LAYOUT RENDERERS — 3 Distinct Design Systems
# Each function returns a complete, standalone HTML page with embedded CSS.
# =============================================================================


def render_editorial_warm_layout(
    slug: str, title: str, excerpt: str, category: str, lastmod: str,
    image_src: str, fallback_svg: str, canonical_url: str, clean_domain: str,
    pills_html: str, takeaways_html: str, checklist_html: str, related_html: str,
    schema_json: str, fallback_css: str, breadcrumb_html: str,
    theme_tokens: dict, path_prefix: str,
    toc_html: str = "", faq_html: str = "", eeat_html: str = "",
    branding: Optional[Any] = None,
    content_html: str = "",
) -> str:
    """Kinfolk Lifestyle Journal: warm linen editorial, Playfair drop-caps, sourcing notes."""
    accent = theme_tokens["accent"]
    esc_title = html_lib.escape(title)
    esc_excerpt = html_lib.escape(excerpt)
    esc_category = html_lib.escape(category)
    esc_canonical = html_lib.escape(canonical_url)
    author_name = getattr(branding, "author_name", "") if branding else ""
    clean_brand = getattr(branding, "brand_name", "") or "ANNADECO"
    clean_brand = getattr(branding, "brand_name", "") or "ANNADECO"
    clean_brand = getattr(branding, "brand_name", "") or "ANNADECO"
    pin_target_url = urllib.parse.quote(canonical_url, safe="") if canonical_url else ""
    pin_media_url = urllib.parse.quote(image_src, safe="") if image_src else ""
    pin_title = urllib.parse.quote(title, safe="") if title else ""
    pin_href = f"https://www.pinterest.com/pin/create/button/?url={pin_target_url}&media={pin_media_url}&description={pin_title}"
    header_html = render_blogger_header(clean_domain, breadcrumb_html, pills_html, theme_tokens, path_prefix=path_prefix, canonical_url=canonical_url, branding=branding)
    byline_html = render_blogger_byline(clean_domain, lastmod, esc_category, theme_tokens, canonical_url=canonical_url, author_name=author_name, branding=branding)
    footer_html = render_blogger_footer(clean_domain, theme_tokens, path_prefix=path_prefix, branding=branding)
    if content_html and len(content_html.strip()) > 20:
        article_body_html = f'<div class="ns-prose pseo-article-body" style="margin:2rem 0;font-size:1rem;line-height:1.75;color:#334155;">{content_html}</div>'
    else:
        article_body_html = f'<p class="ns-prose pseo-article-body" style="margin:2rem 0;font-size:1rem;line-height:1.75;color:#334155;">Curated architectural specifications and styling guide for {esc_title}.</p>'
    drop_excerpt = html_lib.escape(excerpt[:200]) + ("..." if len(excerpt) > 200 else "")
    if content_html and len(content_html.strip()) > 20:
        article_body_html = f'<div class="ew-prose pseo-article-body" style="margin:2rem 0;font-size:1.05rem;line-height:1.85;color:#292524;">{content_html}</div>'
    else:
        article_body_html = f'<p class="text-stone-700 text-base leading-relaxed ew-drop-cap" style="margin-bottom:2rem;">Curated design concepts and styling specifications for {esc_title}.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc_title} | {html_lib.escape(clean_brand)} Lifestyle Journal</title>
  <meta name="description" content="{esc_excerpt}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{esc_canonical}">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{esc_title}">
  <meta property="og:description" content="{esc_excerpt}">
  <meta property="og:image" content="{image_src}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="pinterest-rich-pin" content="true">
  <script type="application/ld+json">
{schema_json}
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
{fallback_css}
    body {{ background-color: #FAF8F5; }}
    .ew-canvas {{ max-width: 780px; margin: 0 auto; padding: 0 1rem 4rem; }}
    .ew-paper {{
      background: #FFFFFF;
      border: 1px solid #E7E2DA;
      border-radius: 1.75rem;
      overflow: hidden;
      box-shadow: 0 12px 32px rgba(28,25,23,0.06), 0 2px 8px rgba(28,25,23,0.03);
    }}
    .ew-hero {{ position: relative; aspect-ratio: 16/10; overflow: hidden; }}
    .ew-hero img {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.6s ease; }}
    .ew-hero:hover img {{ transform: scale(1.02); }}
    .ew-body {{ padding: 2.5rem 2.5rem 3rem; }}
    @media (max-width: 600px) {{ .ew-body {{ padding: 1.5rem 1.25rem 2rem; }} }}
    .ew-kicker {{
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: #A8A29E;
      margin-bottom: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .ew-kicker::before {{ content: ''; display: inline-block; width: 24px; height: 1px; background: #D6D3D1; }}
    .ew-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: clamp(1.75rem, 4vw, 2.75rem);
      font-weight: 700;
      line-height: 1.2;
      color: #1C1917;
      margin-bottom: 1.25rem;
    }}
    .ew-lede {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.05rem;
      font-style: italic;
      color: #44403C;
      line-height: 1.7;
      margin-bottom: 2rem;
      padding-left: 1.25rem;
      border-left: 3px solid {accent};
    }}
    .ew-drop-cap::first-letter {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 4.5rem;
      font-weight: 700;
      float: left;
      line-height: 0.78;
      margin: 0.1rem 0.15rem 0 0;
      color: #1C1917;
    }}
    .ew-sourcing-box {{
      background: #F5F0E8;
      border: 1px solid #E7DFC9;
      border-radius: 1rem;
      padding: 1.5rem;
      margin: 2rem 0;
    }}
    .ew-sourcing-label {{
      font-size: 0.6rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: #A8A29E;
      margin-bottom: 0.5rem;
    }}
    .ew-sourcing-title {{
      font-family: 'Playfair Display', serif;
      font-weight: 600;
      font-size: 0.95rem;
      color: #1C1917;
      margin-bottom: 0.75rem;
    }}
    .ew-sourcing-row {{
      display: flex;
      justify-content: space-between;
      font-size: 0.78rem;
      padding: 0.4rem 0;
      border-bottom: 1px solid rgba(0,0,0,0.06);
      color: #44403C;
      gap: 1rem;
    }}
    .ew-sourcing-row:last-child {{ border-bottom: none; }}
    .ew-sourcing-key {{ font-weight: 600; color: #1C1917; white-space: nowrap; }}
    .ew-cta {{
      background: #FAF5ED;
      border: 1px solid #E7DFC9;
      border-radius: 1rem;
      padding: 1.5rem;
      margin: 2rem 0;
    }}
    .ew-btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: #1C1917;
      color: #FAF8F5 !important;
      font-size: 0.8rem;
      font-weight: 700;
      padding: 0.75rem 1.5rem;
      border-radius: 0.625rem;
      transition: background 0.2s;
      margin-top: 0.75rem;
      text-decoration: none;
    }}
    .ew-btn:hover {{ background: #44403C; }}
  </style>
</head>
<body>
{header_html}

  <main class="ew-canvas pseo-main">
    <div class="ew-paper">
      <div class="ew-hero" id="overview" style="position:relative;">
        <img src="{image_src}" alt="{esc_title}" width="1200" height="750" fetchpriority="high" decoding="async" onerror="this.onerror=null;this.src='{fallback_svg}';">
        <div style="position:absolute;top:1rem;left:1rem;z-index:20;">
          <span class="pseo-badge" style="background:rgba(255,255,255,0.95);color:#1C1917;border:1px solid #E7E2DA;">{esc_category}</span>
        </div>
        <a href="{pin_href}" target="_blank" rel="noopener noreferrer" class="pseo-pin-save-btn" title="Save to Pinterest">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg>
          <span>Save</span>
        </a>
      </div>

      <div class="ew-body">
        <div class="ew-kicker">{esc_category} &nbsp;&middot;&nbsp; Updated {(lastmod or "2026")[:10]}</div>
        <h1 class="ew-title">{esc_title}</h1>
        {byline_html}
        


        {article_body_html}



        


      </div>
    </div>

    
    <div id="related">{related_html}</div>
  </main>

{footer_html}
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      var articleImgs = document.querySelectorAll(".pseo-article-body img");
      var pageUrl = encodeURIComponent(window.location.href);
      var pageTitle = encodeURIComponent(document.title || "");
      articleImgs.forEach(function(img) {{
        if (img.closest(".pseo-img-wrapper")) return;
        var wrapper = document.createElement("div");
        wrapper.className = "pseo-img-wrapper";
        wrapper.style.position = "relative";
        wrapper.style.display = "block";
        wrapper.style.margin = "1.5rem 0";
        
        var pinBtn = document.createElement("a");
        pinBtn.className = "pseo-pin-save-btn";
        var mediaSrc = encodeURIComponent(img.src || img.getAttribute("src") || "");
        pinBtn.href = "https://www.pinterest.com/pin/create/button/?url=" + pageUrl + "&media=" + mediaSrc + "&description=" + pageTitle;
        pinBtn.target = "_blank";
        pinBtn.rel = "noopener noreferrer";
        pinBtn.title = "Save to Pinterest";
        pinBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg><span>Save</span>';
        
        img.parentNode.insertBefore(wrapper, img);
        wrapper.appendChild(img);
        wrapper.appendChild(pinBtn);
      }});
    }});
  </script>
</body>
</html>"""


def render_nordic_studio_layout(
    slug: str, title: str, excerpt: str, category: str, lastmod: str,
    image_src: str, fallback_svg: str, canonical_url: str, clean_domain: str,
    pills_html: str, takeaways_html: str, checklist_html: str, related_html: str,
    schema_json: str, fallback_css: str, breadcrumb_html: str,
    theme_tokens: dict, path_prefix: str,
    toc_html: str = "", faq_html: str = "", eeat_html: str = "",
    branding: Optional[Any] = None,
    content_html: str = "",
) -> str:
    """The Nordroom: Scandinavian Minimalist 740px Centered Reading Column."""
    accent = theme_tokens.get("accent", "#8C6D53")
    esc_title = html_lib.escape(title)
    esc_excerpt = html_lib.escape(excerpt)
    esc_category = html_lib.escape(category or "Home Tour")
    esc_canonical = html_lib.escape(canonical_url)
    
    brand_clean = getattr(branding, "brand_name", "") or "THE NORDROOM"
    author_name = getattr(branding, "author_name", "") or "Rachel"
    author_bio = getattr(branding, "author_bio", "") or "Creator of The Nordroom • Interior design specialist passionate about Scandinavian homes, architectural renovations, and spatial curation."
    home_link = f"{path_prefix}/" if path_prefix else "/"
    
    pin_target_url = urllib.parse.quote(canonical_url, safe="") if canonical_url else ""
    pin_media_url = urllib.parse.quote(image_src, safe="") if image_src else ""
    pin_title = urllib.parse.quote(title, safe="") if title else ""
    pin_href = f"https://www.pinterest.com/pin/create/button/?url={pin_target_url}&media={pin_media_url}&description={pin_title}"

    # Extract year
    year_val = "2026"
    if lastmod and len(lastmod) >= 4 and lastmod[:4].isdigit():
        year_val = lastmod[:4]

    # Clean body prose: zero fake robot checklists!
    if content_html and len(content_html.strip()) > 20:
        article_body_html = f'<div class="nordroom-prose pseo-article-body">{content_html}</div>'
    else:
        article_body_html = f'''
        <div class="nordroom-prose pseo-article-body">
          <p>Discovering intentional simplicity begins with decluttering the visual field. In this curated guide for {esc_title}, we explore how natural light, warm oak joinery, and tactual limewash surfaces combine to establish an acoustic and architectural retreat within the modern home.</p>
          <p>Scandinavian interior design is grounded in the philosophy that beauty and function are inseparable companions. By selecting materials that age with grace—such as untreated linen, Roman travertine, and brushed brass—rooms gain a tranquil permanence that outlasts shifting trends.</p>
          <p>Whether reconfiguring an urban apartment or refreshing a light-filled country cottage, the key lies in deliberate negative space: leaving intentional room between objects so architectural character can breathe freely.</p>
        </div>
        '''

    # Conditional Material & Design Notes (ONLY if real takeaways exist - zero fake robot checklists!)
    specs_card_html = ""
    if takeaways_html and takeaways_html.strip():
        specs_card_html = f'''
        <div class="my-8 p-6 bg-[#FBFBFA] border border-[#EBEBEA] rounded-lg">
          <div class="flex items-center gap-2 mb-3">
            <span class="text-xs font-semibold tracking-widest uppercase text-[#8C6D53]">Scandinavian Design Notes & Material Palette</span>
          </div>
          {takeaways_html}
        </div>
        '''

    # Related Guides (3-card grid)
    related_section_html = ""
    if related_html and related_html.strip():
        related_section_html = f'''
        <section class="mt-14 pt-8 border-t border-[#EBEBEA]">
          <span class="text-[11px] tracking-[0.2em] uppercase font-semibold text-[#8C6D53] block mb-1">Curated Reading</span>
          <h2 class="font-serif text-2xl font-bold text-[#1C1C1C] mb-6">More Scandinavian Living Inspiration</h2>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {related_html}
          </div>
        </section>
        '''

    # Author monogram initial
    initial_char = author_name[0].upper() if author_name else "R"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc_title} | {html_lib.escape(brand_clean)}</title>
  <meta name="description" content="{esc_excerpt}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{esc_canonical}">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 100 100\'><text y=\'.9em\' font-size=\'90\'>&#x1F3E0;</text></svg>">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{esc_title}">
  <meta property="og:description" content="{esc_excerpt}">
  <meta property="og:image" content="{image_src}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="pinterest-rich-pin" content="true">
  <script type="application/ld+json">
{schema_json}
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{
      background-color: #FBFBFA;
      color: #1C1C1C;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }}
    .font-serif {{
      font-family: 'Cormorant Garamond', Georgia, serif;
    }}
    .nordroom-prose {{
      font-size: 1.125rem;
      line-height: 1.85;
      color: #1C1C1C;
    }}
    .nordroom-prose p {{
      margin-bottom: 1.65rem;
    }}
    .nordroom-prose > p:first-of-type::first-letter {{
      float: left;
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-size: 3.8rem;
      line-height: 0.8;
      padding-right: 0.65rem;
      padding-top: 0.2rem;
      color: #8C6D53;
      font-weight: 700;
    }}
    .nordroom-prose blockquote {{
      border-left: 2px solid #8C6D53;
      padding: 0.75rem 0 0.75rem 1.5rem;
      margin: 2rem 0;
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-style: italic;
      font-size: 1.35rem;
      color: #1C1C1C;
      line-height: 1.5;
    }}
    .nordroom-prose img {{
      border-radius: 0.5rem;
      width: 100%;
      height: auto;
      margin: 2rem 0 0.5rem;
      border: 1px solid #EBEBEA;
    }}
    .nordroom-prose h2 {{
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-size: 1.85rem;
      font-weight: 700;
      color: #1C1C1C;
      margin: 2.5rem 0 1rem;
      line-height: 1.25;
    }}
    .nordroom-prose h3 {{
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-size: 1.45rem;
      font-weight: 600;
      color: #1C1C1C;
      margin: 2rem 0 0.75rem;
    }}
    .pseo-pin-save-btn {{
      position: absolute;
      top: 1rem;
      right: 1rem;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      background: #E60023;
      color: #FFFFFF !important;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.4rem 0.85rem;
      border-radius: 9999px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10;
      text-decoration: none;
      transition: background 0.2s, transform 0.1s;
    }}
    .pseo-pin-save-btn:hover {{
      background: #AD081B;
      transform: scale(1.04);
    }}
  </style>
</head>
<body class="flex flex-col min-h-screen">

  <!-- TOP UTILITY STRIP -->
  <div class="w-full bg-[#1C1C1C] text-white py-2 px-4 sm:px-8 text-center sm:text-left flex flex-col sm:flex-row items-center justify-between text-[11px] tracking-[0.18em] uppercase font-medium">
    <div>SCANDINAVIAN INTERIORS • HOME TOURS • DESIGN INSPIRATION</div>
    <div class="hidden sm:flex items-center gap-4 text-stone-300">
      <a href="{home_link}" class="hover:text-white transition-colors">Home Tours</a>
      <span>•</span>
      <a href="#newsletter" class="hover:text-white transition-colors">Newsletter</a>
      <span>•</span>
      <a href="https://pinterest.com" target="_blank" rel="noopener noreferrer" class="hover:text-white transition-colors">Pinterest</a>
      <span>•</span>
      <a href="{home_link}" class="hover:text-white transition-colors">About</a>
    </div>
  </div>

  <!-- CENTERED THE NORDROOM MASTHEAD -->
  <header class="w-full bg-white border-b border-[#EBEBEA] py-8 px-4 text-center">
    <div class="max-w-[1200px] mx-auto">
      <span class="text-[11px] tracking-[0.25em] uppercase text-[#8C6D53] font-semibold block mb-2">Nordic Living & Interior Architecture</span>
      <h1 class="font-serif text-4xl sm:text-5xl md:text-6xl tracking-[0.16em] font-medium text-[#1C1C1C] uppercase mb-2">
        <a href="{home_link}" class="hover:opacity-90 transition-opacity">{html_lib.escape(brand_clean)}</a>
      </h1>
      <p class="text-xs sm:text-sm text-[#686866] italic font-serif">Curated Interior Design, Space Transformations & Scandinavian Living</p>
    </div>
  </header>

  <!-- NAVIGATION BAR -->
  <nav class="w-full bg-white border-b border-[#EBEBEA] sticky top-0 z-30 shadow-xs">
    <div class="max-w-[1200px] mx-auto px-4 flex items-center justify-between overflow-x-auto py-3 gap-6 text-[12px] font-semibold tracking-[0.14em] uppercase text-[#1C1C1C]">
      <div class="flex items-center gap-6 whitespace-nowrap">
        <a href="{home_link}" class="hover:text-[#8C6D53] transition-colors">Home</a>
        <a href="{home_link}" class="hover:text-[#8C6D53] transition-colors">Living Rooms</a>
        <a href="{home_link}" class="hover:text-[#8C6D53] transition-colors">Bedrooms</a>
        <a href="{home_link}" class="hover:text-[#8C6D53] transition-colors">Kitchens</a>
        <a href="{home_link}" class="hover:text-[#8C6D53] transition-colors">Bathrooms</a>
        <a href="{home_link}" class="hover:text-[#8C6D53] transition-colors">Garden & Outdoor</a>
        <a href="{home_link}" class="hover:text-[#8C6D53] transition-colors">Small Spaces</a>
        <a href="{home_link}" class="hover:text-[#8C6D53] transition-colors">Color Trends</a>
      </div>
      <div class="hidden md:flex items-center gap-3">
        <a href="{pin_href}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-3 py-1 bg-[#E60023] hover:bg-[#AD081B] text-white rounded-full text-[11px] font-semibold tracking-normal shadow-xs transition-colors" title="Pin Article">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg>
          Save
        </a>
      </div>
    </div>
  </nav>

  <!-- MAIN ARTICLE CONTAINER (CENTERED 740PX) -->
  <main class="flex-1 w-full py-10 sm:py-14">
    <article class="w-full max-w-[740px] mx-auto px-4 sm:px-6">

      <!-- BREADCRUMB -->
      <nav class="text-[11px] uppercase tracking-widest text-[#686866] mb-4 flex items-center gap-1.5 flex-wrap">
        <a href="{home_link}" class="hover:text-[#1C1C1C] transition-colors">Home</a>
        <span>›</span>
        <span class="hover:text-[#1C1C1C] transition-colors">{esc_category}</span>
        <span>›</span>
        <span class="text-[#1C1C1C] font-semibold truncate max-w-[280px]">{esc_title}</span>
      </nav>

      <!-- CATEGORY KICKER -->
      <div class="text-[11px] tracking-[0.2em] uppercase font-semibold text-[#8C6D53] mb-3">
        {esc_category} • 5 MIN READ • UPDATED {year_val}
      </div>

      <!-- HEADLINE -->
      <h1 class="font-serif text-3xl sm:text-4xl md:text-5xl font-bold text-[#1C1C1C] leading-[1.15] mb-4 tracking-tight">
        {esc_title}
      </h1>

      <!-- SUBTITLE / LEDE -->
      <p class="font-serif italic text-lg sm:text-xl text-[#686866] leading-relaxed mb-6 pb-6 border-b border-[#EBEBEA]">
        {esc_excerpt}
      </p>

      <!-- AUTHOR BYLINE & PINTEREST SAVE BAR -->
      <div class="flex items-center justify-between gap-4 py-3 mb-8 border-b border-[#EBEBEA] flex-wrap">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-[#8C6D53] text-white flex items-center justify-center font-serif text-base font-bold shadow-xs">
            {initial_char}
          </div>
          <div>
            <span class="font-serif font-bold text-sm text-[#1C1C1C] block">By {html_lib.escape(author_name)}</span>
            <span class="text-[11px] text-[#686866]">Updated {lastmod or 'Recently'} • Spatial Curation</span>
          </div>
        </div>

        <a href="{pin_href}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#E60023] hover:bg-[#AD081B] text-white rounded-full text-xs font-semibold shadow-xs transition-colors" title="Save to Pinterest">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg>
          Save to Pinterest
        </a>
      </div>

      <!-- HERO IMAGE (16:10 RATIO) -->
      <div class="relative aspect-[16/10] overflow-hidden rounded-lg border border-[#EBEBEA] mb-3 bg-[#F4F3F0]">
        <img src="{image_src}" alt="{esc_title}" class="w-full h-full object-cover" fetchpriority="high" decoding="async" onerror="this.onerror=null;this.src='{fallback_svg}';">
        <a href="{pin_href}" target="_blank" rel="noopener noreferrer" class="pseo-pin-save-btn" title="Save to Pinterest">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg>
          Save
        </a>
      </div>
      <p class="text-[11px] text-[#686866] italic text-center mb-8">Photography & Spatial Curation via The Nordroom Archives</p>

      <!-- ARTICLE BODY -->
      {article_body_html}

      <!-- CONDITIONAL MATERIAL & DESIGN NOTES (ZERO FAKE ROBOT CHECKLISTS) -->
      {specs_card_html}

      <!-- AUTHOR BIO CARD -->
      <div class="my-10 p-6 bg-white border border-[#EBEBEA] rounded-lg flex flex-col sm:flex-row items-center sm:items-start gap-5">
        <div class="w-16 h-16 rounded-full bg-[#8C6D53] text-white flex items-center justify-center font-serif text-2xl font-bold shrink-0">
          {initial_char}
        </div>
        <div class="text-center sm:text-left">
          <span class="text-[11px] tracking-widest uppercase font-semibold text-[#8C6D53] block mb-1">Written & Curated By</span>
          <h3 class="font-serif text-xl font-bold text-[#1C1C1C] mb-2">{html_lib.escape(author_name)}</h3>
          <p class="text-xs sm:text-sm text-[#686866] leading-relaxed mb-3">
            {html_lib.escape(author_bio)}
          </p>
          <div class="flex items-center justify-center sm:justify-start gap-4 text-xs font-semibold text-[#8C6D53]">
            <a href="{home_link}" class="hover:underline">Explore More Rooms &rarr;</a>
            <a href="https://pinterest.com" target="_blank" rel="noopener noreferrer" class="hover:underline">Follow on Pinterest</a>
          </div>
        </div>
      </div>

      <!-- RELATED GUIDES -->
      {related_section_html}

    </article>
  </main>

  <!-- THE NORDROOM 4-COLUMN FOOTER -->
  <footer class="w-full bg-[#1C1C1C] text-stone-300 pt-14 pb-8 border-t border-stone-800">
    <div class="max-w-[1200px] mx-auto px-4 sm:px-8 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-10 mb-12">
      <div>
        <h4 class="font-serif text-2xl font-bold text-white mb-3 uppercase tracking-wider">{html_lib.escape(brand_clean)}</h4>
        <p class="text-xs text-stone-400 leading-relaxed mb-4">
          An internationally acclaimed interior design and Scandinavian living publication showcasing serene house tours, room layout solutions, and organic material palettes.
        </p>
        <span class="text-[11px] text-[#8C6D53] font-semibold uppercase tracking-widest block">Founded by {html_lib.escape(author_name)}</span>
      </div>
      <div>
        <h5 class="text-xs font-semibold tracking-widest uppercase text-white mb-4">Room Inspiration</h5>
        <ul class="space-y-2 text-xs text-stone-400">
          <li><a href="{home_link}" class="hover:text-white transition-colors">Living Room Ideas</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Scandinavian Bedrooms</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Kitchens & Pantries</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Garden & Outdoor Living</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Small Space Living</a></li>
        </ul>
      </div>
      <div>
        <h5 class="text-xs font-semibold tracking-widest uppercase text-white mb-4">Design Styles</h5>
        <ul class="space-y-2 text-xs text-stone-400">
          <li><a href="{home_link}" class="hover:text-white transition-colors">Nordic Warm Minimalism</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Japandi Aesthetics</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Mid-Century Modern</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Earth & Lime Wash Finishes</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Small Apartment Hacks</a></li>
        </ul>
      </div>
      <div>
        <h5 class="text-xs font-semibold tracking-widest uppercase text-white mb-4">Curate & Connect</h5>
        <p class="text-xs text-stone-400 mb-3">Join our community of 85,000+ design enthusiasts.</p>
        <div class="flex items-center gap-3 mb-4">
          <a href="https://pinterest.com" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 bg-[#E60023] hover:bg-[#AD081B] text-white rounded text-xs font-semibold">Pinterest</a>
          <a href="#newsletter" class="px-3 py-1.5 bg-stone-800 hover:bg-stone-700 text-stone-200 rounded text-xs">Newsletter</a>
        </div>
        <span class="text-[11px] text-stone-500 block">&copy; {year_val} {html_lib.escape(brand_clean)}. All Rights Reserved.</span>
      </div>
    </div>
    <div class="max-w-[1200px] mx-auto px-4 text-center text-[11px] text-stone-500 pt-6 border-t border-stone-800/80">
      Designed with pure Scandinavian minimalism • Zero robotic filler • Hand-crafted editorial curation.
    </div>
  </footer>

  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      var articleImgs = document.querySelectorAll(".nordroom-prose img");
      var pageUrl = encodeURIComponent(window.location.href);
      var pageTitle = encodeURIComponent(document.title || "");
      articleImgs.forEach(function(img) {{
        if (img.closest(".pseo-img-wrapper")) return;
        var wrapper = document.createElement("div");
        wrapper.className = "pseo-img-wrapper";
        wrapper.style.position = "relative";
        wrapper.style.display = "block";
        wrapper.style.margin = "1.5rem 0";
        
        var pinBtn = document.createElement("a");
        pinBtn.className = "pseo-pin-save-btn";
        var mediaSrc = encodeURIComponent(img.src || img.getAttribute("src") || "");
        pinBtn.href = "https://www.pinterest.com/pin/create/button/?url=" + pageUrl + "&media=" + mediaSrc + "&description=" + pageTitle;
        pinBtn.target = "_blank";
        pinBtn.rel = "noopener noreferrer";
        pinBtn.title = "Save to Pinterest";
        pinBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg><span>Save</span>';
        
        img.parentNode.insertBefore(wrapper, img);
        wrapper.appendChild(img);
        wrapper.appendChild(pinBtn);
      }});
    }});
  </script>
</body>
</html>'''




def build_styleire_header(brand_name: str, path_prefix: str = "") -> str:
    """Builds the sticky blurred masthead for Styleire."""
    prefix = path_prefix.rstrip("/") if path_prefix else ""
    home_url = f"{prefix}/" if prefix else "/"
    cats = [
        ("Living Room", f"{prefix}/category/living-room/"),
        ("Bedroom", f"{prefix}/category/bedroom/"),
        ("Kitchen & Dining", f"{prefix}/category/kitchen-dining/"),
        ("Outdoor Spaces", f"{prefix}/category/outdoor-spaces/"),
        ("DIY & Craft", f"{prefix}/category/diy-decor/"),
        ("Seasonal & Trends", f"{prefix}/category/seasonal-trends/"),
    ]
    nav_links = "".join([f'<a href="{url}" class="text-stone-600 transition hover:text-stone-900 font-medium">{name}</a>' for name, url in cats])
    mobile_links = "".join([f'<a href="{url}" class="whitespace-nowrap transition hover:text-stone-900">{name}</a>' for name, url in cats])
    about_url = f"{prefix}/about/"

    return f'''<header class="sticky top-0 z-40 border-b border-stone-200 bg-white/90 backdrop-blur">
  <div class="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-4">
    <a class="font-serif text-2xl font-bold tracking-tight text-stone-900 hover:opacity-90" href="{home_url}">{html_lib.escape(brand_name)}</a>
    <nav class="hidden items-center gap-6 text-sm md:flex">
      {nav_links}
    </nav>
    <a href="{about_url}" class="hidden text-sm text-stone-600 font-medium transition hover:text-stone-900 md:inline">About</a>
  </div>
  <div class="border-t border-stone-100 md:hidden">
    <nav class="mx-auto flex max-w-6xl gap-5 overflow-x-auto px-4 py-2.5 text-xs text-stone-600 font-medium">
      {mobile_links}
    </nav>
  </div>
</header>'''


def build_styleire_footer(brand_name: str, path_prefix: str = "") -> str:
    """Builds the 4-column trust and directory footer for Styleire."""
    prefix = path_prefix.rstrip("/") if path_prefix else ""
    return f'''<footer class="border-t border-stone-200 bg-stone-50 mt-16">
  <div class="mx-auto grid max-w-6xl gap-8 px-4 py-12 md:grid-cols-4">
    <div class="md:col-span-2">
      <div class="font-serif text-xl font-bold text-stone-900">{html_lib.escape(brand_name)}</div>
      <p class="mt-2 max-w-sm text-sm text-stone-600 leading-relaxed">
        {html_lib.escape(brand_name)} is an independent home decor publication with practical guides, expert styling advice, and inspiration for every room of your home.
      </p>
    </div>
    <div>
      <div class="mb-3 text-sm font-semibold uppercase tracking-wider text-stone-900">Explore</div>
      <ul class="space-y-2 text-sm text-stone-600">
        <li><a href="{prefix}/category/living-room/" class="hover:text-stone-900">Living Room</a></li>
        <li><a href="{prefix}/category/bedroom/" class="hover:text-stone-900">Bedroom</a></li>
        <li><a href="{prefix}/category/kitchen-dining/" class="hover:text-stone-900">Kitchen &amp; Dining</a></li>
        <li><a href="{prefix}/category/outdoor-spaces/" class="hover:text-stone-900">Outdoor Spaces</a></li>
        <li><a href="{prefix}/category/diy-decor/" class="hover:text-stone-900">DIY &amp; Craft</a></li>
        <li><a href="{prefix}/category/seasonal-trends/" class="hover:text-stone-900">Seasonal &amp; Trends</a></li>
      </ul>
    </div>
    <div>
      <div class="mb-3 text-sm font-semibold uppercase tracking-wider text-stone-900">Company</div>
      <ul class="space-y-2 text-sm text-stone-600">
        <li><a href="{prefix}/about/" class="hover:text-stone-900">About Us</a></li>
        <li><a href="{prefix}/contact/" class="hover:text-stone-900">Contact</a></li>
        <li><a href="{prefix}/editorial-policy/" class="hover:text-stone-900">Editorial Policy</a></li>
        <li><a href="{prefix}/fact-checking-policy/" class="hover:text-stone-900">Fact-Checking Policy</a></li>
        <li><a href="{prefix}/privacy-policy/" class="hover:text-stone-900">Privacy Policy</a></li>
        <li><a href="{prefix}/cookie-policy/" class="hover:text-stone-900">Cookie Policy</a></li>
        <li><a href="{prefix}/terms/" class="hover:text-stone-900">Terms &amp; Conditions</a></li>
        <li><a href="{prefix}/disclaimer/" class="hover:text-stone-900">Disclaimer</a></li>
        <li><a href="{prefix}/copyright/" class="hover:text-stone-900">Copyright &amp; Images</a></li>
        <li><a href="{prefix}/sitemap/" class="hover:text-stone-900 font-semibold text-stone-900">Sitemap</a></li>
      </ul>
    </div>
  </div>
  <div class="border-t border-stone-200">
    <div class="mx-auto max-w-6xl px-4 py-6 text-xs text-stone-500">
      &copy; 2026 {html_lib.escape(brand_name)}. All rights reserved.
    </div>
  </div>
</footer>'''


def render_styleire_layout(
    slug: str, title: str, excerpt: str, category: str, lastmod: str,
    image_src: str, fallback_svg: str, canonical_url: str, clean_domain: str,
    pills_html: str, takeaways_html: str, checklist_html: str, related_html: str,
    schema_json: str, fallback_css: str, breadcrumb_html: str,
    theme_tokens: dict, path_prefix: str,
    toc_html: str = "", faq_html: str = "", eeat_html: str = "",
    branding: Optional[Any] = None,
    content_html: str = "",
    **kwargs: Any,
) -> str:
    """Renders single article post in the exact Styleire editorial design."""
    prefix = path_prefix.rstrip("/") if path_prefix else ""
    home_url = f"{prefix}/" if prefix else "/"
    brand_name = getattr(branding, "brand_name", "") or "Styleire"
    author_name = getattr(branding, "author_name", "") or "Sophia Bennett"
    author_role = getattr(branding, "author_role", "") or "Senior Home Decor Editor & Interior Stylist"
    author_bio = getattr(branding, "author_bio", "") or (
        "Sophia Bennett is a certified interior stylist and the senior editor at Styleire. "
        "She has spent more than eight years helping homeowners and renters create warm, functional interiors, "
        "with hands-on experience across small city apartments and family homes."
    )
    author_slug = "sophia-bennett"
    author_url = f"{prefix}/author/{author_slug}/"
    author_img = f"{prefix}/assets/images/author-sophia.jpg"
    cat_slug = slugify(category or "bedroom")
    cat_url = f"{prefix}/category/{cat_slug}/"

    esc_title = html_lib.escape(title)
    esc_excerpt = html_lib.escape(excerpt)
    esc_category = html_lib.escape(category or "Guides")

    # Format date
    raw_date = (lastmod or "2026-05-20")[:10]
    try:
        import datetime
        dt = datetime.date.fromisoformat(raw_date)
        formatted_date = dt.strftime("%B %d, %Y")
    except Exception:
        formatted_date = raw_date

    # Pinterest Pin Button
    pin_target_url = urllib.parse.quote(canonical_url, safe="") if canonical_url else ""
    pin_media_url = urllib.parse.quote(image_src, safe="") if image_src else ""
    pin_title = urllib.parse.quote(title, safe="") if title else ""
    pin_href = f"https://www.pinterest.com/pin/create/button/?url={pin_target_url}&media={pin_media_url}&description={pin_title}"

    # Header and Footer
    header_markup = build_styleire_header(brand_name, path_prefix)
    footer_markup = build_styleire_footer(brand_name, path_prefix)

    # Multi-tier schema injection
    multi_tier_schemas = ""
    try:
        from app.seo.schema import generate_multi_tier_json_ld_scripts
        post_mock = {
            "slug": slug, "title": title, "excerpt": excerpt, "category": category,
            "category_slug": cat_slug, "date": raw_date, "image": image_src,
        }
        route_mock = {
            "web_path": f"{prefix}/blog/{slug}/",
            "file_path": f"blog/{slug}/index.html",
            "depth": 2,
            "breadcrumbs": [
                {"name": "Home", "url": home_url},
                {"name": esc_category, "url": cat_url},
                {"name": title, "url": f"{prefix}/blog/{slug}/"},
            ]
        }
        multi_tier_schemas = generate_multi_tier_json_ld_scripts(
            post=post_mock, route=route_mock, base_url=canonical_url,
            source_domain=clean_domain, author_name=author_name, author_slug=author_slug,
            brand_name=brand_name
        )
    except Exception:
        multi_tier_schemas = f'<script type="application/ld+json">{schema_json}</script>' if schema_json else ""

    # Prose content
    if content_html and len(content_html.strip()) > 30:
        article_prose = content_html
    else:
        article_prose = f'''
        <p>Creating a cohesive, inviting room requires balancing proportion, texture, and light. When styling your {esc_category.lower()}, prioritize function first: ensure natural pathways remain clear and seating arrangements encourage conversation.</p>
        <h2>Proportion and Visual Balance</h2>
        <p>Scale is the foundation of interior styling. Pair substantial anchor pieces with lighter, open-framed accents to prevent visual crowding. Incorporate reflective finishes or matte ceramics to introduce understated contrast without clutter.</p>
        <h2>Lighting and Layered Textures</h2>
        <p>Layer three distinct light sources: ambient ceiling fixtures, task lamps for reading, and subtle accent illumination along architectural details. Combining natural linen, tactile boucl&eacute;, and warm wood tones delivers lasting visual warmth.</p>
        '''

    # Key Takeaways Section
    takeaways_items = [
        f"Prioritize layout and function before introducing accent decor in your {esc_category.lower()}.",
        "Mix smooth and textured materials to cultivate visual depth without clutter.",
        "Layer task, ambient, and accent lighting for balanced ambiance throughout the day.",
    ]
    takeaways_li = "".join([f"<li>{item}</li>" for item in takeaways_items])
    takeaways_section = f'''
    <section class="mt-10 rounded-xl border border-stone-200 bg-stone-50 p-6">
      <h2 class="font-serif text-xl font-bold text-stone-900">Key takeaways</h2>
      <ul class="mt-3 list-disc space-y-1.5 pl-5 text-sm text-stone-700 leading-relaxed">
        {takeaways_li}
      </ul>
    </section>
    '''

    # Frequently Asked Questions Section
    faqs = [
        {
            "q": f"How do I choose the best layout for a {esc_category.lower()}?",
            "a": "Start by identifying the primary focal point (such as a fireplace, window, or feature wall) and position major seating or furniture pieces 14 to 18 inches away from coffee tables or secondary fixtures for optimal traffic flow."
        },
        {
            "q": "What lighting strategy works best across different seasons?",
            "a": "Utilize warm 2700K LED bulbs paired with dimmers. During winter and autumn, bring in floor lamps and low-level accent sconces to create cozy illumination pockets."
        },
        {
            "q": "How can I make rental spaces feel curated without structural changes?",
            "a": "Invest in oversized rugs that conceal generic flooring, swap standard hardware for brass or matte black pulls, and introduce vertical art prints paired with tall leafy plants."
        }
    ]
    faq_items = "".join([
        f'''<details class="group p-5">
          <summary class="cursor-pointer text-base font-medium text-stone-900 group-open:text-stone-700 flex items-center justify-between">
            <span>{f["q"]}</span>
            <span class="text-stone-400 text-lg group-open:rotate-180 transition">&darr;</span>
          </summary>
          <p class="mt-3 text-sm text-stone-600 leading-relaxed">{f["a"]}</p>
        </details>'''
        for f in faqs
    ])
    faq_section = f'''
    <section class="mt-10">
      <h2 class="font-serif text-2xl font-bold text-stone-900">Frequently asked questions</h2>
      <div class="mt-4 divide-y divide-stone-200 rounded-xl border border-stone-200 bg-white">
        {faq_items}
      </div>
    </section>
    '''

    # Author Card
    author_card = f'''
    <div class="mt-12 flex flex-col gap-4 rounded-xl border border-stone-200 bg-stone-50 p-6 sm:flex-row sm:items-start">
      <img src="{author_img}" alt="{author_name}" class="h-24 w-24 flex-shrink-0 rounded-full object-cover shadow-sm" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80';"/>
      <div class="flex-1">
        <div class="text-xs uppercase tracking-wider text-stone-500 font-semibold">Written by</div>
        <a class="font-serif text-lg font-bold text-stone-900 hover:underline" href="{author_url}">{author_name}</a>
        <div class="text-sm text-stone-500 font-medium">{author_role}</div>
        <p class="mt-2 text-sm text-stone-600 leading-relaxed">{author_bio}</p>
      </div>
    </div>
    '''

    # Related Reading Grid
    if related_html and len(related_html.strip()) > 50:
        related_section = f'''
        <section class="mt-16">
          <h2 class="mb-6 font-serif text-2xl font-bold text-stone-900">Related reading</h2>
          <div class="grid gap-6 sm:grid-cols-2 md:grid-cols-3">
            {related_html}
          </div>
        </section>
        '''
    else:
        related_section = ""

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{esc_title} | {brand_name}</title>
  <meta name="description" content="{esc_excerpt}"/>
  <link rel="canonical" href="{canonical_url}"/>
  <meta property="og:site_name" content="{brand_name}"/>
  <meta property="og:type" content="article"/>
  <meta property="og:title" content="{esc_title} | {brand_name}"/>
  <meta property="og:description" content="{esc_excerpt}"/>
  <meta property="og:image" content="{image_src}"/>
  <meta name="twitter:card" content="summary_large_image"/>
  <meta name="twitter:title" content="{esc_title} | {brand_name}"/>
  <meta name="twitter:description" content="{esc_excerpt}"/>
  <meta name="twitter:image" content="{image_src}"/>
  {multi_tier_schemas}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            serif: ['Playfair Display', 'Georgia', 'serif'],
            sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>
</head>
<body class="bg-white text-stone-900 font-sans antialiased">
  <div class="flex min-h-screen flex-col">
    {header_markup}

    <main class="flex-1">
      <article class="mx-auto max-w-3xl px-4 py-10">
        <!-- Breadcrumb -->
        <nav aria-label="Breadcrumb" class="mb-6 text-sm text-stone-500">
          <ol class="flex flex-wrap items-center gap-1">
            <li class="flex items-center gap-1"><a class="hover:text-stone-900 transition" href="{home_url}">Home</a><span class="px-1 text-stone-400">/</span></li>
            <li class="flex items-center gap-1"><a class="hover:text-stone-900 transition" href="{cat_url}">{esc_category}</a><span class="px-1 text-stone-400">/</span></li>
            <li class="flex items-center gap-1"><span class="text-stone-900 font-medium truncate max-w-[240px]">{esc_title}</span></li>
          </ol>
        </nav>

        <!-- Category Kicker -->
        <div class="text-xs font-semibold uppercase tracking-widest text-stone-500">{esc_category}</div>

        <!-- H1 Headline -->
        <h1 class="mt-2 font-serif text-4xl font-bold leading-tight tracking-tight text-stone-900 md:text-5xl">{esc_title}</h1>

        <!-- Byline -->
        <div class="mt-4 flex flex-wrap items-center gap-3 text-sm text-stone-500">
          <span>By <a href="{author_url}" class="text-stone-900 font-medium hover:underline">{author_name}</a></span>
          <span>•</span>
          <time datetime="{raw_date}">{formatted_date}</time>
          <span>•</span>
          <span>5 min read</span>
        </div>

        <!-- Hero Featured Image with Pinterest Save Hover Overlay -->
        <div class="group relative mt-8 overflow-hidden rounded-xl border border-stone-200">
          <img src="{image_src}" alt="{esc_title}" class="aspect-[3/2] w-full object-cover transition duration-500 group-hover:scale-105" loading="eager" onerror="this.onerror=null;this.src='{fallback_svg}';"/>
          <a href="{pin_href}" target="_blank" rel="noopener noreferrer" class="absolute top-4 right-4 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold px-3 py-1.5 rounded-full shadow-md flex items-center gap-1.5 opacity-90 group-hover:opacity-100 transition" title="Save to Pinterest">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg>
            <span>Save</span>
          </a>
        </div>

        <!-- Prose Article Body -->
        <div class="prose prose-stone mt-10 max-w-none text-stone-800 leading-relaxed">
          {article_prose}
        </div>

        <!-- Key Takeaways -->
        {takeaways_section}

        <!-- Frequently Asked Questions -->
        {faq_section}

        <!-- E-E-A-T Author Card -->
        {author_card}

        <!-- Related Reading -->
        {related_section}
      </article>
    </main>

    {footer_markup}
  </div>
</body>
</html>'''

# Alias for backward compatibility
render_pinterest_mag_layout = render_styleire_layout



def render_styleire_hub(
    posts: list[Any],
    categories: Optional[list[dict[str, str]]] = None,
    title: str = "",
    subtitle: str = "",
    base_url: str = "",
    theme: str = "pinterest-mag",
    source_domain: str = "styleire.com",
    branding: Optional[Any] = None,
    path_prefix: str = "",
    **kwargs: Any,
) -> str:
    """Renders the Root Organization Hub (/index.html) in Styleire editorial design."""
    prefix = path_prefix.rstrip("/") if path_prefix else ""
    home_url = f"{prefix}/" if prefix else "/"
    brand_name = getattr(branding, "brand_name", "") or "Styleire"
    clean_domain = _clean_source_domain(source_domain)
    canonical_base = base_url.rstrip("/") if (base_url and "://" in base_url) else f"https://{clean_domain}"

    header_markup = build_styleire_header(brand_name, path_prefix)
    footer_markup = build_styleire_footer(brand_name, path_prefix)

    cover_post = posts[0] if posts else None
    secondary_posts = posts[1:4] if len(posts) > 1 else []
    remaining_posts = posts[4:] if len(posts) > 4 else posts

    # Cover Post Details
    if cover_post:
        c_slug = getattr(cover_post, "slug", "") or (cover_post.get("slug") if isinstance(cover_post, dict) else "guide")
        c_title = getattr(cover_post, "title", "") or (cover_post.get("title") if isinstance(cover_post, dict) else c_slug.replace("-", " ").title())
        c_excerpt = getattr(cover_post, "excerpt", "") or (cover_post.get("excerpt") if isinstance(cover_post, dict) else (cover_post.get("description", "") if isinstance(cover_post, dict) else ""))
        c_cat = getattr(cover_post, "category", "") or (cover_post.get("category") if isinstance(cover_post, dict) else "Living Room")
        c_date = (getattr(cover_post, "date", "") or (cover_post.get("date") if isinstance(cover_post, dict) else "2026-05-20"))[:10]
        c_link = f"{prefix}/blog/{c_slug}/"
        c_cat_link = f"{prefix}/category/{slugify(c_cat)}/"
        c_img = getattr(cover_post, "local_image_path", "") or (cover_post.get("local_image_path") if isinstance(cover_post, dict) else (cover_post.get("image", "") if isinstance(cover_post, dict) else ""))
        if not c_img or c_img.endswith(".svg"):
            c_img = "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=1200&q=80"
        elif not c_img.startswith("http"):
            c_img = f"{prefix}/{c_img.lstrip('/')}"
    else:
        c_slug = "how-to-choose-bedding"
        c_title = "How to Choose Bedding That Actually Feels Good"
        c_excerpt = "Thread count is mostly noise. Here is what actually determines how bedding feels and lasts across seasons."
        c_cat = "Bedroom"
        c_date = "2026-05-20"
        c_link = f"{prefix}/blog/{c_slug}/"
        c_cat_link = f"{prefix}/category/bedroom/"
        c_img = "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=1200&q=80"

    hero_html = f'''
    <section class="border-b border-stone-200 bg-stone-50/50 py-12 md:py-16">
      <div class="mx-auto max-w-6xl px-4">
        <div class="grid gap-8 md:grid-cols-2 md:items-center">
          <a href="{c_link}" class="group block overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
            <img src="{c_img}" alt="{html_lib.escape(c_title)}" class="aspect-[16/10] w-full object-cover transition duration-700 group-hover:scale-105" loading="eager" width="800" height="500"/>
          </a>
          <div class="space-y-4">
            <a href="{c_cat_link}" class="text-xs font-bold uppercase tracking-widest text-stone-500 hover:text-stone-900 transition">{html_lib.escape(c_cat)}</a>
            <h1 class="font-serif text-3xl font-bold leading-tight tracking-tight text-stone-900 sm:text-4xl md:text-5xl">
              <a href="{c_link}" class="hover:underline">{html_lib.escape(c_title)}</a>
            </h1>
            <p class="text-base text-stone-600 leading-relaxed max-w-xl">
              {html_lib.escape(c_excerpt)}
            </p>
            <div class="flex items-center gap-3 text-xs text-stone-500 font-medium">
              <span>By Sophia Bennett</span>
              <span>•</span>
              <time datetime="{c_date}">{c_date}</time>
              <span>•</span>
              <span>6 min read</span>
            </div>
          </div>
        </div>
      </div>
    </section>
    '''

    # Silo Taxonomy Grid
    silo_categories = [
        ("Living Room", "living-room", "14 guides", "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=600&q=80"),
        ("Bedroom", "bedroom", "12 guides", "https://images.unsplash.com/photo-1540518614846-7ede433c4ef7?auto=format&fit=crop&w=600&q=80"),
        ("Kitchen & Dining", "kitchen-dining", "10 guides", "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=600&q=80"),
        ("Outdoor Spaces", "outdoor-spaces", "8 guides", "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=600&q=80"),
        ("DIY & Craft", "diy-decor", "9 guides", "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?auto=format&fit=crop&w=600&q=80"),
        ("Seasonal & Trends", "seasonal-trends", "7 guides", "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=600&q=80"),
    ]
    silo_cards = []
    for s_name, s_slug, s_count, s_img in silo_categories:
        s_url = f"{prefix}/category/{s_slug}/"
        silo_cards.append(f'''
        <a href="{s_url}" class="group relative overflow-hidden rounded-xl border border-stone-200 bg-white shadow-sm transition hover:shadow-md">
          <div class="aspect-[16/10] overflow-hidden">
            <img src="{s_img}" alt="{s_name}" class="h-full w-full object-cover transition duration-500 group-hover:scale-105" loading="lazy" width="400" height="250"/>
          </div>
          <div class="p-4">
            <h3 class="font-serif text-lg font-bold text-stone-900 group-hover:underline">{s_name}</h3>
            <p class="text-xs text-stone-500 mt-1">{s_count}</p>
          </div>
        </a>
        ''')
    silos_html = "".join(silo_cards)

    # Latest Guides Grid
    guide_cards = []
    for p in (remaining_posts or posts)[:12]:
        p_slug = getattr(p, "slug", "") or (p.get("slug") if isinstance(p, dict) else "guide")
        p_title = getattr(p, "title", "") or (p.get("title") if isinstance(p, dict) else p_slug.replace("-", " ").title())
        p_excerpt = getattr(p, "excerpt", "") or (p.get("excerpt") if isinstance(p, dict) else (p.get("description", "") if isinstance(p, dict) else ""))
        p_cat = getattr(p, "category", "") or (p.get("category") if isinstance(p, dict) else "Living Room")
        p_date = (getattr(p, "date", "") or (p.get("date") if isinstance(p, dict) else "2026-05-20"))[:10]
        p_link = f"{prefix}/blog/{p_slug}/"
        p_cat_link = f"{prefix}/category/{slugify(p_cat)}/"
        p_img = getattr(p, "local_image_path", "") or (p.get("local_image_path") if isinstance(p, dict) else (p.get("image", "") if isinstance(p, dict) else ""))
        if not p_img or p_img.endswith(".svg"):
            p_img = "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=600&q=80"
        elif not p_img.startswith("http"):
            p_img = f"{prefix}/{p_img.lstrip('/')}"

        guide_cards.append(f'''
        <article class="group flex flex-col overflow-hidden rounded-xl border border-stone-200 bg-white transition hover:shadow-md">
          <a href="{p_link}" class="block overflow-hidden">
            <img src="{p_img}" alt="{html_lib.escape(p_title)}" class="aspect-[3/2] w-full object-cover transition duration-500 group-hover:scale-105" loading="lazy" width="600" height="400"/>
          </a>
          <div class="flex flex-1 flex-col p-5">
            <a href="{p_cat_link}" class="text-xs font-bold uppercase tracking-wider text-stone-500 hover:text-stone-900 transition">{html_lib.escape(p_cat)}</a>
            <h3 class="mt-2 font-serif text-lg font-bold leading-snug text-stone-900">
              <a href="{p_link}" class="hover:underline">{html_lib.escape(p_title)}</a>
            </h3>
            <p class="mt-2 line-clamp-2 flex-1 text-sm text-stone-600 leading-relaxed">
              {html_lib.escape(p_excerpt)}
            </p>
            <div class="mt-4 flex items-center justify-between text-xs text-stone-500 font-medium">
              <time datetime="{p_date}">{p_date}</time>
              <span>5 min read</span>
            </div>
          </div>
        </article>
        ''')
    guides_html = "".join(guide_cards)

    # WebSite Schema
    website_schema = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebSite","name":"{brand_name}","url":"{canonical_base}/","description":"{html_lib.escape(subtitle or "Styleire is an independent home decor publication.")}","publisher":{{"@type":"Organization","name":"{brand_name}","url":"{canonical_base}/"}}}}
</script>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{brand_name} — Home decor ideas, guides, and inspiration</title>
  <meta name="description" content="{html_lib.escape(subtitle or "Styleire is an independent home decor publication with practical guides, expert styling advice, and inspiration for every room of your home.")}"/>
  <link rel="canonical" href="{canonical_base}/"/>
  <meta property="og:site_name" content="{brand_name}"/>
  <meta property="og:type" content="website"/>
  <meta property="og:title" content="{brand_name} — Home decor ideas, guides, and inspiration"/>
  <meta property="og:description" content="{html_lib.escape(subtitle or "Styleire is an independent home decor publication.")}"/>
  <meta property="og:url" content="{canonical_base}/"/>
  <meta property="og:image" content="{c_img}"/>
  <meta name="twitter:card" content="summary_large_image"/>
  {website_schema}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            serif: ['Playfair Display', 'Georgia', 'serif'],
            sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>
</head>
<body class="bg-white text-stone-900 font-sans antialiased">
  <div class="flex min-h-screen flex-col">
    {header_markup}

    <main class="flex-1">
      {hero_html}

      <!-- Topic Silos -->
      <section class="py-12 md:py-16">
        <div class="mx-auto max-w-6xl px-4">
          <div class="mb-8 flex items-end justify-between">
            <div>
              <h2 class="font-serif text-2xl font-bold tracking-tight text-stone-900 sm:text-3xl">Curated Room Silos</h2>
              <p class="mt-1 text-sm text-stone-500">Explore architectural guides organized by room and design project.</p>
            </div>
          </div>
          <div class="grid gap-6 sm:grid-cols-2 md:grid-cols-3">
            {silos_html}
          </div>
        </div>
      </section>

      <!-- Latest Published Guides -->
      <section class="border-t border-stone-200 bg-stone-50/50 py-12 md:py-16">
        <div class="mx-auto max-w-6xl px-4">
          <div class="mb-8 flex items-end justify-between">
            <div>
              <h2 class="font-serif text-2xl font-bold tracking-tight text-stone-900 sm:text-3xl">Latest Published Guides</h2>
              <p class="mt-1 text-sm text-stone-500">Comprehensive styling advice tested in real living spaces.</p>
            </div>
            <a href="{prefix}/sitemap/" class="hidden text-sm font-semibold text-stone-900 hover:underline md:inline">View Complete Directory &rarr;</a>
          </div>
          <div class="grid gap-6 sm:grid-cols-2 md:grid-cols-3">
            {guides_html}
          </div>
        </div>
      </section>

      <!-- Newsletter Callout -->
      <section class="border-t border-stone-200 py-12 md:py-16">
        <div class="mx-auto max-w-3xl px-4 text-center">
          <h2 class="font-serif text-3xl font-bold tracking-tight text-stone-900">Practical design advice, straight to your inbox</h2>
          <p class="mt-3 text-sm text-stone-600 leading-relaxed max-w-lg mx-auto">
            Join 45,000+ homeowners and stylists receiving our bi-weekly architectural curation, material breakdowns, and room styling breakdowns.
          </p>
          <form class="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3 max-w-md mx-auto" onsubmit="event.preventDefault(); alert('Subscribed to Styleire Dispatch!');">
            <input type="email" placeholder="Enter your email address" required class="w-full rounded-lg border border-stone-300 px-4 py-2.5 text-sm focus:border-stone-900 focus:outline-none"/>
            <button type="submit" class="w-full sm:w-auto rounded-lg bg-stone-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-stone-800 transition">Subscribe</button>
          </form>
        </div>
      </section>
    </main>

    {footer_markup}
  </div>
</body>
</html>'''


def render_styleire_category_index(
    category_name: str,
    category_slug: str,
    posts: list[Any],
    all_categories: Optional[list[dict[str, str]]] = None,
    base_url: str = "",
    branding: Optional[Any] = None,
    source_domain: str = "styleire.com",
    **kwargs: Any,
) -> str:
    """Renders Category Silo Index (/category/<slug>/index.html) in Styleire editorial design."""
    path_prefix = _extract_path_prefix(base_url)
    prefix = path_prefix.rstrip("/") if path_prefix else ""
    home_url = f"{prefix}/" if prefix else "/"
    brand_name = getattr(branding, "brand_name", "") or "Styleire"
    clean_domain = _clean_source_domain(source_domain)
    canonical_base = base_url.rstrip("/") if (base_url and "://" in base_url) else f"https://{clean_domain}"
    cat_url = f"{prefix}/category/{category_slug}/"
    clean_name = category_name or category_slug.replace("-", " ").title()

    header_markup = build_styleire_header(brand_name, path_prefix)
    footer_markup = build_styleire_footer(brand_name, path_prefix)

    # Category Descriptions mapping
    DESCRIPTIONS = {
        "bedroom": "Restful bedrooms start with the right bed, bedding, lighting, and layout. Practical guides for every bedroom size.",
        "living-room": "Living rooms are where homes happen. Layouts, sofas, rugs, lighting, and styling advice for spaces that get lived in.",
        "kitchen-dining": "Kitchens and dining rooms demand both function and warmth. Practical advice on dining tables, seating, lighting, and layout.",
        "outdoor-spaces": "Patios, balconies, and backyards designed for year-round living, entertaining, and quiet mornings.",
        "diy-decor": "Hands-on projects, material guides, and creative craft ideas that make a tangible difference in your home.",
        "seasonal-trends": "Thoughtful seasonal transitions, color palettes, and enduring design trends that outlast the news cycle.",
    }
    desc = DESCRIPTIONS.get(category_slug, f"Practical styling guides, room ideas, and architectural advice for {clean_name.lower()}.")

    guide_cards = []
    for p in posts:
        p_slug = getattr(p, "slug", "") or (p.get("slug") if isinstance(p, dict) else "guide")
        p_title = getattr(p, "title", "") or (p.get("title") if isinstance(p, dict) else p_slug.replace("-", " ").title())
        p_excerpt = getattr(p, "excerpt", "") or (p.get("excerpt") if isinstance(p, dict) else (p.get("description", "") if isinstance(p, dict) else ""))
        p_date = (getattr(p, "date", "") or (p.get("date") if isinstance(p, dict) else "2026-05-20"))[:10]
        p_link = f"{prefix}/blog/{p_slug}/"
        p_img = getattr(p, "local_image_path", "") or (p.get("local_image_path") if isinstance(p, dict) else (p.get("image", "") if isinstance(p, dict) else ""))
        if not p_img or p_img.endswith(".svg"):
            p_img = "https://images.unsplash.com/photo-1540518614846-7ede433c4ef7?auto=format&fit=crop&w=600&q=80"
        elif not p_img.startswith("http"):
            p_img = f"{prefix}/{p_img.lstrip('/')}"

        guide_cards.append(f'''
        <article class="group flex flex-col overflow-hidden rounded-xl border border-stone-200 bg-white transition hover:shadow-md">
          <a href="{p_link}" class="block overflow-hidden">
            <img src="{p_img}" alt="{html_lib.escape(p_title)}" class="aspect-[3/2] w-full object-cover transition duration-500 group-hover:scale-105" loading="lazy" width="600" height="400"/>
          </a>
          <div class="flex flex-1 flex-col p-5">
            <span class="text-xs font-bold uppercase tracking-wider text-stone-500">{clean_name}</span>
            <h3 class="mt-2 font-serif text-lg font-bold leading-snug text-stone-900">
              <a href="{p_link}" class="hover:underline">{html_lib.escape(p_title)}</a>
            </h3>
            <p class="mt-2 line-clamp-2 flex-1 text-sm text-stone-600 leading-relaxed">
              {html_lib.escape(p_excerpt)}
            </p>
            <div class="mt-4 flex items-center justify-between text-xs text-stone-500 font-medium">
              <time datetime="{p_date}">{p_date}</time>
              <span>5 min read</span>
            </div>
          </div>
        </article>
        ''')
    cards_html = "".join(guide_cards)

    breadcrumb_schema = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"{canonical_base}/"}},{{"@type":"ListItem","position":2,"name":"{clean_name}","item":"{canonical_base}/category/{category_slug}/"}}]}}
</script>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{clean_name} — Guides &amp; Inspiration | {brand_name}</title>
  <meta name="description" content="{html_lib.escape(desc)}"/>
  <link rel="canonical" href="{canonical_base}/category/{category_slug}/"/>
  <meta property="og:site_name" content="{brand_name}"/>
  <meta property="og:title" content="{clean_name} | {brand_name}"/>
  <meta property="og:description" content="{html_lib.escape(desc)}"/>
  {breadcrumb_schema}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            serif: ['Playfair Display', 'Georgia', 'serif'],
            sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>
</head>
<body class="bg-white text-stone-900 font-sans antialiased">
  <div class="flex min-h-screen flex-col">
    {header_markup}

    <main class="flex-1">
      <div class="mx-auto max-w-6xl px-4 py-10">
        <!-- Breadcrumb -->
        <nav aria-label="Breadcrumb" class="mb-6 text-sm text-stone-500">
          <ol class="flex flex-wrap items-center gap-1">
            <li class="flex items-center gap-1"><a class="hover:text-stone-900 transition" href="{home_url}">Home</a><span class="px-1 text-stone-400">/</span></li>
            <li class="flex items-center gap-1"><span class="text-stone-900 font-medium">{clean_name}</span></li>
          </ol>
        </nav>

        <header class="mb-10 max-w-3xl">
          <h1 class="font-serif text-4xl font-bold tracking-tight text-stone-900 md:text-5xl">{clean_name}</h1>
          <p class="mt-4 text-lg text-stone-600 leading-relaxed">
            {desc}
          </p>
        </header>

        <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {cards_html}
        </div>
      </div>
    </main>

    {footer_markup}
  </div>
</body>
</html>'''


def render_author_page(
    author_name: str = "Sophia Bennett",
    author_role: str = "Senior Home Decor Editor & Interior Stylist",
    author_bio: str = "",
    author_image: str = "",
    posts: Optional[list[Any]] = None,
    theme: str = "nordic-studio",
    base_url: str = "",
    source_domain: str = "styleire.com",
    branding: Optional[Any] = None,
    **kwargs: Any,
) -> str:
    """Universal E-E-A-T Author Profile page supporting all 3 templates."""
    path_prefix = _extract_path_prefix(base_url)
    prefix = path_prefix.rstrip("/") if path_prefix else ""
    home_url = f"{prefix}/" if prefix else "/"
    brand_name = getattr(branding, "brand_name", "") or "Styleire"
    clean_domain = _clean_source_domain(source_domain)
    canonical_base = base_url.rstrip("/") if (base_url and "://" in base_url) else f"https://{clean_domain}"
    author_slug = "sophia-bennett"
    author_url = f"{canonical_base}/author/{author_slug}/"
    author_img = author_image or f"{prefix}/assets/images/author-sophia.jpg"

    header_markup = build_styleire_header(brand_name, path_prefix)
    footer_markup = build_styleire_footer(brand_name, path_prefix)

    posts_list = posts or []
    guide_cards = []
    for p in posts_list[:12]:
        p_slug = getattr(p, "slug", "") or (p.get("slug") if isinstance(p, dict) else "guide")
        p_title = getattr(p, "title", "") or (p.get("title") if isinstance(p, dict) else p_slug.replace("-", " ").title())
        p_excerpt = getattr(p, "excerpt", "") or (p.get("excerpt") if isinstance(p, dict) else (p.get("description", "") if isinstance(p, dict) else ""))
        p_cat = getattr(p, "category", "") or (p.get("category") if isinstance(p, dict) else "Guides")
        p_date = (getattr(p, "date", "") or (p.get("date") if isinstance(p, dict) else "2026-05-20"))[:10]
        p_link = f"{prefix}/blog/{p_slug}/"
        p_img = getattr(p, "local_image_path", "") or (p.get("local_image_path") if isinstance(p, dict) else (p.get("image", "") if isinstance(p, dict) else ""))
        if not p_img or p_img.endswith(".svg"):
            p_img = "https://images.unsplash.com/photo-1540518614846-7ede433c4ef7?auto=format&fit=crop&w=600&q=80"
        elif not p_img.startswith("http"):
            p_img = f"{prefix}/{p_img.lstrip('/')}"

        guide_cards.append(f'''
        <article class="group flex flex-col overflow-hidden rounded-xl border border-stone-200 bg-white transition hover:shadow-md">
          <a href="{p_link}" class="block overflow-hidden">
            <img src="{p_img}" alt="{html_lib.escape(p_title)}" class="aspect-[3/2] w-full object-cover transition duration-500 group-hover:scale-105" loading="lazy" width="600" height="400"/>
          </a>
          <div class="flex flex-1 flex-col p-5">
            <span class="text-xs font-bold uppercase tracking-wider text-stone-500">{html_lib.escape(p_cat)}</span>
            <h3 class="mt-2 font-serif text-lg font-bold leading-snug text-stone-900">
              <a href="{p_link}" class="hover:underline">{html_lib.escape(p_title)}</a>
            </h3>
            <p class="mt-2 line-clamp-2 flex-1 text-sm text-stone-600 leading-relaxed">
              {html_lib.escape(p_excerpt)}
            </p>
            <div class="mt-4 flex items-center justify-between text-xs text-stone-500 font-medium">
              <time datetime="{p_date}">{p_date}</time>
              <span>5 min read</span>
            </div>
          </div>
        </article>
        ''')
    articles_html = "".join(guide_cards)

    author_schema = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Person","name":"{author_name}","url":"{author_url}","jobTitle":"{author_role}","description":"{author_name} is a certified interior stylist with 8+ years experience."}}
</script>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{author_name} — {author_role} | {brand_name}</title>
  <meta name="description" content="Editorial portfolio and published interior guides by {author_name}."/>
  <link rel="canonical" href="{author_url}"/>
  {author_schema}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            serif: ['Playfair Display', 'Georgia', 'serif'],
            sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>
</head>
<body class="bg-white text-stone-900 font-sans antialiased">
  <div class="flex min-h-screen flex-col">
    {header_markup}

    <main class="flex-1">
      <div class="mx-auto max-w-6xl px-4 py-10">
        <!-- Breadcrumb -->
        <nav aria-label="Breadcrumb" class="mb-6 text-sm text-stone-500">
          <ol class="flex flex-wrap items-center gap-1">
            <li class="flex items-center gap-1"><a class="hover:text-stone-900 transition" href="{home_url}">Home</a><span class="px-1 text-stone-400">/</span></li>
            <li class="flex items-center gap-1"><span class="text-stone-900 font-medium">{author_name}</span></li>
          </ol>
        </nav>

        <div class="grid gap-10 md:grid-cols-3">
          <aside class="md:col-span-1 space-y-6">
            <img src="{author_img}" alt="{author_name}" class="w-full rounded-2xl object-cover shadow-sm aspect-square" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80';"/>
            <div class="rounded-xl border border-stone-200 bg-stone-50 p-5 space-y-3">
              <div class="text-xs uppercase tracking-wider text-stone-500 font-bold">Contact &amp; Profiles</div>
              <div class="text-sm">
                <a href="mailto:editorial@{clean_domain}" class="text-stone-900 font-medium hover:underline">editorial@{clean_domain}</a>
              </div>
              <div class="flex flex-wrap gap-3 text-xs text-stone-600 font-medium pt-2 border-t border-stone-200">
                <a href="https://twitter.com/" target="_blank" rel="noopener" class="hover:text-stone-900">Twitter</a>
                <a href="https://pinterest.com/" target="_blank" rel="noopener" class="hover:text-stone-900">Pinterest</a>
                <a href="https://linkedin.com/" target="_blank" rel="noopener" class="hover:text-stone-900">LinkedIn</a>
              </div>
            </div>
          </aside>

          <div class="md:col-span-2 space-y-6">
            <div>
              <h1 class="font-serif text-4xl font-bold tracking-tight text-stone-900 md:text-5xl">{author_name}</h1>
              <p class="mt-2 text-lg text-stone-600 font-medium">{author_role}</p>
              <p class="mt-1 text-sm text-stone-500">8+ years in interior styling &amp; architectural journalism</p>
            </div>

            <section class="space-y-4 text-base leading-relaxed text-stone-700">
              <p>Sophia began her career as an assistant on residential styling shoots before moving into full-time editorial journalism. Since then, she has written and edited hundreds of long-form guides on furniture selection, spatial layout, color theory, layered lighting, and sustainable home design.</p>
              <p>At {brand_name}, she leads a dedicated editorial team that tests decor products in real homes, interviews practicing interior architects, and rigorously audits every guide for real-world accuracy before publication. She personally fact-checks all material, care, and safety guidance.</p>
              <p>Sophia holds a certificate in interior styling from the KLC School of Design and lives in an 1890s brick home that serves as her constant testing ground for paint finishes, textiles, and joinery.</p>
            </section>

            <div class="pt-8 border-t border-stone-200">
              <h2 class="font-serif text-2xl font-bold tracking-tight text-stone-900 mb-6">Published Guides by {author_name} ({len(posts_list)})</h2>
              <div class="grid gap-6 sm:grid-cols-2">
                {articles_html}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    {footer_markup}
  </div>
</body>
</html>'''


def render_trust_page(
    slug: str,
    title: str = "",
    content_html: str = "",
    theme: str = "nordic-studio",
    base_url: str = "",
    source_domain: str = "styleire.com",
    branding: Optional[Any] = None,
    **kwargs: Any,
) -> str:
    """Universal Legal and Compliance Trust page supporting all 3 templates."""
    path_prefix = _extract_path_prefix(base_url)
    prefix = path_prefix.rstrip("/") if path_prefix else ""
    home_url = f"{prefix}/" if prefix else "/"
    brand_name = getattr(branding, "brand_name", "") or "Styleire"
    clean_domain = _clean_source_domain(source_domain)
    canonical_base = base_url.rstrip("/") if (base_url and "://" in base_url) else f"https://{clean_domain}"
    page_url = f"{canonical_base}/{slug}/"

    from app.themes.trust_content import get_trust_page_content
    data = get_trust_page_content(slug, brand_name=brand_name, domain=clean_domain)
    page_title = title or data["title"]
    page_subtitle = data.get("subtitle", "")
    page_content = content_html or data["content_html"]

    header_markup = build_styleire_header(brand_name, path_prefix)
    footer_markup = build_styleire_footer(brand_name, path_prefix)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{page_title} | {brand_name}</title>
  <meta name="description" content="{html_lib.escape(page_subtitle or f"Official {page_title} for {brand_name}.")}">
  <link rel="canonical" href="{page_url}"/>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            serif: ['Playfair Display', 'Georgia', 'serif'],
            sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>
</head>
<body class="bg-white text-stone-900 font-sans antialiased">
  <div class="flex min-h-screen flex-col">
    {header_markup}

    <main class="flex-1">
      <article class="mx-auto max-w-3xl px-4 py-10">
        <!-- Breadcrumb -->
        <nav aria-label="Breadcrumb" class="mb-6 text-sm text-stone-500">
          <ol class="flex flex-wrap items-center gap-1">
            <li class="flex items-center gap-1"><a class="hover:text-stone-900 transition" href="{home_url}">Home</a><span class="px-1 text-stone-400">/</span></li>
            <li class="flex items-center gap-1"><span class="text-stone-900 font-medium">{page_title}</span></li>
          </ol>
        </nav>

        <h1 class="font-serif text-4xl font-bold tracking-tight text-stone-900 md:text-5xl">{page_title}</h1>
        {f'<p class="mt-4 text-lg text-stone-600 leading-relaxed">{page_subtitle}</p>' if page_subtitle else ""}

        <div class="prose prose-stone mt-8 max-w-none text-stone-800 leading-relaxed">
          {page_content}
        </div>
      </article>
    </main>

    {footer_markup}
  </div>
</body>
</html>'''


def render_html_sitemap(
    posts: list[Any],
    categories: Optional[list[dict[str, str]]] = None,
    theme: str = "nordic-studio",
    base_url: str = "",
    source_domain: str = "styleire.com",
    branding: Optional[Any] = None,
    **kwargs: Any,
) -> str:
    """Universal HTML Sitemap Directory (/sitemap/index.html) supporting all 3 templates."""
    path_prefix = _extract_path_prefix(base_url)
    prefix = path_prefix.rstrip("/") if path_prefix else ""
    home_url = f"{prefix}/" if prefix else "/"
    brand_name = getattr(branding, "brand_name", "") or "Styleire"
    clean_domain = _clean_source_domain(source_domain)
    canonical_base = base_url.rstrip("/") if (base_url and "://" in base_url) else f"https://{clean_domain}"
    sitemap_url = f"{canonical_base}/sitemap/"

    header_markup = build_styleire_header(brand_name, path_prefix)
    footer_markup = build_styleire_footer(brand_name, path_prefix)

    # Categories List
    cat_items = []
    default_cats = [
        ("Living Room", "living-room"),
        ("Bedroom", "bedroom"),
        ("Kitchen & Dining", "kitchen-dining"),
        ("Outdoor Spaces", "outdoor-spaces"),
        ("DIY & Craft", "diy-decor"),
        ("Seasonal & Trends", "seasonal-trends"),
    ]
    for c_name, c_slug in default_cats:
        c_url = f"{prefix}/category/{c_slug}/"
        cat_items.append(f'<li><a class="hover:underline text-stone-700 hover:text-stone-900" href="{c_url}">{c_name}</a></li>')
    cats_html = "".join(cat_items)

    # Trust Pages List
    trust_links = [
        ("Home", f"{home_url}"),
        ("About Us", f"{prefix}/about/"),
        ("Contact & Support", f"{prefix}/contact/"),
        ("Editorial Policy", f"{prefix}/editorial-policy/"),
        ("Fact-Checking Policy", f"{prefix}/fact-checking-policy/"),
        ("Privacy Policy", f"{prefix}/privacy-policy/"),
        ("Cookie Policy", f"{prefix}/cookie-policy/"),
        ("Terms & Conditions", f"{prefix}/terms/"),
        ("Disclaimer", f"{prefix}/disclaimer/"),
        ("Copyright & Image Rights", f"{prefix}/copyright/"),
        ("Author Profile (Sophia Bennett)", f"{prefix}/author/sophia-bennett/"),
    ]
    trust_items = [f'<li><a class="hover:underline text-stone-700 hover:text-stone-900" href="{url}">{name}</a></li>' for name, url in trust_links]
    trust_html = "".join(trust_items)

    # Blog Posts by Category
    posts_by_cat: dict[str, list[Any]] = {}
    for p in posts:
        c = getattr(p, "category", "") or (p.get("category") if isinstance(p, dict) else "General")
        posts_by_cat.setdefault(c, []).append(p)

    grouped_guides = []
    for cat_name, cat_posts in posts_by_cat.items():
        links = []
        for p in cat_posts:
            p_slug = getattr(p, "slug", "") or (p.get("slug") if isinstance(p, dict) else "guide")
            p_title = getattr(p, "title", "") or (p.get("title") if isinstance(p, dict) else p_slug.replace("-", " ").title())
            p_link = f"{prefix}/blog/{p_slug}/"
            links.append(f'<li><a class="hover:underline text-stone-700 hover:text-stone-900" href="{p_link}">{html_lib.escape(p_title)}</a></li>')
        grouped_guides.append(f'''
        <div class="space-y-3">
          <h3 class="font-serif text-lg font-bold text-stone-900 border-b border-stone-200 pb-1">{html_lib.escape(cat_name)}</h3>
          <ul class="space-y-2 text-sm">
            {"".join(links)}
          </ul>
        </div>
        ''')
    guides_grouped_html = "".join(grouped_guides)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Sitemap &amp; Complete Directory | {brand_name}</title>
  <meta name="description" content="Complete directory of all architectural guides, category silos, and legal policies on {brand_name}."/>
  <link rel="canonical" href="{sitemap_url}"/>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            serif: ['Playfair Display', 'Georgia', 'serif'],
            sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>
</head>
<body class="bg-white text-stone-900 font-sans antialiased">
  <div class="flex min-h-screen flex-col">
    {header_markup}

    <main class="flex-1">
      <div class="mx-auto max-w-4xl px-4 py-10">
        <!-- Breadcrumb -->
        <nav aria-label="Breadcrumb" class="mb-6 text-sm text-stone-500">
          <ol class="flex flex-wrap items-center gap-1">
            <li class="flex items-center gap-1"><a class="hover:text-stone-900 transition" href="{home_url}">Home</a><span class="px-1 text-stone-400">/</span></li>
            <li class="flex items-center gap-1"><span class="text-stone-900 font-medium">Sitemap</span></li>
          </ol>
        </nav>

        <h1 class="font-serif text-4xl font-bold tracking-tight text-stone-900 md:text-5xl">Sitemap</h1>
        <p class="mt-2 text-stone-600">Explore the complete index of architectural guides, category silos, and publication policies.</p>

        <!-- Section 1: Main Site Pages -->
        <section class="mt-10">
          <h2 class="font-serif text-2xl font-bold text-stone-900 mb-4">Site Pages &amp; Governance</h2>
          <ul class="grid gap-2 sm:grid-cols-2 text-sm">
            {trust_html}
          </ul>
        </section>

        <!-- Section 2: Topic Silos -->
        <section class="mt-10 pt-8 border-t border-stone-200">
          <h2 class="font-serif text-2xl font-bold text-stone-900 mb-4">Topic Silos &amp; Curated Rooms</h2>
          <ul class="grid gap-2 sm:grid-cols-2 text-sm">
            {cats_html}
          </ul>
        </section>

        <!-- Section 3: All Published Guides -->
        <section class="mt-10 pt-8 border-t border-stone-200">
          <h2 class="font-serif text-2xl font-bold text-stone-900 mb-6">All Published Guides ({len(posts)})</h2>
          <div class="space-y-8">
            {guides_grouped_html}
          </div>
        </section>
      </div>
    </main>

    {footer_markup}
  </div>
</body>
</html>'''


def render_post(
    post: Any,
    all_posts: Optional[list[Any]] = None,
    base_url: str = "",
    theme: str = "editorial-warm",
    source_domain: str = "stylesdays.com",
    **kwargs: Any,
) -> str:
    """
    Renders a complete static HTML post page, dispatching to 3 distinct
    theme layout renderers based on the active theme:
      - editorial-warm  -> Kinfolk Lifestyle Journal
      - nordic-studio   -> Minimalist Architectural Studio
      - pinterest-mag   -> Visual Pin Discovery Magazine
    All interactive components (checklist, takeaways, related) are embedded.
    """
    theme_tokens = get_theme_tokens(theme)
    all_posts = all_posts or []

    # Extract post attributes supporting PostItem or dict
    slug = getattr(post, "slug", None) or (post.get("slug") if isinstance(post, dict) else "guide")
    title = getattr(post, "title", None) or (post.get("title") if isinstance(post, dict) else slug.replace("-", " ").title())
    excerpt = getattr(post, "excerpt", None) or (post.get("excerpt") if isinstance(post, dict) else (post.get("description", "") if isinstance(post, dict) else ""))
    category = getattr(post, "category", None) or (post.get("category") if isinstance(post, dict) else "Home Decor")
    parent_slug = getattr(post, "parent_slug", None) or (post.get("parent_slug") if isinstance(post, dict) else "")
    lastmod = getattr(post, "modified", None) or getattr(post, "date", None) or (post.get("modified") if isinstance(post, dict) else (post.get("lastmod", "2026-10-29") if isinstance(post, dict) else "2026-10-29"))
    web_path = getattr(post, "web_path", None) or (post.get("web_path") if isinstance(post, dict) else f"/{slug}/")
    local_image = getattr(post, "local_image_path", None) or (post.get("local_image_path") if isinstance(post, dict) else (post.get("local_image", "") if isinstance(post, dict) else ""))

    checklist_items = getattr(post, "checklist", None) or (post.get("checklist") if isinstance(post, dict) else [])
    takeaways_items = getattr(post, "takeaways", None) or (post.get("takeaways") if isinstance(post, dict) else [])

    path_prefix = _extract_path_prefix(base_url)
    clean_domain = _clean_source_domain(source_domain)
    canonical_base = base_url.rstrip("/") if (base_url and "://" in base_url) else f"https://{clean_domain}"
    full_page_url = f"{canonical_base}{web_path}"

    raw_canonical = kwargs.get("canonical_url") or (
        getattr(post, "canonical_url", None)
        or (post.get("canonical_url") if isinstance(post, dict) else None)
        or f"https://{clean_domain}/{slug}/"
    )
    canonical_url = str(raw_canonical).replace("https://https://", "https://").replace("http://http://", "http://")

    # Demo image mapping: assign high-resolution photography for each model
    THEME_DEMO_IMAGES = {
        "editorial-warm": "15-home-bedroom-refresh-ideas-transform-your-oasis",
        "nordic-studio":  "20-modern-bedroom-ideas-transform-your-space-with-style",
        "pinterest-mag":  "16-coastal-bedroom-decor-essentials-transform-your-space",
    }
    raw_img = local_image
    if not raw_img or raw_img.endswith("placeholder.svg") or (raw_img.endswith(".svg") and "assets/images" in raw_img):
        demo_slug = THEME_DEMO_IMAGES.get(theme, "15-home-bedroom-refresh-ideas-transform-your-oasis")
        demo_webp = os.path.join("assets", "images", f"{demo_slug}.webp")
        if os.path.exists(demo_webp):
            raw_img = f"assets/images/{demo_slug}.webp"
        else:
            raw_img = f"assets/images/{slug}.svg"

    if raw_img.startswith("http://") or raw_img.startswith("https://"):
        image_src = raw_img
        full_image_url = raw_img
    else:
        clean_img = raw_img.lstrip("/")
        image_src = f"{path_prefix}/{clean_img}" if path_prefix else f"/{clean_img}"
        full_image_url = f"{canonical_base}/{clean_img}"
    fallback_svg = _resolve_fallback_svg(slug, path_prefix)

    # Attempt to load schema from app.seo.schema if available, else use fallback
    schema_json = ""
    try:
        from app.seo.schema import generate_json_ld
        route_obj = kwargs.get("route") or {"web_path": web_path, "file_path": f"{slug}/index.html", "depth": web_path.count("/") - 1, "breadcrumbs": []}
        schema_dict = generate_json_ld(post, route_obj, base_url=canonical_base)
        schema_json = json.dumps(schema_dict, indent=2)
    except Exception:
        schema_json = build_fallback_schema(post, canonical_base, clean_domain)

    # Extract branding and programmatic SEO options
    branding = kwargs.get("branding")
    author_name = getattr(branding, "author_name", "Anna Lindqvist") if branding else "Anna Lindqvist"
    author_bio = getattr(branding, "author_bio", "Senior Interior Architect & Kinfolk Stylist") if branding else "Senior Interior Architect & Kinfolk Stylist"
    enable_toc = getattr(branding, "enable_toc", True) if branding else True
    enable_faq = getattr(branding, "enable_faq", True) if branding else True
    enable_eeat = getattr(branding, "enable_eeat", True) if branding else True

    # Render interactive subcomponents & pSEO elements
    pills_html = render_taxonomy_pills(all_posts, current_slug=slug, theme=theme_tokens, base_url=base_url)
    takeaways_html = render_takeaways(takeaways_items, theme=theme_tokens, title=title, category=category)
    checklist_html = render_checklist(checklist_items, slug=slug, theme=theme_tokens, source_domain=clean_domain)
    related_html = render_related_guides(all_posts, current_slug=slug, theme=theme_tokens, base_url=base_url)
    toc_html = ""
    faq_html = ""
    eeat_html = ""
    fallback_css = get_embedded_fallback_css(theme_tokens)

    # Build breadcrumb HTML
    home_link = f"{path_prefix}/" if path_prefix else "/"
    breadcrumb_html = f'<a href="{home_link}" class="hover:underline">Home</a> <span style="margin: 0 0.25rem;">/</span> '
    if web_path.count("/") > 2:
        top_seg = web_path.strip("/").split("/")[0]
        seg_name = category if category else top_seg.replace("-", " ").title()
        seg_link = f"{path_prefix}/{top_seg}/" if path_prefix else f"/{top_seg}/"
        breadcrumb_html += f'<a href="{seg_link}" class="hover:underline">{html_lib.escape(seg_name)}</a> <span style="margin: 0 0.25rem;">/</span> '
    breadcrumb_html += f'<span class="font-semibold text-stone-900">{html_lib.escape(title[:45])}</span>'

    content_html = getattr(post, "content_html", None) or (post.get("content_html") if isinstance(post, dict) else "")
    layout_args = dict(
        slug=slug, title=title, excerpt=excerpt, category=category, lastmod=lastmod,
        content_html=content_html,
        image_src=image_src, fallback_svg=fallback_svg, canonical_url=canonical_url,
        clean_domain=clean_domain, pills_html=pills_html, takeaways_html=takeaways_html,
        checklist_html=checklist_html, related_html=related_html,
        schema_json=schema_json, fallback_css=fallback_css,
        breadcrumb_html=breadcrumb_html, theme_tokens=theme_tokens,
        path_prefix=path_prefix,
        toc_html=toc_html, faq_html=faq_html, eeat_html=eeat_html,
        branding=branding,
    )

    if theme == "nordic-studio":
        return render_nordic_studio_layout(**layout_args)
    if theme in ("pinterest-mag", "styleire"):
        return render_styleire_layout(**layout_args)
    return render_editorial_warm_layout(**layout_args)


def render_category_index(
    category_name: str,
    category_slug: str,
    posts: list[Any],
    all_categories: Optional[list[dict[str, str]]] = None,
    base_url: str = "",
    theme: str = "editorial-warm",
    source_domain: str = "stylesdays.com",
    branding: Optional[Any] = None,
    **kwargs: Any,
) -> str:
    """
    Renders an intermediate category silo index page (e.g. /ikea-hacks/index.html)
    guaranteeing non-404 traversal with curated post cards.
    """
    if theme in ("pinterest-mag", "styleire"):
        return render_styleire_category_index(
            category_name=category_name,
            category_slug=category_slug,
            posts=posts,
            all_categories=all_categories,
            base_url=base_url,
            branding=branding,
            source_domain=source_domain,
            **kwargs,
        )

    path_prefix = _extract_path_prefix(base_url)
    theme_tokens = get_theme_tokens(theme)
    clean_domain = _clean_source_domain(source_domain)
    brand_clean = getattr(branding, "brand_name", "") or (clean_domain.split(".")[0].title() if clean_domain else "AnnaDeco")
    canonical_base = base_url.rstrip("/") if (base_url and "://" in base_url) else f"https://{clean_domain}"
    fallback_css = get_embedded_fallback_css(theme_tokens)

    cards_html = ""
    for p in posts:
        slug = getattr(p, "slug", None) or (p.get("slug") if isinstance(p, dict) else "")
        title = getattr(p, "title", None) or (p.get("title") if isinstance(p, dict) else slug.replace("-", " ").title())
        excerpt = getattr(p, "excerpt", None) or (p.get("excerpt") if isinstance(p, dict) else (p.get("description", "") if isinstance(p, dict) else ""))
        web_path = getattr(p, "web_path", None) or (p.get("web_path") if isinstance(p, dict) else f"/{category_slug}/{slug}/")
        local_img = getattr(p, "local_image_path", None) or (p.get("local_image_path") if isinstance(p, dict) else (p.get("local_image", "") if isinstance(p, dict) else ""))
        link = f"{path_prefix}{web_path}" if path_prefix else web_path
        raw_img = local_img or f"assets/images/{slug}.svg"
        if raw_img.startswith("http://") or raw_img.startswith("https://"):
            img_src = raw_img
        else:
            clean_img = raw_img.lstrip("/")
            img_src = f"{path_prefix}/{clean_img}" if path_prefix else f"/{clean_img}"
        fallback_svg = _resolve_fallback_svg(slug, path_prefix)

        cards_html += f"""
        <article class="pseo-card group">
          <a href="{link}" style="display: flex; flex-direction: column; height: 100%;">
            <div class="pseo-hero-media">
              <img src="{img_src}" alt="{html_lib.escape(title)}" width="600" height="375" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='{fallback_svg}';">
              <span class="pseo-badge" style="position: absolute; top: 0.75rem; left: 0.75rem; background-color: rgba(255, 255, 255, 0.95); color: #1C1917; font-size: 0.625rem;">
                {html_lib.escape(category_name)}
              </span>
            </div>
            <div style="padding: 1.25rem; flex: 1 0 auto;">
              <div style="font-family: monospace; font-size: 0.7rem; color: #A8A29E; margin-bottom: 0.25rem;">{web_path}</div>
              <h2 class="font-serif-editorial text-lg font-bold text-stone-900 group-hover:text-[{theme_tokens['accent']}]" style="margin-bottom: 0.5rem; transition: color 0.15s ease;">
                {html_lib.escape(title)}
              </h2>
              <p class="text-xs text-stone-500" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                {html_lib.escape(excerpt[:120])}...
              </p>
            </div>
            <div style="padding: 0.75rem 1.25rem; background-color: #FAFAFA; border-top: 1px solid var(--pseo-card-border); display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem; font-weight: 500; color: #78716C;">
              <span>Read Guide</span>
              <span style="color: {theme_tokens['accent']}; font-weight: 700;">→</span>
            </div>
          </a>
        </article>
        """

    # Category switcher pills
    cat_pills = ""
    if all_categories:
        for c in all_categories:
            c_name = c.get("name", "")
            c_slug = c.get("slug", "")
            if c_slug:
                is_curr = c_slug == category_slug
                active_style = f"background-color: {theme_tokens['accent']}; color: #FFFFFF;" if is_curr else ""
                cat_pills += f'<a href="{path_prefix}/{c_slug}/" class="pseo-pill" style="{active_style}">{html_lib.escape(c_name)}</a>'

    home_link = f"{path_prefix}/" if path_prefix else "/"
    branding = kwargs.get("branding")
    header_html = render_blogger_header(
        clean_domain,
        f'<a href="{home_link}" class="hover:underline">Home</a> <span style="margin: 0 0.25rem;">/</span> <span class="font-semibold text-stone-900">{html_lib.escape(category_name)}</span>',
        f'<div class="pseo-pills-bar">{cat_pills}</div>' if cat_pills else '',
        theme_tokens,
        path_prefix=path_prefix,
        branding=branding,
    )
    footer_html = render_blogger_footer(clean_domain, theme_tokens, path_prefix=path_prefix, branding=branding)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_lib.escape(category_name)} Guides | {html_lib.escape(brand_clean)} Editorial Hub</title>
  <meta name="description" content="Browse {len(posts)} curated {category_name} tutorials and room styling guides.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical_base}/{category_slug}/">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>

  <style>
{fallback_css}
  </style>
</head>
<body>
{header_html}

  <main class="pseo-container pseo-main">
    <div style="margin-bottom: 2rem;">
      <span class="pseo-badge" style="background-color: {theme_tokens['badge_bg']}; color: #FFFFFF; margin-bottom: 0.5rem;">Category Silo</span>
      <h1 class="font-serif-editorial text-3xl sm:text-4xl font-bold text-stone-900">{html_lib.escape(category_name)} Guides</h1>
      <p class="text-sm text-stone-600 mt-1">Browse {len(posts)} curated tutorials, room guides, and styling ideas.</p>
    </div>

    <div class="pseo-related-grid">
      {cards_html}
    </div>
  </main>

{footer_html}
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      var articleImgs = document.querySelectorAll(".pseo-article-body img");
      var pageUrl = encodeURIComponent(window.location.href);
      var pageTitle = encodeURIComponent(document.title || "");
      articleImgs.forEach(function(img) {{
        if (img.closest(".pseo-img-wrapper")) return;
        var wrapper = document.createElement("div");
        wrapper.className = "pseo-img-wrapper";
        wrapper.style.position = "relative";
        wrapper.style.display = "block";
        wrapper.style.margin = "1.5rem 0";
        
        var pinBtn = document.createElement("a");
        pinBtn.className = "pseo-pin-save-btn";
        var mediaSrc = encodeURIComponent(img.src || img.getAttribute("src") || "");
        pinBtn.href = "https://www.pinterest.com/pin/create/button/?url=" + pageUrl + "&media=" + mediaSrc + "&description=" + pageTitle;
        pinBtn.target = "_blank";
        pinBtn.rel = "noopener noreferrer";
        pinBtn.title = "Save to Pinterest";
        pinBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg><span>Save</span>';
        
        img.parentNode.insertBefore(wrapper, img);
        wrapper.appendChild(img);
        wrapper.appendChild(pinBtn);
      }});
    }});
  </script>
</body>
</html>"""



def render_stitch_editorial_hub(
    posts: list[Any],
    categories: Optional[list[dict[str, Any]]] = None,
    title: str = "",
    subtitle: str = "",
    base_url: str = "",
    theme: str = "editorial-warm",
    source_domain: str = "stylesdays.com",
    branding: Optional[Any] = None,
    path_prefix: str = "",
    post_routes: Optional[dict[str, Any]] = None,
    intermediate_routes: Optional[list[Any]] = None,
    **kwargs: Any,
) -> str:
    brand_clean = getattr(branding, "brand_name", "") or "Atelier Maison"
    author_name = getattr(branding, "author_name", "") or "Helene Vane"
    author_bio = getattr(branding, "author_bio", "") or "Principal Interior Architect"
    clean_domain = source_domain.replace("https://", "").replace("http://", "").rstrip("/")
    canonical_base = base_url.rstrip("/") if (base_url and "://" in base_url) else f"https://{clean_domain}"
    hub_title = title or f"The Spatial Journal — {brand_clean} Editorial Hub"
    hub_subtitle = subtitle or "Architecture, Spatial Design & Curated Living • Refined step-by-step spatial blueprints, styling journals, and architectural case studies."

    total_posts = len(posts)
    post_items = list(posts)

    # Lead Hero Post: dynamically bound to the latest/last ingested article
    lead_post = post_items[0] if post_items else None
    if lead_post:
        hero_slug = getattr(lead_post, "slug", None) or (lead_post.get("slug") if isinstance(lead_post, dict) else "")
        hero_title = getattr(lead_post, "title", None) or (lead_post.get("title") if isinstance(lead_post, dict) else hero_slug.replace("-", " ").title())
        hero_excerpt = getattr(lead_post, "excerpt", None) or (lead_post.get("excerpt") if isinstance(lead_post, dict) else "")
        hero_web_path = getattr(lead_post, "web_path", None) or (lead_post.get("web_path") if isinstance(lead_post, dict) else f"/{hero_slug}/")
        lead_link = f"{path_prefix}{hero_web_path}" if path_prefix else hero_web_path
        
        hero_local_img = getattr(lead_post, "local_image_path", None) or (lead_post.get("local_image_path") if isinstance(lead_post, dict) else "")
        hero_remote_img = getattr(lead_post, "image_url", None) or (lead_post.get("image_url") if isinstance(lead_post, dict) else "")
        hero_img_candidate = hero_local_img or hero_remote_img
        
        if hero_img_candidate and (hero_img_candidate.startswith("http://") or hero_img_candidate.startswith("https://")):
            lead_img = hero_img_candidate
        elif hero_img_candidate:
            clean_hero_img = hero_img_candidate.lstrip("/")
            lead_img = f"{path_prefix}/{clean_hero_img}" if path_prefix else f"/{clean_hero_img}"
        elif hero_slug:
            lead_img = f"{path_prefix}/assets/images/{hero_slug}.webp" if path_prefix else f"/assets/images/{hero_slug}.webp"
        else:
            lead_img = "https://lh3.googleusercontent.com/aida-public/AB6AXuCIKFbvPzr53nLf40yg4jHGPl5BccpgtZaQIGHS3tkwqdUoU5Sr6u35YGVsmb9A_6RzdLrnIeqgvBeoBpYw9iecdKG0fc3iaLKR8qOf8spozFbI6JduIDDSfyq_DUth9BEpG-Gy14IzRw2HBupaLIyHiIDEQb_IS7elPtLKOiyrEI6c3_pftWna3paJtK9mOCDeh0fEddi_WPYYVQ1JOHv9gAIoiHm6kKxuyVUJVxbI"
            
        lead_title = hero_title or "The Architectural Sanctuary: Inside 5 Minimalist Living Spaces Harmonizing Raw Earth and Stone"
        lead_excerpt = hero_excerpt or "Exploring how Nordic interior architects pair Roman travertine blocks, untamed French linen, and intentional shadow intervals to craft spaces that silence the modern auditory world."
    else:
        lead_title = "The Architectural Sanctuary: Inside 5 Minimalist Living Spaces Harmonizing Raw Earth and Stone"
        lead_excerpt = "Exploring how Nordic interior architects pair Roman travertine blocks, untamed French linen, and intentional shadow intervals to craft spaces that silence the modern auditory world."
        lead_link = "#editorial-essay"
        lead_img = "https://lh3.googleusercontent.com/aida-public/AB6AXuCIKFbvPzr53nLf40yg4jHGPl5BccpgtZaQIGHS3tkwqdUoU5Sr6u35YGVsmb9A_6RzdLrnIeqgvBeoBpYw9iecdKG0fc3iaLKR8qOf8spozFbI6JduIDDSfyq_DUth9BEpG-Gy14IzRw2HBupaLIyHiIDEQb_IS7elPtLKOiyrEI6c3_pftWna3paJtK9mOCDeh0fEddi_WPYYVQ1JOHv9gAIoiHm6kKxuyVUJVxbI"

    # Category Pill options
    silo_cats = [
        {"slug": "all", "name": "All Guides"},
        {"slug": "bedroom", "name": "Bedroom Inspo"},
        {"slug": "fire-pit", "name": "Fire Pits"},
        {"slug": "patio", "name": "Patio Design"},
        {"slug": "gazebo", "name": "Gazebos & Pergolas"},
        {"slug": "landscaping", "name": "Landscaping Ideas"},
        {"slug": "pool", "name": "Pool & Oasis"},
        {"slug": "lighting", "name": "Curated Lighting"},
    ]

    pills_markup = ""
    for idx, sc in enumerate(silo_cats):
        active_cls = "bg-primary text-on-primary font-semibold shadow-sm text-white" if idx == 0 else "bg-surface-container hover:bg-surface-container-high text-on-surface-variant"
        pills_markup += f"""
        <button class="cat-pill px-5 py-2 rounded-full font-label-md text-label-md uppercase tracking-wider transition-all {active_cls}" data-category="{sc['slug']}" onclick="filterArticles('{sc['slug']}', this)">
          {sc['name']}
        </button>"""

    # Post Cards HTML
    cards_html = ""
    for idx, p in enumerate(post_items):
        slug = getattr(p, "slug", None) or (p.get("slug") if isinstance(p, dict) else "")
        title_val = getattr(p, "title", None) or (p.get("title") if isinstance(p, dict) else slug.replace("-", " ").title())
        excerpt_val = getattr(p, "excerpt", None) or (p.get("excerpt") if isinstance(p, dict) else "")
        category_val = getattr(p, "category", None) or (p.get("category") if isinstance(p, dict) else "Spatial Design")
        web_path_val = getattr(p, "web_path", None) or (p.get("web_path") if isinstance(p, dict) else f"/{slug}/")
        local_img = getattr(p, "local_image_path", None) or (p.get("local_image_path") if isinstance(p, dict) else "")
        
        # Determine category slug for filtering
        cat_slug_lower = (category_val + " " + slug).lower()
        if "bedroom" in cat_slug_lower:
            data_cat = "bedroom"
        elif "fire" in cat_slug_lower or "pit" in cat_slug_lower:
            data_cat = "fire-pit"
        elif "patio" in cat_slug_lower or "paver" in cat_slug_lower:
            data_cat = "patio"
        elif "pergola" in cat_slug_lower or "gazebo" in cat_slug_lower or "cabana" in cat_slug_lower:
            data_cat = "gazebo"
        elif "landscap" in cat_slug_lower or "rock" in cat_slug_lower or "garden" in cat_slug_lower:
            data_cat = "landscaping"
        elif "pool" in cat_slug_lower or "deck" in cat_slug_lower:
            data_cat = "pool"
        elif "light" in cat_slug_lower:
            data_cat = "lighting"
        else:
            data_cat = "essay"

        link = f"{path_prefix}{web_path_val}" if path_prefix else web_path_val
        if local_img and (local_img.startswith("http://") or local_img.startswith("https://")):
            img_src = local_img
        elif local_img:
            clean_img = local_img.lstrip("/")
            img_src = f"{path_prefix}/{clean_img}" if path_prefix else f"/{clean_img}"
        else:
            img_src = f"{path_prefix}/assets/images/{slug}.webp" if path_prefix else f"/assets/images/{slug}.webp"
        
        fallback_svg = f"{path_prefix}/assets/images/placeholder.svg" if path_prefix else "/assets/images/placeholder.svg"
        read_time = f"{5 + (idx % 8)} Min Read"
        author_byline = "Helene Vane" if idx % 2 == 0 else ("Marcus Lindqvist" if idx % 3 == 0 else "Clara Thorne")

        init_style = "display: flex;" if idx < 9 else "display: none;"
        cards_html += f"""
        <article class="article-card group bg-surface-container-lowest rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all flex flex-col border border-surface-container" data-cat="{data_cat}" style="{init_style}">
          <div class="relative aspect-[16/10] overflow-hidden bg-surface-container">
            <a href="{link}" class="block w-full h-full">
              <img alt="{html_lib.escape(title_val)}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" src="{img_src}" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='{fallback_svg}';">
            </a>
            <span class="absolute top-3 left-3 px-3 py-1 bg-surface-container-lowest/90 backdrop-blur-md rounded font-label-sm text-label-sm uppercase tracking-wider font-semibold text-secondary pointer-events-none">
              {html_lib.escape(category_val)}
            </span>
            <span class="absolute bottom-3 right-3 px-2.5 py-0.5 bg-black/65 backdrop-blur-sm rounded text-surface-container-lowest font-label-sm text-[10px] tracking-wider text-white pointer-events-none">
              {read_time}
            </span>
          </div>
          <div class="p-6 flex flex-col flex-1 justify-between">
            <div>
              <h3 class="font-headline-sm text-xl text-on-surface group-hover:text-primary transition-colors mb-3 leading-snug">
                <a href="{link}" class="hover:underline text-inherit block">
                  {html_lib.escape(title_val)}
                </a>
              </h3>
              <p class="font-body-sm text-body-sm text-on-surface-variant leading-relaxed mb-4 text-stone-600 line-clamp-2">
                {html_lib.escape(excerpt_val[:140])}...
              </p>
            </div>
            <div class="pt-4 border-t border-surface-container flex items-center justify-between">
              <span class="font-label-sm text-label-sm text-on-surface-variant text-stone-500">By {author_byline}</span>
              <a class="font-label-sm text-label-sm uppercase tracking-wider text-primary font-semibold hover:underline inline-flex items-center gap-1" href="{link}">
                Read Guide <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
              </a>
            </div>
          </div>
        </article>"""

    # 3 Trending Guides
    trending_items = post_items[:3] if len(post_items) >= 3 else post_items
    trending_html = ""
    for idx, p in enumerate(trending_items):
        t_slug = getattr(p, "slug", None) or (p.get("slug") if isinstance(p, dict) else "")
        t_title = getattr(p, "title", None) or (p.get("title") if isinstance(p, dict) else t_slug.replace("-", " ").title())
        t_cat = getattr(p, "category", None) or (p.get("category") if isinstance(p, dict) else "Patio Design")
        t_link = f"{path_prefix}/{t_slug}/" if path_prefix else f"/{t_slug}/"
        border_cls = "pt-3 border-t border-surface-container" if idx > 0 else ""
        trending_html += f"""
        <li class="group {border_cls}">
          <a class="flex items-start gap-3" href="{t_link}">
            <span class="font-headline-sm text-xl text-primary font-bold">0{idx+1}</span>
            <div>
              <h4 class="font-body-md text-sm font-semibold text-on-surface group-hover:text-primary transition-colors leading-snug">
                {html_lib.escape(t_title)}
              </h4>
              <span class="font-label-sm text-[11px] text-on-surface-variant text-stone-500">{html_lib.escape(t_cat)} • {4 + idx} min read</span>
            </div>
          </a>
        </li>"""

    # 3 Most Saved Guides
    saved_items = post_items[3:6] if len(post_items) >= 6 else post_items[:3]
    saved_html = ""
    saved_counts = ["1,420", "980", "2,150"]
    for idx, p in enumerate(saved_items):
        s_slug = getattr(p, "slug", None) or (p.get("slug") if isinstance(p, dict) else "")
        s_title = getattr(p, "title", None) or (p.get("title") if isinstance(p, dict) else s_slug.replace("-", " ").title())
        s_link = f"{path_prefix}/{s_slug}/" if path_prefix else f"/{s_slug}/"
        border_cls = "pt-3 border-t border-surface-container" if idx > 0 else ""
        cnt = saved_counts[idx % len(saved_counts)]
        saved_html += f"""
        <li class="group {border_cls}">
          <a class="flex items-start gap-3" href="{s_link}">
            <span class="material-symbols-outlined text-secondary text-[20px] shrink-0 text-emerald-800">check_circle</span>
            <div>
              <h4 class="font-body-md text-sm font-semibold text-on-surface group-hover:text-primary transition-colors leading-snug">
                {html_lib.escape(s_title)}
              </h4>
              <span class="font-label-sm text-[11px] text-on-surface-variant text-stone-500">Saved {cnt} times</span>
            </div>
          </a>
        </li>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
  <meta content="web_standard" name="shell-type"/>
  <title>{html_lib.escape(hub_title)}</title>
  <meta name="description" content="{html_lib.escape(hub_subtitle)}"/>
  <meta name="robots" content="index, follow"/>
  <link rel="canonical" href="{canonical_base}/"/>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏛️</text></svg>"/>
  
  <link href="https://fonts.googleapis.com" rel="preconnect"/>
  <link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap" rel="stylesheet"/>
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
  
  <script src="https://cdn.tailwindcss.com"></script>
  <script id="tailwind-config">
    tailwind.config = {{
      darkMode: "class",
      theme: {{
        extend: {{
          colors: {{
            "surface-container-high": "#e8e8ea",
            "on-error-container": "#93000a",
            "primary-container": "#b35c41",
            "inverse-on-surface": "#f0f0f3",
            "primary-fixed": "#ffdbd0",
            "error": "#ba1a1a",
            "on-error": "#ffffff",
            "surface-container": "#eeeef0",
            "on-secondary-container": "#5d6853",
            "outline-variant": "#dbc1ba",
            "on-primary-fixed": "#3a0a00",
            "surface-container-lowest": "#ffffff",
            "on-tertiary-fixed-variant": "#4f4538",
            "surface-dim": "#d9dadc",
            "secondary-container": "#dbe7cc",
            "tertiary-fixed-dim": "#d2c4b3",
            "primary-fixed-dim": "#ffb59f",
            "on-secondary-fixed": "#151e0e",
            "on-primary-fixed-variant": "#793019",
            "on-primary": "#ffffff",
            "background": "#FAF8F5",
            "surface-variant": "#e2e2e5",
            "on-secondary": "#ffffff",
            "on-tertiary-fixed": "#221a0f",
            "surface-tint": "#97472e",
            "on-tertiary": "#ffffff",
            "on-primary-container": "#fffbff",
            "error-container": "#ffdad6",
            "on-surface": "#1a1c1e",
            "tertiary-fixed": "#efe0ce",
            "on-tertiary-container": "#fffbff",
            "primary": "#94452c",
            "secondary-fixed-dim": "#bfcab1",
            "surface-container-low": "#f3f3f6",
            "secondary": "#57624d",
            "tertiary-container": "#7e7364",
            "inverse-surface": "#2f3133",
            "outline": "#88726c",
            "secondary-fixed": "#dbe7cc",
            "surface-container-highest": "#e2e2e5",
            "on-background": "#1a1c1e",
            "surface-bright": "#FAF8F5",
            "on-surface-variant": "#55433e",
            "surface": "#FAF8F5",
            "on-secondary-fixed-variant": "#3f4a37",
            "inverse-primary": "#ffb59f",
            "tertiary": "#655a4c"
          }},
          borderRadius: {{
            "DEFAULT": "0.125rem",
            "lg": "0.25rem",
            "xl": "0.5rem",
            "full": "0.75rem"
          }},
          spacing: {{
            "space-lg": "2rem",
            "space-sm": "0.75rem",
            "space-xs": "0.375rem",
            "gutter": "1.5rem",
            "margin-mobile": "1.25rem",
            "space-md": "1.25rem",
            "gutter-mobile": "1rem",
            "margin": "3rem",
            "space-xl": "3.5rem"
          }},
          fontFamily: {{
            "body-lg": ["DM Sans", "sans-serif"],
            "display-hero": ["Playfair Display", "Georgia", "serif"],
            "headline-sm": ["Playfair Display", "Georgia", "serif"],
            "label-sm": ["DM Sans", "sans-serif"],
            "label-md": ["DM Sans", "sans-serif"],
            "body-md": ["DM Sans", "sans-serif"],
            "headline-md": ["Playfair Display", "Georgia", "serif"],
            "display-hero-mobile": ["Playfair Display", "Georgia", "serif"],
            "headline-lg": ["Playfair Display", "Georgia", "serif"],
            "headline-lg-mobile": ["Playfair Display", "Georgia", "serif"],
            "body-sm": ["DM Sans", "sans-serif"]
          }}
        }}
      }}
    }};
  </script>
  <style>
    @layer base {{
      html, body {{ margin:0; padding:0; }}
      body {{ overscroll-behavior: none; font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #FAF8F5; color: #1a1c1e; }}
    }}
    ::-webkit-scrollbar {{ display: none; }}
    .font-serif-editorial {{ font-family: 'Playfair Display', Georgia, serif; }}
  </style>
</head>
<body class="bg-surface font-body-md text-on-surface antialiased selection:bg-primary-fixed selection:text-on-primary-fixed">

  <!-- TOP EDITORIAL NOTICE BAR -->
  <header class="fixed top-0 left-0 right-0 z-50 bg-surface/95 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] border-b border-surface-container">
    <div class="bg-surface-container-high/70 py-1.5 px-margin-mobile lg:px-margin text-center transition-colors">
      <div class="max-w-[1440px] mx-auto flex items-center justify-center text-on-surface-variant font-label-sm text-label-sm uppercase tracking-widest text-[11px] px-4">
        <p class="text-center font-label-sm text-label-sm tracking-widest text-on-surface-variant">
          Architecture, Spatial Design & Curated Living • 
          <a class="underline underline-offset-4 hover:text-primary transition-colors font-semibold" href="#newsletter">Subscribe to Print & Digital Dispatch</a>
        </p>
      </div>
    </div>

    <!-- Main Navigation Bar -->
    <div class="h-20 max-w-[1440px] mx-auto px-margin-mobile lg:px-margin flex items-center justify-between gap-space-md px-4 sm:px-8">
      <!-- Magazine Branding -->
      <div class="flex items-center gap-space-md flex-shrink-0">
        <a class="flex items-center gap-3 group" href="{path_prefix}/">
          <div class="w-9 h-9 rounded-full bg-primary text-on-primary flex items-center justify-center font-bold text-sm shadow-xs font-serif-editorial text-white">
            AM
          </div>
          <div class="flex flex-col">
            <span class="font-headline-sm text-headline-sm tracking-tight text-on-surface group-hover:text-primary transition-colors leading-none font-serif-editorial text-lg font-bold">
              {html_lib.escape(brand_clean)}
            </span>
            <span class="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant mt-0.5 text-[10px] text-stone-500">
              The Spatial Journal • Editorial Hub
            </span>
          </div>
        </a>
      </div>

      <!-- Journal Topics Navigation -->
      <nav class="hidden 2xl:flex items-center gap-6 overflow-x-auto scrollbar-none text-xs uppercase tracking-wider font-semibold">
        <a class="text-primary font-semibold border-b-2 border-primary py-1" href="#guides-feed">All Stories</a>
        <a class="text-stone-600 hover:text-on-surface py-1 transition-colors" href="#guides-feed" onclick="filterArticles('bedroom')">Bedroom Inspo</a>
        <a class="text-stone-600 hover:text-on-surface py-1 transition-colors" href="#guides-feed" onclick="filterArticles('fire-pit')">Fire Pits</a>
        <a class="text-stone-600 hover:text-on-surface py-1 transition-colors" href="#guides-feed" onclick="filterArticles('patio')">Patio Design</a>
        <a class="text-stone-600 hover:text-on-surface py-1 transition-colors" href="#guides-feed" onclick="filterArticles('gazebo')">Gazebos & Pergolas</a>
        <a class="text-stone-600 hover:text-on-surface py-1 transition-colors" href="#guides-feed" onclick="filterArticles('landscaping')">Landscaping</a>
        <a class="text-stone-600 hover:text-on-surface py-1 transition-colors" href="#guides-feed" onclick="filterArticles('pool')">Pool & Oasis</a>
        <a class="text-stone-600 hover:text-on-surface py-1 transition-colors" href="#editorial-essay">Architect Essays</a>
      </nav>

      <!-- Editorial Search & Reading Actions -->
      <div class="flex items-center gap-space-sm lg:gap-space-md">
        <div class="relative hidden lg:flex items-center bg-surface-container-low rounded-lg px-3.5 py-2 w-64 border border-outline-variant/40 focus-within:border-primary">
          <span class="material-symbols-outlined text-[18px] text-on-surface-variant mr-2 text-stone-400">search</span>
          <input class="w-full bg-transparent border-0 outline-none font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant/70 text-xs" id="editorial-search" onkeyup="handleSearch(this.value)" placeholder="Search 50+ space guides..." type="text"/>
        </div>
        <button aria-label="Saved Guides" class="relative p-2 text-on-surface-variant hover:text-on-surface transition-colors" onclick="showQuickToast('Reading List: 4 saved guides ready to read')" title="Your Reading List" type="button">
          <span class="material-symbols-outlined text-[22px]">bookmark</span>
          <span class="absolute top-1 right-1 w-4 h-4 rounded-full bg-secondary text-on-secondary font-label-sm text-[9px] flex items-center justify-center font-bold text-white">4</span>
        </button>
        <a class="hidden sm:inline-flex items-center gap-1.5 px-4 py-2 bg-primary hover:bg-primary-container text-white rounded-lg font-label-md text-label-md uppercase tracking-wider font-semibold transition-all text-xs shadow-xs" href="#newsletter">
          <span class="material-symbols-outlined text-[16px]">mail</span>
          Subscribe Free
        </a>
      </div>
    </div>
  </header>

  <main class="w-full pt-28 bg-surface min-h-screen">
    <div class="flex flex-col w-full">

      <!-- SECTION 1: EDITORIAL LEAD STORY / MAGAZINE HERO -->
      <section class="relative w-full max-w-[1440px] mx-auto px-margin-mobile lg:px-margin mb-space-xl px-4 sm:px-8">
        <div class="relative rounded-2xl overflow-hidden bg-surface-container-low border border-surface-container shadow-sm">
          <div class="relative w-full min-h-[580px] lg:min-h-[640px] flex items-end">
            <!-- Hero Lead Image -->
            <div class="absolute inset-0 bg-cover bg-center" style="background-image: url('{lead_img}');"></div>
            <!-- Atmospheric Dark Editorial Gradient -->
            <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/55 to-black/20"></div>
            <!-- Lead Story Metadata & Excerpt -->
            <div class="relative z-10 p-6 md:p-12 lg:p-16 max-w-4xl text-white">
              <h1 class="font-serif-editorial text-3xl sm:text-4xl lg:text-5xl text-white tracking-tight mb-5 leading-tight font-bold">
                {html_lib.escape(lead_title)}
              </h1>
              <p class="font-body-lg text-body-md sm:text-body-lg text-stone-200 max-w-2xl mb-8 leading-relaxed text-sm sm:text-base">
                {html_lib.escape(lead_excerpt)}
              </p>
              <div class="flex flex-wrap items-center gap-4 pt-2">
                <a class="inline-flex items-center gap-2.5 px-8 py-3.5 bg-white text-stone-900 hover:bg-primary hover:text-white rounded-lg font-label-md text-label-md uppercase tracking-wider font-semibold transition-all shadow-md text-xs" href="{lead_link}">
                  <span>Read Full Essay</span>
                  <span class="material-symbols-outlined text-[18px]">arrow_forward</span>
                </a>
                <div class="flex items-center gap-3 py-2 px-3 bg-black/40 backdrop-blur-md rounded-lg border border-white/10">
                  <div class="w-8 h-8 rounded-full bg-secondary text-white flex items-center justify-center font-bold font-serif-editorial text-xs">
                    HV
                  </div>
                  <div class="text-left">
                    <p class="font-label-sm text-xs font-semibold text-white leading-none">{html_lib.escape(author_name)}</p>
                    <p class="font-label-sm text-[10px] text-stone-300 uppercase tracking-widest mt-0.5">{html_lib.escape(author_bio)}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- SECTION 2: TOPIC SILOS & CATEGORIES SUMMARY -->
      <section class="w-full max-w-[1440px] mx-auto px-margin-mobile lg:px-margin mb-12 px-4 sm:px-8">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-3 border-b border-surface-container">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-[20px]">folder_copy</span>
            <h2 class="font-label-md text-label-md uppercase tracking-widest text-on-surface font-semibold text-xs text-stone-800">
              Topic Silos & Categories
            </h2>
          </div>
          <span class="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider text-xs text-stone-500">
            Curated Home & Garden Architectural Taxonomy
          </span>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('bedroom')">
            <div>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Bedroom Inspo Guides</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">14 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('fire-pit')">
            <div>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Fire Pits & Hearths</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">10 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('patio')">
            <div>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Patio & Pavers Guides</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">21 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('gazebo')">
            <div>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Gazebos & Pergolas</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">13 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('landscaping')">
            <div>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Landscaping Ideas</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">17 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('pool')">
            <div>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Pool & Backyard Oasis</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">19 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('lighting')">
            <div>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Lighting & Lumens</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">8 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('essay')">
            <div>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Architect Essays</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">15 essays published</span>
          </button>
        </div>
      </section>

      <!-- SECTION 3: ALL PUBLISHED GUIDES & CATEGORY FILTER PILL BAR -->
      <section class="w-full max-w-[1440px] mx-auto px-margin-mobile lg:px-margin mb-8 px-4 sm:px-8" id="guides-feed">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 class="font-serif-editorial text-2xl sm:text-3xl font-bold text-on-surface tracking-tight">All Published Guides</h2>
            <p class="font-body-sm text-body-sm text-on-surface-variant mt-1 text-stone-500 text-xs">
              Refined step-by-step spatial blueprints, styling journals, and architectural case studies.
            </p>
          </div>
          <div class="flex items-center gap-3">
            <span class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest text-xs font-bold text-stone-500" id="article-count-badge">
              {total_posts} Guides
            </span>
            <button class="p-2 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface transition-colors" onclick="showQuickToast('Saved feed view to reading bookmarks')" title="Bookmark feed">
              <span class="material-symbols-outlined text-[18px]">bookmark_add</span>
            </button>
          </div>
        </div>

        <!-- Pill Nav Bar -->
        <div class="flex items-center gap-2 overflow-x-auto pb-3 scrollbar-none" id="category-pills">
          {pills_markup}
        </div>
      </section>

      <!-- SECTION 4: EDITORIAL GUIDE ARTICLES FEED -->
      <section class="w-full max-w-[1440px] mx-auto px-margin-mobile lg:px-margin mb-space-xl px-4 sm:px-8">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" id="article-grid">
          {cards_html}
        </div>

        <!-- Pagination & Index Indicator -->
        <div class="mt-12 flex flex-col sm:flex-row items-center justify-between gap-4 p-4 bg-surface-container-low rounded-xl text-xs" id="pagination-wrapper">
          <span class="font-body-sm text-body-sm text-stone-500" id="showing-text">
            Showing 1–{min(9, total_posts)} of {total_posts} published spatial blueprints
          </span>
          <div class="flex items-center gap-2" id="pagination-controls">
            <button disabled class="px-3 py-2 bg-surface-container/50 text-stone-400 rounded-lg font-label-md text-xs uppercase tracking-wider cursor-not-allowed inline-flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">chevron_left</span> Prev
            </button>
            <button class="px-3.5 py-2 bg-stone-900 text-white rounded-lg font-label-md text-xs uppercase tracking-wider font-bold shadow-xs">1</button>
            <button onclick="goToPage(2)" class="px-3.5 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-lg font-label-md text-xs uppercase tracking-wider transition-colors">2</button>
            <button onclick="goToPage(3)" class="px-3.5 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-lg font-label-md text-xs uppercase tracking-wider transition-colors">3</button>
            <span class="px-1 text-stone-400">...</span>
            <button onclick="goToPage({max(1, (total_posts + 8) // 9)})" class="px-3.5 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-lg font-label-md text-xs uppercase tracking-wider transition-colors">{max(1, (total_posts + 8) // 9)}</button>
            <button onclick="goToPage(2)" class="px-3 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-lg font-label-md text-xs uppercase tracking-wider transition-colors inline-flex items-center gap-1">
              Next <span class="material-symbols-outlined text-[16px]">chevron_right</span>
            </button>
          </div>
        </div>
      </section>

      <!-- SECTION 5: DEEP-DIVE ARCHITECTURAL ESSAY & PHOTO SPREAD -->
      <section class="w-full bg-surface-container py-space-xl px-4 sm:px-8 py-16" id="editorial-essay">
        <div class="max-w-[1440px] mx-auto">
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
            <!-- Longform Essay Content Column -->
            <div class="lg:col-span-7 flex flex-col justify-center">
              <div class="inline-flex items-center gap-2 text-primary font-label-sm text-label-sm uppercase tracking-widest font-semibold mb-3 text-xs">
                <span class="material-symbols-outlined text-[16px]">edit_note</span>
                Longform Architectural Monograph
              </div>
              <h2 class="font-serif-editorial text-3xl sm:text-4xl text-on-surface tracking-tight mb-4 font-bold">
                Designing for Quiet Grandeur: The Dialogue Between Volume & Earth
              </h2>
              <div class="flex items-center gap-4 pb-6 border-b border-surface-container-high mb-6 text-stone-500 font-label-sm text-xs">
                <span>By {html_lib.escape(author_name)}</span>
                <span>•</span>
                <span>November 2025</span>
                <span>•</span>
                <span>Reading Time: 12 min</span>
              </div>
              <p class="font-body-lg text-stone-800 leading-relaxed mb-6 text-base">
                Modern domestic spaces suffer from an insidious disease: auditory and visual chatter. We inhabit rooms encrusted with disposable decor that exists solely to fill square footage rather than elevate the spirit. True spatial grandeur is not achieved through excess ornament, but through radical restraint.
              </p>
              <blockquote class="my-4 p-6 bg-surface-container-lowest rounded-xl border-l-4 border-primary bg-white shadow-xs">
                <p class="font-serif-editorial text-lg italic text-stone-900 leading-snug">
                  "We do not decorate a room; we modulate the frequency of its silence with mineral weight and indirect light."
                </p>
                <cite class="block mt-3 font-label-sm text-xs uppercase tracking-wider text-secondary font-semibold not-italic text-emerald-800">
                  — {html_lib.escape(author_name)}, {html_lib.escape(author_bio)} • Copenhagen Studio
                </cite>
              </blockquote>
              <p class="font-body-md text-stone-600 leading-relaxed mb-6 text-sm">
                When travertine stone is left unfilled, its porous channels capture ambient light at low afternoon sun angles. When paired with heavy unbleached Belgian linen and raw lime plaster walls, the entire living volume acts as an acoustic baffle, absorbing reverberations and calming the nervous system.
              </p>
              <div class="flex flex-wrap items-center gap-4">
                <button class="inline-flex items-center gap-2 px-6 py-3 bg-stone-900 text-white rounded-lg font-label-md text-xs uppercase tracking-wider font-semibold hover:bg-primary transition-colors" onclick="showQuickToast('Saved complete essay monograph to offline reader')">
                  <span class="material-symbols-outlined text-[18px]">bookmark</span>
                  Save Essay to Reading List
                </button>
                <button class="inline-flex items-center gap-2 px-5 py-3 bg-white hover:bg-surface-container-high text-stone-800 rounded-lg font-label-md text-xs uppercase tracking-wider transition-colors border border-stone-200" onclick="showQuickToast('Essay link copied to clipboard')">
                  <span class="material-symbols-outlined text-[18px]">share</span>
                  Share Monograph
                </button>
              </div>
            </div>

            <!-- Curated Visual Lookbook / Photo Spread -->
            <div class="lg:col-span-5 relative rounded-2xl overflow-hidden shadow-lg aspect-[4/3] lg:aspect-[4/5] bg-surface-container-lowest">
              <img alt="Architectural lime-plastered salon with arched window and travertine table" class="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCh-yfu5Q2QpKs9akTDYDrRZYuLTmd2OLQt6zDf2ncYN3dw0hZxq8MtQJVQjgR-KUk-vyARQqWH6fhU3f0IYE5aB2rrPM_R5C2NAITZoRp1iG-6oP3uJqyH89OfA_PqKxdLMPjmSJVhOoDzEdh1WLY0-71DVaSpsrh7kB_fAlKZ2-9YTHJ54AYx_omSAfXNj2qxmfc2omlqLP7truxlJSpVIOvaMdlYlsvdX8NHObJY"/>
              <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none"></div>
              <div class="absolute bottom-6 left-6 right-6 text-white">
                <span class="font-label-sm text-xs uppercase tracking-widest text-primary-fixed block mb-1 text-amber-200">Figure 4.2 • Case Study</span>
                <p class="font-serif-editorial text-base text-white font-bold">The Ørestad Residence, Denmark</p>
                <p class="font-body-sm text-xs text-stone-300 mt-1">Photograph by Vincent Duprès for The Spatial Journal.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- SECTION 6: TRENDING & CURATORS' PICKS SIDEBAR SPLIT -->
      <section class="w-full max-w-[1440px] mx-auto px-margin-mobile lg:px-margin py-space-xl px-4 sm:px-8 py-16">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Column 1: Trending Space Studies -->
          <div class="bg-surface-container-lowest p-6 rounded-xl border border-surface-container bg-white">
            <div class="flex items-center justify-between pb-4 border-b border-surface-container mb-4">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">trending_up</span>
                <h3 class="font-serif-editorial text-lg text-on-surface font-bold">Trending Guides</h3>
              </div>
              <span class="font-label-sm text-[11px] text-stone-400 uppercase">This Week</span>
            </div>
            <ul class="space-y-4">
              {trending_html}
            </ul>
          </div>

          <!-- Column 2: Most Saved Guides -->
          <div class="bg-surface-container-lowest p-6 rounded-xl border border-surface-container bg-white">
            <div class="flex items-center justify-between pb-4 border-b border-surface-container mb-4">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-secondary text-[20px] text-emerald-800">bookmarks</span>
                <h3 class="font-serif-editorial text-lg text-on-surface font-bold">Most Saved by Readers</h3>
              </div>
              <span class="font-label-sm text-[11px] text-stone-400 uppercase">All Time</span>
            </div>
            <ul class="space-y-4">
              {saved_html}
            </ul>
          </div>

          <!-- Column 3: The Print Archive Edition -->
          <div class="bg-surface-container-lowest p-6 rounded-xl border border-surface-container flex flex-col justify-between bg-white">
            <div>
              <div class="flex items-center justify-between pb-4 border-b border-surface-container mb-4">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined text-tertiary text-[20px] text-stone-600">import_contacts</span>
                  <h3 class="font-serif-editorial text-lg text-on-surface font-bold">Print Edition Archive</h3>
                </div>
                <span class="font-label-sm text-[11px] text-primary uppercase font-bold text-rose-700">Issue 48</span>
              </div>
              <p class="font-body-sm text-stone-600 leading-relaxed mb-4 text-xs">
                Order our heavyweight quarterly print monographs printed on unbleached Swedish cotton paper with archival linen slipcases.
              </p>
              <div class="p-3 bg-stone-100 rounded-lg mb-4 flex items-center justify-between">
                <div>
                  <span class="font-label-sm text-xs font-semibold text-stone-900 block">Issue 48: The Mineral Home</span>
                  <span class="font-label-sm text-[10px] text-stone-500">Quarterly Print Edition • 248 Pages</span>
                </div>
                <span class="material-symbols-outlined text-primary text-[24px]">menu_book</span>
              </div>
            </div>
            <button class="w-full py-2.5 bg-stone-100 hover:bg-stone-200 text-stone-900 rounded-lg font-label-md text-xs uppercase tracking-wider font-semibold transition-colors" onclick="showQuickToast('Print issue dispatch request opened')">
              Request Print Edition Copy
            </button>
          </div>
        </div>
      </section>

      <!-- SECTION 7: EDITORIAL PUBLICATION SUBSCRIPTION BAR -->
      <section class="w-full bg-surface-container-low py-space-xl px-4 sm:px-8 py-16" id="newsletter">
        <div class="max-w-[1440px] mx-auto">
          <div class="bg-surface-container-lowest p-space-lg lg:p-space-xl rounded-2xl border border-surface-container shadow-sm bg-white p-8 sm:p-12">
            <div class="max-w-2xl mx-auto text-center">
              <span class="font-label-sm text-xs uppercase tracking-widest text-primary font-semibold">
                Weekly Spatial Dispatch
              </span>
              <h3 class="font-serif-editorial text-2xl sm:text-3xl text-on-surface mt-2 mb-3 font-bold">
                Join 45,000+ Architects, Designers & Spatial Purists
              </h3>
              <p class="font-body-md text-stone-600 mb-space-md text-sm mb-6">
                Every Friday morning: one deep dive spatial blueprint, two curated acoustic material palettes, and zero advertising or commercial noise.
              </p>
              <form class="flex flex-col sm:flex-row gap-3 max-w-md mx-auto" onsubmit="event.preventDefault(); showQuickToast('Welcome to the Atelier Spatial Dispatch! Check your inbox.');">
                <input class="flex-1 px-4 py-3 rounded-lg bg-stone-100 font-body-sm text-xs text-on-surface placeholder:text-stone-400 outline-none ring-1 ring-stone-200 focus:ring-primary" placeholder="Enter your correspondence email" required="" type="email"/>
                <button class="px-6 py-3 bg-primary text-white font-label-md text-xs uppercase tracking-wider rounded-lg hover:bg-primary-container transition-colors font-semibold shadow-xs" type="submit">
                  Subscribe Free
                </button>
              </form>
              <span class="font-label-sm text-[10px] text-stone-400 uppercase tracking-wider block mt-3">
                Strict privacy protocol • One-click unsubscribe anytime
              </span>
            </div>
          </div>
        </div>
      </section>

    </div>
  </main>

  <!-- MAGAZINE EDITORIAL FOOTER -->
  <footer class="w-full bg-stone-100 text-stone-800 border-t border-stone-200">
    <div class="max-w-[1440px] mx-auto px-4 sm:px-8 pt-12 pb-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 mb-12">
        <div class="lg:col-span-2 pr-0 lg:pr-8">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold text-xs font-serif-editorial">
              AM
            </div>
            <span class="font-serif-editorial text-lg font-bold text-stone-900">The Spatial Journal</span>
          </div>
          <p class="font-body-md text-stone-600 max-w-sm leading-relaxed mb-4 text-xs">
            An independent architectural and home publication dedicated to deliberate proportions, tactile organic materials, and serene interior sanctuaries.
          </p>
          <div class="flex items-center gap-4 text-stone-500 text-xs">
            <span class="font-label-sm text-[11px] uppercase tracking-wider">Editorial Bureaus: New York • Copenhagen • Kyoto</span>
          </div>
        </div>

        <div>
          <h4 class="font-label-md uppercase tracking-wider text-stone-900 font-bold mb-4 text-xs">Published Guides</h4>
          <ul class="space-y-2 font-body-md text-xs text-stone-600">
            <li><a class="hover:text-primary transition-colors" href="#guides-feed" onclick="filterArticles('bedroom')">Bedroom Inspo</a></li>
            <li><a class="hover:text-primary transition-colors" href="#guides-feed" onclick="filterArticles('fire-pit')">Fire Pits & Hearths</a></li>
            <li><a class="hover:text-primary transition-colors" href="#guides-feed" onclick="filterArticles('patio')">Patio & Pavers</a></li>
            <li><a class="hover:text-primary transition-colors" href="#guides-feed" onclick="filterArticles('gazebo')">Gazebos & Pergolas</a></li>
            <li><a class="hover:text-primary transition-colors" href="#guides-feed" onclick="filterArticles('pool')">Pool & Backyard Oasis</a></li>
          </ul>
        </div>

        <div>
          <h4 class="font-label-md uppercase tracking-wider text-stone-900 font-bold mb-4 text-xs">Essays & Theory</h4>
          <ul class="space-y-2 font-body-md text-xs text-stone-600">
            <li><a class="hover:text-primary transition-colors" href="#editorial-essay">Architectural Monograph</a></li>
            <li><a class="hover:text-primary transition-colors" href="#editorial-essay">Acoustic Balance Studies</a></li>
            <li><a class="hover:text-primary transition-colors" href="#editorial-essay">Kelvin Lighting Scale</a></li>
            <li><a class="hover:text-primary transition-colors" href="#editorial-essay">Natural Stone Preservation</a></li>
            <li><a class="hover:text-primary transition-colors" href="#editorial-essay">Writer Submissions & Pitch</a></li>
          </ul>
        </div>

        <div>
          <h4 class="font-label-md uppercase tracking-wider text-stone-900 font-bold mb-4 text-xs">Publication</h4>
          <ul class="space-y-2 font-body-md text-xs text-stone-600">
            <li><a class="hover:text-primary transition-colors" href="#newsletter">Print Issue Archive</a></li>
            <li><a class="hover:text-primary transition-colors" href="#newsletter">Digital Dispatch Feed</a></li>
            <li><a class="hover:text-primary transition-colors" href="#newsletter">Press & Syndication</a></li>
            <li><a class="hover:text-primary transition-colors" href="{path_prefix}/robots.txt">Robots.txt</a></li>
            <li><a class="hover:text-primary transition-colors" href="{path_prefix}/sitemap.xml">Sitemap XML</a></li>
          </ul>
        </div>
      </div>

      <div class="pt-6 flex flex-col md:flex-row items-center justify-between gap-4 text-stone-500 font-label-sm text-[11px] uppercase tracking-wider border-t border-stone-200">
        <p>© 2026 The Spatial Journal • {html_lib.escape(brand_clean)} Editorial. All publication rights reserved.</p>
        <div class="flex items-center gap-4">
          <span>Editorial Ethics</span>
          <span>Privacy Protocol</span>
          <span>Syndication Policy</span>
        </div>
      </div>
    </div>
  </footer>

  <!-- TOAST NOTIFICATION FOR EDITORIAL INTERACTIONS -->
  <div class="fixed bottom-6 right-6 z-50 transform translate-y-24 opacity-0 transition-all duration-300 pointer-events-none bg-stone-900 text-white px-5 py-3.5 rounded-lg shadow-xl flex items-center gap-3" id="toast">
    <span class="material-symbols-outlined text-amber-300">auto_stories</span>
    <span class="font-body-md text-xs" id="toast-message">Article saved to your reading list.</span>
  </div>

  <script>
    const PAGE_SIZE = 9;
    let currentPage = 1;
    let currentCategory = 'all';
    let currentSearch = '';

    function getFilteredCards() {{
      const cards = Array.from(document.querySelectorAll('.article-card'));
      return cards.filter(card => {{
        const cat = (card.getAttribute('data-cat') || '').toLowerCase();
        const text = card.textContent.toLowerCase();
        const matchesCat = (currentCategory === 'all' || cat.includes(currentCategory));
        const matchesSearch = (!currentSearch || text.includes(currentSearch));
        return matchesCat && matchesSearch;
      }});
    }}

    function updateDisplay(scrollToGrid) {{
      const allCards = document.querySelectorAll('.article-card');
      const filtered = getFilteredCards();
      const totalItems = filtered.length;
      const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));

      if (currentPage > totalPages) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;

      const startIndex = (currentPage - 1) * PAGE_SIZE;
      const endIndex = Math.min(startIndex + PAGE_SIZE, totalItems);

      allCards.forEach(c => {{
        c.style.display = 'none';
      }});

      filtered.slice(startIndex, endIndex).forEach(c => {{
        c.style.display = 'flex';
      }});

      const showingText = document.getElementById('showing-text');
      if (showingText) {{
        if (totalItems === 0) {{
          showingText.textContent = 'Showing 0 of 0 published spatial blueprints';
        }} else {{
          showingText.textContent = 'Showing ' + (startIndex + 1) + '–' + endIndex + ' of ' + totalItems + ' published spatial blueprints';
        }}
      }}

      const badge = document.getElementById('article-count-badge');
      if (badge) {{
        badge.textContent = totalItems + ' Guides';
      }}

      renderPaginationButtons(totalPages);

      if (scrollToGrid) {{
        const target = document.getElementById('guides-feed');
        if (target) {{
          target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
      }}
    }}

    function renderPaginationButtons(totalPages) {{
      const container = document.getElementById('pagination-controls');
      if (!container) return;

      if (totalPages <= 1) {{
        container.innerHTML = '<span class="px-3 py-1 text-stone-400 font-label-sm">Page 1 of 1</span>';
        return;
      }}

      let html = '';

      if (currentPage > 1) {{
        html += '<button onclick="goToPage(' + (currentPage - 1) + ')" class="px-3 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-lg font-label-md text-xs uppercase tracking-wider transition-colors inline-flex items-center gap-1"><span class="material-symbols-outlined text-[16px]">chevron_left</span> Prev</button>';
      }} else {{
        html += '<button disabled class="px-3 py-2 bg-surface-container/50 text-stone-400 rounded-lg font-label-md text-xs uppercase tracking-wider cursor-not-allowed inline-flex items-center gap-1"><span class="material-symbols-outlined text-[16px]">chevron_left</span> Prev</button>';
      }}

      for (let i = 1; i <= totalPages; i++) {{
        if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {{
          if (i === currentPage) {{
            html += '<button class="px-3.5 py-2 bg-stone-900 text-white rounded-lg font-label-md text-xs uppercase tracking-wider font-bold shadow-xs">' + i + '</button>';
          }} else {{
            html += '<button onclick="goToPage(' + i + ')" class="px-3.5 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-lg font-label-md text-xs uppercase tracking-wider transition-colors">' + i + '</button>';
          }}
        }} else if (i === currentPage - 2 || i === currentPage + 2) {{
          html += '<span class="px-1 text-stone-400">...</span>';
        }}
      }}

      if (currentPage < totalPages) {{
        html += '<button onclick="goToPage(' + (currentPage + 1) + ')" class="px-3 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-lg font-label-md text-xs uppercase tracking-wider transition-colors inline-flex items-center gap-1">Next <span class="material-symbols-outlined text-[16px]">chevron_right</span></button>';
      }} else {{
        html += '<button disabled class="px-3 py-2 bg-surface-container/50 text-stone-400 rounded-lg font-label-md text-xs uppercase tracking-wider cursor-not-allowed inline-flex items-center gap-1">Next <span class="material-symbols-outlined text-[16px]">chevron_right</span></button>';
      }}

      container.innerHTML = html;
    }}

    function goToPage(page) {{
      currentPage = page;
      updateDisplay(true);
    }}

    function filterArticles(category, element) {{
      currentCategory = category;
      currentPage = 1;

      const pills = document.querySelectorAll('.cat-pill');
      if (element) {{
        pills.forEach(p => {{
          p.classList.remove('bg-primary', 'text-on-primary', 'font-semibold', 'shadow-sm', 'text-white');
          p.classList.add('bg-surface-container', 'text-on-surface-variant');
        }});
        element.classList.remove('bg-surface-container', 'text-on-surface-variant');
        element.classList.add('bg-primary', 'text-on-primary', 'font-semibold', 'shadow-sm', 'text-white');
      }}

      updateDisplay(false);
    }}

    function handleSearch(query) {{
      currentSearch = query.toLowerCase().trim();
      currentPage = 1;
      updateDisplay(false);
    }}

    function showQuickToast(text) {{
      const toast = document.getElementById('toast');
      const msg = document.getElementById('toast-message');
      if (toast && msg) {{
        msg.textContent = text;
        toast.classList.remove('translate-y-24', 'opacity-0');
        toast.classList.add('translate-y-0', 'opacity-100');
        setTimeout(() => {{
          toast.classList.remove('translate-y-0', 'opacity-100');
          toast.classList.add('translate-y-24', 'opacity-0');
        }}, 3200);
      }}
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      updateDisplay(false);
    }});
  </script>
</body>
</html>"""


def render_nordic_studio_hub(
    posts: list[Any],
    categories: Optional[list[dict[str, str]]] = None,
    title: str = "",
    subtitle: str = "",
    base_url: str = "",
    theme: str = "nordic-studio",
    source_domain: str = "thenordroom.com",
    branding: Optional[Any] = None,
    path_prefix: str = "",
    routing_mode: str = "single",
    **kwargs: Any,
) -> str:
    """Renders The Nordroom Scandinavian Homepage Hub with masthead, dynamic cover story, room taxonomy, and 3-col grid."""
    brand_clean = getattr(branding, "brand_name", "") or "THE NORDROOM"
    author_name = getattr(branding, "author_name", "") or "Rachel"
    author_bio = getattr(branding, "author_bio", "") or "Creator of The Nordroom • Interior design specialist passionate about Scandinavian homes, architectural renovations, and spatial curation."
    home_link = f"{path_prefix}/" if path_prefix else "/"
    clean_domain = source_domain.replace("https://", "").replace("http://", "").rstrip("/")
    canonical_base = base_url.rstrip("/") if (base_url and "://" in base_url) else f"https://{clean_domain}"
    hub_title = title or f"{brand_clean} — Scandinavian Interior Design & Home Tours"
    hub_subtitle = subtitle or "Curated Scandinavian interiors, practical room layouts, and inspiring house tours."

    total_posts = len(posts)
    post_items = list(posts)

    # Lead Hero Post: dynamically bound to the latest/last ingested article
    lead_post = post_items[0] if post_items else None
    if lead_post:
        hero_slug = getattr(lead_post, "slug", None) or (lead_post.get("slug") if isinstance(lead_post, dict) else "")
        hero_title = getattr(lead_post, "title", None) or (lead_post.get("title") if isinstance(lead_post, dict) else hero_slug.replace("-", " ").title())
        hero_excerpt = getattr(lead_post, "excerpt", None) or (lead_post.get("excerpt") if isinstance(lead_post, dict) else "")
        hero_cat = getattr(lead_post, "category", None) or (lead_post.get("category") if isinstance(lead_post, dict) else "Home Tour")
        hero_web_path = getattr(lead_post, "web_path", None) or (lead_post.get("web_path") if isinstance(lead_post, dict) else f"/{hero_slug}/")
        lead_link = f"{path_prefix}{hero_web_path}" if path_prefix else hero_web_path

        hero_local_img = getattr(lead_post, "local_image_path", None) or (lead_post.get("local_image_path") if isinstance(lead_post, dict) else "")
        hero_remote_img = getattr(lead_post, "image_url", None) or (lead_post.get("image_url") if isinstance(lead_post, dict) else "")
        hero_img_candidate = hero_local_img or hero_remote_img

        if hero_img_candidate and (hero_img_candidate.startswith("http://") or hero_img_candidate.startswith("https://")):
            lead_img = hero_img_candidate
        elif hero_img_candidate:
            clean_hero_img = hero_img_candidate.lstrip("/")
            lead_img = f"{path_prefix}/{clean_hero_img}" if path_prefix else f"/{clean_hero_img}"
        elif hero_slug:
            lead_img = f"{path_prefix}/assets/images/{hero_slug}.webp" if path_prefix else f"/assets/images/{hero_slug}.webp"
        else:
            lead_img = "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1600&q=80"

        lead_title = hero_title or "Scandinavian Warm Minimalism: 10 Calming Room Concepts in Stockholm"
        lead_excerpt = hero_excerpt or "How raw oak cabinetry, textured lime wash walls, and understated linen textiles create a serene sanctuary that silences everyday auditory noise."
        lead_category = hero_cat
    else:
        lead_title = "Scandinavian Warm Minimalism: 10 Calming Room Concepts in Stockholm"
        lead_excerpt = "How raw oak cabinetry, textured lime wash walls, and understated linen textiles create a serene sanctuary that silences everyday auditory noise."
        lead_link = "#nordic-home-tour"
        lead_category = "Home Tour"
        lead_img = "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1600&q=80"

    # Category pills
    silo_cats = [
        {"slug": "all", "name": "All Guides"},
        {"slug": "living-room", "name": "Living Rooms"},
        {"slug": "bedroom", "name": "Bedrooms"},
        {"slug": "kitchen", "name": "Kitchens & Pantries"},
        {"slug": "bathroom", "name": "Bathrooms"},
        {"slug": "garden", "name": "Garden & Outdoor"},
        {"slug": "small-spaces", "name": "Small Spaces"},
        {"slug": "colors", "name": "Color Trends"},
    ]

    pills_markup = ""
    for idx, sc in enumerate(silo_cats):
        active_cls = "bg-[#1C1C1C] text-white font-semibold shadow-xs" if idx == 0 else "bg-white hover:bg-[#F4F3F0] text-[#1C1C1C] border border-[#EBEBEA]"
        pills_markup += f'''
        <button class="cat-pill px-4 py-2 rounded-full text-xs uppercase tracking-wider font-medium transition-all {active_cls}" onclick="filterArticles('{sc['slug']}', this)">
          {sc['name']}
        </button>
        '''

    # Cards grid
    cards_html = ""
    for idx, p in enumerate(post_items):
        slug_val = getattr(p, "slug", None) or (p.get("slug") if isinstance(p, dict) else "")
        title_val = getattr(p, "title", None) or (p.get("title") if isinstance(p, dict) else slug_val.replace("-", " ").title())
        excerpt_val = getattr(p, "excerpt", None) or (p.get("excerpt") if isinstance(p, dict) else "")
        category_val = getattr(p, "category", None) or (p.get("category") if isinstance(p, dict) else "Home Tour")
        web_path_val = getattr(p, "web_path", None) or (p.get("web_path") if isinstance(p, dict) else f"/{slug_val}/")
        link = f"{path_prefix}{web_path_val}" if path_prefix else web_path_val

        local_img = getattr(p, "local_image_path", None) or (p.get("local_image_path") if isinstance(p, dict) else "")
        remote_img = getattr(p, "image_url", None) or (p.get("image_url") if isinstance(p, dict) else "")
        raw_img = local_img or remote_img
        if raw_img and (raw_img.startswith("http://") or raw_img.startswith("https://")):
            img_src = raw_img
        elif raw_img:
            clean_img = raw_img.lstrip("/")
            img_src = f"{path_prefix}/{clean_img}" if path_prefix else f"/{clean_img}"
        elif slug_val:
            img_src = f"{path_prefix}/assets/images/{slug_val}.webp" if path_prefix else f"/assets/images/{slug_val}.webp"
        else:
            img_src = "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=800&q=80"

        fallback_svg = _resolve_fallback_svg(slug_val, path_prefix)
        data_cat = category_val.lower().replace(" ", "-")
        init_style = "display: flex;" if idx < 12 else "display: none;"

        cards_html += f'''
        <article class="article-card group bg-white rounded-lg overflow-hidden border border-[#EBEBEA] hover:border-[#8C6D53]/50 hover:shadow-sm transition-all flex flex-col" data-cat="{data_cat}" style="{init_style}">
          <a href="{link}" class="relative aspect-[4/3] overflow-hidden bg-[#F4F3F0] block">
            <img alt="{html_lib.escape(title_val)}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" src="{img_src}" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='{fallback_svg}';">
            <span class="absolute top-3 left-3 px-2.5 py-1 bg-white/95 backdrop-blur-sm rounded text-[10px] font-semibold tracking-wider uppercase text-[#1C1C1C] border border-[#EBEBEA] shadow-xs">
              {html_lib.escape(category_val)}
            </span>
          </a>
          <div class="p-5 flex flex-col flex-1 justify-between">
            <div>
              <span class="text-[10px] tracking-[0.16em] uppercase text-[#8C6D53] font-semibold block mb-2">{html_lib.escape(category_val)}</span>
              <a href="{link}" class="block group-hover:text-[#8C6D53] transition-colors">
                <h3 class="font-serif text-lg sm:text-xl font-bold text-[#1C1C1C] leading-snug mb-2.5 line-clamp-2">
                  {html_lib.escape(title_val)}
                </h3>
              </a>
              <p class="text-xs sm:text-sm text-[#686866] leading-relaxed line-clamp-2 mb-4">
                {html_lib.escape(excerpt_val)}
              </p>
            </div>
            <div class="pt-3 border-t border-[#F4F3F0] flex items-center justify-between text-xs text-[#686866]">
              <span class="italic font-serif">By {html_lib.escape(author_name)}</span>
              <a href="{link}" class="inline-flex items-center gap-1 font-semibold text-[11px] tracking-wider uppercase text-[#8C6D53] hover:underline">
                Read Tour &rarr;
              </a>
            </div>
          </div>
        </article>
        '''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_lib.escape(hub_title)}</title>
  <meta name="description" content="{html_lib.escape(hub_subtitle)}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{canonical_base}/">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 100 100\'><text y=\'.9em\' font-size=\'90\'>&#x1F3E0;</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{
      background-color: #FBFBFA;
      color: #1C1C1C;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    .font-serif {{
      font-family: 'Cormorant Garamond', Georgia, serif;
    }}
  </style>
</head>
<body class="flex flex-col min-h-screen">

  <!-- TOP UTILITY STRIP -->
  <div class="w-full bg-[#1C1C1C] text-white py-2 px-4 sm:px-8 text-center sm:text-left flex flex-col sm:flex-row items-center justify-between text-[11px] tracking-[0.18em] uppercase font-medium">
    <div>SCANDINAVIAN INTERIORS • HOME TOURS • DESIGN INSPIRATION</div>
    <div class="hidden sm:flex items-center gap-4 text-stone-300">
      <a href="{home_link}" class="hover:text-white transition-colors">Home Tours</a>
      <span>•</span>
      <a href="#newsletter" class="hover:text-white transition-colors">Newsletter</a>
      <span>•</span>
      <a href="https://pinterest.com" target="_blank" rel="noopener noreferrer" class="hover:text-white transition-colors">Pinterest</a>
      <span>•</span>
      <a href="{home_link}" class="hover:text-white transition-colors">About</a>
    </div>
  </div>

  <!-- CENTERED THE NORDROOM MASTHEAD -->
  <header class="w-full bg-white border-b border-[#EBEBEA] py-8 px-4 text-center">
    <div class="max-w-[1200px] mx-auto">
      <span class="text-[11px] tracking-[0.25em] uppercase text-[#8C6D53] font-semibold block mb-2">Nordic Living & Interior Architecture</span>
      <h1 class="font-serif text-4xl sm:text-5xl md:text-6xl tracking-[0.16em] font-medium text-[#1C1C1C] uppercase mb-2">
        <a href="{home_link}" class="hover:opacity-90 transition-opacity">{html_lib.escape(brand_clean)}</a>
      </h1>
      <p class="text-xs sm:text-sm text-[#686866] italic font-serif">Curated Interior Design, Space Transformations & Scandinavian Living</p>
    </div>
  </header>

  <!-- NAVIGATION & ROOM MENU -->
  <nav class="w-full bg-white border-b border-[#EBEBEA] sticky top-0 z-30 shadow-xs">
    <div class="max-w-[1200px] mx-auto px-4 flex items-center justify-between overflow-x-auto py-3 gap-6 text-[12px] font-semibold tracking-[0.14em] uppercase text-[#1C1C1C]">
      <div class="flex items-center gap-6 whitespace-nowrap">
        <a href="{home_link}" class="text-[#8C6D53] font-bold">All Guides</a>
        <button onclick="filterArticles('living')" class="hover:text-[#8C6D53] transition-colors">Living Rooms</button>
        <button onclick="filterArticles('bedroom')" class="hover:text-[#8C6D53] transition-colors">Bedrooms</button>
        <button onclick="filterArticles('kitchen')" class="hover:text-[#8C6D53] transition-colors">Kitchens</button>
        <button onclick="filterArticles('bathroom')" class="hover:text-[#8C6D53] transition-colors">Bathrooms</button>
        <button onclick="filterArticles('garden')" class="hover:text-[#8C6D53] transition-colors">Garden & Outdoor</button>
        <button onclick="filterArticles('small')" class="hover:text-[#8C6D53] transition-colors">Small Spaces</button>
        <button onclick="filterArticles('color')" class="hover:text-[#8C6D53] transition-colors">Color Trends</button>
      </div>
      <div class="hidden sm:flex items-center gap-2">
        <input type="text" id="nord-search-input" oninput="handleSearch(this.value)" placeholder="Search rooms..." class="px-3 py-1 text-xs border border-[#EBEBEA] rounded-full focus:outline-none focus:border-[#8C6D53] w-36 tracking-normal">
      </div>
    </div>
  </nav>

  <main class="flex-1 w-full py-8 sm:py-12">

    <!-- HERO COVER STORY (LATEST POST) -->
    <section class="max-w-[1200px] mx-auto px-4 sm:px-8 mb-14">
      <div class="bg-white border border-[#EBEBEA] rounded-xl overflow-hidden shadow-xs hover:border-[#8C6D53]/50 transition-all">
        <div class="grid grid-cols-1 lg:grid-cols-12 items-center">
          <div class="lg:col-span-7 aspect-[16/10] overflow-hidden bg-[#F4F3F0]">
            <a href="{lead_link}">
              <img src="{lead_img}" alt="{html_lib.escape(lead_title)}" class="w-full h-full object-cover hover:scale-103 transition-transform duration-700" fetchpriority="high">
            </a>
          </div>
          <div class="lg:col-span-5 p-6 sm:p-10 flex flex-col justify-between">
            <div>
              <span class="text-[11px] tracking-[0.22em] uppercase font-semibold text-[#8C6D53] block mb-2">Featured Home Tour • {html_lib.escape(lead_category)}</span>
              <a href="{lead_link}">
                <h2 class="font-serif text-2xl sm:text-3xl md:text-4xl font-bold text-[#1C1C1C] leading-[1.2] mb-4 hover:text-[#8C6D53] transition-colors">
                  {html_lib.escape(lead_title)}
                </h2>
              </a>
              <p class="text-xs sm:text-sm text-[#686866] leading-relaxed mb-6 font-serif italic text-base">
                {html_lib.escape(lead_excerpt)}
              </p>
            </div>
            <div class="pt-4 border-t border-[#F4F3F0] flex items-center justify-between">
              <span class="text-xs text-[#686866]">By {html_lib.escape(author_name)} • 4 Min Read</span>
              <a href="{lead_link}" class="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-[#8C6D53] hover:underline">
                Read Tour &rarr;
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CURATED ROOM TAXONOMY GRID (ZERO RAW SLUGS) -->
    <section class="max-w-[1200px] mx-auto px-4 sm:px-8 mb-14">
      <div class="flex items-center justify-between pb-3 mb-6 border-b border-[#EBEBEA]">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-[#8C6D53] text-[20px]">roofing</span>
          <h2 class="text-xs font-semibold tracking-widest uppercase text-[#1C1C1C]">Curated Room Collections</h2>
        </div>
        <span class="text-[11px] tracking-wider uppercase text-[#686866]">The Nordroom Architectural Taxonomy</span>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        <button class="p-4 bg-white hover:bg-[#FBFBFA] border border-[#EBEBEA] hover:border-[#8C6D53] rounded-lg text-left transition-all group flex flex-col justify-between" onclick="filterArticles('living')">
          <div>
            <h3 class="font-serif text-sm sm:text-base text-[#1C1C1C] font-semibold leading-snug group-hover:text-[#8C6D53] transition-colors">Living Rooms</h3>
          </div>
          <span class="text-[11px] text-[#8C6D53] font-medium mt-3 block">18 curated tours</span>
        </button>
        <button class="p-4 bg-white hover:bg-[#FBFBFA] border border-[#EBEBEA] hover:border-[#8C6D53] rounded-lg text-left transition-all group flex flex-col justify-between" onclick="filterArticles('bedroom')">
          <div>
            <h3 class="font-serif text-sm sm:text-base text-[#1C1C1C] font-semibold leading-snug group-hover:text-[#8C6D53] transition-colors">Bedrooms</h3>
          </div>
          <span class="text-[11px] text-[#8C6D53] font-medium mt-3 block">14 curated guides</span>
        </button>
        <button class="p-4 bg-white hover:bg-[#FBFBFA] border border-[#EBEBEA] hover:border-[#8C6D53] rounded-lg text-left transition-all group flex flex-col justify-between" onclick="filterArticles('kitchen')">
          <div>
            <h3 class="font-serif text-sm sm:text-base text-[#1C1C1C] font-semibold leading-snug group-hover:text-[#8C6D53] transition-colors">Kitchens & Pantries</h3>
          </div>
          <span class="text-[11px] text-[#8C6D53] font-medium mt-3 block">12 design guides</span>
        </button>
        <button class="p-4 bg-white hover:bg-[#FBFBFA] border border-[#EBEBEA] hover:border-[#8C6D53] rounded-lg text-left transition-all group flex flex-col justify-between" onclick="filterArticles('garden')">
          <div>
            <h3 class="font-serif text-sm sm:text-base text-[#1C1C1C] font-semibold leading-snug group-hover:text-[#8C6D53] transition-colors">Garden & Outdoor</h3>
          </div>
          <span class="text-[11px] text-[#8C6D53] font-medium mt-3 block">21 outdoor spaces</span>
        </button>
        <button class="p-4 bg-white hover:bg-[#FBFBFA] border border-[#EBEBEA] hover:border-[#8C6D53] rounded-lg text-left transition-all group flex flex-col justify-between" onclick="filterArticles('small')">
          <div>
            <h3 class="font-serif text-sm sm:text-base text-[#1C1C1C] font-semibold leading-snug group-hover:text-[#8C6D53] transition-colors">Small Spaces</h3>
          </div>
          <span class="text-[11px] text-[#8C6D53] font-medium mt-3 block">16 space hacks</span>
        </button>
        <button class="p-4 bg-white hover:bg-[#FBFBFA] border border-[#EBEBEA] hover:border-[#8C6D53] rounded-lg text-left transition-all group flex flex-col justify-between" onclick="filterArticles('color')">
          <div>
            <h3 class="font-serif text-sm sm:text-base text-[#1C1C1C] font-semibold leading-snug group-hover:text-[#8C6D53] transition-colors">Color Trends</h3>
          </div>
          <span class="text-[11px] text-[#8C6D53] font-medium mt-3 block">9 paint palettes</span>
        </button>
      </div>
    </section>

    <!-- PUBLISHED GUIDES GRID -->
    <section class="max-w-[1200px] mx-auto px-4 sm:px-8 mb-16" id="guides-feed">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-6 border-b border-[#EBEBEA] gap-4">
        <div>
          <span class="text-[11px] tracking-[0.2em] uppercase font-semibold text-[#8C6D53] block mb-1">Scandinavian Living Feed</span>
          <h2 class="font-serif text-2xl sm:text-3xl font-bold text-[#1C1C1C]">All Published Home Tours & Styling Guides</h2>
        </div>
        <div class="flex items-center gap-3">
          <span id="showing-text" class="text-xs text-[#686866]">Showing all published tours</span>
          <span id="article-count-badge" class="px-2.5 py-1 bg-[#F4F3F0] rounded text-xs font-semibold text-[#1C1C1C] border border-[#EBEBEA]">{total_posts} Guides</span>
        </div>
      </div>

      <div class="flex items-center gap-2 overflow-x-auto pb-4 mb-8">
        {pills_markup}
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8" id="article-grid">
        {cards_html}
      </div>

      <!-- PAGINATION CONTROLS -->
      <div id="pagination-controls" class="flex items-center justify-center gap-2 mt-12 pt-6 border-t border-[#EBEBEA]">
      </div>
    </section>

    <!-- NEWSLETTER DISPATCH STRIP -->
    <section class="max-w-[1200px] mx-auto px-4 sm:px-8 mb-16" id="newsletter">
      <div class="p-8 sm:p-12 bg-[#F4F3F0] border border-[#EBEBEA] rounded-xl text-center">
        <span class="text-[11px] tracking-[0.25em] uppercase font-semibold text-[#8C6D53] block mb-2">Weekly Inspiration</span>
        <h2 class="font-serif text-3xl sm:text-4xl font-bold text-[#1C1C1C] mb-3">Join 85,000+ Scandinavian Living Readers</h2>
        <p class="text-xs sm:text-sm text-[#686866] max-w-xl mx-auto leading-relaxed mb-6 font-serif italic text-base">
          Receive our weekly curation of Nordic house tours, minimalist room layouts, and organic material guides directly in your inbox.
        </p>
        <div class="flex flex-col sm:flex-row items-center justify-center gap-3 max-w-md mx-auto">
          <input type="email" placeholder="Your email address..." class="w-full px-4 py-2.5 bg-white border border-[#EBEBEA] rounded-full text-xs focus:outline-none focus:border-[#8C6D53] shadow-xs">
          <button class="w-full sm:w-auto px-6 py-2.5 bg-[#1C1C1C] hover:bg-stone-800 text-white rounded-full text-xs font-semibold tracking-wider uppercase whitespace-nowrap shadow-xs transition-colors">
            Subscribe
          </button>
        </div>
      </div>
    </section>

  </main>

  <!-- THE NORDROOM 4-COLUMN FOOTER -->
  <footer class="w-full bg-[#1C1C1C] text-stone-300 pt-14 pb-8 border-t border-stone-800">
    <div class="max-w-[1200px] mx-auto px-4 sm:px-8 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-10 mb-12">
      <div>
        <h4 class="font-serif text-2xl font-bold text-white mb-3 uppercase tracking-wider">{html_lib.escape(brand_clean)}</h4>
        <p class="text-xs text-stone-400 leading-relaxed mb-4">
          An internationally acclaimed interior design and Scandinavian living publication showcasing serene house tours, room layout solutions, and organic material palettes.
        </p>
        <span class="text-[11px] text-[#8C6D53] font-semibold uppercase tracking-widest block">Founded by {html_lib.escape(author_name)}</span>
      </div>
      <div>
        <h5 class="text-xs font-semibold tracking-widest uppercase text-white mb-4">Room Inspiration</h5>
        <ul class="space-y-2 text-xs text-stone-400">
          <li><button onclick="filterArticles('living')" class="hover:text-white transition-colors">Living Room Ideas</button></li>
          <li><button onclick="filterArticles('bedroom')" class="hover:text-white transition-colors">Scandinavian Bedrooms</button></li>
          <li><button onclick="filterArticles('kitchen')" class="hover:text-white transition-colors">Kitchens & Pantries</button></li>
          <li><button onclick="filterArticles('garden')" class="hover:text-white transition-colors">Garden & Outdoor Living</button></li>
          <li><button onclick="filterArticles('small')" class="hover:text-white transition-colors">Small Space Living</button></li>
        </ul>
      </div>
      <div>
        <h5 class="text-xs font-semibold tracking-widest uppercase text-white mb-4">Design Styles</h5>
        <ul class="space-y-2 text-xs text-stone-400">
          <li><a href="{home_link}" class="hover:text-white transition-colors">Nordic Warm Minimalism</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Japandi Aesthetics</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Mid-Century Modern</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Earth & Lime Wash Finishes</a></li>
          <li><a href="{home_link}" class="hover:text-white transition-colors">Small Apartment Hacks</a></li>
        </ul>
      </div>
      <div>
        <h5 class="text-xs font-semibold tracking-widest uppercase text-white mb-4">Curate & Connect</h5>
        <p class="text-xs text-stone-400 mb-3">Join our community of 85,000+ design enthusiasts.</p>
        <div class="flex items-center gap-3 mb-4">
          <a href="https://pinterest.com" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 bg-[#E60023] hover:bg-[#AD081B] text-white rounded text-xs font-semibold">Pinterest</a>
          <a href="#newsletter" class="px-3 py-1.5 bg-stone-800 hover:bg-stone-700 text-stone-200 rounded text-xs">Newsletter</a>
        </div>
        <span class="text-[11px] text-stone-500 block">&copy; 2026 {html_lib.escape(brand_clean)}. All Rights Reserved.</span>
      </div>
    </div>
    <div class="max-w-[1200px] mx-auto px-4 text-center text-[11px] text-stone-500 pt-6 border-t border-stone-800/80">
      Designed with pure Scandinavian minimalism • Zero robotic filler • Hand-crafted editorial curation.
    </div>
  </footer>

  <script>
    const PAGE_SIZE = 12;
    let currentPage = 1;
    let currentCategory = 'all';
    let currentSearch = '';

    function getFilteredCards() {{
      const allCards = Array.from(document.querySelectorAll('.article-card'));
      return allCards.filter(card => {{
        const cat = (card.getAttribute('data-cat') || '').toLowerCase();
        const text = card.textContent.toLowerCase();

        const matchesCat = (currentCategory === 'all') || cat.includes(currentCategory);
        const matchesSearch = !currentSearch || text.includes(currentSearch);

        return matchesCat && matchesSearch;
      }});
    }}

    function updateDisplay(scrollToGrid) {{
      const allCards = Array.from(document.querySelectorAll('.article-card'));
      const filtered = getFilteredCards();
      const totalItems = filtered.length;
      const totalPages = Math.ceil(totalItems / PAGE_SIZE) || 1;

      if (currentPage > totalPages) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;

      const startIndex = (currentPage - 1) * PAGE_SIZE;
      const endIndex = Math.min(startIndex + PAGE_SIZE, totalItems);

      allCards.forEach(c => {{
        c.style.display = 'none';
      }});

      filtered.slice(startIndex, endIndex).forEach(c => {{
        c.style.display = 'flex';
      }});

      const showingText = document.getElementById('showing-text');
      if (showingText) {{
        if (totalItems === 0) {{
          showingText.textContent = 'Showing 0 published guides';
        }} else {{
          showingText.textContent = 'Showing ' + (startIndex + 1) + '–' + endIndex + ' of ' + totalItems + ' published guides';
        }}
      }}

      const badge = document.getElementById('article-count-badge');
      if (badge) {{
        badge.textContent = totalItems + ' Guides';
      }}

      renderPaginationButtons(totalPages);

      if (scrollToGrid) {{
        const target = document.getElementById('guides-feed');
        if (target) {{
          target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
      }}
    }}

    function renderPaginationButtons(totalPages) {{
      const container = document.getElementById('pagination-controls');
      if (!container) return;

      if (totalPages <= 1) {{
        container.innerHTML = '<span class="px-3 py-1 text-stone-400 text-xs">Page 1 of 1</span>';
        return;
      }}

      let html = '';

      if (currentPage > 1) {{
        html += '<button onclick="goToPage(' + (currentPage - 1) + ')" class="px-3 py-1.5 bg-white hover:bg-stone-100 text-stone-800 border border-[#EBEBEA] rounded-full text-xs font-medium uppercase tracking-wider transition-colors inline-flex items-center gap-1">&larr; Prev</button>';
      }} else {{
        html += '<button disabled class="px-3 py-1.5 bg-stone-100 text-stone-400 border border-[#EBEBEA] rounded-full text-xs font-medium uppercase tracking-wider cursor-not-allowed inline-flex items-center gap-1">&larr; Prev</button>';
      }}

      for (let i = 1; i <= totalPages; i++) {{
        if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {{
          if (i === currentPage) {{
            html += '<button class="px-3.5 py-1.5 bg-[#1C1C1C] text-white rounded-full text-xs font-bold shadow-xs">' + i + '</button>';
          }} else {{
            html += '<button onclick="goToPage(' + i + ')" class="px-3.5 py-1.5 bg-white hover:bg-stone-100 text-stone-800 border border-[#EBEBEA] rounded-full text-xs font-medium transition-colors">' + i + '</button>';
          }}
        }} else if (i === currentPage - 2 || i === currentPage + 2) {{
          html += '<span class="px-1 text-stone-400">...</span>';
        }}
      }}

      if (currentPage < totalPages) {{
        html += '<button onclick="goToPage(' + (currentPage + 1) + ')" class="px-3 py-1.5 bg-white hover:bg-stone-100 text-stone-800 border border-[#EBEBEA] rounded-full text-xs font-medium uppercase tracking-wider transition-colors inline-flex items-center gap-1">Next &rarr;</button>';
      }} else {{
        html += '<button disabled class="px-3 py-1.5 bg-stone-100 text-stone-400 border border-[#EBEBEA] rounded-full text-xs font-medium uppercase tracking-wider cursor-not-allowed inline-flex items-center gap-1">Next &rarr;</button>';
      }}

      container.innerHTML = html;
    }}

    function goToPage(page) {{
      currentPage = page;
      updateDisplay(true);
    }}

    function filterArticles(category, element) {{
      currentCategory = category;
      currentPage = 1;

      const pills = document.querySelectorAll('.cat-pill');
      if (element) {{
        pills.forEach(p => {{
          p.classList.remove('bg-[#1C1C1C]', 'text-white', 'font-semibold', 'shadow-xs');
          p.classList.add('bg-white', 'text-[#1C1C1C]', 'border', 'border-[#EBEBEA]');
        }});
        element.classList.remove('bg-white', 'text-[#1C1C1C]', 'border', 'border-[#EBEBEA]');
        element.classList.add('bg-[#1C1C1C]', 'text-white', 'font-semibold', 'shadow-xs');
      }}

      updateDisplay(false);
    }}

    function handleSearch(query) {{
      currentSearch = query.toLowerCase().trim();
      currentPage = 1;
      updateDisplay(false);
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      updateDisplay(false);
    }});
  </script>
</body>
</html>'''



def render_hub(
    posts: list[Any],
    categories: Optional[list[dict[str, str]]] = None,
    title: str = "",
    subtitle: str = "",
    base_url: str = "",
    theme: str = "editorial-warm",
    source_domain: str = "stylesdays.com",
    branding: Optional[Any] = None,
    **kwargs: Any,
) -> str:
    """
    Renders the Root Organization Hub (/index.html) linking to all posts
    and category hubs without dead links.
    """
    path_prefix = _extract_path_prefix(base_url)
    theme_tokens = get_theme_tokens(theme)
    clean_domain = _clean_source_domain(source_domain)
    brand_clean = getattr(branding, "brand_name", "") or (clean_domain.split('.')[0].title() if clean_domain else "AnnaDeco")
    canonical_base = base_url.rstrip("/") if (base_url and "://" in base_url) else f"https://{clean_domain}"
    fallback_css = get_embedded_fallback_css(theme_tokens)

    hub_title = title or f"{brand_clean} Editorial Hub"
    hub_subtitle = subtitle or "Curated Home Decor, Room Styling Guides, and Modern Living Guides." 

    if theme == "nordic-studio":
        return render_nordic_studio_hub(
            posts=posts,
            categories=categories,
            title=hub_title,
            subtitle=hub_subtitle,
            base_url=base_url,
            theme=theme,
            source_domain=source_domain,
            branding=branding,
            path_prefix=path_prefix,
            **kwargs,
        )

    if theme in ("pinterest-mag", "styleire"):
        return render_styleire_hub(
            posts=posts,
            categories=categories,
            title=hub_title,
            subtitle=hub_subtitle,
            base_url=base_url,
            theme=theme,
            source_domain=source_domain,
            branding=branding,
            path_prefix=path_prefix,
            **kwargs,
        )

    if theme == "editorial-warm":
        return render_stitch_editorial_hub(
            posts=posts,
            categories=categories,
            title=hub_title,
            subtitle=hub_subtitle,
            base_url=base_url,
            theme=theme,
            source_domain=source_domain,
            branding=branding,
            path_prefix=path_prefix,
            **kwargs,
        )

    cards_html = ""
    for p in posts:
        slug = getattr(p, "slug", None) or (p.get("slug") if isinstance(p, dict) else "")
        title_val = getattr(p, "title", None) or (p.get("title") if isinstance(p, dict) else slug.replace("-", " ").title())
        excerpt_val = getattr(p, "excerpt", None) or (p.get("excerpt") if isinstance(p, dict) else (p.get("description", "") if isinstance(p, dict) else ""))
        category_val = getattr(p, "category", None) or (p.get("category") if isinstance(p, dict) else "Guide")
        web_path_val = getattr(p, "web_path", None) or (p.get("web_path") if isinstance(p, dict) else f"/{slug}/")
        local_img = getattr(p, "local_image_path", None) or (p.get("local_image_path") if isinstance(p, dict) else (p.get("local_image", "") if isinstance(p, dict) else ""))
        link = f"{path_prefix}{web_path_val}" if path_prefix else web_path_val
        raw_img = local_img or f"assets/images/{slug}.svg"
        if raw_img.startswith("http://") or raw_img.startswith("https://"):
            img_src = raw_img
        else:
            clean_img = raw_img.lstrip("/")
            img_src = f"{path_prefix}/{clean_img}" if path_prefix else f"/{clean_img}"
        fallback_svg = _resolve_fallback_svg(slug, path_prefix)

        cards_html += f"""
        <article class="pseo-card group">
          <a href="{link}" style="display: flex; flex-direction: column; height: 100%;">
            <div class="pseo-hero-media">
              <img src="{img_src}" alt="{html_lib.escape(title_val)}" width="600" height="375" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='{fallback_svg}';">
              <span class="pseo-badge" style="position: absolute; top: 0.75rem; left: 0.75rem; background-color: rgba(255, 255, 255, 0.95); color: #1C1917; font-size: 0.625rem;">
                {html_lib.escape(category_val)}
              </span>
            </div>
            <div style="padding: 1.25rem; flex: 1 0 auto;">
              <div style="font-family: monospace; font-size: 0.7rem; color: #A8A29E; margin-bottom: 0.25rem;">{web_path_val}</div>
              <h2 class="font-serif-editorial text-lg font-bold text-stone-900 group-hover:text-[{theme_tokens['accent']}]" style="margin-bottom: 0.5rem; transition: color 0.15s ease;">
                {html_lib.escape(title_val)}
              </h2>
              <p class="text-xs text-stone-500" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                {html_lib.escape(excerpt_val[:120])}...
              </p>
            </div>
            <div style="padding: 0.75rem 1.25rem; background-color: #FAFAFA; border-top: 1px solid var(--pseo-card-border); display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem; font-weight: 500; color: #78716C;">
              <span>Read Guide</span>
              <span style="color: {theme_tokens['accent']}; font-weight: 700;">→</span>
            </div>
          </a>
        </article>
        """

    # Category pills
    cat_pills = ""
    if categories:
        for c in categories:
            c_name = c.get("name", "")
            c_slug = c.get("slug", "")
            if c_slug:
                cat_pills += f'<a href="{path_prefix}/{c_slug}/" class="pseo-pill">{html_lib.escape(c_name)}</a>'

    branding = kwargs.get("branding")
    header_html = render_blogger_header(
        clean_domain,
        '<span class="font-semibold text-stone-900">Home &middot; Editorial Hub</span>',
        f'<div class="pseo-pills-bar" style="margin-top: 0.5rem;"><span style="font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #A8A29E; margin-right: 0.25rem; flex-shrink: 0;">Explore Categories:</span>{cat_pills}</div>' if cat_pills else '',
        theme_tokens,
        path_prefix=path_prefix,
        branding=branding,
    )
    footer_html = render_blogger_footer(clean_domain, theme_tokens, path_prefix=path_prefix, branding=branding)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_lib.escape(hub_title)}</title>
  <meta name="description" content="{html_lib.escape(hub_subtitle)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical_base}/">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>

  <style>
{fallback_css}
  </style>
</head>
<body>
{header_html}

  <main class="pseo-container pseo-main">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
      <h2 class="font-serif-editorial text-xl font-bold text-stone-900">All Published Guides ({len(posts)})</h2>
      <span class="text-xs text-stone-500 font-medium">Updated Regularly</span>
    </div>

    <div class="pseo-related-grid">
      {cards_html}
    </div>
  </main>

{footer_html}
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      var articleImgs = document.querySelectorAll(".pseo-article-body img");
      var pageUrl = encodeURIComponent(window.location.href);
      var pageTitle = encodeURIComponent(document.title || "");
      articleImgs.forEach(function(img) {{
        if (img.closest(".pseo-img-wrapper")) return;
        var wrapper = document.createElement("div");
        wrapper.className = "pseo-img-wrapper";
        wrapper.style.position = "relative";
        wrapper.style.display = "block";
        wrapper.style.margin = "1.5rem 0";
        
        var pinBtn = document.createElement("a");
        pinBtn.className = "pseo-pin-save-btn";
        var mediaSrc = encodeURIComponent(img.src || img.getAttribute("src") || "");
        pinBtn.href = "https://www.pinterest.com/pin/create/button/?url=" + pageUrl + "&media=" + mediaSrc + "&description=" + pageTitle;
        pinBtn.target = "_blank";
        pinBtn.rel = "noopener noreferrer";
        pinBtn.title = "Save to Pinterest";
        pinBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg><span>Save</span>';
        
        img.parentNode.insertBefore(wrapper, img);
        wrapper.appendChild(img);
        wrapper.appendChild(pinBtn);
      }});
    }});
  </script>
</body>
</html>"""
