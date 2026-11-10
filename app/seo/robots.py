"""Robots.txt generator strictly conforming to R5 and RFC 9309."""

from __future__ import annotations

from typing import Optional


def generate_robots_txt(
    base_url: str = "",
    sitemap_url: str = "",
    domain: Optional[str] = None,
) -> str:
    """
    Generates robots.txt strictly conforming to requirement R5:
    - User-agent: *
    - Allow: /
    - Sitemap: {base_url}/sitemap.xml

    Accepts base_url as the primary parameter. sitemap_url and domain are
    kept for backward-compatibility.
    """
    # Derive sitemap URL from base_url first, then fall back to legacy params
    if base_url:
        clean_base_url = base_url.rstrip("/")
        resolved_sitemap = f"{clean_base_url}/sitemap.xml"
    elif domain:
        clean_domain = domain.strip().replace("http://", "").replace("https://", "").strip("/")
        resolved_sitemap = f"https://{clean_domain}/sitemap.xml"
    elif sitemap_url:
        resolved_sitemap = sitemap_url.strip()
        if not (resolved_sitemap.startswith("http://") or resolved_sitemap.startswith("https://")):
            resolved_sitemap = f"https://{resolved_sitemap}"
        if not resolved_sitemap.endswith(".xml"):
            resolved_sitemap = f"{resolved_sitemap.rstrip('/')}/sitemap.xml"
    else:
        resolved_sitemap = "https://home-organization.github.io/sitemap.xml"

    return f"""User-agent: *
Allow: /

Sitemap: {resolved_sitemap}
"""
