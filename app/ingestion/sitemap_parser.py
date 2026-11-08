"""Recursive XML Sitemap parser and bulk URL list parser for WordPress ingestion."""

from __future__ import annotations

import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Set, Union

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class SitemapImage:
    """Representation of an image element embedded in a sitemap URL."""

    loc: str
    title: str = ""


@dataclass
class SitemapEntry:
    """Representation of a URL entry extracted from a sitemap."""

    loc: str
    slug: str = ""
    lastmod: str = ""
    changefreq: str = ""
    priority: str = ""
    images: List[SitemapImage] = field(default_factory=list)

    @property
    def image_urls(self) -> List[str]:
        """Returns list of image URLs associated with this sitemap entry."""
        return [img.loc for img in self.images if img.loc]


def extract_slug_from_url(url: str) -> str:
    """Extracts the clean post slug from a web URL or relative path.

    Handles trailing slashes, query parameters, anchors, and file extensions.
    Example:
        'https://stylesdays.com/cozy-ikea-pax-hack/' -> 'cozy-ikea-pax-hack'
        'https://example.com/category/decor/room-styling' -> 'room-styling'
        '/articles/modern-living.html?ref=1' -> 'modern-living'
    """
    if not url:
        return ""

    parsed = urllib.parse.urlparse(url.strip())
    path = parsed.path.strip("/")
    if not path:
        return ""

    segments = [s for s in path.split("/") if s]
    if not segments:
        return ""

    slug = segments[-1]
    # Strip common web file extensions if present
    for ext in (".html", ".htm", ".php", ".json"):
        if slug.lower().endswith(ext):
            slug = slug[: -len(ext)]
            break

    return slug.strip()


