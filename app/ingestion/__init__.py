"""WordPress & Sitemap content ingestion, manifest diffing, and asset downloader."""

from app.ingestion.image_downloader import (
    detect_image_extension,
    download_image_to_repo,
    download_images_for_posts,
    download_post_image,
    generate_svg_badge,
)
from app.ingestion.manifest_diff import (
    apply_diff_to_manifest,
    diff_manifest,
    is_post_updated,
    merge_post_preserving_edits,
    parse_date_to_timestamp,
    update_manifest_with_posts,
)
from app.ingestion.sitemap_parser import (
    SitemapEntry,
    SitemapImage,
    SitemapParser,
    discover_sitemap_urls,
    extract_slug_from_url,
    parse_sitemap,
    parse_sitemap_entries,
    parse_sitemap_xml,
    parse_url_list,
)
from app.ingestion.web_scraper import (
    clean_article_container,
    extract_domain,
    extract_subdomain,
    get_domain_storage_paths,
    get_subdomain_storage_paths,
    scrape_post_from_html,
    scrape_sitemap,
    scrape_url_list,
)
from app.ingestion.wp_client import (
    WordPressClient,
    extract_category_and_slug,
    extract_featured_image,
    fetch_wp_post_by_slug,
    fetch_wp_posts,
    fetch_wp_rest_posts,
    infer_category_and_parent,
    strip_html,
)

__all__ = [
    # Sitemap
    "SitemapParser",
    "SitemapEntry",
    "SitemapImage",
    "extract_slug_from_url",
    "parse_sitemap",
    "parse_sitemap_entries",
    "parse_sitemap_xml",
    "parse_url_list",
    "discover_sitemap_urls",
    # Web Scraper
    "clean_article_container",
    "extract_domain",
    "extract_subdomain",
    "get_domain_storage_paths",
    "get_subdomain_storage_paths",
    "scrape_post_from_html",
    "scrape_sitemap",
    "scrape_url_list",
    # WordPress REST
    "WordPressClient",
    "fetch_wp_posts",
    "fetch_wp_post_by_slug",
    "fetch_wp_rest_posts",
    "strip_html",
    "extract_featured_image",
    "extract_category_and_slug",
    "infer_category_and_parent",
    # Manifest Diff
    "diff_manifest",
    "apply_diff_to_manifest",
    "update_manifest_with_posts",
    "merge_post_preserving_edits",
    "is_post_updated",
    "parse_date_to_timestamp",
    # Image Downloader
    "download_post_image",
    "download_image_to_repo",
    "download_images_for_posts",
    "generate_svg_badge",
    "detect_image_extension",
]
