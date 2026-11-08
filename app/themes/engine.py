"""Theme engine coordinating template rendering, palettes, and typography configurations."""

from __future__ import annotations

from typing import Any, Optional

from app.themes.templates import (
    THEMES,
    get_embedded_fallback_css,
    get_theme_tokens,
    render_author_page,
    render_category_index,
    render_checklist,
    render_html_sitemap,
    render_hub,
    render_post,
    render_related_guides,
    render_styleire_hub,
    render_styleire_layout,
    render_takeaways,
    render_taxonomy_pills,
    render_trust_page,
)


class ThemeEngine:
    """Core theme rendering engine managing layouts, visual palettes, and interactive components."""

    def __init__(self, default_theme: str = "nordic-studio") -> None:
        if default_theme not in THEMES:
            self.default_theme = "nordic-studio"
        else:
            self.default_theme = default_theme

    @classmethod
    def list_themes(cls) -> list[str]:
        """Returns list of supported theme identifiers."""
        return list(THEMES.keys())

    @classmethod
    def get_theme(cls, theme_name: Optional[str] = None) -> dict[str, str]:
        """Retrieves dictionary of theme tokens for specified or default theme."""
        key = theme_name or "nordic-studio"
        return get_theme_tokens(key)

    def render_post(
        self,
        post: Any,
        all_posts: Optional[list[Any]] = None,
        base_url: str = "",
        theme: Optional[str] = None,
        source_domain: str = "stylesdays.com",
        **kwargs: Any,
    ) -> str:
        """Renders static HTML for an individual post using active theme."""
        theme_key = theme or self.default_theme
        return render_post(
            post=post,
            all_posts=all_posts,
            base_url=base_url,
            theme=theme_key,
            source_domain=source_domain,
            **kwargs,
        )

    def render_category_index(
        self,
        category_name: str,
        category_slug: str,
        posts: list[Any],
        all_categories: Optional[list[dict[str, str]]] = None,
        base_url: str = "",
        theme: Optional[str] = None,
        source_domain: str = "stylesdays.com",
        **kwargs: Any,
    ) -> str:
        """Renders intermediate category index page."""
        theme_key = theme or self.default_theme
        return render_category_index(
            category_name=category_name,
            category_slug=category_slug,
            posts=posts,
            all_categories=all_categories,
            base_url=base_url,
            theme=theme_key,
            source_domain=source_domain,
            **kwargs,
        )

    def render_hub(
        self,
        posts: list[Any],
        categories: Optional[list[dict[str, str]]] = None,
        title: str = "",
        subtitle: str = "",
        base_url: str = "",
        theme: Optional[str] = None,
        source_domain: str = "stylesdays.com",
        **kwargs: Any,
    ) -> str:
        """Renders root organization hub index page."""
        theme_key = theme or self.default_theme
        return render_hub(
            posts=posts,
            categories=categories,
            title=title,
            subtitle=subtitle,
            base_url=base_url,
            theme=theme_key,
            source_domain=source_domain,
            **kwargs,
        )

    def render_author_page(
        self,
        author_name: str = "Sophia Bennett",
        author_role: str = "Senior Home Decor Editor & Interior Stylist",
        author_bio: str = "",
        author_image: str = "",
        posts: Optional[list[Any]] = None,
        theme: Optional[str] = None,
        base_url: str = "",
        source_domain: str = "styleire.com",
        **kwargs: Any,
    ) -> str:
        """Renders author E-E-A-T profile page."""
        theme_key = theme or self.default_theme
        return render_author_page(
            author_name=author_name,
            author_role=author_role,
            author_bio=author_bio,
            author_image=author_image,
            posts=posts,
            theme=theme_key,
            base_url=base_url,
            source_domain=source_domain,
            **kwargs,
        )

    def render_trust_page(
        self,
        slug: str,
        title: str = "",
        content_html: str = "",
        theme: Optional[str] = None,
        base_url: str = "",
        source_domain: str = "styleire.com",
        **kwargs: Any,
    ) -> str:
        """Renders trust/legal compliance page."""
        theme_key = theme or self.default_theme
        return render_trust_page(
            slug=slug,
            title=title,
            content_html=content_html,
            theme=theme_key,
            base_url=base_url,
            source_domain=source_domain,
            **kwargs,
        )

    def render_html_sitemap(
        self,
        posts: list[Any],
        categories: Optional[list[dict[str, str]]] = None,
        theme: Optional[str] = None,
        base_url: str = "",
        source_domain: str = "styleire.com",
        **kwargs: Any,
    ) -> str:
        """Renders HTML sitemap directory."""
        theme_key = theme or self.default_theme
        return render_html_sitemap(
            posts=posts,
            categories=categories,
            theme=theme_key,
            base_url=base_url,
            source_domain=source_domain,
            **kwargs,
        )
