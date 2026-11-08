"""HTML layout templates and responsive components for the pSEO static site generator."""

from __future__ import annotations

import html as html_lib
import json
import os
import random
import urllib.parse
from typing import Any, Optional


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
        "name": "Nordic Studio (Minimalist Scandinavian)",
        "bg_body": "#F3F5F4",
        "text_body": "#0F172A",
        "accent": "#0F766E",
        "accent_hover": "#115E59",
        "card_bg": "#FFFFFF",
        "card_border": "#E2E8F0",
        "CheckBoxBg": "#E6ECEA",
        "badge_bg": "#0F766E",
        "font_headline": "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "font_body": "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "header_bg": "#FFFFFF",
        "muted_text": "#64748B",
        "tag_bg": "#E2E8F0",
    },
    "pinterest-mag": {
        "id": "pinterest-mag",
        "name": "Pinterest Mag (Visual Discovery & Pin Focus)",
        "bg_body": "#FFFDF9",
        "text_body": "#18181B",
        "accent": "#BE123C",
        "accent_hover": "#9F1239",
        "card_bg": "#FFFFFF",
        "card_border": "#F3E8E2",
        "CheckBoxBg": "#FCE7F3",
        "badge_bg": "#BE123C",
        "font_headline": "'Playfair Display', Georgia, serif",
        "font_body": "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "header_bg": "#FFFFFF",
        "muted_text": "#71717A",
        "tag_bg": "#FCE7F3",
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
    """Minimalist Architectural Studio: 2-col asymmetric grid, spec drawer, teal accents."""
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

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc_title} | {html_lib.escape(clean_brand)} Architectural Studio</title>
  <meta name="description" content="{esc_excerpt}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{esc_canonical}">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x1F3E0;</text></svg>">
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
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
{fallback_css}
    body {{ background-color: #F3F5F4; font-family: 'Plus Jakarta Sans', sans-serif; }}
    .ns-grid {{
      display: grid;
      grid-template-columns: 7fr 5fr;
      gap: 2rem;
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 1.5rem 4rem;
      align-items: start;
    }}
    @media (max-width: 900px) {{ .ns-grid {{ grid-template-columns: 1fr; }} }}
    .ns-main-col {{ display: flex; flex-direction: column; gap: 1.5rem; }}
    .ns-aside {{ display: flex; flex-direction: column; gap: 1.5rem; position: sticky; top: 1rem; }}
    .ns-hero {{
      position: relative; aspect-ratio: 16/10; overflow: hidden;
      border-radius: 0.5rem; border: 1px solid #E2E8F0;
    }}
    .ns-hero img {{ width:100%; height:100%; object-fit:cover; transition: transform 0.5s ease; }}
    .ns-hero:hover img {{ transform: scale(1.02); }}
    .ns-article {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 0.5rem; padding: 2rem; }}
    .ns-category-tag {{
      display: inline-block; font-size: 0.65rem; font-weight: 700;
      letter-spacing: 0.12em; text-transform: uppercase;
      color: {accent}; border: 1.5px solid {accent};
      padding: 0.2rem 0.6rem; border-radius: 0.25rem; margin-bottom: 1rem;
    }}
    .ns-title {{
      font-size: clamp(1.5rem, 3vw, 2.25rem); font-weight: 800;
      line-height: 1.15; color: #0F172A; letter-spacing: -0.02em; margin-bottom: 1rem;
    }}
    .ns-excerpt {{
      font-size: 0.95rem; color: #475569; line-height: 1.65; margin-bottom: 1.5rem;
      border-left: 3px solid {accent}; padding-left: 1rem;
    }}
    .ns-meta {{
      display: flex; gap: 1.5rem; font-size: 0.72rem; color: #64748B;
      padding: 0.75rem 0; border-top: 1px solid #E2E8F0;
      border-bottom: 1px solid #E2E8F0; margin-bottom: 1.5rem; font-weight: 500; flex-wrap: wrap;
    }}
    .ns-cta-btn {{
      display: inline-flex; align-items: center; gap: 0.4rem;
      background: {accent}; color: #FFFFFF !important;
      font-size: 0.8rem; font-weight: 700; padding: 0.875rem 1.5rem;
      border-radius: 0.375rem; transition: background 0.2s, transform 0.1s;
      letter-spacing: 0.02em; text-decoration: none;
    }}
    .ns-cta-btn:hover {{ background: #115E59; transform: translateY(-1px); }}
    .ns-spec-drawer {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 0.5rem; overflow: hidden; }}
    .ns-spec-header {{
      background: {accent}; color: #FFFFFF; padding: 0.875rem 1.25rem;
      font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em;
      text-transform: uppercase; display: flex; align-items: center; gap: 0.5rem;
    }}
    .ns-spec-row {{
      padding: 0.875rem 1.25rem; border-bottom: 1px solid #F1F5F9;
      display: flex; flex-direction: column; gap: 0.2rem;
    }}
    .ns-spec-row:last-child {{ border-bottom: none; }}
    .ns-spec-key {{ font-size: 0.62rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #94A3B8; }}
    .ns-spec-val {{ font-size: 0.82rem; font-weight: 600; color: #0F172A; }}
    .ns-info-card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 0.5rem; padding: 1.25rem; }}
  </style>
</head>
<body>
{header_html}

  <main class="pseo-main">
    <div class="ns-grid">
      <div class="ns-main-col">
        <div class="ns-hero" id="overview" style="position:relative;">
          <img src="{image_src}" alt="{esc_title}" width="1200" height="750" fetchpriority="high" decoding="async" onerror="this.onerror=null;this.src='{fallback_svg}';">
          <div style="position:absolute;top:1rem;left:1rem;">
            <span style="background:rgba(255,255,255,0.95);color:#0F172A;border:1px solid #E2E8F0;font-size:0.625rem;font-weight:700;padding:0.25rem 0.6rem;border-radius:0.25rem;">{esc_category}</span>
          </div>
          <a href="{pin_href}" target="_blank" rel="noopener noreferrer" class="pseo-pin-save-btn" title="Save to Pinterest">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg>
            <span>Save</span>
          </a>
        </div>

        <div class="ns-article" style="max-width:100%;">
          <span class="ns-category-tag">{esc_category}</span>
          <h1 class="ns-title">{esc_title}</h1>
          {byline_html}
          {article_body_html}
        </div>
        <div id="related">{related_html}</div>
      </div>
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


def render_pinterest_mag_layout(
    slug: str, title: str, excerpt: str, category: str, lastmod: str,
    image_src: str, fallback_svg: str, canonical_url: str, clean_domain: str,
    pills_html: str, takeaways_html: str, checklist_html: str, related_html: str,
    schema_json: str, fallback_css: str, breadcrumb_html: str,
    theme_tokens: dict, path_prefix: str,
    toc_html: str = "", faq_html: str = "", eeat_html: str = "",
    branding: Optional[Any] = None,
    content_html: str = "",
) -> str:
    """Visual Pin Discovery Magazine: moodboard grid, floating save badge, ruby accents."""
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
        article_body_html = f'<div class="pm-prose pseo-article-body" style="margin:2rem 0;font-size:1.02rem;line-height:1.8;color:#27272A;">{content_html}</div>'
    else:
        article_body_html = f'<p class="pm-prose pseo-article-body" style="margin:2rem 0;font-size:1.02rem;line-height:1.8;color:#27272A;">Curated visual inspiration and room design ideas for {esc_title}.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc_title} | {clean_domain} Pin Discovery</title>
  <meta name="description" content="{esc_excerpt}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{esc_canonical}">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x1F4CC;</text></svg>">
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
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,400;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
{fallback_css}
    body {{ background-color: #FFFDF9; }}
    .pm-container {{ max-width: 1100px; margin: 0 auto; padding: 0 1rem 4rem; }}
    .pm-floating-pin {{
      position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 999;
      background: {accent}; color: #FFFFFF; font-size: 0.8rem; font-weight: 700;
      padding: 0.75rem 1.25rem; border-radius: 9999px;
      box-shadow: 0 4px 20px rgba(190,18,60,0.35);
      transition: transform 0.2s, box-shadow 0.2s;
      text-decoration: none !important; display: flex; align-items: center; gap: 0.4rem;
    }}
    .pm-floating-pin:hover {{ transform: translateY(-2px) scale(1.03); box-shadow: 0 8px 28px rgba(190,18,60,0.4); }}
    .pm-magazine-banner {{
      background: {accent}; color: #FFFFFF; text-align: center; padding: 0.5rem 1rem;
      font-size: 0.65rem; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase;
    }}
    .pm-hero-section {{ position: relative; border-radius: 1rem; overflow: hidden; margin-bottom: 2rem; }}
    .pm-hero-img {{ width: 100%; aspect-ratio: 16/10; object-fit: cover; display: block; transition: transform 0.5s ease; }}
    .pm-hero-section:hover .pm-hero-img {{ transform: scale(1.02); }}
    .pm-hero-overlay {{ position: absolute; inset: 0; background: linear-gradient(to top, rgba(18,18,18,0.6) 0%, transparent 55%); }}
    .pm-hero-meta {{ position: absolute; bottom: 0; left: 0; right: 0; padding: 2rem 2rem 1.5rem; }}
    .pm-kicker {{ font-size: 0.65rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.75); margin-bottom: 0.4rem; }}
    .pm-hero-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: clamp(1.4rem, 3.5vw, 2.5rem); font-weight: 700; font-style: italic;
      color: #FFFFFF; line-height: 1.2; text-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}
    .pm-moodboard {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.5rem 0; }}
    @media (max-width: 600px) {{ .pm-moodboard {{ grid-template-columns: 1fr; }} }}
    .pm-pin-card {{
      background: #FFFFFF; border: 1px solid #F3E8E2; border-radius: 0.875rem;
      overflow: hidden; transition: transform 0.2s, box-shadow 0.2s; cursor: pointer;
    }}
    .pm-pin-card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 28px rgba(0,0,0,0.08); }}
    .pm-pin-img {{ width: 100%; aspect-ratio: 4/3; object-fit: cover; display: block; }}
    .pm-pin-body {{ padding: 0.875rem; }}
    .pm-pin-title {{ font-family: 'Playfair Display', serif; font-size: 0.9rem; font-weight: 600; color: #18181B; margin-bottom: 0.25rem; }}
    .pm-pin-tag {{ font-size: 0.68rem; color: {accent}; font-weight: 600; }}
    .pm-article-card {{ background: #FFFFFF; border: 1px solid #F3E8E2; border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; }}
    .pm-article-title {{ font-family: 'Playfair Display', Georgia, serif; font-size: clamp(1.5rem, 3vw, 2.25rem); font-weight: 700; color: #18181B; line-height: 1.25; margin-bottom: 1rem; }}
    .pm-excerpt {{ font-size: 1rem; color: #3F3F46; line-height: 1.7; margin-bottom: 1.5rem; font-style: italic; border-left: 3px solid {accent}; padding-left: 1rem; }}
    .pm-viral-bar {{ background: #FFF1F2; border: 1px solid #FCE7EF; border-radius: 0.75rem; padding: 1.25rem; margin: 1.5rem 0; }}
    .pm-viral-label {{ font-size: 0.62rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: {accent}; margin-bottom: 0.5rem; }}
    .pm-viral-score {{ font-family: 'Playfair Display', serif; font-size: 1.75rem; font-weight: 700; color: #18181B; }}
    .pm-tags {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.75rem; }}
    .pm-hashtag {{ font-size: 0.72rem; font-weight: 600; color: {accent}; background: #FFF1F2; padding: 0.25rem 0.6rem; border-radius: 9999px; }}
    .pm-cta-btn {{
      display: inline-flex; align-items: center; gap: 0.4rem;
      background: {accent}; color: #FFFFFF !important; font-size: 0.8rem; font-weight: 700;
      padding: 0.875rem 1.75rem; border-radius: 0.625rem; transition: background 0.2s, transform 0.1s;
      text-decoration: none;
    }}
    .pm-cta-btn:hover {{ background: #9F1239; transform: translateY(-1px); }}
  </style>
</head>
<body>


  

{header_html}

  <main class="pseo-main">
    <div class="pm-container">
      <div class="pm-hero-section" id="overview" style="position:relative;">
        <img class="pm-hero-img" src="{image_src}" alt="{esc_title}" width="1100" height="688" fetchpriority="high" decoding="async" onerror="this.onerror=null;this.src='{fallback_svg}';">
        <div class="pm-hero-overlay"></div>
        <div class="pm-hero-meta">
          <div class="pm-kicker">&#x1F4CC; {esc_category} &middot; Visual Inspiration</div>
          <h1 class="pm-hero-title">{esc_title}</h1>
        </div>
        <a href="{pin_href}" target="_blank" rel="noopener noreferrer" class="pseo-pin-save-btn" title="Save to Pinterest">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg>
          <span>Save</span>
        </a>
      </div>

      <div class="pm-article-card">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
          <span style="font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{accent};">{esc_category}</span>
          <span style="font-size:0.72rem;color:#71717A;">Updated {(lastmod or "2026")[:10]}</span>
        </div>
        <h2 class="pm-article-title">{esc_title}</h2>
        {byline_html}
        {article_body_html}
      </div>

      <div id="related">{related_html}</div>
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
    if theme == "pinterest-mag":
        return render_pinterest_mag_layout(**layout_args)
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

    # Lead Hero Post: featured cover story
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
            <img alt="{html_lib.escape(title_val)}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" src="{img_src}" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='{fallback_svg}';">
            <span class="absolute top-3 left-3 px-3 py-1 bg-surface-container-lowest/90 backdrop-blur-md rounded font-label-sm text-label-sm uppercase tracking-wider font-semibold text-secondary">
              {html_lib.escape(category_val)}
            </span>
            <span class="absolute bottom-3 right-3 px-2.5 py-0.5 bg-black/65 backdrop-blur-sm rounded text-surface-container-lowest font-label-sm text-[10px] tracking-wider text-white">
              {read_time}
            </span>
          </div>
          <div class="p-6 flex flex-col flex-1 justify-between">
            <div>
              <span class="font-label-sm text-[11px] font-mono uppercase tracking-widest text-on-surface-variant block mb-2 text-stone-500">
                {web_path_val}
              </span>
              <h3 class="font-headline-sm text-xl text-on-surface group-hover:text-primary transition-colors mb-3 leading-snug">
                {html_lib.escape(title_val)}
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
      <div class="max-w-[1440px] mx-auto flex items-center justify-between text-on-surface-variant font-label-sm text-label-sm uppercase tracking-widest text-[11px] px-4">
        <span class="hidden md:inline-flex items-center gap-1.5 text-secondary font-semibold">
          <span class="w-1.5 h-1.5 rounded-full bg-secondary"></span>
          The Spatial Journal • Vol. XII
        </span>
        <p class="flex-1 text-center font-label-sm text-label-sm tracking-widest text-on-surface-variant">
          Architecture, Spatial Design & Curated Living • Issue No. 48 Autumn/Winter • 
          <a class="underline underline-offset-4 hover:text-primary transition-colors font-semibold" href="#newsletter">Subscribe to Print & Digital Dispatch</a>
        </p>
        <div class="hidden md:flex items-center gap-space-xs text-on-surface-variant">
          <span class="material-symbols-outlined text-[14px]">auto_stories</span>
          <span>{total_posts} Guides Published</span>
        </div>
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
              <div class="flex flex-wrap items-center gap-3 mb-4">
                <span class="px-3 py-1 bg-primary text-white rounded-full font-label-sm text-label-sm uppercase tracking-widest font-semibold text-xs shadow-xs">
                  Featured Cover Story
                </span>
                <span class="inline-flex items-center gap-1.5 text-stone-200 font-label-sm text-label-sm uppercase tracking-wider text-xs">
                  <span class="material-symbols-outlined text-[14px]">schedule</span> 8 Min Read
                </span>
                <span class="text-stone-400">•</span>
                <span class="text-stone-200 font-label-sm text-label-sm uppercase tracking-wider text-xs">Volume 48 • Autumn/Winter</span>
              </div>
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
              <span class="font-label-sm text-[11px] text-stone-500 block mb-1 group-hover:text-primary transition-colors">/bedroom-inspo/</span>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Bedroom Inspo Guides</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">14 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('fire-pit')">
            <div>
              <span class="font-label-sm text-[11px] text-stone-500 block mb-1 group-hover:text-primary transition-colors">/fire-pits/</span>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Fire Pits & Hearths</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">10 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('patio')">
            <div>
              <span class="font-label-sm text-[11px] text-stone-500 block mb-1 group-hover:text-primary transition-colors">/patio-design/</span>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Patio & Pavers Guides</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">21 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('gazebo')">
            <div>
              <span class="font-label-sm text-[11px] text-stone-500 block mb-1 group-hover:text-primary transition-colors">/gazebos-pergolas/</span>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Gazebos & Pergolas</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">13 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('landscaping')">
            <div>
              <span class="font-label-sm text-[11px] text-stone-500 block mb-1 group-hover:text-primary transition-colors">/landscaping-ideas/</span>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Landscaping Ideas</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">17 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('pool')">
            <div>
              <span class="font-label-sm text-[11px] text-stone-500 block mb-1 group-hover:text-primary transition-colors">/pool-oasis/</span>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Pool & Backyard Oasis</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">19 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('lighting')">
            <div>
              <span class="font-label-sm text-[11px] text-stone-500 block mb-1 group-hover:text-primary transition-colors">/curated-lighting/</span>
              <h3 class="font-serif-editorial text-base text-on-surface font-semibold leading-snug group-hover:text-primary transition-colors">Lighting & Lumens</h3>
            </div>
            <span class="font-label-sm text-[11px] text-secondary font-medium mt-3 block text-emerald-800">8 curated guides available</span>
          </button>

          <button class="p-4 bg-surface-container-low hover:bg-surface-container border border-surface-container hover:border-outline-variant/60 rounded-xl text-left transition-all group flex flex-col justify-between" onclick="filterArticles('essay')">
            <div>
              <span class="font-label-sm text-[11px] text-stone-500 block mb-1 group-hover:text-primary transition-colors">/architect-essays/</span>
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
                Longform Architectural Essay • Volume 48
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
                  <span class="font-label-sm text-[10px] text-stone-500">Autumn/Winter 2025 • 248 Pages</span>
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
