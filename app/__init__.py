"""pSEO Static Site Generator & Management Dashboard Application Package.

This package provides:
- Core configuration dataclasses and environment/file loaders (app.config)
- Canonical data models and serialization for posts, manifest, diffing, routing, and deployment (app.models)
- WordPress ingestion and image downloading (app.ingestion)
- Multi-slug URL and folder routing (app.routing)
- Static site building orchestrator (app.generator)
- Multi-theme responsive rendering engine (app.themes)
- Schema.org JSON-LD, OpenGraph, Pinterest, and SEO generators (app.seo)
- GitHub Git Data API Pages deployer (app.deployer)
- Interactive local management web dashboard (app.dashboard)
"""

__version__ = "2.0.0"

from app.config import (
    AppConfig,
    BuildConfig,
    DashboardConfig,
    GitHubConfig,
    IngestionConfig,
)
from app.models import (
    DeployJob,
    DiffSummary,
    Manifest,
    PostItem,
    RouteResult,
)

__all__ = [
    "__version__",
    "AppConfig",
    "GitHubConfig",
    "IngestionConfig",
    "BuildConfig",
    "DashboardConfig",
    "PostItem",
    "Manifest",
    "DiffSummary",
    "RouteResult",
    "DeployJob",
]
