"""Configuration dataclasses and loaders for the pSEO Static Site Generator & Dashboard."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GitHubConfig:
    """GitHub repository and Pages deployment settings."""

    token: str = ""
    owner: str = ""
    repo: str = ""
    branch: str = "main"
    is_org: bool = False
    base_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "owner": self.owner,
            "repo": self.repo,
            "branch": self.branch,
            "is_org": self.is_org,
            "base_path": self.base_path,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> GitHubConfig:
        if not data:
            return cls()
        is_org_val = data.get("is_org", False)
        if isinstance(is_org_val, str):
            is_org = is_org_val.lower() in ("true", "1", "yes")
        else:
            is_org = bool(is_org_val)

        return cls(
            token=str(data.get("token") or ""),
            owner=str(data.get("owner") or ""),
            repo=str(data.get("repo") or ""),
            branch=str(data.get("branch") or "main"),
            is_org=is_org,
            base_path=str(data.get("base_path") or ""),
        )


@dataclass
class CloudflareConfig:
    """Cloudflare Workers & Pages deployment configuration."""

    api_token: str = ""
    account_id: str = ""
    account_subdomain: str = ""
    project_name: str = ""
    deployment_type: str = "workers_assets"  # "workers_assets" | "pages"
    custom_domain: str = ""
    compatibility_date: str = "2024-11-01"
    worker_dir: str = "my-worker"

    def get_worker_url(self) -> str:
        """Computes the authoritative workers.dev endpoint containing the worker name."""
        proj = (self.project_name or "worker").strip().lower()
        if self.account_subdomain:
            sub = self.account_subdomain.strip().lower()
            return f"https://{proj}.{sub}.workers.dev"
        return f"https://{proj}.workers.dev"

    def get_live_url(self) -> str:
        """Computes the authoritative public URL for the Cloudflare deployment, keeping worker name in final domain."""
        if self.deployment_type == "pages":
            return f"https://{self.project_name or 'worker'}.pages.dev"
        return self.get_worker_url()

    def to_dict(self) -> dict[str, Any]:
        d = {
            "api_token": self.api_token,
            "account_id": self.account_id,
            "project_name": self.project_name,
            "deployment_type": self.deployment_type,
            "custom_domain": self.custom_domain,
            "compatibility_date": self.compatibility_date,
            "worker_dir": self.worker_dir,
        }
        if self.account_subdomain:
            d["account_subdomain"] = self.account_subdomain
        return d

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> CloudflareConfig:
        if not data:
            return cls()
        return cls(
            api_token=str(data.get("api_token") or ""),
            account_id=str(data.get("account_id") or ""),
            account_subdomain=str(data.get("account_subdomain") or data.get("subdomain") or ""),
            project_name=str(data.get("project_name") or ""),
            deployment_type=str(data.get("deployment_type") or "workers_assets"),
            custom_domain=str(data.get("custom_domain") or ""),
            compatibility_date=str(data.get("compatibility_date") or "2024-11-01"),
            worker_dir=str(data.get("worker_dir") or "my-worker"),
        )


@dataclass
class IngestionConfig:
    """WordPress and Sitemap ingestion settings."""

    sitemap_url: str = ""
    wp_api_url: str = ""
    max_posts: int = 100
    download_images: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "sitemap_url": self.sitemap_url,
            "wp_api_url": self.wp_api_url,
            "max_posts": self.max_posts,
            "download_images": self.download_images,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> IngestionConfig:
        if not data:
            return cls()
        max_posts_raw = data.get("max_posts", 100)
        try:
            max_posts = int(max_posts_raw)
        except (ValueError, TypeError):
            max_posts = 100

        download_images_raw = data.get("download_images", True)
        if isinstance(download_images_raw, str):
            download_images = download_images_raw.lower() in ("true", "1", "yes")
        else:
            download_images = bool(download_images_raw)

        return cls(
            sitemap_url=str(data.get("sitemap_url") or ""),
            wp_api_url=str(data.get("wp_api_url") or ""),
            max_posts=max_posts,
            download_images=download_images,
        )


@dataclass
class BuildConfig:
    """Static site generation and routing options."""

    theme: str = "nordic-studio"
    routing_mode: str = "single"  # single | category_slug | parent_slug | silo_nested
    output_dir: str = "dist"

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme": self.theme,
            "routing_mode": self.routing_mode,
            "output_dir": self.output_dir,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> BuildConfig:
        if not data:
            return cls()
        return cls(
            theme=str(data.get("theme") or "nordic-studio"),
            routing_mode=str(data.get("routing_mode") or "single"),
            output_dir=str(data.get("output_dir") or "dist"),
        )


@dataclass
class DashboardConfig:
    """Local management web server configuration."""

    host: str = "127.0.0.1"
    port: int = 8080

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> DashboardConfig:
        if not data:
            return cls()
        port_raw = data.get("port", 8080)
        try:
            port = int(port_raw)
        except (ValueError, TypeError):
            port = 8080
        return cls(
            host=str(data.get("host") or "127.0.0.1"),
            port=port,
        )


@dataclass
class BrandingConfig:
    """Site branding and programmatic SEO enhancement options."""

    brand_name: str = "Anna Deco"
    tagline: str = "Interior Design & Curated Living"
    logo_path: str = ""  # If empty, default vector SVG emblem is used
    author_name: str = "Anna Lindqvist"
    author_bio: str = "Senior Interior Architect & Kinfolk Stylist"
    enable_toc: bool = True
    enable_faq: bool = True
    enable_eeat: bool = True
    social_links: dict[str, str] = field(default_factory=lambda: {
        "pinterest": "",
        "facebook": "",
        "instagram": "",
        "twitter": "",
        "tiktok": "",
        "youtube": "",
    })

    def to_dict(self) -> dict[str, Any]:
        return {
            "brand_name": self.brand_name,
            "tagline": self.tagline,
            "logo_path": self.logo_path,
            "author_name": self.author_name,
            "author_bio": self.author_bio,
            "enable_toc": self.enable_toc,
            "enable_faq": self.enable_faq,
            "enable_eeat": self.enable_eeat,
            "social_links": dict(self.social_links),
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> BrandingConfig:
        if not data:
            return cls()

        def _bool(val: Any, default: bool = True) -> bool:
            if val is None:
                return default
            if isinstance(val, str):
                return val.lower() in ("true", "1", "yes")
            return bool(val)

        raw_social = data.get("social_links")
        social_dict = {
            "pinterest": "",
            "facebook": "",
            "instagram": "",
            "twitter": "",
            "tiktok": "",
            "youtube": "",
        }
        if isinstance(raw_social, dict):
            for k, v in raw_social.items():
                if k in social_dict and v is not None:
                    social_dict[k] = str(v).strip()
                elif v is not None:
                    social_dict[k] = str(v).strip()

        return cls(
            brand_name=str(data.get("brand_name") or "Anna Deco"),
            tagline=str(data.get("tagline") or "Interior Design & Curated Living"),
            logo_path=str(data.get("logo_path") or ""),
            author_name=str(data.get("author_name") or "Anna Lindqvist"),
            author_bio=str(data.get("author_bio") or "Senior Interior Architect & Kinfolk Stylist"),
            enable_toc=_bool(data.get("enable_toc"), True),
            enable_faq=_bool(data.get("enable_faq"), True),
            enable_eeat=_bool(data.get("enable_eeat"), True),
            social_links=social_dict,
        )


@dataclass
class AppConfig:
    """Master application configuration containing all subsystem settings."""

    github: GitHubConfig = field(default_factory=GitHubConfig)
    cloudflare: CloudflareConfig = field(default_factory=CloudflareConfig)
    ingestion: IngestionConfig = field(default_factory=IngestionConfig)
    build: BuildConfig = field(default_factory=BuildConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    branding: BrandingConfig = field(default_factory=BrandingConfig)
    active_project: str = "stylesdays"
    projects: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "github": self.github.to_dict(),
            "cloudflare": self.cloudflare.to_dict(),
            "ingestion": self.ingestion.to_dict(),
            "build": self.build.to_dict(),
            "dashboard": self.dashboard.to_dict(),
            "branding": self.branding.to_dict(),
            "active_project": self.active_project,
            "projects": self.projects,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save_to_json(self, path: str) -> None:
        """Saves current configuration to a JSON file."""
        abs_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]] = None) -> AppConfig:
        if not data:
            return cls()
        return cls(
            github=GitHubConfig.from_dict(data.get("github")),
            cloudflare=CloudflareConfig.from_dict(data.get("cloudflare")),
            ingestion=IngestionConfig.from_dict(data.get("ingestion")),
            build=BuildConfig.from_dict(data.get("build")),
            dashboard=DashboardConfig.from_dict(data.get("dashboard")),
            branding=BrandingConfig.from_dict(data.get("branding")),
            active_project=str(data.get("active_project") or "stylesdays"),
            projects=dict(data.get("projects") or {}),
        )

    @classmethod
    def load_from_json(cls, path: str) -> AppConfig:
        """Loads configuration from a JSON file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_env(cls) -> AppConfig:
        """Loads configuration overrides from environment variables."""
        config = cls()

        # GitHub overrides
        if "GITHUB_TOKEN" in os.environ:
            config.github.token = os.environ["GITHUB_TOKEN"]
        if "GITHUB_OWNER" in os.environ:
            config.github.owner = os.environ["GITHUB_OWNER"]
        elif "GITHUB_ORG" in os.environ:
            config.github.owner = os.environ["GITHUB_ORG"]
        if "GITHUB_REPO" in os.environ:
            config.github.repo = os.environ["GITHUB_REPO"]
        if "GITHUB_BRANCH" in os.environ:
            config.github.branch = os.environ["GITHUB_BRANCH"]
        if "GITHUB_IS_ORG" in os.environ:
            config.github.is_org = os.environ["GITHUB_IS_ORG"].lower() in ("true", "1", "yes")
        if "GITHUB_BASE_PATH" in os.environ:
            config.github.base_path = os.environ["GITHUB_BASE_PATH"]

        # Cloudflare overrides
        if "CLOUDFLARE_API_TOKEN" in os.environ:
            config.cloudflare.api_token = os.environ["CLOUDFLARE_API_TOKEN"]
        elif "CF_API_TOKEN" in os.environ:
            config.cloudflare.api_token = os.environ["CF_API_TOKEN"]
        if "CLOUDFLARE_ACCOUNT_ID" in os.environ:
            config.cloudflare.account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
        elif "CF_ACCOUNT_ID" in os.environ:
            config.cloudflare.account_id = os.environ["CF_ACCOUNT_ID"]
        if "CLOUDFLARE_PROJECT_NAME" in os.environ:
            config.cloudflare.project_name = os.environ["CLOUDFLARE_PROJECT_NAME"]
        elif "CF_PROJECT_NAME" in os.environ:
            config.cloudflare.project_name = os.environ["CF_PROJECT_NAME"]
        if "CLOUDFLARE_ACCOUNT_SUBDOMAIN" in os.environ:
            config.cloudflare.account_subdomain = os.environ["CLOUDFLARE_ACCOUNT_SUBDOMAIN"]
        elif "CLOUDFLARE_SUBDOMAIN" in os.environ:
            config.cloudflare.account_subdomain = os.environ["CLOUDFLARE_SUBDOMAIN"]
        if "CLOUDFLARE_DEPLOYMENT_TYPE" in os.environ:
            config.cloudflare.deployment_type = os.environ["CLOUDFLARE_DEPLOYMENT_TYPE"]
        if "CLOUDFLARE_CUSTOM_DOMAIN" in os.environ:
            config.cloudflare.custom_domain = os.environ["CLOUDFLARE_CUSTOM_DOMAIN"]

        # Ingestion overrides
        if "SITEMAP_URL" in os.environ:
            config.ingestion.sitemap_url = os.environ["SITEMAP_URL"]
        if "WP_API_URL" in os.environ:
            config.ingestion.wp_api_url = os.environ["WP_API_URL"]
        elif "WP_DOMAIN" in os.environ:
            config.ingestion.wp_api_url = os.environ["WP_DOMAIN"]
        if "MAX_POSTS" in os.environ:
            try:
                config.ingestion.max_posts = int(os.environ["MAX_POSTS"])
            except ValueError:
                pass
        if "DOWNLOAD_IMAGES" in os.environ:
            config.ingestion.download_images = os.environ["DOWNLOAD_IMAGES"].lower() in ("true", "1", "yes")

        # Build overrides
        if "THEME" in os.environ:
            config.build.theme = os.environ["THEME"]
        if "ROUTING_MODE" in os.environ:
            config.build.routing_mode = os.environ["ROUTING_MODE"]
        elif "ROUTE_STRUCTURE" in os.environ:
            config.build.routing_mode = os.environ["ROUTE_STRUCTURE"]
        if "OUTPUT_DIR" in os.environ:
            config.build.output_dir = os.environ["OUTPUT_DIR"]

        # Dashboard overrides
        if "DASHBOARD_HOST" in os.environ:
            config.dashboard.host = os.environ["DASHBOARD_HOST"]
        elif "HOST" in os.environ:
            config.dashboard.host = os.environ["HOST"]
        if "DASHBOARD_PORT" in os.environ:
            try:
                config.dashboard.port = int(os.environ["DASHBOARD_PORT"])
            except ValueError:
                pass
        elif "PORT" in os.environ:
            try:
                config.dashboard.port = int(os.environ["PORT"])
            except ValueError:
                pass

        # Branding overrides
        if "BRAND_NAME" in os.environ:
            config.branding.brand_name = os.environ["BRAND_NAME"]
        if "BRAND_TAGLINE" in os.environ:
            config.branding.tagline = os.environ["BRAND_TAGLINE"]
        if "BRAND_LOGO_PATH" in os.environ:
            config.branding.logo_path = os.environ["BRAND_LOGO_PATH"]

        return config

    @classmethod
    def load(cls, config_path: Optional[str] = None, use_env: bool = True) -> AppConfig:
        """Loads configuration from optional file and overlays environment variables."""
        if config_path and os.path.exists(config_path):
            config = cls.load_from_json(config_path)
        else:
            config = cls()

        if use_env:
            env_config = cls.from_env()

            # GitHub overlay
            if "GITHUB_TOKEN" in os.environ:
                config.github.token = env_config.github.token
            if "GITHUB_OWNER" in os.environ or "GITHUB_ORG" in os.environ:
                config.github.owner = env_config.github.owner
            if "GITHUB_REPO" in os.environ:
                config.github.repo = env_config.github.repo
            if "GITHUB_BRANCH" in os.environ:
                config.github.branch = env_config.github.branch
            if "GITHUB_IS_ORG" in os.environ:
                config.github.is_org = env_config.github.is_org
            if "GITHUB_BASE_PATH" in os.environ:
                config.github.base_path = env_config.github.base_path

            # Cloudflare overlay
            if "CLOUDFLARE_API_TOKEN" in os.environ or "CF_API_TOKEN" in os.environ:
                config.cloudflare.api_token = env_config.cloudflare.api_token
            if "CLOUDFLARE_ACCOUNT_ID" in os.environ or "CF_ACCOUNT_ID" in os.environ:
                config.cloudflare.account_id = env_config.cloudflare.account_id
            if "CLOUDFLARE_PROJECT_NAME" in os.environ or "CF_PROJECT_NAME" in os.environ:
                config.cloudflare.project_name = env_config.cloudflare.project_name
            if "CLOUDFLARE_ACCOUNT_SUBDOMAIN" in os.environ or "CLOUDFLARE_SUBDOMAIN" in os.environ:
                config.cloudflare.account_subdomain = env_config.cloudflare.account_subdomain
            if "CLOUDFLARE_DEPLOYMENT_TYPE" in os.environ:
                config.cloudflare.deployment_type = env_config.cloudflare.deployment_type
            if "CLOUDFLARE_CUSTOM_DOMAIN" in os.environ:
                config.cloudflare.custom_domain = env_config.cloudflare.custom_domain

            # Ingestion overlay
            if "SITEMAP_URL" in os.environ:
                config.ingestion.sitemap_url = env_config.ingestion.sitemap_url
            if "WP_API_URL" in os.environ or "WP_DOMAIN" in os.environ:
                config.ingestion.wp_api_url = env_config.ingestion.wp_api_url
            if "MAX_POSTS" in os.environ:
                config.ingestion.max_posts = env_config.ingestion.max_posts
            if "DOWNLOAD_IMAGES" in os.environ:
                config.ingestion.download_images = env_config.ingestion.download_images

            # Build overlay
            if "THEME" in os.environ:
                config.build.theme = env_config.build.theme
            if "ROUTING_MODE" in os.environ or "ROUTE_STRUCTURE" in os.environ:
                config.build.routing_mode = env_config.build.routing_mode
            if "OUTPUT_DIR" in os.environ:
                config.build.output_dir = env_config.build.output_dir

            # Dashboard overlay
            if "DASHBOARD_HOST" in os.environ or "HOST" in os.environ:
                config.dashboard.host = env_config.dashboard.host
            if "DASHBOARD_PORT" in os.environ or "PORT" in os.environ:
                config.dashboard.port = env_config.dashboard.port

            # Branding overlay
            if "BRAND_NAME" in os.environ:
                config.branding.brand_name = env_config.branding.brand_name
            if "BRAND_TAGLINE" in os.environ:
                config.branding.tagline = env_config.branding.tagline
            if "BRAND_LOGO_PATH" in os.environ:
                config.branding.logo_path = env_config.branding.logo_path

        return config