def parse_url_list(text_or_lines: Union[str, Iterable[str]]) -> List[str]:
    """Parses a newline-separated raw text, file path, or iterable of URL strings.

    Strips whitespace, ignores blank lines and comment lines starting with '#',
    only retains valid http:// and https:// URLs, and removes duplicates while preserving order.
    """
    if isinstance(text_or_lines, str):
        if os.path.exists(text_or_lines) and os.path.isfile(text_or_lines):
            with open(text_or_lines, "r", encoding="utf-8") as f:
                lines = f.readlines()
        else:
            lines = text_or_lines.splitlines()
    else:
        lines = list(text_or_lines)

    seen: Set[str] = set()
    urls: List[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if not (line.startswith("http://") or line.startswith("https://")):
            continue

        if line not in seen:
            seen.add(line)
            urls.append(line)

    return urls


def _local_tag_name(element: ET.Element) -> str:
    """Returns element tag without XML namespace prefix."""
    return element.tag.split("}")[-1] if "}" in element.tag else element.tag


def _fetch_url(url: str, timeout: int = 20, user_agent: str = DEFAULT_USER_AGENT) -> bytes:
    """Fetches raw content bytes from HTTP/HTTPS URL with configured User-Agent and timeout."""
    headers = {"User-Agent": user_agent, "Accept": "application/xml, text/xml, */*"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


class SitemapParser:
    """Recursive XML Sitemap parser supporting <sitemapindex> and <urlset> with image tags."""

    def __init__(
        self,
        timeout: int = 20,
        user_agent: str = DEFAULT_USER_AGENT,
        fetcher: Optional[Callable[[str], bytes]] = None,
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self._fetcher = fetcher or (lambda u: _fetch_url(u, timeout=self.timeout, user_agent=self.user_agent))

    def parse(self, url: str, max_depth: int = 5) -> List[str]:
        """Recursively parses a sitemap or sitemap index URL and returns a list of post URLs."""
        entries = self.parse_entries(url, max_depth=max_depth)
        return [e.loc for e in entries]

    def parse_entries(self, url: str, max_depth: int = 5) -> List[SitemapEntry]:
        """Recursively parses a sitemap URL and returns detailed SitemapEntry objects."""
        visited: Set[str] = set()
        entries: List[SitemapEntry] = []
        self._parse_recursive(url, depth=0, max_depth=max_depth, visited=visited, results=entries)
        return entries

    def _parse_recursive(
        self,
        url: str,
        depth: int,
        max_depth: int,
        visited: Set[str],
        results: List[SitemapEntry],
    ) -> None:
        if depth > max_depth or url in visited:
            return
        visited.add(url)

        try:
            raw_xml = self._fetcher(url)
        except Exception as exc:
            logger.warning("Failed to fetch sitemap at %s: %s", url, exc)
            return

        self._parse_xml_bytes(raw_xml, depth, max_depth, visited, results)

    def parse_xml_string(self, xml_content: Union[str, bytes]) -> List[SitemapEntry]:
        """Parses raw XML string or bytes directly without network requests."""
        results: List[SitemapEntry] = []
        visited: Set[str] = set()
        raw_bytes = xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content
        self._parse_xml_bytes(raw_bytes, depth=0, max_depth=1, visited=visited, results=results)
        return results

    def _parse_xml_bytes(
        self,
        raw_xml: bytes,
        depth: int,
        max_depth: int,
        visited: Set[str],
        results: List[SitemapEntry],
    ) -> None:
        idx = raw_xml.rfind(b"</urlset>")
        if idx != -1:
            raw_xml = raw_xml[: idx + len(b"</urlset>")]
        else:
            idx_idx = raw_xml.rfind(b"</sitemapindex>")
            if idx_idx != -1:
                raw_xml = raw_xml[: idx_idx + len(b"</sitemapindex>")]

        try:
            root = ET.fromstring(raw_xml)
        except ET.ParseError as exc:
            logger.warning("Malformed XML in sitemap: %s", exc)
            return

        root_tag = _local_tag_name(root).lower()

        if root_tag == "sitemapindex":
            # Nested sitemap index: recurse into child <sitemap><loc> elements
            child_sitemaps: List[str] = []
            for child in root:
                if _local_tag_name(child).lower() == "sitemap":
                    for sub in child:
                        if _local_tag_name(sub).lower() == "loc" and sub.text:
                            sub_url = sub.text.strip()
                            if sub_url and sub_url not in visited:
                                child_sitemaps.append(sub_url)

            # Prioritize post and page sitemaps, skipping author/tag/tax sitemaps if post sitemaps exist
            has_post_sitemaps = any(
                ("post-sitemap" in u.lower() or "page-sitemap" in u.lower() or "article" in u.lower() or "story" in u.lower())
                for u in child_sitemaps
            )
            if has_post_sitemaps:
                child_sitemaps = [
                    u for u in child_sitemaps
                    if not any(x in u.lower() for x in ("author", "tag", "category", "tax"))
                ]

            def _sitemap_priority(s_url: str) -> int:
                lower = s_url.lower()
                if "post-sitemap" in lower:
                    return 0
                if "page-sitemap" in lower or "article" in lower or "story" in lower:
                    return 1
                return 2

            child_sitemaps.sort(key=_sitemap_priority)

            for sub_url in child_sitemaps:
                self._parse_recursive(
                    sub_url,
                    depth=depth + 1,
                    max_depth=max_depth,
                    visited=visited,
                    results=results,
                )
        elif root_tag == "urlset":
            # Terminal URL set: extract each <url>
            seen_locs = {e.loc for e in results}
            for child in root:
                if _local_tag_name(child).lower() == "url":
                    entry = self._parse_url_element(child)
                    if entry.loc and entry.loc not in seen_locs:
                        seen_locs.add(entry.loc)
                        results.append(entry)
        else:
            logger.warning("Unrecognized sitemap root tag: <%s>", root_tag)

    def _parse_url_element(self, url_elem: ET.Element) -> SitemapEntry:
        """Extracts location, metadata, and embedded Google image tags from a <url> element."""
        loc = ""
        lastmod = ""
        changefreq = ""
        priority = ""
        images: List[SitemapImage] = []

        for sub in url_elem:
            tag = _local_tag_name(sub).lower()
            if tag == "loc" and sub.text:
                loc = sub.text.strip()
            elif tag == "lastmod" and sub.text:
                lastmod = sub.text.strip()
            elif tag == "changefreq" and sub.text:
                changefreq = sub.text.strip()
            elif tag == "priority" and sub.text:
                priority = sub.text.strip()
            elif tag == "image":
                # Google Image extension tag <image:image>
                img_loc = ""
                img_title = ""
                for img_sub in sub:
                    img_tag = _local_tag_name(img_sub).lower()
                    if img_tag == "loc" and img_sub.text:
                        img_loc = img_sub.text.strip()
                    elif img_tag == "title" and img_sub.text:
                        img_title = img_sub.text.strip()
                if img_loc:
                    images.append(SitemapImage(loc=img_loc, title=img_title))

        slug = extract_slug_from_url(loc)
        return SitemapEntry(
            loc=loc,
            slug=slug,
            lastmod=lastmod,
            changefreq=changefreq,
            priority=priority,
            images=images,
        )


def parse_sitemap(
    url: str,
    max_depth: int = 5,
    timeout: int = 20,
    fetcher: Optional[Callable[[str], bytes]] = None,
) -> List[str]:
    """Convenience functional interface to recursively parse a sitemap URL into a list of URLs."""
    parser = SitemapParser(timeout=timeout, fetcher=fetcher)
    return parser.parse(url, max_depth=max_depth)


def parse_sitemap_entries(
    url: str,
    max_depth: int = 5,
    timeout: int = 20,
    fetcher: Optional[Callable[[str], bytes]] = None,
) -> List[SitemapEntry]:
    """Convenience functional interface to recursively parse a sitemap URL into SitemapEntry objects."""
    parser = SitemapParser(timeout=timeout, fetcher=fetcher)
    return parser.parse_entries(url, max_depth=max_depth)


def parse_sitemap_xml(xml_content: Union[str, bytes]) -> List[SitemapEntry]:
    """Convenience functional interface to parse an XML string or bytes directly."""
    parser = SitemapParser()
    return parser.parse_xml_string(xml_content)


def discover_sitemap_urls(
    sitemap_url: str,
    max_urls: Optional[int] = None,
    max_depth: int = 5,
    timeout: int = 20,
    fetcher: Optional[Callable[[str], bytes]] = None,
    user_agent: str = DEFAULT_USER_AGENT,
) -> List[str]:
    """Recursively discovers and deduplicates article post URLs from a sitemap or sitemap index."""
    parser = SitemapParser(timeout=timeout, user_agent=user_agent, fetcher=fetcher)
    entries = parser.parse_entries(sitemap_url, max_depth=max_depth)
    seen: Set[str] = set()
    urls: List[str] = []
    for entry in entries:
        if not entry.loc:
            continue
        slug = entry.slug or extract_slug_from_url(entry.loc)
        if not slug:
            continue
        if entry.loc not in seen:
            seen.add(entry.loc)
            urls.append(entry.loc)
            if max_urls is not None and len(urls) >= max_urls:
                break
    return urls

