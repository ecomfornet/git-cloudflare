"""Robots.txt generator strictly conforming to R5 and RFC 9309."""

from __future__ import annotations

from typing import Optional


def generate_robots_txt(
    sitemap_url: str = "https://home-organization.github.io/sitemap.xml",
    domain: Optional[str] = None,
) -> str:
    """
    Generates robots.txt strictly conforming to requirement R5:
    - User-agent: *
    - Allow: /
    - Allow: /assets/images/
    - User-agent: Pinterestbot
    - Allow: /
    - Allow: /assets/images/
    - Sitemap: https://<domain>/sitemap.xml
    """
    resolved_sitemap = sitemap_url
    if domain:
        clean_domain = domain.strip().replace("http://", "").replace("https://", "").strip("/")
        resolved_sitemap = f"https://{clean_domain}/sitemap.xml"
    elif resolved_sitemap:
        resolved_sitemap = resolved_sitemap.strip()
        if not (resolved_sitemap.startswith("http://") or resolved_sitemap.startswith("https://")):
            resolved_sitemap = f"https://{resolved_sitemap}"
        if not resolved_sitemap.endswith(".xml"):
            resolved_sitemap = f"{resolved_sitemap.rstrip('/')}/sitemap.xml"

    return f"""User-agent: *
Allow: /
Allow: /assets/images/

User-agent: Pinterestbot
Allow: /
Allow: /assets/images/

Sitemap: {resolved_sitemap}
"""
