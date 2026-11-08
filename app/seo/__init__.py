"""SEO, structured data (JSON-LD), sitemap, and crawler control subsystem for pSEO."""

from app.seo.robots import generate_robots_txt
from app.seo.schema import (
    build_article_schema,
    build_breadcrumb_list,
    generate_json_ld,
    generate_json_ld_script,
    generate_opengraph_tags,
    generate_pinterest_tags,
    generate_seo_head,
    generate_twitter_tags,
    resolve_image_url,
)
from app.seo.sitemap import generate_sitemap_xml

__all__ = [
    "build_article_schema",
    "build_breadcrumb_list",
    "generate_json_ld",
    "generate_json_ld_script",
    "generate_opengraph_tags",
    "generate_pinterest_tags",
    "generate_twitter_tags",
    "generate_seo_head",
    "generate_sitemap_xml",
    "generate_robots_txt",
    "resolve_image_url",
]
