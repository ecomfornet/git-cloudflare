"""Domain models and data structures for the pSEO Static Site Generator & Dashboard."""

from __future__ import annotations

import datetime
import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PostItem:
    """Canonical representation of an ingested editorial post."""

    slug: str = ""
    title: str = ""
    excerpt: str = ""
    content_html: str = ""
    category: str = ""
    category_slug: str = ""
    parent_slug: str = ""
    date: str = ""  # ISO format YYYY-MM-DD
    modified: str = ""  # ISO format YYYY-MM-DD
    image_url: str = ""  # Remote source URL
    local_image_path: str = ""  # e.g. "assets/images/<slug>.jpg"
    image_width: int = 1200  # Web-standard width in pixels
    image_height: int = 750  # Web-standard height in pixels (16:10 aspect ratio)
    custom_edited: bool = False  # True if customized in dashboard
    checklist: list[dict[str, Any]] = field(default_factory=list)  # [{"text": str, "id": str, ...}]
    takeaways: list[str] = field(default_factory=list)
    domain: str = ""
    raw_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serializes PostItem to a dictionary strictly adhering to the contract."""
        return {
            "slug": self.slug,
            "title": self.title,
            "excerpt": self.excerpt,
            "content_html": self.content_html,
            "category": self.category,
            "category_slug": self.category_slug,
            "parent_slug": self.parent_slug,
            "date": self.date,
            "modified": self.modified,
            "image_url": self.image_url,
            "local_image_path": self.local_image_path,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "custom_edited": self.custom_edited,
            "checklist": [dict(c) for c in self.checklist],
            "takeaways": [str(t) for t in self.takeaways],
            "domain": self.domain,
            "raw_meta": dict(self.raw_meta),
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> PostItem:
        """Constructs a PostItem from a dictionary, handling common key aliases gracefully."""
        if not data:
            return cls()

        known_keys = {
            "slug",
            "title",
            "excerpt",
            "description",
            "content_html",
            "content",
            "category",
            "category_slug",
            "parent_slug",
            "date",
            "published",
            "modified",
            "lastmod",
            "image_url",
            "image",
            "featured_image",
            "local_image_path",
            "local_image",
            "image_width",
            "image_height",
            "width",
            "height",
            "custom_edited",
            "checklist",
            "takeaways",
            "domain",
            "raw_meta",
        }

        # Resolve field values with fallback aliases
        slug = str(data.get("slug") or "")
        title = str(data.get("title") or "")
        excerpt = str(data.get("excerpt") or data.get("description") or "")
        content_html = str(data.get("content_html") or data.get("content") or "")
        category = str(data.get("category") or "")
        category_slug = str(data.get("category_slug") or "")
        parent_slug = str(data.get("parent_slug") or "")
        date = str(data.get("date") or data.get("published") or "")
        modified = str(data.get("modified") or data.get("lastmod") or date or "")
        image_url = str(data.get("image_url") or data.get("image") or data.get("featured_image") or "")
        local_image_path = str(data.get("local_image_path") or data.get("local_image") or "")
        domain = str(data.get("domain") or "")
        try:
            image_width = int(data.get("image_width") or data.get("width") or 1200)
        except (ValueError, TypeError):
            image_width = 1200
        try:
            image_height = int(data.get("image_height") or data.get("height") or 750)
        except (ValueError, TypeError):
            image_height = 750

        custom_edited_val = data.get("custom_edited", False)
        if isinstance(custom_edited_val, str):
            custom_edited = custom_edited_val.lower() in ("true", "1", "yes")
        else:
            custom_edited = bool(custom_edited_val)

        raw_checklist = data.get("checklist") or []
        checklist: list[dict[str, Any]] = []
        for idx, item in enumerate(raw_checklist):
            if isinstance(item, dict):
                checklist.append(dict(item))
            elif isinstance(item, str):
                checklist.append({"id": f"item-{idx + 1}", "text": item})

        raw_takeaways = data.get("takeaways") or []
        takeaways = [str(t) for t in raw_takeaways if t]

        # Preserve extra metadata
        raw_meta = dict(data.get("raw_meta") or {})
        for k, v in data.items():
            if k not in known_keys and k not in raw_meta:
                raw_meta[k] = v

        return cls(
            slug=slug,
            title=title,
            excerpt=excerpt,
            content_html=content_html,
            category=category,
            category_slug=category_slug,
            parent_slug=parent_slug,
            date=date,
            modified=modified,
            image_url=image_url,
            local_image_path=local_image_path,
            image_width=image_width,
            image_height=image_height,
            custom_edited=custom_edited,
            checklist=checklist,
            takeaways=takeaways,
            domain=domain,
            raw_meta=raw_meta,
        )


@dataclass
class Manifest:
    """Persistent storage manifest for ingested content and custom overrides."""

    version: str = "2.0"
    updated_at: str = ""
    posts: dict[str, PostItem] = field(default_factory=dict)
    categories: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.updated_at:
            self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def get_post(self, slug: str) -> Optional[PostItem]:
        """Retrieves a post by slug or None if not found."""
        return self.posts.get(slug)

    def upsert_post(self, post: PostItem) -> None:
        """Inserts or replaces a post in the manifest, updating manifest timestamp and taxonomy."""
        if not post.slug:
            raise ValueError("Cannot upsert PostItem with empty slug")
        self.posts[post.slug] = post
        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Update category taxonomy if category is present and not yet registered
        if post.category and post.category_slug:
            existing = any(c.get("slug") == post.category_slug for c in self.categories)
            if not existing:
                self.categories.append({"name": post.category, "slug": post.category_slug})

    def delete_post(self, slug: str) -> Optional[PostItem]:
        """Deletes a post by slug from the manifest."""
        post = self.posts.pop(slug, None)
        if post:
            self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return post

    def to_dict(self) -> dict[str, Any]:
        """Serializes Manifest to dictionary conforming to Interface Contract 1."""
        return {
            "version": self.version,
            "updated_at": self.updated_at,
            "posts": {slug: post.to_dict() for slug, post in self.posts.items()},
            "categories": [dict(c) for c in self.categories],
        }

    def to_json(self, indent: int = 2) -> str:
        """Serializes Manifest to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save_to_json(self, path: str) -> None:
        """Saves Manifest to a JSON file."""
        abs_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> Manifest:
        """Constructs a Manifest from a dictionary (supports both dict and list posts)."""
        if not data:
            return cls()

        posts_data = data.get("posts") or {}
        posts: dict[str, PostItem] = {}

        if isinstance(posts_data, dict):
            for key, post_val in posts_data.items():
                if isinstance(post_val, PostItem):
                    posts[post_val.slug or key] = post_val
                elif isinstance(post_val, dict):
                    item = PostItem.from_dict(post_val)
                    if not item.slug:
                        item.slug = key
                    posts[item.slug] = item
        elif isinstance(posts_data, list):
            for post_val in posts_data:
                if isinstance(post_val, PostItem):
                    posts[post_val.slug] = post_val
                elif isinstance(post_val, dict):
                    item = PostItem.from_dict(post_val)
                    if item.slug:
                        posts[item.slug] = item

        raw_categories = data.get("categories") or []
        categories = [dict(c) for c in raw_categories if isinstance(c, dict)]

        return cls(
            version=str(data.get("version") or "2.0"),
            updated_at=str(data.get("updated_at") or datetime.datetime.now(datetime.timezone.utc).isoformat()),
            posts=posts,
            categories=categories,
        )

    @classmethod
    def load_from_json(cls, path: str) -> Manifest:
        """Loads Manifest from a JSON file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Manifest file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def create_empty(cls, project_id: str = "") -> Manifest:
        """Initializes a brand-new empty Manifest with 0 posts and empty categories."""
        return cls(
            version="2.0",
            updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            posts={},
            categories=[],
        )

    # Convenience alias for PostManifest / Manifest loading
    load = load_from_json


# Backward compatibility and schema alias
PostManifest = Manifest



@dataclass
class DiffSummary:
    """Summary of manifest diffing result comparing incoming feed against current state."""

    new_posts: list[PostItem] = field(default_factory=list)
    updated_posts: list[PostItem] = field(default_factory=list)
    synced_posts: list[PostItem] = field(default_factory=list)
    unchanged_posts: list[PostItem] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return len(self.new_posts) + len(self.updated_posts) + len(self.synced_posts) + len(self.unchanged_posts)

    def to_dict(self) -> dict[str, Any]:
        """Serializes DiffSummary to dictionary with per-category post items and summary counts."""
        return {
            "new_posts": [p.to_dict() for p in self.new_posts],
            "updated_posts": [p.to_dict() for p in self.updated_posts],
            "synced_posts": [p.to_dict() for p in self.synced_posts],
            "unchanged_posts": [p.to_dict() for p in self.unchanged_posts],
            "counts": {
                "new": len(self.new_posts),
                "updated": len(self.updated_posts),
                "synced": len(self.synced_posts),
                "unchanged": len(self.unchanged_posts),
                "total": self.total_count,
            },
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> DiffSummary:
        """Reconstructs DiffSummary from dictionary."""
        if not data:
            return cls()

        def parse_list(items: Any) -> list[PostItem]:
            if not isinstance(items, list):
                return []
            result: list[PostItem] = []
            for item in items:
                if isinstance(item, PostItem):
                    result.append(item)
                elif isinstance(item, dict):
                    result.append(PostItem.from_dict(item))
            return result

        return cls(
            new_posts=parse_list(data.get("new_posts")),
            updated_posts=parse_list(data.get("updated_posts")),
            synced_posts=parse_list(data.get("synced_posts")),
            unchanged_posts=parse_list(data.get("unchanged_posts")),
        )


@dataclass
class RouteResult:
    """Result of resolving a post or taxonomy URL to its web path and local disk path."""

    web_path: str = ""  # e.g. "/guides/decor/cozy-living-room/"
    file_path: str = ""  # e.g. "guides/decor/cozy-living-room/index.html"
    depth: int = 1  # Hierarchy depth
    breadcrumbs: list[dict[str, str]] = field(default_factory=list)  # [{"name": "Home", "url": "/"}, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serializes RouteResult conforming to Interface Contract 2."""
        return {
            "web_path": self.web_path,
            "file_path": self.file_path,
            "depth": self.depth,
            "breadcrumbs": [dict(b) for b in self.breadcrumbs],
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> RouteResult:
        if not data:
            return cls()
        raw_breadcrumbs = data.get("breadcrumbs") or []
        breadcrumbs = [dict(b) for b in raw_breadcrumbs if isinstance(b, dict)]
        return cls(
            web_path=str(data.get("web_path") or ""),
            file_path=str(data.get("file_path") or ""),
            depth=int(data.get("depth", 1)),
            breadcrumbs=breadcrumbs,
        )


@dataclass
class DeployJob:
    """State tracking for a GitHub Pages deployment job."""

    status: str = "pending"  # "pending" | "in_progress" | "success" | "failed"
    started_at: str = ""
    completed_at: str = ""
    total_files: int = 0
    deployed_files: int = 0
    commit_sha: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serializes DeployJob to dictionary."""
        return {
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_files": self.total_files,
            "deployed_files": self.deployed_files,
            "commit_sha": self.commit_sha,
            "errors": [str(e) for e in self.errors],
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> DeployJob:
        if not data:
            return cls()
        raw_errors = data.get("errors") or []
        errors = [str(e) for e in raw_errors]
        return cls(
            status=str(data.get("status") or "pending"),
            started_at=str(data.get("started_at") or ""),
            completed_at=str(data.get("completed_at") or ""),
            total_files=int(data.get("total_files", 0)),
            deployed_files=int(data.get("deployed_files", 0)),
            commit_sha=str(data.get("commit_sha") or ""),
            errors=errors,
        )


@dataclass
class ProjectItem:
    """Canonical representation of an isolated project configuration."""

    id: str = ""
    name: str = ""
    created_at: str = ""
    platform: str = "cloudflare"  # "cloudflare" | "github" | "dual"
    cf_project_name: str = ""
    cf_custom_domain: str = ""
    gh_owner: str = ""
    gh_repo: str = ""
    gh_branch: str = "main"
    gh_is_org: bool = True
    gh_base_path: str = ""
    sitemap_url: str = ""
    theme: str = "editorial-warm"
    routing_mode: str = "single"
    manifest_path: str = ""
    output_dir: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "platform": self.platform,
            "cf_project_name": self.cf_project_name,
            "cf_custom_domain": self.cf_custom_domain,
            "gh_owner": self.gh_owner,
            "gh_repo": self.gh_repo,
            "gh_branch": self.gh_branch,
            "gh_is_org": self.gh_is_org,
            "gh_base_path": self.gh_base_path,
            "sitemap_url": self.sitemap_url,
            "theme": self.theme,
            "routing_mode": self.routing_mode,
            "manifest_path": self.manifest_path,
            "output_dir": self.output_dir,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> ProjectItem:
        if not data:
            return cls()
        return cls(
            id=str(data.get("id") or ""),
            name=str(data.get("name") or data.get("id") or "Untitled Project"),
            created_at=str(data.get("created_at") or datetime.datetime.now(datetime.timezone.utc).isoformat()),
            platform=str(data.get("platform") or "cloudflare"),
            cf_project_name=str(data.get("cf_project_name") or ""),
            cf_custom_domain=str(data.get("cf_custom_domain") or ""),
            gh_owner=str(data.get("gh_owner") or ""),
            gh_repo=str(data.get("gh_repo") or ""),
            gh_branch=str(data.get("gh_branch") or "main"),
            gh_is_org=bool(data.get("gh_is_org", True)),
            gh_base_path=str(data.get("gh_base_path") or ""),
            sitemap_url=str(data.get("sitemap_url") or ""),
            theme=str(data.get("theme") or "editorial-warm"),
            routing_mode=str(data.get("routing_mode") or "single"),
            manifest_path=str(data.get("manifest_path") or ""),
            output_dir=str(data.get("output_dir") or ""),
        )

