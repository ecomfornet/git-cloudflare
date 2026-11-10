"""Production Web Dashboard HTTP server and REST API for pSEO static site generation and deployment."""

from __future__ import annotations

import base64
import datetime
import html as html_lib
import http.server
import json
import mimetypes
import os
import re
import shutil
import socketserver
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from app.config import AppConfig, BuildConfig, DashboardConfig, GitHubConfig, IngestionConfig
from app.models import DeployJob, DiffSummary, IngestJob, Manifest, PostItem, ProjectItem, RouteResult
from app.themes.engine import ThemeEngine
from app.themes.templates import THEMES, render_category_index, render_hub, render_post


STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))


def mask_token(token: str) -> str:
    """Masks a sensitive personal access token for safe API display."""
    if not token:
        return ""
    if len(token) <= 8:
        return "****"
    return f"{token[:4]}****{token[-4:]}"


def resolve_project_output_dir(
    config: Any,
    target_cloud: Optional[str] = None,
    subdomain: Optional[str] = None,
    project_name: Optional[str] = None,
    base_dir: Optional[str] = None,
) -> tuple[str, str]:
    """
    Resolves the canonical project token and isolated local output directory.
    Returns: (project_token, absolute_output_dir)
    """
    raw_base = base_dir or getattr(getattr(config, "build", None), "output_dir", None) or "dist"
    # Sanitize legacy distooso path
    if os.path.basename(os.path.normpath(raw_base)).lower() == "distooso":
        raw_base = "dist"

    tc = (target_cloud or "").lower().strip()
    cf = getattr(config, "cloudflare", None)
    gh = getattr(config, "github", None)

    active_plat = (
        getattr(getattr(config, "build", None), "active_platform", None)
        or getattr(config, "active_platform", None)
        or "cloudflare"
    )

    if tc in ("cloudflare", "cf"):
        token = (
            subdomain
            or getattr(cf, "project_name", "")
            or project_name
            or "styleire"
        ).strip()
    elif tc in ("github", "gh"):
        token = (
            getattr(gh, "owner", "")
            or getattr(gh, "repo", "").replace(".github.io", "")
            or project_name
            or subdomain
            or "styleire"
        ).strip()
    else:
        # Auto-detect: prioritize explicit project identifiers, then platform configs
        if subdomain or project_name:
            token = (subdomain or project_name).strip()
        elif active_plat in ("cloudflare", "cf") and getattr(cf, "project_name", None):
            token = cf.project_name.strip()
        elif active_plat in ("github", "gh") and getattr(gh, "owner", None):
            token = gh.owner.strip()
        else:
            token = (getattr(cf, "project_name", "") or getattr(gh, "owner", "") or "default").strip()

    # Sanitize token for filesystem safety
    clean_token = re.sub(r"[^a-zA-Z0-9_-]", "-", token).strip("-_") or "default"

    # Guard against nested dist/<token>/<token>
    norm_base = os.path.normpath(raw_base)
    if os.path.basename(norm_base).lower() == clean_token.lower():
        output_dir = os.path.abspath(norm_base)
    else:
        output_dir = os.path.abspath(os.path.join(raw_base, clean_token))

    return clean_token, output_dir


class DashboardManager:
    """State manager handling configuration, manifest data, background builds, and deployment jobs."""

    def __init__(self, config_path: str = "pseo_config.json", manifest_path: str = "pseo_manifest.json") -> None:
        self.config_path = os.path.abspath(config_path)
        self.manifest_path = os.path.abspath(manifest_path)
        self.lock = threading.RLock()

        # Load configuration
        if os.path.exists(self.config_path):
            try:
                self.config = AppConfig.load_from_json(self.config_path)
            except Exception as e:
                self.config = AppConfig()
        else:
            self.config = AppConfig()

        # Load or initialize manifest
        if os.path.exists(self.manifest_path):
            try:
                self.manifest = Manifest.load_from_json(self.manifest_path)
            except Exception:
                self.manifest = Manifest()
        else:
            self.manifest = Manifest()

        # State tracking
        self.theme_engine = ThemeEngine(default_theme=self.config.build.theme)
        self.deploy_job = DeployJob(status="idle")
        self.ingest_job = IngestJob(status="idle")
        self.logs: list[str] = []
        self.last_build_time: str = ""
        self.last_build_files: int = 0
        self.active_project_id: str = getattr(self.config, "active_project", None) or "styleire"
        self.active_manifest_path: str = self.manifest_path
        self.projects: dict[str, ProjectItem] = {}
        self._init_projects()
        self.log("Dashboard system initialized and ready.")

    def _init_projects(self) -> None:
        """Loads configured projects from config and sets up active manifest."""
        self.projects = {}
        # 1. Load explicitly configured projects
        for pid, pdata in getattr(self.config, "projects", {}).items():
            if isinstance(pdata, dict):
                item = ProjectItem.from_dict(pdata)
                item.id = pid
                self.projects[pid] = item

        # 2. Pick or initialize active project
        if self.projects:
            if self.active_project_id not in self.projects:
                active_p = getattr(self.config, "active_project", "")
                self.active_project_id = active_p if active_p in self.projects else list(self.projects.keys())[0]
            proj_manifest = os.path.abspath(os.path.join("scraped_data", self.active_project_id, "manifest.json"))
            if os.path.exists(proj_manifest):
                try:
                    self.manifest = Manifest.load_from_json(proj_manifest)
                    self.active_manifest_path = proj_manifest
                except Exception as e:
                    self.log(f"Notice: Error loading project manifest {proj_manifest}: {e}")
                    self.manifest = Manifest.create_empty(self.active_project_id)
                    self.active_manifest_path = proj_manifest
            else:
                self.manifest = Manifest.create_empty(self.active_project_id)
                self.active_manifest_path = proj_manifest
        else:
            self.active_project_id = ""
            self.manifest = Manifest.create_empty("")
            self.active_manifest_path = ""

    def list_projects(self) -> list[dict[str, Any]]:
        """Returns serialized list of registered projects with post/category metrics."""
        with self.lock:
            result = []
            for pid, p in self.projects.items():
                d = p.to_dict()
                d["active"] = (pid == self.active_project_id)
                mpath = os.path.abspath(os.path.join("scraped_data", pid, "manifest.json"))
                if pid == self.active_project_id:
                    d["total_posts"] = len(self.manifest.posts)
                    d["categories_count"] = len(self.manifest.categories)
                elif os.path.exists(mpath):
                    try:
                        m = Manifest.load_from_json(mpath)
                        d["total_posts"] = len(m.posts)
                        d["categories_count"] = len(m.categories)
                    except Exception:
                        d["total_posts"] = 0
                        d["categories_count"] = 0
                elif pid == "stylesdays" and os.path.exists(self.manifest_path):
                    try:
                        m = Manifest.load_from_json(self.manifest_path)
                        d["total_posts"] = len(m.posts)
                        d["categories_count"] = len(m.categories)
                    except Exception:
                        d["total_posts"] = 0
                        d["categories_count"] = 0
                else:
                    d["total_posts"] = 0
                    d["categories_count"] = 0
                result.append(d)
            return result

    def create_project(
        self,
        name: str,
        platform: str = "cloudflare",
        cf_project_name: str = "",
        cf_custom_domain: str = "",
        gh_owner: str = "",
        gh_repo: str = "",
        gh_branch: str = "main",
        gh_is_org: bool = True,
        sitemap_url: str = "",
        theme: Optional[str] = None,
        routing_mode: Optional[str] = None,
    ) -> dict[str, Any]:
        """Creates a brand new isolated project with an EMPTY manifest (0 posts, 0 categories)."""
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("Project name cannot be empty")

        pid = re.sub(r"[^a-zA-Z0-9_-]", "-", clean_name.lower()).strip("-_") or "project"
        with self.lock:
            # Ensure unique id
            base_pid = pid
            counter = 1
            while pid in self.projects:
                pid = f"{base_pid}-{counter}"
                counter += 1

            proj_dir = os.path.abspath(os.path.join("scraped_data", pid))
            html_dir = os.path.join(proj_dir, "html")
            assets_dir = os.path.abspath(os.path.join("assets", pid, "images"))
            os.makedirs(html_dir, exist_ok=True)
            os.makedirs(assets_dir, exist_ok=True)

            # Create EMPTY manifest for new project!
            manifest_file = os.path.join(proj_dir, "manifest.json")
            empty_manifest = Manifest.create_empty(project_id=pid)
            empty_manifest.save_to_json(manifest_file)

            # Defaults
            cf_proj = cf_project_name.strip() or pid
            gh_own = gh_owner.strip() or getattr(self.config.github, "owner", "")
            gh_rp = gh_repo.strip() or (f"{gh_own}.github.io" if gh_own else f"{pid}.github.io")

            item = ProjectItem(
                id=pid,
                name=clean_name,
                created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                platform=platform,
                cf_project_name=cf_proj,
                cf_custom_domain=cf_custom_domain.strip(),
                gh_owner=gh_own,
                gh_repo=gh_rp,
                gh_branch=gh_branch.strip() or "main",
                gh_is_org=gh_is_org,
                gh_base_path="",
                sitemap_url=sitemap_url.strip(),
                theme=theme.strip() if theme else (self.config.build.theme or "editorial-warm"),
                routing_mode=routing_mode.strip() if routing_mode else (self.config.build.routing_mode or "single"),
                manifest_path=os.path.relpath(manifest_file),
                output_dir=os.path.join("dist", cf_proj if platform == "cloudflare" else pid),
            )

            self.projects[pid] = item
            if not hasattr(self.config, "projects"):
                self.config.projects = {}
            self.config.projects[pid] = item.to_dict()

            # Switch active project to this new project
            self.active_project_id = pid
            self.active_manifest_path = manifest_file
            self.manifest = empty_manifest
            self.config.active_project = pid

            if cf_proj:
                self.config.cloudflare.project_name = cf_proj
            if cf_custom_domain:
                self.config.cloudflare.custom_domain = cf_custom_domain
            if gh_own:
                self.config.github.owner = gh_own
            if gh_rp:
                self.config.github.repo = gh_rp
            if sitemap_url:
                self.config.ingestion.sitemap_url = sitemap_url

            self.save_config()
            self.log(f"Created new isolated project '{clean_name}' (id={pid}) with empty category catalog.")
            return {
                "success": True,
                "project": item.to_dict(),
                "active_project": pid,
                "total_posts": 0,
                "categories_count": 0,
                "message": f"Project '{clean_name}' created successfully with empty categories.",
            }

    def update_project(self, project_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Updates configuration fields for a registered project and persists to disk."""
        with self.lock:
            pid = (project_id or self.active_project_id).strip()
            if pid not in self.projects:
                raise KeyError(f"Project '{pid}' not found.")

            item = self.projects[pid]

            # 1. Unpack nested updates payload if present
            raw_updates = dict(updates or {})
            if "updates" in raw_updates and isinstance(raw_updates["updates"], dict):
                raw_updates.update(raw_updates["updates"])

            # 2. Map input aliases to internal dataclass field names
            if "custom_domain" in raw_updates and "cf_custom_domain" not in raw_updates:
                raw_updates["cf_custom_domain"] = raw_updates["custom_domain"]
            if "worker_name" in raw_updates and "cf_project_name" not in raw_updates:
                raw_updates["cf_project_name"] = raw_updates["worker_name"]
            if "github_owner" in raw_updates and "gh_owner" not in raw_updates:
                raw_updates["gh_owner"] = raw_updates["github_owner"]
            if "github_repo" in raw_updates and "gh_repo" not in raw_updates:
                raw_updates["gh_repo"] = raw_updates["github_repo"]

            domain_changed = False
            for field_name in (
                "name", "platform", "cf_project_name", "cf_custom_domain",
                "gh_owner", "gh_repo", "gh_branch", "gh_is_org", "sitemap_url",
                "theme", "routing_mode", "max_posts", "download_images",
            ):
                if field_name in raw_updates and raw_updates[field_name] is not None:
                    val = raw_updates[field_name]
                    if field_name == "max_posts":
                        try:
                            val = int(val)
                        except (ValueError, TypeError):
                            val = 60
                    elif field_name == "download_images":
                        val = bool(val)
                    elif isinstance(val, str):
                        val = val.strip()
                    if field_name == "cf_custom_domain":
                        old_cd = getattr(item, "cf_custom_domain", "") or ""
                        val = re.sub(r"^https?://", "", str(val).strip(), flags=re.IGNORECASE).strip("/ ")
                        if old_cd != val:
                            domain_changed = True
                    setattr(item, field_name, val)

            # Sync to active config if updating the currently active project
            if pid == self.active_project_id:
                if item.theme:
                    self.config.build.theme = item.theme
                    self.theme_engine.default_theme = item.theme
                if item.routing_mode:
                    self.config.build.routing_mode = item.routing_mode
                if item.cf_project_name:
                    self.config.cloudflare.project_name = item.cf_project_name
                if item.cf_custom_domain is not None:
                    clean_cd = re.sub(r"^https?://", "", str(item.cf_custom_domain).strip(), flags=re.IGNORECASE).strip("/ ")
                    item.cf_custom_domain = clean_cd
                    self.config.cloudflare.custom_domain = clean_cd
                    if clean_cd:
                        cur_brand = (getattr(self.config.branding, "brand_name", "") or "").strip()
                        if not cur_brand or (pid and cur_brand.lower() == pid.lower()):
                            from app.generator.site_builder import derive_brand_from_domain
                            derived = derive_brand_from_domain(clean_cd, worker_name=pid)
                            self.config.branding.brand_name = derived
                if item.gh_owner:
                    self.config.github.owner = item.gh_owner
                if item.gh_repo:
                    self.config.github.repo = item.gh_repo
                if item.sitemap_url:
                    self.config.ingestion.sitemap_url = item.sitemap_url
                if hasattr(item, "max_posts") and item.max_posts:
                    self.config.ingestion.max_posts = int(item.max_posts)
                if hasattr(item, "download_images") and item.download_images is not None:
                    self.config.ingestion.download_images = bool(item.download_images)
                if "social_links" in raw_updates and isinstance(raw_updates["social_links"], dict):
                    self.config.branding.social_links.update({str(k): str(v).strip() for k, v in raw_updates["social_links"].items() if v is not None})

            # Persist project item in config
            if not hasattr(self.config, "projects"):
                self.config.projects = {}
            self.config.projects[pid] = item.to_dict()
            self.save_config()

            # Immediate sanitization pass: purge worker name from HTML theme text in dist and worker public
            clean_domain = (getattr(item, "cf_custom_domain", "") or "").strip()
            if clean_domain or domain_changed:
                try:
                    from app.generator.site_builder import SiteBuilder, derive_brand_from_domain
                    brand = derive_brand_from_domain(clean_domain, worker_name=pid) if clean_domain else "Styleire"
                    # Preserve worker name in final domain URLs; user connects custom domain manually
                    worker_base_url = self.config.cloudflare.get_live_url()
                    dist_dir = os.path.abspath(os.path.join("dist", pid))
                    worker_pub = os.path.abspath(os.path.join(self.config.cloudflare.worker_dir or "my-worker", "public"))
                    for target_dir in (dist_dir, worker_pub):
                        if os.path.exists(target_dir):
                            SiteBuilder.sanitize_directory(
                                output_dir=target_dir,
                                worker_names=[pid, item.cf_project_name],
                                base_url=worker_base_url,
                                brand_name=brand,
                                config=self.config,
                            )
                except Exception as exc:
                    self.log(f"[WARN] Sanitization on project update encountered error: {exc}")

        self.log(f"[PROJECT] Updated settings for '{item.name}' (id={pid}, custom_domain='{item.cf_custom_domain}').")
        return {"success": True, "status": "success", "project": item.to_dict()}


    def switch_project(self, project_id: str) -> dict[str, Any]:
        """Switches active project, dynamically re-pointing manifest and reloading isolated categories."""
        pid = str(project_id).strip()
        with self.lock:
            if pid not in self.projects:
                cand = os.path.abspath(os.path.join("scraped_data", pid, "manifest.json"))
                if os.path.exists(cand):
                    self.projects[pid] = ProjectItem(
                        id=pid,
                        name=pid.title(),
                        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        manifest_path=os.path.relpath(cand),
                        output_dir=os.path.join("dist", pid),
                        cf_project_name=pid,
                    )
                else:
                    raise KeyError(f"Project '{pid}' does not exist.")

            item = self.projects[pid]
            manifest_path = os.path.abspath(os.path.join("scraped_data", pid, "manifest.json"))
            if os.path.exists(manifest_path):
                self.manifest = Manifest.load_from_json(manifest_path)
                self.active_manifest_path = manifest_path
            elif pid == "stylesdays" and os.path.exists(self.manifest_path):
                self.manifest = Manifest.load_from_json(self.manifest_path)
                self.active_manifest_path = self.manifest_path
            else:
                self.manifest = Manifest.create_empty(pid)
                self.manifest.save_to_json(manifest_path)
                self.active_manifest_path = manifest_path

            self.active_project_id = pid
            self.config.active_project = pid

            # Apply project attributes to active config
            if item.theme:
                self.config.build.theme = item.theme
                self.theme_engine.default_theme = item.theme
            if item.routing_mode:
                self.config.build.routing_mode = item.routing_mode
            self.config.cloudflare.project_name = item.cf_project_name or item.id
            if item.cf_custom_domain is not None:
                self.config.cloudflare.custom_domain = item.cf_custom_domain
            if item.gh_owner:
                self.config.github.owner = item.gh_owner
            if item.gh_repo:
                self.config.github.repo = item.gh_repo
            if item.sitemap_url:
                self.config.ingestion.sitemap_url = item.sitemap_url

            self.save_config()
            self.log(f"Switched active project to '{item.name}' (id={pid}, {len(self.manifest.posts)} posts, {len(self.manifest.categories)} categories).")
            return {
                "success": True,
                "active_project": pid,
                "project": item.to_dict(),
                "total_posts": len(self.manifest.posts),
                "categories_count": len(self.manifest.categories),
                "message": f"Switched to project '{item.name}'.",
            }

    def delete_project(self, project_id: str) -> dict[str, Any]:
        """Deletes a project from config and memory."""
        pid = str(project_id).strip()
        with self.lock:
            if pid not in self.projects:
                raise KeyError(f"Project '{pid}' does not exist.")
            del self.projects[pid]
            if hasattr(self.config, "projects") and pid in self.config.projects:
                del self.config.projects[pid]
            if self.active_project_id == pid:
                self.active_project_id = list(self.projects.keys())[0] if self.projects else ""
                self.config.active_project = self.active_project_id
            self.save_config()
            return {"success": True, "deleted": pid, "active_project": self.active_project_id}

    def reset_all_projects(self) -> dict[str, Any]:
        """Resets all projects from config and memory, establishing an empty blank slate."""
        with self.lock:
            self.projects.clear()
            self.config.projects = {}
            self.active_project_id = ""
            self.config.active_project = ""
            self.manifest = Manifest.create_empty("")
            self.save_config()
            return {"success": True, "message": "All projects reset to empty blank slate."}

    def resolve_output_dir(
        self,
        target_cloud: Optional[str] = None,
        subdomain: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> tuple[str, str]:
        """Resolves the isolated local output directory for the given or active project."""
        effective_sub = subdomain or self.active_project_id
        effective_proj = project_name or self.active_project_id
        return resolve_project_output_dir(
            self.config,
            target_cloud=target_cloud,
            subdomain=effective_sub,
            project_name=effective_proj,
        )

    def log(self, message: str) -> None:
        """Appends a timestamped message to the server log buffer."""
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        entry = f"[{now}] {message}"
        with self.lock:
            self.logs.append(entry)
            # Keep reasonable buffer size
            if len(self.logs) > 1000:
                self.logs.pop(0)
        try:
            print(entry)
        except Exception:
            try:
                print(entry.encode("ascii", errors="replace").decode("ascii"))
            except Exception:
                pass

    def save_config(self) -> None:
        """Persists current configuration to disk."""
        with self.lock:
            self.config.save_to_json(self.config_path)
        self.log(f"Saved configuration to {self.config_path}")

    def save_manifest(self) -> None:
        """Persists current manifest to active project manifest path and fallback."""
        with self.lock:
            active_path = getattr(self, "active_manifest_path", None)
            if not active_path:
                active_path = os.path.abspath(os.path.join("scraped_data", self.active_project_id, "manifest.json"))
            os.makedirs(os.path.dirname(os.path.abspath(active_path)), exist_ok=True)
            self.manifest.save_to_json(active_path)

            # If active project is stylesdays, also sync to root manifest for backward compatibility
            if self.active_project_id in ("stylesdays", "default"):
                self.manifest.save_to_json(self.manifest_path)
        self.log(f"Saved manifest ({len(self.manifest.posts)} posts, {len(self.manifest.categories)} categories) to {active_path}")

    def get_status(self) -> dict[str, Any]:
        """Returns overall system status, post metrics, and readiness checks."""
        with self.lock:
            total_posts = len(self.manifest.posts)
            custom_count = sum(1 for p in self.manifest.posts.values() if p.custom_edited)
            cats_count = len(self.manifest.categories)
            git_ready = bool(self.config.github.token and self.config.github.repo)
            cf_ready = bool(self.config.cloudflare.api_token or self.config.cloudflare.project_name)
            assets_dir = os.path.abspath(os.path.join("assets", "images"))
            local_images_count = (
                len([f for f in os.listdir(assets_dir) if os.path.isfile(os.path.join(assets_dir, f))])
                if os.path.exists(assets_dir)
                else 0
            )

            return {
                "status": "ok",
                "active_project": self.active_project_id,
                "active_project_name": self.projects.get(self.active_project_id, ProjectItem(name=self.active_project_id)).name,
                "projects_count": len(self.projects),
                "total_posts": total_posts,
                "local_images_count": local_images_count,
                "synced": total_posts - custom_count,
                "updated": 0,
                "new": 0,
                "custom_edited": custom_count,
                "categories_count": cats_count,
                "git_ready": git_ready,
                "cloudflare_ready": cf_ready,
                "cloudflare_project": self.config.cloudflare.project_name,
                "cloudflare_url": self.config.cloudflare.get_live_url(),
                "theme": self.config.build.theme,
                "routing_mode": self.config.build.routing_mode,
                "last_build": self.last_build_time or "never",
                "last_build_files": self.last_build_files,
                "output_dir": self.resolve_output_dir()[1],
                "base_output_dir": (self.config.build.output_dir if self.config.build.output_dir != "distooso" else "dist"),
                "cf_output_dir": self.resolve_output_dir(target_cloud="cloudflare")[1],
                "gh_output_dir": self.resolve_output_dir(target_cloud="github")[1],
                "available_themes": list(THEMES.keys()),
                "available_routing_modes": ["single", "category_slug", "parent_slug", "silo_nested"],
                "branding": self.config.branding.to_dict(),
            }

    def get_config_dict(self) -> dict[str, Any]:
        """Returns active configuration with GitHub PAT and Cloudflare Token masked."""
        with self.lock:
            raw = self.config.to_dict()
            token = self.config.github.token
            raw["github"]["has_token"] = bool(token)
            raw["github"]["token_masked"] = mask_token(token)
            raw["github"]["token"] = mask_token(token)

            cf_token = self.config.cloudflare.api_token
            raw["cloudflare"]["has_token"] = bool(cf_token)
            raw["cloudflare"]["token_masked"] = mask_token(cf_token)
            raw["cloudflare"]["api_token"] = mask_token(cf_token)
            raw["cloudflare"]["account_subdomain"] = self.config.cloudflare.account_subdomain
            raw["cloudflare"]["worker_url"] = self.config.cloudflare.get_live_url()
            raw["cloudflare"]["live_url"] = self.config.cloudflare.get_live_url()
            return raw

    def get_categories(self) -> dict[str, Any]:
        """Returns categories dictionary from active manifest safely."""
        with self.lock:
            return getattr(self.manifest, "categories", {}) or {}

    def update_config_from_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Updates configuration and persists changes."""
        with self.lock:
            gh_data = data.get("github") or {}
            cf_data = data.get("cloudflare") or {}
            ing_data = data.get("ingestion") or {}
            bld_data = data.get("build") or {}
            dash_data = data.get("dashboard") or {}

            # Preserve token if incoming is masked or empty
            new_token = gh_data.get("token")
            if new_token and not new_token.startswith("****") and not "****" in new_token:
                self.config.github.token = str(new_token)
            if "owner" in gh_data:
                self.config.github.owner = str(gh_data["owner"])
            elif "github_org" in data:
                self.config.github.owner = str(data["github_org"])
            if "repo" in gh_data:
                self.config.github.repo = str(gh_data["repo"])
            elif "github_repo" in data:
                self.config.github.repo = str(data["github_repo"])
            if "branch" in gh_data:
                self.config.github.branch = str(gh_data["branch"])
            if "is_org" in gh_data:
                self.config.github.is_org = bool(gh_data["is_org"])
            if "base_path" in gh_data:
                self.config.github.base_path = str(gh_data["base_path"])

            # Cloudflare updates
            new_cf_token = cf_data.get("api_token") or cf_data.get("token")
            if new_cf_token and not new_cf_token.startswith("****") and "****" not in new_cf_token:
                self.config.cloudflare.api_token = str(new_cf_token)
            if "account_id" in cf_data:
                self.config.cloudflare.account_id = str(cf_data["account_id"])
            if "account_subdomain" in cf_data:
                self.config.cloudflare.account_subdomain = str(cf_data["account_subdomain"]).strip()
            elif "subdomain" in cf_data:
                self.config.cloudflare.account_subdomain = str(cf_data["subdomain"]).strip()
            if "project_name" in cf_data:
                self.config.cloudflare.project_name = str(cf_data["project_name"])
            if "deployment_type" in cf_data:
                self.config.cloudflare.deployment_type = str(cf_data["deployment_type"])
            if "custom_domain" in cf_data:
                self.config.cloudflare.custom_domain = str(cf_data["custom_domain"])
            if "compatibility_date" in cf_data:
                self.config.cloudflare.compatibility_date = str(cf_data["compatibility_date"])

            if "sitemap_url" in ing_data:
                self.config.ingestion.sitemap_url = str(ing_data["sitemap_url"])
            elif "sitemap_url" in data:
                self.config.ingestion.sitemap_url = str(data["sitemap_url"])
            if "wp_api_url" in ing_data:
                self.config.ingestion.wp_api_url = str(ing_data["wp_api_url"])
            elif "wp_domain" in data:
                self.config.ingestion.wp_api_url = str(data["wp_domain"])
            if "max_posts" in ing_data:
                self.config.ingestion.max_posts = int(ing_data["max_posts"])
            if "download_images" in ing_data:
                self.config.ingestion.download_images = bool(ing_data["download_images"])

            if "theme" in bld_data:
                self.config.build.theme = str(bld_data["theme"])
            elif "theme" in data:
                self.config.build.theme = str(data["theme"])
            if "routing_mode" in bld_data:
                self.config.build.routing_mode = str(bld_data["routing_mode"])
            elif "route_structure" in data:
                self.config.build.routing_mode = str(data["route_structure"])
            if "output_dir" in bld_data:
                self.config.build.output_dir = str(bld_data["output_dir"])

            # Branding and pSEO updates
            br_data = data.get("branding") or {}
            if "brand_name" in br_data:
                self.config.branding.brand_name = str(br_data["brand_name"])
            elif "brand_name" in data:
                self.config.branding.brand_name = str(data["brand_name"])
            if "tagline" in br_data:
                self.config.branding.tagline = str(br_data["tagline"])
            elif "tagline" in data:
                self.config.branding.tagline = str(data["tagline"])
            if "logo_path" in br_data:
                self.config.branding.logo_path = str(br_data["logo_path"])
            if "author_name" in br_data:
                self.config.branding.author_name = str(br_data["author_name"])
            if "author_bio" in br_data:
                self.config.branding.author_bio = str(br_data["author_bio"])
            if "enable_toc" in br_data:
                self.config.branding.enable_toc = bool(br_data["enable_toc"])
            elif "enable_toc" in data:
                self.config.branding.enable_toc = bool(data["enable_toc"])
            if "enable_faq" in br_data:
                self.config.branding.enable_faq = bool(br_data["enable_faq"])
            elif "enable_faq" in data:
                self.config.branding.enable_faq = bool(data["enable_faq"])
            if "enable_eeat" in br_data:
                self.config.branding.enable_eeat = bool(br_data["enable_eeat"])
            elif "enable_eeat" in data:
                self.config.branding.enable_eeat = bool(data["enable_eeat"])
            if "social_links" in br_data and isinstance(br_data["social_links"], dict):
                self.config.branding.social_links.update({str(k): str(v).strip() for k, v in br_data["social_links"].items() if v is not None})
            elif "social_links" in data and isinstance(data["social_links"], dict):
                self.config.branding.social_links.update({str(k): str(v).strip() for k, v in data["social_links"].items() if v is not None})

            self.theme_engine.default_theme = self.config.build.theme

            # Synchronize theme and routing_mode to active project item
            if self.active_project_id:
                if self.active_project_id in self.projects:
                    self.projects[self.active_project_id].theme = self.config.build.theme
                    self.projects[self.active_project_id].routing_mode = self.config.build.routing_mode
                if hasattr(self.config, "projects") and self.active_project_id in self.config.projects:
                    cfg_proj = self.config.projects[self.active_project_id]
                    if isinstance(cfg_proj, dict):
                        cfg_proj["theme"] = self.config.build.theme
                        cfg_proj["routing_mode"] = self.config.build.routing_mode
                    else:
                        cfg_proj.theme = self.config.build.theme
                        cfg_proj.routing_mode = self.config.build.routing_mode

            # Synchronize active ProjectItem metadata if active project exists
            if self.active_project_id and self.active_project_id in self.config.projects:
                active_proj = self.config.projects[self.active_project_id]
                if isinstance(active_proj, dict):
                    if "owner" in gh_data or "github_org" in data:
                        active_proj["gh_owner"] = self.config.github.owner
                    if "repo" in gh_data or "github_repo" in data:
                        active_proj["gh_repo"] = self.config.github.repo
                    if "project_name" in cf_data:
                        active_proj["cf_project_name"] = self.config.cloudflare.project_name
                    if "custom_domain" in cf_data:
                        active_proj["cf_custom_domain"] = self.config.cloudflare.custom_domain
                    if "sitemap_url" in ing_data or "sitemap_url" in data:
                        active_proj["sitemap_url"] = self.config.ingestion.sitemap_url
                else:
                    if "owner" in gh_data or "github_org" in data:
                        active_proj.gh_owner = self.config.github.owner
                    if "repo" in gh_data or "github_repo" in data:
                        active_proj.gh_repo = self.config.github.repo
                    if "project_name" in cf_data:
                        active_proj.cf_project_name = self.config.cloudflare.project_name
                    if "custom_domain" in cf_data:
                        active_proj.cf_custom_domain = self.config.cloudflare.custom_domain
                    if "sitemap_url" in ing_data or "sitemap_url" in data:
                        active_proj.sitemap_url = self.config.ingestion.sitemap_url

        self.save_config()
        return self.get_config_dict()

    def list_posts(
        self,
        query: str = "",
        category: str = "",
        status_filter: str = "",
        custom_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Lists and filters posts from the active manifest."""
        with self.lock:
            result = []
            q = query.strip().lower()
            cat = category.strip().lower()

            for slug, post in self.manifest.posts.items():
                if custom_only and not post.custom_edited:
                    continue
                if cat and post.category.lower() != cat and post.category_slug.lower() != cat:
                    continue
                if q:
                    match = (
                        q in post.title.lower()
                        or q in post.slug.lower()
                        or q in post.excerpt.lower()
                        or q in post.category.lower()
                    )
                    if not match:
                        continue

                d = post.to_dict()
                d["diff_status"] = "CUSTOM" if post.custom_edited else "SYNCED"
                result.append(d)

            # Sort by modified date descending or title
            result.sort(key=lambda p: p.get("modified") or p.get("date") or "", reverse=True)
            return result

    def get_post(self, slug: str) -> Optional[dict[str, Any]]:
        """Retrieves full post details by slug."""
        with self.lock:
            post = self.manifest.get_post(slug)
            return post.to_dict() if post else None

    def update_post(self, slug: str, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Updates post content fields and marks custom_edited = True."""
        with self.lock:
            post = self.manifest.get_post(slug)
            if not post:
                return None

            if "title" in data:
                post.title = str(data["title"])
            if "excerpt" in data:
                post.excerpt = str(data["excerpt"])
            elif "description" in data:
                post.excerpt = str(data["description"])
            if "category" in data:
                post.category = str(data["category"])
            if "category_slug" in data:
                post.category_slug = str(data["category_slug"])
            if "parent_slug" in data:
                post.parent_slug = str(data["parent_slug"])
            if "takeaways" in data and isinstance(data["takeaways"], list):
                post.takeaways = [str(t) for t in data["takeaways"] if t]
            if "checklist" in data and isinstance(data["checklist"], list):
                cl_list: list[dict[str, Any]] = []
                for idx, c in enumerate(data["checklist"]):
                    if isinstance(c, dict):
                        cl_list.append(c)
                    elif isinstance(c, str):
                        cl_list.append({"id": f"{slug}-step-{idx+1}", "text": c})
                post.checklist = cl_list

            post.custom_edited = True
            post.modified = datetime.date.today().isoformat()
            self.manifest.upsert_post(post)

        self.save_manifest()
        self.log(f"Updated post '{slug}' (custom_edited=True)")
        return post.to_dict()

    def render_preview(
        self,
        slug: Optional[str] = None,
        post_data: Optional[dict[str, Any]] = None,
        theme: Optional[str] = None,
        routing_mode: Optional[str] = None,
        view_mode: Optional[str] = None,
    ) -> str:
        """Renders live HTML in memory for a given post or homepage hub and theme."""
        theme_name = theme or self.config.build.theme
        r_mode = routing_mode or self.config.build.routing_mode

        # Check if user requested homepage / hub preview
        is_hub_request = (
            view_mode == "hub"
            or (isinstance(slug, str) and slug.strip("/") in ("__hub__", "hub", "index", "home", "__home__"))
        )

        if is_hub_request:
            with self.lock:
                all_posts_list = list(self.manifest.posts.values())
            if not all_posts_list:
                all_posts_list = [
                    PostItem(
                        slug="japanese-wabi-sabi-minimalist-living-room",
                        title="Japanese Wabi-Sabi: 7 Intentional Living Room Concepts Celebrating Imperfection",
                        excerpt="Explore how reclaimed cedar timbers, textured limewash, and natural flax textures shape an acoustic calm sanctuary away from modern noise.",
                        category="Living Room",
                        category_slug="living-room",
                        local_image_path="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=80",
                    ),
                    PostItem(
                        slug="minimalist-travertine-fire-pit-guide",
                        title="Minimalist Travertine Fire Pits: Architectural Hearth Designs for Twilight Living",
                        excerpt="How circular Roman travertine benches and low smokeless gas inserts ground evening conversation in textural harmony.",
                        category="Fire Pits",
                        category_slug="fire-pits",
                        local_image_path="https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
                    ),
                    PostItem(
                        slug="scandinavian-linen-bedroom-styling",
                        title="Scandinavian Linen Bedding: Muted Palettes and Raw Oak Joinery",
                        excerpt="Curating an earthy retreat with heavy unbleached Belgian linen, low platform oak beds, and diffused 2700K ambient illumination.",
                        category="Bedroom Inspo",
                        category_slug="bedroom-inspo",
                        local_image_path="https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1200&q=80",
                    ),
                ]
            brand_clean = getattr(self.config.branding, "brand_name", "") or "Atelier Maison"
            hub_title = f"{brand_clean} Editorial Hub"
            return render_hub(
                posts=all_posts_list,
                categories=self.manifest.categories,
                title=hub_title,
                subtitle="Curated Home Organization, Room Checklists, and DIY Tutorials.",
                base_url="",
                theme=theme_name,
                source_domain=self.config.ingestion.wp_api_url or "stylesdays.com",
                branding=self.config.branding,
                routing_mode=r_mode,
            )

        target_post: Optional[PostItem] = None
        if post_data:
            target_post = PostItem.from_dict(post_data)
        elif slug:
            with self.lock:
                target_post = self.manifest.get_post(slug)

        if not target_post or (slug in ("sample-guide", "__sample__", None) and not post_data):
            if theme_name == "nordic-studio":
                target_post = PostItem(
                    slug="20-modern-bedroom-ideas-transform-your-space-with-style",
                    title="20 Modern Bedroom Ideas: Transform Your Space with Architectural Style",
                    excerpt="An asymmetric 2-column architectural studio layout featuring technical spec drawers with room dimensions, 2700K lighting specs, and White Oak herringbone flooring plans.",
                    category="Modern Architecture",
                    category_slug="modern-architecture",
                    parent_slug="bedroom-ideas",
                    date="2026-10-20",
                    modified="2026-10-20",
                    local_image_path="/assets/images/20-modern-bedroom-ideas-transform-your-space-with-style.webp",
                    takeaways=[
                        "Room Dimensions First: Always start with a measured floor plan — 14' × 16' is the ideal studio bedroom.",
                        "Lighting Specification: 2700K warm neutral kelvin ceiling and task lights create architectural depth.",
                        "White Oak Herringbone: Parquet flooring in wide plank or herringbone adds tactile geometric character.",
                    ],
                    checklist=[
                        {"id": "step-1", "text": "Draft a scaled floor plan at 14ft x 16ft with traffic flow paths mapped"},
                        {"id": "step-2", "text": "Source White Oak herringbone flooring samples and compare plank widths"},
                        {"id": "step-3", "text": "Install 2700K warm neutral ceiling lights + bedside task lighting"},
                        {"id": "step-4", "text": "Select matte black hardware for wardrobe, drawers, and door levers"},
                    ],
                )
            elif theme_name == "pinterest-mag":
                target_post = PostItem(
                    slug="16-coastal-bedroom-decor-essentials-transform-your-space",
                    title="16 Coastal Bedroom Decor Essentials: Transform Your Beach House Space",
                    excerpt="A high-fashion visual pin discovery magazine layout with floating 📌 Save to Pinterest badge, 2-column moodboard pin cards, 98% viral save score bar, and ruby-red editorial accents.",
                    category="Coastal Decor",
                    category_slug="coastal-decor",
                    parent_slug="bedroom-ideas",
                    date="2026-10-16",
                    modified="2026-10-16",
                    local_image_path="/assets/images/16-coastal-bedroom-decor-essentials-transform-your-space.webp",
                    takeaways=[
                        "Coastal Palette: Sandy neutrals, seafoam whites, and driftwood greys create instant beach house atmosphere.",
                        "Natural Fibre Textiles: Jute rugs, linen throws, and rattan furniture bring organic coastal warmth indoors.",
                        "Pinterest-Worthy Styling: Vertical stripes, oversized mirrors, and layered cushion arrangements drive 98% save rates.",
                    ],
                    checklist=[
                        {"id": "step-1", "text": "Choose a coastal neutral palette: Sandy, Seafoam, Driftwood, and Coral accent"},
                        {"id": "step-2", "text": "Source jute or seagrass rug as the room anchor piece"},
                        {"id": "step-3", "text": "Add 3 layers of cushions in varying textures: linen, velvet, embroidered"},
                        {"id": "step-4", "text": "Style a decorative shelf with shells, coral pieces, and whitewashed driftwood frames"},
                    ],
                )
            else:
                target_post = PostItem(
                    slug="15-home-bedroom-refresh-ideas-transform-your-oasis",
                    title="15 Bedroom Refresh Ideas: Transform Your Oasis with Linen & Warmth",
                    excerpt="A warm, editorial-styled bedroom sanctuary using Belgian linen bedding, bouclé accents, and Playfair serif typography. Sourced exclusively from slow-living Kinfolk aesthetic.",
                    category="Bedroom Refresh",
                    category_slug="bedroom-refresh",
                    parent_slug="bedroom-ideas",
                    date="2026-10-15",
                    modified="2026-10-15",
                    local_image_path="/assets/images/15-home-bedroom-refresh-ideas-transform-your-oasis.webp",
                    takeaways=[
                        "Belgian Linen Bedding: Choose natural flax weave in fog or oat colourways for a lived-in warmth.",
                        "Warm Amber Lighting: Install 2700K Edison pendants at 3 varying heights to eliminate cold dark corners.",
                        "Editor Sourcing: Source bouclé throws from ethical Merino wool producers for lasting tactile comfort.",
                    ],
                    checklist=[
                        {"id": "step-1", "text": "Wash and pre-shrink all linen bedding before making up the bed"},
                        {"id": "step-2", "text": "Layer textures: linen duvet + woven throw + embroidered cushions"},
                        {"id": "step-3", "text": "Install warm amber bulb pendants with dimmable switch"},
                        {"id": "step-4", "text": "Add live dried botanicals (pampas, lunaria) for editorial styling"},
                    ],
                )

        # Resolve custom domain if present for preview source_domain & base_url
        active_proj = self.projects.get(self.active_project_id) if hasattr(self, "projects") else None
        custom_dom = ""
        if active_proj:
            custom_dom = (getattr(active_proj, "cf_custom_domain", "") or getattr(active_proj, "custom_domain", "") or "").strip()
        if not custom_dom and hasattr(self.config, "cloudflare") and self.config.cloudflare.custom_domain:
            custom_dom = self.config.cloudflare.custom_domain.strip()
        preview_source_domain = re.sub(r"^https?://", "", custom_dom, flags=re.IGNORECASE).strip("/ ") if custom_dom else (self.config.ingestion.wp_api_url or "stylesdays.com")
        preview_base_url = f"https://{preview_source_domain}" if custom_dom else ""

        all_posts_list = list(self.manifest.posts.values())
        return render_post(
            post=target_post,
            all_posts=all_posts_list,
            base_url=preview_base_url,
            theme=theme_name,
            source_domain=preview_source_domain,
            branding=self.config.branding,
            categories=self.get_categories(),
            routing_mode=r_mode,
        )

    def start_ingest_job(
        self,
        source_type: str = "sitemap",
        url_or_list: str = "",
        max_posts: Optional[int] = None,
        download_images: Optional[bool] = None,
        force_full_resync: bool = False,
        cf_custom_domain: Optional[str] = None,
        cf_project_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Launches an asynchronous ingestion job in a background daemon thread."""
        with self.lock:
            if self.ingest_job.status == "running":
                return {
                    "success": False,
                    "error": "An ingestion job is already running.",
                    "job": self.ingest_job.to_dict(),
                }

            # Persist entered sitemap_url & max_posts into active project immediately
            if url_or_list and source_type == "sitemap":
                self.config.ingestion.sitemap_url = url_or_list.strip()
                if self.active_project_id in self.projects:
                    self.projects[self.active_project_id].sitemap_url = url_or_list.strip()
            if max_posts is not None:
                self.config.ingestion.max_posts = int(max_posts)
                if self.active_project_id in self.projects:
                    self.projects[self.active_project_id].max_posts = int(max_posts)
            if download_images is not None:
                self.config.ingestion.download_images = bool(download_images)
                if self.active_project_id in self.projects:
                    self.projects[self.active_project_id].download_images = bool(download_images)

            if cf_custom_domain is not None:
                clean_cd = re.sub(r"^https?://", "", str(cf_custom_domain).strip(), flags=re.IGNORECASE).strip("/ ")
                self.config.cloudflare.custom_domain = clean_cd
                if self.active_project_id in self.projects:
                    self.projects[self.active_project_id].cf_custom_domain = clean_cd
                if clean_cd:
                    from app.generator.site_builder import derive_brand_from_domain
                    self.config.branding.brand_name = derive_brand_from_domain(clean_cd, worker_name=self.active_project_id)

            if cf_project_name is not None and str(cf_project_name).strip():
                clean_pn = str(cf_project_name).strip()
                self.config.cloudflare.project_name = clean_pn
                if self.active_project_id in self.projects:
                    self.projects[self.active_project_id].cf_project_name = clean_pn

            if self.active_project_id in self.projects:
                if not hasattr(self.config, "projects"):
                    self.config.projects = {}
                self.config.projects[self.active_project_id] = self.projects[self.active_project_id].to_dict()
            self.save_config()

            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self.ingest_job = IngestJob(
                status="running",
                started_at=now_iso,
                message=f"Starting ingestion (source={source_type})...",
                counts={"new": 0, "updated": 0, "synced": 0, "total": 0},
            )

        def _worker() -> None:
            try:
                def progress_cb(level: str, msg: str, processed: int = 0, total: int = 0, current_url: str = "") -> None:
                    with self.lock:
                        if total > 0:
                            self.ingest_job.total_count = total
                        if processed > 0:
                            self.ingest_job.processed_count = processed
                        if current_url:
                            self.ingest_job.current_post = current_url
                        self.ingest_job.message = msg
                    self.log(f"[{level.upper()}] {msg}")

                diff_summary = self.run_ingest(
                    source_type=source_type,
                    url_or_list=url_or_list,
                    max_posts=max_posts,
                    download_images=download_images,
                    force_full_resync=force_full_resync,
                    progress_callback=progress_cb,
                )
                with self.lock:
                    self.ingest_job.status = "success"
                    self.ingest_job.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    self.ingest_job.counts = diff_summary.to_dict().get("counts", {})
                    self.ingest_job.new_posts = [p.to_dict() for p in diff_summary.new_posts]
                    self.ingest_job.updated_posts = [p.to_dict() for p in diff_summary.updated_posts]
                    self.ingest_job.synced_posts = [p.to_dict() for p in diff_summary.synced_posts]
                    self.ingest_job.message = (
                        f"Ingestion complete: {len(diff_summary.new_posts)} new, "
                        f"{len(diff_summary.updated_posts)} updated, {len(diff_summary.synced_posts)} synced."
                    )

                # Automatically re-compile static build and update worker public assets
                try:
                    self.run_build(
                        clean=False,
                        target_cloud="cloudflare",
                        project_name=self.active_project_id,
                        subdomain=self.active_project_id,
                    )
                except Exception as auto_bld_err:
                    self.log(f"[WARN] Ingestion post-build sync encountered notice: {auto_bld_err}")
            except Exception as e:
                err_msg = str(e)
                self.log(f"[ERROR] Ingestion job failed: {err_msg}")
                with self.lock:
                    self.ingest_job.status = "error"
                    self.ingest_job.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    self.ingest_job.error = err_msg
                    self.ingest_job.message = f"Ingestion failed: {err_msg}"

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return {
            "success": True,
            "status": "running",
            "job_id": f"job_{int(time.time())}",
            "message": "Ingestion job started in background.",
            "job": self.ingest_job.to_dict(),
        }

    def get_ingest_status(self) -> dict[str, Any]:
        """Returns the serialized status of the background ingestion job."""
        with self.lock:
            return self.ingest_job.to_dict()

    def run_ingest(
        self,
        source_type: str = "sitemap",
        url_or_list: str = "",
        max_posts: Optional[int] = None,
        download_images: Optional[bool] = None,
        force_full_resync: bool = False,
        progress_callback: Optional[Any] = None,
    ) -> DiffSummary:
        """Executes ingestion from sitemap XML, URL list, or WordPress REST API."""
        self.log(f"Starting ingestion (source={source_type})...")
        max_count = max_posts if max_posts is not None else self.config.ingestion.max_posts
        dl_images = download_images if download_images is not None else self.config.ingestion.download_images
        sitemap_url = url_or_list if source_type == "sitemap" and url_or_list else self.config.ingestion.sitemap_url
        wp_api_url = self.config.ingestion.wp_api_url or "https://stylesdays.com"

        discovered_posts: list[PostItem] = []

        # Ingestion logic based on source type
        if source_type == "sitemap" and sitemap_url:
            self.log(f"Scraping full article content and images from XML sitemap: {sitemap_url}...")
            try:
                from app.ingestion.web_scraper import scrape_sitemap
                cb = progress_callback or (lambda lvl, msg: self.log(f"[{lvl.upper()}] {msg}"))
                discovered_posts = scrape_sitemap(
                    sitemap_url=sitemap_url,
                    max_posts=max_count,
                    download_images=dl_images,
                    base_dir=".",
                    progress_callback=cb,
                    project_id=self.active_project_id,
                )
            except Exception as exc:
                self.log(f"Notice: Sitemap scraper fallback ({exc}); attempting WP REST client...")
                try:
                    from app.ingestion.wp_client import fetch_wp_posts
                    discovered_posts = fetch_wp_posts(wp_api_url, max_posts=max_count)
                except Exception:
                    discovered_posts = self._fallback_ingestion(source_type, url_or_list, max_count)
        elif source_type == "url_list" and url_or_list:
            self.log("Ingesting and scraping from URL list...")
            try:
                from app.ingestion.sitemap_parser import parse_url_list
                from app.ingestion.web_scraper import scrape_url_list
                urls = parse_url_list(url_or_list)
                if urls:
                    discovered_posts = scrape_url_list(
                        urls=urls,
                        max_posts=max_count,
                        download_images=dl_images,
                        base_dir=".",
                        progress_callback=lambda lvl, msg: self.log(f"[{lvl.upper()}] {msg}"),
                    )
                else:
                    discovered_posts = self._fallback_ingestion(source_type, url_or_list, max_count)
            except Exception as exc:
                self.log(f"Notice: URL list scraping fallback ({exc}), using core engine.")
                discovered_posts = self._fallback_ingestion(source_type, url_or_list, max_count)
        elif source_type == "wp_api":
            self.log(f"Fetching posts from WordPress REST API ({wp_api_url})...")
            try:
                from app.ingestion.wp_client import fetch_wp_posts
                discovered_posts = fetch_wp_posts(wp_api_url, max_posts=max_count)
            except Exception as exc:
                self.log(f"Notice: WP REST API client error ({exc}), using fallback.")
                discovered_posts = self._fallback_ingestion(source_type, url_or_list, max_count)
        else:
            discovered_posts = self._fallback_ingestion(source_type, url_or_list, max_count)

        # Execute diffing while preserving custom edits on matching slugs
        diff_summary = DiffSummary()
        scoped_posts: dict[str, PostItem] = {}
        with self.lock:
            for new_p in discovered_posts:
                existing = self.manifest.get_post(new_p.slug)
                if not existing:
                    diff_summary.new_posts.append(new_p)
                    scoped_posts[new_p.slug] = new_p
                else:
                    if existing.custom_edited and not force_full_resync:
                        # Strictly preserve user custom edits!
                        existing.image_url = new_p.image_url or existing.image_url
                        if new_p.local_image_path:
                            existing.local_image_path = new_p.local_image_path
                        diff_summary.synced_posts.append(existing)
                        scoped_posts[new_p.slug] = existing
                    else:
                        if existing.modified != new_p.modified or existing.title != new_p.title:
                            new_p.checklist = existing.checklist or new_p.checklist
                            new_p.takeaways = existing.takeaways or new_p.takeaways
                            diff_summary.updated_posts.append(new_p)
                            scoped_posts[new_p.slug] = new_p
                        else:
                            diff_summary.synced_posts.append(existing)
                            scoped_posts[new_p.slug] = existing

            # Rebind manifest.posts strictly to discovered posts, purging alien posts
            self.manifest.posts = scoped_posts
            self.manifest.recompute_categories()

            # Download & save images to project assets
            if dl_images:
                self.log("Downloading/saving featured images to project assets...")
                try:
                    from app.ingestion.image_downloader import download_post_image
                    domain_to_use = self.active_project_id if self.active_project_id not in ("styleire", "stylesdays", "default") else None
                    for p in (diff_summary.new_posts + diff_summary.updated_posts):
                        saved_path = download_post_image(p, output_dir=".", force=force_full_resync, domain=domain_to_use or p.domain)
                        p.local_image_path = saved_path
                        self.manifest.upsert_post(p)
                    for p in diff_summary.synced_posts:
                        if not p.local_image_path or not os.path.exists(p.local_image_path):
                            saved_path = download_post_image(p, output_dir=".", domain=domain_to_use or p.domain)
                            p.local_image_path = saved_path
                            self.manifest.upsert_post(p)
                except Exception as exc:
                    self.log(f"Notice: Image download encountered an issue: {exc}")

            self.manifest.recompute_categories()
            self.save_manifest()
        self.log(
            f"Ingestion complete: {len(diff_summary.new_posts)} new, "
            f"{len(diff_summary.updated_posts)} updated, {len(diff_summary.synced_posts)} synced."
        )
        return diff_summary

    def sync_all_post_images(self, force: bool = False) -> dict[str, Any]:
        """Ensures every post in the manifest has an image saved in the project assets/images/ directory."""
        self.log("Syncing all post images to project assets/images/...")
        from app.ingestion.image_downloader import download_post_image
        if self.active_project_id in ("styleire", "stylesdays", "default"):
            proj_assets_dir = os.path.abspath(os.path.join("assets", "images"))
            domain_param = None
            asset_rel_prefix = "assets/images"
        else:
            proj_assets_dir = os.path.abspath(os.path.join("assets", self.active_project_id, "images"))
            domain_param = self.active_project_id
            asset_rel_prefix = f"assets/{self.active_project_id}/images"
        os.makedirs(proj_assets_dir, exist_ok=True)

        # Ensure placeholder.svg exists in target directory
        placeholder_src = os.path.join(proj_assets_dir, "placeholder.svg")
        if not os.path.exists(placeholder_src):
            try:
                from app.generator.site_builder import _generate_svg_fallback
                with open(placeholder_src, "w", encoding="utf-8") as f:
                    f.write(_generate_svg_fallback("Editorial Organization Guide", self.active_project_id.title(), "#B45309"))
            except Exception:
                pass

        synced = 0
        downloaded = 0
        svg_generated = 0
        with self.lock:
            for post in self.manifest.posts.values():
                slug = post.slug
                proj_img = None
                clean_path = (post.local_image_path or "").lstrip("/").replace("\\", "/")
                if not force and clean_path and os.path.exists(clean_path) and os.path.getsize(clean_path) > 64:
                    proj_img = clean_path
                else:
                    for ext in (".webp", ".jpg", ".jpeg", ".png", ".svg"):
                        c = os.path.join(proj_assets_dir, f"{slug}{ext}")
                        if os.path.exists(c) and os.path.getsize(c) > 64:
                            proj_img = f"{asset_rel_prefix}/{slug}{ext}"
                            break

                if proj_img and not force:
                    post.local_image_path = proj_img
                    synced += 1
                else:
                    res = download_post_image(post, output_dir=".", force=force, domain=domain_param)
                    post.local_image_path = res
                    if res.endswith(".svg"):
                        svg_generated += 1
                    else:
                        downloaded += 1
                    synced += 1
            self.save_manifest()
        self.log(f"Image asset sync complete: {synced} total ({downloaded} downloaded, {svg_generated} generated SVGs).")

        # Auto-compile static site and sync assets into my-worker/public
        try:
            self.run_build(
                clean=False,
                target_cloud="cloudflare",
                project_name=self.active_project_id,
                subdomain=self.active_project_id,
            )
        except Exception as bld_err:
            self.log(f"[WARN] Post-asset-sync build auto-compilation: {bld_err}")

        return {
            "success": True,
            "total": synced,
            "downloaded": downloaded,
            "generated_svg": svg_generated,
        }

    def optimize_all_images(self, quality: int = 82) -> dict[str, Any]:
        """Batch optimizes all project images to standard WebP and updates active project manifest."""
        self.log("Starting batch image optimization to WebP (16:10 / 1200x750)...")
        from app.ingestion.image_downloader import batch_optimize_directory
        with self.lock:
            # Strictly resolve active manifest path
            target_manifest = getattr(self, "active_manifest_path", None)
            if not target_manifest:
                target_manifest = os.path.abspath(
                    os.path.join("scraped_data", self.active_project_id, "manifest.json")
                )

            # Resolve project image assets directory
            if self.active_project_id in ("styleire", "stylesdays", "default"):
                images_dir = os.path.abspath(os.path.join("assets", "images"))
            else:
                proj_images = os.path.abspath(os.path.join("assets", self.active_project_id, "images"))
                if os.path.exists(proj_images):
                    images_dir = proj_images
                else:
                    images_dir = os.path.abspath(os.path.join("assets", "images"))

            stats = batch_optimize_directory(
                images_dir=images_dir,
                manifest_path=target_manifest,
                quality=quality,
            )
            # Re-read active manifest to keep state strictly in sync — NEVER reload root pseo_manifest.json for custom projects!
            if os.path.exists(target_manifest):
                self.manifest = Manifest.load_from_json(target_manifest)
                self.active_manifest_path = target_manifest
        self.log(
            f"Optimization finished: {stats['converted']} files optimized. "
            f"Size reduced from {stats['original_bytes']:,} to {stats['optimized_bytes']:,} bytes "
            f"({stats['percent_reduction']}% reduction)."
        )
        return {
            "success": True,
            "stats": stats,
        }

    def _fallback_ingestion(self, source_type: str, url_or_list: str, max_count: int) -> list[PostItem]:
        """Built-in fallback ingestion logic using standard library."""
        posts: list[PostItem] = []
        if source_type == "url_list" and url_or_list:
            lines = [l.strip() for l in url_or_list.splitlines() if l.strip() and not l.startswith("#")]
            for u in lines[:max_count]:
                parts = [p for p in u.strip("/").split("/") if p]
                slug = parts[-1] if parts else "guide"
                posts.append(
                    PostItem(
                        slug=slug,
                        title=slug.replace("-", " ").title(),
                        excerpt=f"Editorial styling and room layout guide for {slug.replace('-', ' ')}.",
                        category="Home Organization",
                        category_slug="home-organization",
                        parent_slug="home-organization",
                        date=datetime.date.today().isoformat(),
                        modified=datetime.date.today().isoformat(),
                    )
                )
        else:
            # Generate sample seed posts if manifest is empty or default demo
            sample_slugs = [
                ("best-ikea-pax-wardrobe-hacks", "15 Best IKEA PAX Wardrobe Hacks for Luxury Closets", "IKEA Hacks", "ikea-hacks"),
                ("small-walk-in-closet-ideas", "Small Walk-In Closet Ideas for Maximum Storage", "IKEA Storage & Closet", "closet-storage"),
                ("ikea-kallax-nursery-storage", "IKEA Kallax Nursery Storage Transformations", "IKEA Hacks", "ikea-hacks"),
                ("minimalist-bedroom-styling", "Minimalist Scandinavian Bedroom Styling Tips", "Bedroom Ideas", "bedroom-design"),
                ("cozy-living-room-layout", "Cozy Living Room Layouts with Layered Lighting", "Living Room Styling", "living-room"),
            ]
            for s, t, cat, parent in sample_slugs:
                posts.append(
                    PostItem(
                        slug=s,
                        title=t,
                        excerpt=f"Explore our comprehensive {t.lower()} with step-by-step room prep instructions.",
                        category=cat,
                        category_slug=parent,
                        parent_slug=parent,
                        date="2026-10-25",
                        modified="2026-10-25",
                        local_image_path=f"/assets/images/{s}.svg",
                    )
                )
        return posts

    def run_build(
        self,
        clean: bool = True,
        base_url: Optional[str] = None,
        target_cloud: Optional[str] = None,
        project_name: Optional[str] = None,
        subdomain: Optional[str] = None,
        theme: Optional[str] = None,
        routing_mode: Optional[str] = None,
    ) -> dict[str, Any]:
        """Compiles the static site by delegating directly to the unified SiteBuilder pipeline."""
        # 1. Resolve effective project identifier with strict active project fallback
        effective_sub = (subdomain or project_name or self.active_project_id or "default").strip()

        project_token, output_dir = self.resolve_output_dir(
            target_cloud=target_cloud,
            subdomain=effective_sub,
            project_name=effective_sub,
        )

        proj_item = self.projects.get(effective_sub) if hasattr(self, "projects") else None

        # Check for configured Custom Domain (Highest Priority)
        effective_custom_domain = ""
        clean_dom = ""
        if proj_item:
            effective_custom_domain = (getattr(proj_item, "cf_custom_domain", "") or getattr(proj_item, "custom_domain", "") or "").strip()
        if not effective_custom_domain and hasattr(self.config, "cloudflare") and self.config.cloudflare.custom_domain:
            effective_custom_domain = self.config.cloudflare.custom_domain.strip()

        # 2. Canonical base URL resolution and brand derivation
        if effective_custom_domain:
            clean_dom = re.sub(r"^https?://", "", effective_custom_domain, flags=re.IGNORECASE).strip("/ ")
            if self.config.cloudflare.custom_domain != clean_dom:
                self.config.cloudflare.custom_domain = clean_dom
            if proj_item and getattr(proj_item, "cf_custom_domain", "") != clean_dom:
                proj_item.cf_custom_domain = clean_dom
            from app.generator.site_builder import derive_brand_from_domain
            derived = derive_brand_from_domain(clean_dom, worker_name=effective_sub)
            self.config.branding.brand_name = derived

        if base_url is None:
            active_plat = (
                getattr(getattr(self.config, "build", None), "active_platform", None)
                or getattr(self.config, "active_platform", None)
                or "cloudflare"
            )
            # If a custom domain is configured, static HTML must strictly use the domain as base_url
            if clean_dom:
                base_url = f"https://{clean_dom}"
            elif target_cloud in ("cloudflare", "cf") or (target_cloud is None and active_plat in ("cloudflare", "cf")):
                cf = self.config.cloudflare
                if cf.account_subdomain and effective_sub:
                    base_url = f"https://{effective_sub}.{cf.account_subdomain}.workers.dev"
                elif cf.project_name == effective_sub:
                    base_url = cf.get_live_url()
                elif cf.custom_domain:
                    base_url = f"https://{cf.custom_domain.strip('/')}"
                elif effective_sub:
                    base_url = f"https://{effective_sub}.workers.dev"
                else:
                    base_url = cf.get_live_url()
            elif target_cloud in ("github", "gh") or (target_cloud is None and active_plat in ("github", "gh")):
                gh = self.config.github
                if gh.repo.endswith(".github.io"):
                    base_url = f"https://{gh.repo}"
                elif gh.owner:
                    base_url = f"https://{gh.owner}.github.io/{gh.repo}" if gh.repo else f"https://{gh.owner}.github.io"
                else:
                    base_url = ""
            elif self.config.cloudflare.project_name:
                base_url = self.config.cloudflare.get_live_url()
            else:
                base_url = ""
        effective_routing_mode = (
            routing_mode
            or (getattr(proj_item, "routing_mode", None) if proj_item else None)
            or getattr(getattr(self.config, "build", None), "routing_mode", None)
            or "single"
        )
        effective_theme = (
            theme
            or (getattr(proj_item, "theme", None) if proj_item else None)
            or getattr(getattr(self.config, "build", None), "theme", None)
            or "editorial-warm"
        )
        # Harmonize project item, build config, and theme engine with effective theme
        if proj_item:
            proj_item.theme = effective_theme
            proj_item.routing_mode = effective_routing_mode
        self.config.build.theme = effective_theme
        self.config.build.routing_mode = effective_routing_mode
        self.theme_engine.default_theme = effective_theme
        routing_mode = effective_routing_mode
        theme = effective_theme

        self.log(
            f"Building static site via SiteBuilder to {output_dir} "
            f"(project={effective_sub}, mode={routing_mode}, theme={theme}, base_url={base_url or 'relative'})..."
        )

        with self.lock:
            # Persist active manifest to disk prior to compilation
            self.save_manifest()

            from app.generator.site_builder import SiteBuilder
            builder = SiteBuilder(
                config=self.config,
                output_dir=output_dir,
                subdomain=effective_sub,
                base_url=base_url,
                theme=theme,
                routing_mode=routing_mode,
            )

            # Build strictly with the active project manifest (never allow None fallback)
            summary = builder.build(manifest_or_posts=self.manifest, subdomain=effective_sub)

            self.last_build_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self.last_build_files = len(summary.files_created)

        # Log errors if any occurred during build
        if summary.errors:
            for err in summary.errors:
                self.log(f"[BUILD ERROR] {err}")

        self.log(
            f"Build completed successfully via SiteBuilder: {len(summary.files_created)} files generated "
            f"in {output_dir} ({summary.duration_seconds}s)."
        )

        # Auto-sync to my-worker/public for Cloudflare edge deployment
        try:
            worker_pub = os.path.abspath(os.path.join(self.config.cloudflare.worker_dir or "my-worker", "public"))
            if os.path.exists(os.path.dirname(worker_pub)):
                from app.deployer.cloudflare import CloudflareDeployer
                deployer = CloudflareDeployer(self.config.cloudflare)
                deployer.sync_worker_assets(output_dir=output_dir, subdomain=effective_sub)
        except Exception as auto_sync_exc:
            self.log(f"[WARN] Auto-sync to worker public assets: {auto_sync_exc}")

        # Return backward-compatible response dictionary conforming to app.js and test expectations
        return {
            "success": summary.status in ("success", "partial_success"),
            "status": summary.status,
            "project_name": project_token,
            "output_dir": output_dir,
            "files_generated": len(summary.files_created),
            "files_count": len(summary.files_created),
            "assets_copied": summary.images_copied,
            "images_copied": summary.images_copied,
            "total_posts": summary.total_posts,
            "post_pages_generated": summary.post_pages_generated,
            "intermediate_pages_generated": summary.intermediate_pages_generated,
            "total_pages_generated": summary.total_pages_generated,
            "duration_seconds": summary.duration_seconds,
            "theme": theme,
            "routing_mode": routing_mode,
            "timestamp": self.last_build_time,
            "errors": [str(e) for e in summary.errors],
        }

    def run_deploy(self, dry_run: bool = False, project_name: Optional[str] = None) -> dict[str, Any]:
        """Executes GitHub Pages deployment via Git Data API (or simulated dry-run)."""
        project_token, output_dir = self.resolve_output_dir(
            target_cloud="github",
            project_name=project_name,
        )
        self.log(f"Starting GitHub Pages deployment job (project={project_token}, output_dir={output_dir}, dry_run={dry_run})...")
        with self.lock:
            self.deploy_job = DeployJob(
                status="in_progress",
                started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )

        def deploy_worker() -> None:
            try:
                if not os.path.exists(output_dir):
                    self.log(f"Project directory {output_dir} missing. Running static build first...")
                    self.run_build(target_cloud="github", project_name=project_token)

                files_to_deploy = []
                for root, _, files in os.walk(output_dir):
                    for f in files:
                        full = os.path.join(root, f)
                        rel = os.path.relpath(full, output_dir).replace("\\", "/")
                        files_to_deploy.append((rel, full))

                self.log(f"Collected {len(files_to_deploy)} files to deploy.")

                if dry_run:
                    # Simulate atomic Git Data API operations
                    self.log("[DRY-RUN] Simulating Git Data API payload assembly...")
                    for rel, _ in files_to_deploy:
                        self.log(f"[DRY-RUN] Validated Base64 blob payload: {rel}")
                    self.log(f"[DRY-RUN] Assembled Git tree with {len(files_to_deploy)} entries (mode 100644).")
                    mock_commit = "c0ffee" + "0" * 34
                    self.log(f"[DRY-RUN] Simulated commit created: {mock_commit}")
                    self.log(f"[DRY-RUN] Simulated ref patched: refs/heads/{self.config.github.branch}")

                    with self.lock:
                        self.deploy_job.status = "success"
                        self.deploy_job.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                        self.deploy_job.total_files = len(files_to_deploy)
                        self.deploy_job.deployed_files = len(files_to_deploy)
                        self.deploy_job.commit_sha = mock_commit
                    self.log("Dry run deployment completed successfully.")
                    return

                # Real GitHub Pages deployment
                token = self.config.github.token
                owner = self.config.github.owner
                repo = self.config.github.repo
                branch = self.config.github.branch
                is_org = self.config.github.is_org

                if not token or not owner or not repo:
                    err = "GitHub token, owner, and repo must be configured before deploying."
                    self.log(f"[ERROR] {err}")
                    with self.lock:
                        self.deploy_job.status = "failed"
                        self.deploy_job.errors.append(err)
                    return

                # Attempt to use app.deployer.github if available
                try:
                    from app.deployer.github import deploy_to_github_pages
                    self.log("Invoking app.deployer.github engine...")
                    job = deploy_to_github_pages(
                        output_dir=output_dir,
                        owner=owner,
                        repo=repo,
                        token=token,
                        branch=branch,
                        is_org=is_org,
                        logger=self.log,
                    )
                    commit_sha = job.commit_sha if hasattr(job, "commit_sha") else str(job)
                except Exception as exc:
                    self.log(f"Notice: Modular deployer not loaded ({exc}), calling reference deployer...")
                    from pseo_github_deployer import deploy_to_github_pages as ref_deploy
                    ref_deploy(
                        output_dir=output_dir,
                        owner=owner,
                        repo=repo,
                        token=token,
                        is_org=is_org,
                        branch=branch,
                    )
                    commit_sha = "deployed-via-reference"

                with self.lock:
                    self.deploy_job.status = "success"
                    self.deploy_job.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    self.deploy_job.total_files = len(files_to_deploy)
                    self.deploy_job.deployed_files = len(files_to_deploy)
                    self.deploy_job.commit_sha = commit_sha

                self.log(f"Deployment to GitHub Pages succeeded (commit={commit_sha}).")

            except Exception as e:
                err_msg = f"Deployment failed: {e}"
                self.log(f"[ERROR] {err_msg}")
                with self.lock:
                    self.deploy_job.status = "failed"
                    self.deploy_job.errors.append(str(e))

        t = threading.Thread(target=deploy_worker, daemon=True)
        t.start()

        return {
            "success": True,
            "message": "Deployment job started in background.",
            "dry_run": dry_run,
            "job": self.deploy_job.to_dict(),
        }

    def verify_cloudflare_credentials(self, token: Optional[str] = None, account_id: Optional[str] = None) -> dict[str, Any]:
        """Probes Cloudflare API to verify API Token status."""
        self.log("Verifying Cloudflare API credentials...")
        from app.deployer.cloudflare import CloudflareDeployer
        
        # Fallback if token is empty, masked, or placeholder
        if not token or token.startswith("****") or token.startswith("cfat****") or "****" in token:
            token = self.config.cloudflare.api_token

        effective_account_id = account_id or self.config.cloudflare.account_id or None
        deployer = CloudflareDeployer(self.config.cloudflare)
        res = deployer.verify_token(token=token, account_id=effective_account_id)
        is_valid = bool(res.get("valid", False))
        res["success"] = is_valid
        res["verified"] = is_valid
        if is_valid:
            discovered_subdomain = res.get("subdomain")
            if discovered_subdomain and (not self.config.cloudflare.account_subdomain or self.config.cloudflare.account_subdomain != discovered_subdomain):
                self.config.cloudflare.account_subdomain = str(discovered_subdomain).strip()
                self.save_config()
            self.log(f"[SUCCESS] Cloudflare token verified: {res.get('message')}")
        else:
            self.log(f"[WARNING] Cloudflare token check failed: {res.get('message')}")
        return res

    def start_cloudflare_deploy_job(
        self,
        dry_run: bool = False,
        subdomain: Optional[str] = None,
        verify_edge: bool = True,
        theme: Optional[str] = None,
    ) -> dict[str, Any]:
        """Launches Cloudflare deployment in a background daemon thread."""
        with self.lock:
            if self.deploy_job.status == "running":
                return {
                    "success": False,
                    "status": "running",
                    "error": "A deployment job is already in progress.",
                    "job": self.deploy_job.to_dict(),
                }

            project_token, dist_dir = self.resolve_output_dir(
                target_cloud="cloudflare",
                subdomain=subdomain,
            )
            effective_sub = project_token or self.active_project_id

            self.deploy_job = DeployJob(
                status="running",
                stage="setup",
                percent=10,
                message=f"Starting Cloudflare deployment for '{effective_sub}'...",
                target="Cloudflare Workers",
                subdomain=effective_sub,
                started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )

        def _worker():
            try:
                def progress_cb(stage: str, percent: int, msg: str):
                    with self.lock:
                        self.deploy_job.stage = stage
                        self.deploy_job.percent = percent
                        self.deploy_job.message = msg

                res = self.run_cloudflare_deploy(
                    dry_run=dry_run,
                    subdomain=subdomain,
                    verify_edge=verify_edge,
                    theme=theme,
                    progress_callback=progress_cb,
                )
                with self.lock:
                    self.deploy_job.status = "success" if res.get("success") else "error"
                    self.deploy_job.percent = 100
                    self.deploy_job.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    self.deploy_job.live_url = res.get("live_url", "")
                    self.deploy_job.duration = res.get("duration", 0.0)
                    self.deploy_job.files_count = res.get("files_count", 0)
                    self.deploy_job.edge_verification = res.get("edge_verification", {})
                    self.deploy_job.output = res.get("output", "")
                    if res.get("success"):
                        self.deploy_job.message = res.get("message") or f"Deployment succeeded! Live URL: {self.deploy_job.live_url}"
                    else:
                        self.deploy_job.error = res.get("error") or "Deployment failed."
                        self.deploy_job.message = self.deploy_job.error
            except Exception as e:
                err_msg = str(e)
                self.log(f"[ERROR] Deployment worker failed: {err_msg}")
                with self.lock:
                    self.deploy_job.status = "error"
                    self.deploy_job.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    self.deploy_job.error = err_msg
                    self.deploy_job.message = f"Deployment failed: {err_msg}"

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        return {
            "success": True,
            "status": "running",
            "job_id": f"deploy_{int(time.time())}",
            "message": "Cloudflare deployment job started in background.",
            "job": self.deploy_job.to_dict(),
        }

    def run_cloudflare_deploy(
        self,
        dry_run: bool = False,
        subdomain: Optional[str] = None,
        verify_edge: bool = True,
        theme: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
    ) -> dict[str, Any]:
        """Deploys static site to Cloudflare Workers with Static Assets."""
        def report(stage: str, percent: int, msg: str) -> None:
            if progress_callback:
                try:
                    progress_callback(stage, percent, msg)
                except Exception:
                    pass
            self.log(msg)

        effective_sub = (subdomain or self.active_project_id or "").strip()
        project_token, dist_dir = self.resolve_output_dir(
            target_cloud="cloudflare",
            subdomain=effective_sub,
            project_name=effective_sub,
        )
        effective_sub = project_token or self.active_project_id
        report("setup", 10, f"Starting Cloudflare Workers deployment (Worker Name={effective_sub}, local dir={dist_dir}, dry_run={dry_run})...")
        from app.deployer.cloudflare import CloudflareDeployer

        # If effective_sub is specified, sync project_name
        if effective_sub and self.config.cloudflare.project_name != effective_sub:
            self.config.cloudflare.project_name = effective_sub

        # Check for configured Custom Domain (Highest Priority)
        proj_item = self.projects.get(effective_sub) if hasattr(self, "projects") else None
        eff_cd = ""
        if proj_item:
            eff_cd = (getattr(proj_item, "cf_custom_domain", "") or getattr(proj_item, "custom_domain", "") or "").strip()
        if not eff_cd and hasattr(self.config, "cloudflare") and self.config.cloudflare.custom_domain:
            eff_cd = self.config.cloudflare.custom_domain.strip()

        if eff_cd:
            clean_dom = re.sub(r"^https?://", "", eff_cd, flags=re.IGNORECASE).strip("/ ")
            self.config.cloudflare.custom_domain = clean_dom
            if proj_item and getattr(proj_item, "cf_custom_domain", "") != clean_dom:
                proj_item.cf_custom_domain = clean_dom
            from app.generator.site_builder import derive_brand_from_domain
            derived = derive_brand_from_domain(clean_dom, worker_name=effective_sub)
            self.config.branding.brand_name = derived

        # Final domain retains worker name; user connects custom domain manually in Cloudflare
        cf_base_url = self.config.cloudflare.get_live_url()

        # Compile site into isolated subdomain dist directory using unified run_build pipeline
        report("compiling", 25, f"Compiling static site for subdomain '{effective_sub}' into '{dist_dir}'...")
        build_res = self.run_build(
            clean=False,
            base_url=cf_base_url,
            target_cloud="cloudflare",
            subdomain=effective_sub,
            project_name=effective_sub,
            theme=theme,
        )
        if not build_res.get("success"):
            err_list = build_res.get("errors") or ["Unknown build error"]
            raise RuntimeError(f"Static site compilation failed: {'; '.join(str(e) for e in err_list)}")
        if build_res.get("output_dir"):
            dist_dir = build_res["output_dir"]
        report("compiling", 35, f"Compiled static site for subdomain '{effective_sub}' into '{dist_dir}'.")

        deployer = CloudflareDeployer(self.config.cloudflare)
        res = deployer.deploy(
            output_dir=dist_dir,
            dry_run=dry_run,
            subdomain=effective_sub,
            verify_edge=verify_edge,
            log_callback=self.log,
            progress_callback=progress_callback,
        )
        res["target"] = "Cloudflare Workers"
        if effective_sub:
            res["subdomain"] = effective_sub
        return res

    def run_dual_deploy(self, dry_run: bool = False) -> dict[str, Any]:
        """Executes simultaneous dual-deployment to Cloudflare Workers and GitHub Pages."""
        self.log(f"Initiating Dual-Cloud Deployment (Cloudflare + GitHub Pages, dry_run={dry_run})...")
        cf_result = self.run_cloudflare_deploy(dry_run=dry_run)
        gh_result = self.run_deploy(dry_run=dry_run)
        return {
            "success": cf_result.get("success", False) and gh_result.get("success", False),
            "dry_run": dry_run,
            "target": "Multi-Cloud (Cloudflare Workers + GitHub Pages)",
            "cloudflare": cf_result,
            "github": gh_result,
            "message": "Dual deployment executed successfully to Cloudflare and GitHub Pages.",
        }


class DashboardRequestHandler(http.server.BaseHTTPRequestHandler):
    """Custom HTTP handler serving the REST API and dashboard SPA frontend."""

    # Reference to the shared DashboardManager
    manager: DashboardManager

    def _set_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def send_json(self, data: Any, status: int = 200) -> None:
        """Sends a JSON response."""
        encoded = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(encoded)

    def send_html(self, html_str: str, status: int = 200) -> None:
        """Sends an HTML response."""
        encoded = html_str.encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def read_json_body(self) -> dict[str, Any]:
        """Parses JSON request body."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
        except Exception:
            return {}

    def serve_static(self, rel_path: str) -> None:
        """Serves static frontend assets (HTML, CSS, JS)."""
        clean_path = rel_path.lstrip("/")
        if not clean_path or clean_path == "index.html":
            file_path = os.path.join(STATIC_DIR, "index.html")
        else:
            file_path = os.path.join(STATIC_DIR, clean_path)

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            # Fallback to index.html for SPA routing
            file_path = os.path.join(STATIC_DIR, "index.html")

        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"
        if file_path.endswith(".css"):
            mime_type = "text/css"
        elif file_path.endswith(".js"):
            mime_type = "application/javascript"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_json({"error": f"Failed reading static file: {e}"}, status=500)

    # -------------------------------------------------------------
    # GET Endpoints
    # -------------------------------------------------------------
    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API: System Status
        # API: List all projects
        if path == "/api/projects":
            self.send_json({
                "success": True,
                "active_project": self.manager.active_project_id,
                "projects": self.manager.list_projects(),
            })
            return

        if path == "/api/status":
            self.send_json(self.manager.get_status())
            return

        # API: Ingestion Job Status Polling
        if path == "/api/ingest/status":
            self.send_json(self.manager.ingest_job.to_dict())
            return

        # 2. API: Config
        if path == "/api/config":
            self.send_json(self.manager.get_config_dict())
            return

        # 2b. API: Cloudflare Status
        if path == "/api/cloudflare/status":
            with self.manager.lock:
                cf = self.manager.config.cloudflare
                self.send_json({
                    "has_token": bool(cf.api_token),
                    "token_masked": mask_token(cf.api_token),
                    "account_id": cf.account_id,
                    "account_subdomain": cf.account_subdomain,
                    "project_name": cf.project_name,
                    "deployment_type": cf.deployment_type,
                    "custom_domain": cf.custom_domain,
                    "worker_url": cf.get_live_url(),
                })
            return

        # 3. API: List Posts
        if path == "/api/posts":
            q = query.get("q", [""])[0]
            cat = query.get("category", [""])[0]
            stat = query.get("status", [""])[0]
            custom_only = query.get("custom_only", ["false"])[0].lower() in ("true", "1")
            posts = self.manager.list_posts(query=q, category=cat, status_filter=stat, custom_only=custom_only)
            self.send_json({"total": len(posts), "posts": posts})
            return

        # 4. API: Single Post Details
        if path.startswith("/api/posts/"):
            slug = path[len("/api/posts/") :].strip("/")
            post_data = self.manager.get_post(slug)
            if post_data:
                self.send_json(post_data)
            else:
                self.send_json({"error": f"Post '{slug}' not found"}, status=404)
            return

        # 5. API: Direct HTML Preview for Iframe
        if path.startswith("/api/preview/"):
            slug = path[len("/api/preview/") :].strip("/")
            theme = query.get("theme", [None])[0]
            routing = query.get("routing_mode", [None])[0]
            view_mode = query.get("view_mode", [None])[0]
            html_out = self.manager.render_preview(
                slug=slug, theme=theme, routing_mode=routing, view_mode=view_mode
            )
            self.send_html(html_out)
            return

        # 6. API: Deployment Status & Logs
        if path in ("/api/deploy/status", "/api/deploy/logs"):
            with self.manager.lock:
                d = self.manager.deploy_job.to_dict()
                d["job"] = self.manager.deploy_job.to_dict()
                d["logs"] = list(self.manager.logs)
                self.send_json(d)
            return

        # 7. API: List Available GitHub Organizations and User Accounts
        if path == "/api/github/orgs":
            token_param = query.get("token", [""])[0].strip()
            token = self.manager.config.github.token if (not token_param or "****" in token_param) else token_param

            # Strict Guard: If token not set, do NOT call GitHub!
            if not token or "****" in token:
                self.send_json({
                    "success": False,
                    "error": "No GitHub token configured. Please enter a Personal Access Token first.",
                    "token_required": True,
                    "accounts": [],
                })
                return

            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": "pSEO-Dashboard/2.0",
                "Authorization": f"Bearer {token}",
            }

            accounts = []
            # Authenticated user account
            try:
                user_req = urllib.request.Request("https://api.github.com/user", headers=headers)
                with urllib.request.urlopen(user_req, timeout=10) as resp:
                    u_data = json.loads(resp.read().decode())
                    accounts.append({
                        "login": u_data.get("login"),
                        "type": "User",
                        "is_org": False,
                        "avatar_url": u_data.get("avatar_url"),
                    })
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    self.send_json({
                        "success": False,
                        "error": "Invalid GitHub token (HTTP 401 Unauthorized).",
                        "token_invalid": True,
                        "accounts": [],
                    })
                    return
            except Exception:
                pass

            # User organizations
            try:
                orgs_req = urllib.request.Request("https://api.github.com/user/orgs", headers=headers)
                with urllib.request.urlopen(orgs_req, timeout=10) as resp:
                    orgs_data = json.loads(resp.read().decode())
                    for o in orgs_data:
                        accounts.append({
                            "login": o.get("login"),
                            "type": "Organization",
                            "is_org": True,
                            "avatar_url": o.get("avatar_url"),
                        })
            except Exception:
                pass

            self.send_json({"success": True, "accounts": accounts, "detected_from_token": True})
            return

        # Asset Route: Serves assets/ (including project-scoped assets/<pid>/images/ and root assets/images/) with correct MIME types
        if path.startswith("/assets/"):
            rel = path[len("/assets/"):].lstrip("/")
            img_path = os.path.abspath(os.path.join("assets", rel))
            assets_root = os.path.abspath("assets")
            if (
                os.path.exists(img_path)
                and os.path.isfile(img_path)
                and (img_path == assets_root or img_path.startswith(assets_root + os.sep))
            ):
                mime_type, _ = mimetypes.guess_type(img_path)
                mime_type = mime_type or "application/octet-stream"
                if img_path.endswith(".webp"):
                    mime_type = "image/webp"
                elif img_path.endswith(".svg"):
                    mime_type = "image/svg+xml"
                try:
                    with open(img_path, "rb") as f:
                        data = f.read()
                    self.send_response(200)
                    self._set_cors_headers()
                    self.send_header("Content-Type", mime_type)
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.end_headers()
                    self.wfile.write(data)
                except Exception as e:
                    self.send_json({"error": f"Failed reading image: {e}"}, status=500)
                return
            else:
                self.send_response(404)
                self._set_cors_headers()
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", "9")
                self.end_headers()
                self.wfile.write(b"Not Found")
                return

        # Fallback: Static Assets & Dashboard SPA
        if path.startswith("/static/"):
            self.serve_static(path[len("/static/") :])
        else:
            self.serve_static(path)

    # -------------------------------------------------------------
    # POST Endpoints
    # -------------------------------------------------------------
    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        # 1. Update Config
        # API: Create new project with empty categories
        if path == "/api/projects":
            name = (body.get("name") or body.get("project_name") or "").strip()
            if not name:
                self.send_json({"success": False, "error": "Project name is required."}, status=400)
                return
            try:
                res = self.manager.create_project(
                    name=name,
                    platform=body.get("platform", "cloudflare"),
                    cf_project_name=body.get("cf_project_name", ""),
                    cf_custom_domain=body.get("cf_custom_domain", ""),
                    gh_owner=body.get("gh_owner", ""),
                    gh_repo=body.get("gh_repo", ""),
                    gh_branch=body.get("gh_branch", "main"),
                    gh_is_org=bool(body.get("gh_is_org", True)),
                    sitemap_url=body.get("sitemap_url", ""),
                    theme=body.get("theme"),
                    routing_mode=body.get("routing_mode"),
                )
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        # API: Update project configuration
        if path == "/api/projects/update":
            pid = (body.get("project_id") or body.get("id") or self.manager.active_project_id).strip()
            try:
                raw_updates = body.get("updates", {})
                merged = dict(body)
                if isinstance(raw_updates, dict):
                    merged.update(raw_updates)
                res = self.manager.update_project(pid, merged)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=400)
            return

        # API: Switch active project
        if path == "/api/projects/switch":
            pid = (body.get("project_id") or body.get("id") or "").strip()
            if not pid:
                self.send_json({"success": False, "error": "Project ID is required."}, status=400)
                return
            try:
                res = self.manager.switch_project(pid)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        # API: Delete project
        if path == "/api/projects/delete":
            pid = (body.get("project_id") or body.get("id") or "").strip()
            if not pid:
                self.send_json({"success": False, "error": "Project ID is required."}, status=400)
                return
            try:
                res = self.manager.delete_project(pid)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=400)
            return

        # API: Reset all projects (empty slate)
        if path == "/api/projects/reset":
            try:
                res = self.manager.reset_all_projects()
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        if path == "/api/config":
            updated = self.manager.update_config_from_dict(body)
            self.send_json({"success": True, "config": updated})
            return

        # 1b. Upload Custom Logo
        if path == "/api/upload-logo":
            reset = bool(body.get("reset", False))
            if reset:
                assets_dir = os.path.abspath(os.path.join("assets", "images"))
                for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
                    p = os.path.join(assets_dir, f"custom-logo{ext}")
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass

                # Also clean project-specific assets if active project exists
                active_pid = getattr(self.manager, "active_project_id", "")
                if active_pid:
                    for sub_dir in (
                        os.path.abspath(os.path.join("assets", active_pid, "images")),
                        os.path.abspath(os.path.join("scraped_data", active_pid, "assets", "images")),
                    ):
                        if os.path.exists(sub_dir):
                            for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
                                p = os.path.join(sub_dir, f"custom-logo{ext}")
                                if os.path.exists(p):
                                    try:
                                        os.remove(p)
                                    except Exception:
                                        pass

                self.manager.config.branding.logo_path = ""
                self.manager.save_config()
                self.manager.log("Reset custom logo to default vector emblem.")
                self.send_json({"success": True, "reset": True, "logo_url": ""})
                return

            data_url = body.get("data", "")
            brand_name = body.get("brand_name")
            tagline = body.get("tagline")
            if brand_name:
                self.manager.config.branding.brand_name = str(brand_name).strip()
            if tagline:
                self.manager.config.branding.tagline = str(tagline).strip()

            if not data_url or not data_url.startswith("data:"):
                self.send_json({"success": False, "error": "Invalid image payload"}, status=400)
                return

            try:
                import base64
                header, base64_str = data_url.split(",", 1)
                mime = header.split(";")[0].replace("data:", "").lower().strip()
                ext_map = {
                    "image/png": ".png",
                    "image/jpeg": ".jpg",
                    "image/jpg": ".jpg",
                    "image/webp": ".webp",
                    "image/svg+xml": ".svg",
                }
                ext = ext_map.get(mime)
                if not ext:
                    if "png" in mime:
                        ext = ".png"
                    elif "jpeg" in mime or "jpg" in mime:
                        ext = ".jpg"
                    elif "webp" in mime:
                        ext = ".webp"
                    elif "svg" in mime:
                        ext = ".svg"
                    else:
                        ext = ".png"

                image_bytes = base64.b64decode(base64_str)
                if len(image_bytes) > 10 * 1024 * 1024:
                    self.send_json({"success": False, "error": "Image file exceeds 10MB limit"}, status=400)
                    return

                assets_dir = os.path.abspath(os.path.join("assets", "images"))
                os.makedirs(assets_dir, exist_ok=True)

                for prev_ext in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
                    p = os.path.join(assets_dir, f"custom-logo{prev_ext}")
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass

                logo_filename = f"custom-logo{ext}"
                target_path = os.path.join(assets_dir, logo_filename)
                with open(target_path, "wb") as f:
                    f.write(image_bytes)

                # Synchronize to active project directories if active
                active_pid = getattr(self.manager, "active_project_id", "")
                if active_pid:
                    for sub_dir in (
                        os.path.abspath(os.path.join("assets", active_pid, "images")),
                        os.path.abspath(os.path.join("scraped_data", active_pid, "assets", "images")),
                    ):
                        try:
                            os.makedirs(sub_dir, exist_ok=True)
                            for prev_ext in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
                                p = os.path.join(sub_dir, f"custom-logo{prev_ext}")
                                if os.path.exists(p):
                                    os.remove(p)
                            import shutil
                            shutil.copy2(target_path, os.path.join(sub_dir, logo_filename))
                        except Exception:
                            pass

                logo_rel_path = f"/assets/images/{logo_filename}"
                self.manager.config.branding.logo_path = logo_rel_path
                self.manager.save_config()
                self.manager.log(f"Custom logo uploaded successfully: {logo_rel_path} ({len(image_bytes)} bytes)")
                self.send_json({
                    "success": True,
                    "logo_url": logo_rel_path,
                    "brand_name": self.manager.config.branding.brand_name,
                    "tagline": self.manager.config.branding.tagline,
                })
                return
            except Exception as exc:
                self.manager.log(f"Error saving custom logo: {exc}")
                self.send_json({"success": False, "error": str(exc)}, status=500)
                return

        # 2. Sitemap Scan (read-only scan)
        if path == "/api/sitemap/scan":
            src = body.get("url_or_list") or self.manager.config.ingestion.sitemap_url
            self.manager.log(f"Scanning sitemap index: {src}")
            urls = []
            try:
                from app.ingestion.sitemap_parser import parse_sitemap
                urls = sorted(list(parse_sitemap(src)))
            except Exception:
                urls = [f"https://stylesdays.com/{p.slug}/" for p in self.manager.manifest.posts.values()]
            self.send_json({"success": True, "discovered_count": len(urls), "urls": urls})
            return

        # 3. Trigger Ingestion (Asynchronous Background Job)
        if path == "/api/ingest":
            source_type = body.get("source_type", "sitemap")
            url_or_list = body.get("url_or_list", "")
            max_posts = body.get("max_posts")
            download_images = body.get("download_images")
            force = bool(body.get("force_full_resync", False))
            cf_custom_domain = body.get("cf_custom_domain") or body.get("custom_domain")
            cf_project_name = body.get("cf_project_name") or body.get("worker_name")

            res = self.manager.start_ingest_job(
                source_type=source_type,
                url_or_list=url_or_list,
                max_posts=max_posts,
                download_images=download_images,
                force_full_resync=force,
                cf_custom_domain=cf_custom_domain,
                cf_project_name=cf_project_name,
            )
            self.send_json(res)
            return

        # 4. In-Memory Live Preview
        if path == "/api/preview":
            post_data = body.get("post")
            slug = body.get("slug")
            theme = body.get("theme")
            routing_mode = body.get("route_structure") or body.get("routing_mode")
            view_mode = body.get("view_mode") or body.get("type")
            html_out = self.manager.render_preview(
                slug=slug,
                post_data=post_data,
                theme=theme,
                routing_mode=routing_mode,
                view_mode=view_mode,
            )
            self.send_json({"success": True, "html": html_out})
            return

        # 5. Static Build Trigger
        if path == "/api/build":
            clean = bool(body.get("clean", True))
            target_cloud = body.get("target_cloud") or body.get("platform")
            project_name = body.get("project_name") or body.get("subdomain") or body.get("worker_name")
            theme = body.get("theme")
            routing_mode = body.get("routing_mode")
            result = self.manager.run_build(
                clean=clean,
                target_cloud=target_cloud,
                project_name=project_name,
                subdomain=project_name,
                theme=theme,
                routing_mode=routing_mode,
            )
            self.send_json(result)
            return

        # 5b. Asset Synchronization Trigger
        if path == "/api/assets/sync":
            force = bool(body.get("force", False))
            cf_custom_domain = body.get("cf_custom_domain") or body.get("custom_domain")
            cf_project_name = body.get("cf_project_name") or body.get("worker_name")
            if cf_custom_domain is not None or cf_project_name is not None:
                p_updates = {}
                if cf_custom_domain is not None:
                    p_updates["cf_custom_domain"] = cf_custom_domain
                if cf_project_name is not None:
                    p_updates["cf_project_name"] = cf_project_name
                try:
                    self.manager.update_project(self.manager.active_project_id, p_updates)
                except Exception:
                    pass
            result = self.manager.sync_all_post_images(force=force)
            self.send_json(result)
            return

        # 5c. WebP Image Optimization Trigger
        if path in ("/api/images/optimize", "/api/assets/optimize-webp"):
            quality = int(body.get("quality", 82))
            result = self.manager.optimize_all_images(quality=quality)
            self.send_json(result)
            return

        # 6. Deployment Trigger (GitHub Pages)
        if path == "/api/deploy":
            dry_run = bool(body.get("dry_run", False))
            project_name = body.get("project_name") or body.get("subdomain") or body.get("owner")
            result = self.manager.run_deploy(dry_run=dry_run, project_name=project_name)
            self.send_json(result)
            return

        # 6b. Cloudflare Deployment Trigger
        if path == "/api/cloudflare/deploy":
            dry_run = bool(body.get("dry_run", False))
            subdomain = body.get("subdomain") or body.get("project_name") or body.get("worker_name")
            verify_edge = bool(body.get("verify_edge", True))
            theme = body.get("theme")
            result = self.manager.start_cloudflare_deploy_job(
                dry_run=dry_run,
                subdomain=subdomain,
                verify_edge=verify_edge,
                theme=theme,
            )
            self.send_json(result)
            return

        # 6b-2. Cloudflare Live Edge Verification Probe
        if path == "/api/cloudflare/verify-edge":
            url = body.get("url") if isinstance(body, dict) else None
            from app.deployer.cloudflare import CloudflareDeployer
            deployer = CloudflareDeployer(self.manager.config.cloudflare)
            result = deployer.verify_live_edge(url=url, log_callback=self.manager.log)
            self.send_json(result)
            return

        # 6c. Dual Deployment Trigger (Both Cloudflare & GitHub)
        if path == "/api/deploy/dual":
            dry_run = bool(body.get("dry_run", False))
            result = self.manager.run_dual_deploy(dry_run=dry_run)
            self.send_json(result)
            return

        # 6d. Cloudflare Token Verification
        if path == "/api/cloudflare/verify":
            token = body.get("token") or body.get("api_token")
            account_id = body.get("account_id")
            result = self.manager.verify_cloudflare_credentials(token=token, account_id=account_id)
            self.send_json(result)
            return

        # 7. Check or Attempt to Create Organization
        if path == "/api/github/check-org":
            org_name = (body.get("org") or self.manager.config.github.owner or "").strip()
            raw_token = (body.get("token") or "").strip()
            token = self.manager.config.github.token if (not raw_token or "****" in raw_token) else raw_token

            if not org_name:
                self.send_json({"success": False, "error": "Organization name is required"}, status=400)
                return

            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": "pSEO-Dashboard/2.0",
            }
            if token:
                headers["Authorization"] = f"Bearer {token}"

            # Step 1: Check if org or user exists on GitHub
            req = urllib.request.Request(f"https://api.github.com/orgs/{org_name}", headers=headers)
            org_data = None
            exists = False
            account_type = "Organization"
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    org_data = json.loads(resp.read().decode())
                    exists = True
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    # Fallback: check if it is a personal user account
                    user_req = urllib.request.Request(f"https://api.github.com/users/{org_name}", headers=headers)
                    try:
                        with urllib.request.urlopen(user_req, timeout=10) as uresp:
                            org_data = json.loads(uresp.read().decode())
                            exists = True
                            account_type = "User"
                    except urllib.error.HTTPError:
                        pass
            except Exception as e:
                self.send_json({"success": False, "error": f"Network error checking GitHub account: {e}"}, status=500)
                return

            if exists and org_data:
                self.send_json({
                    "success": True,
                    "exists": True,
                    "org": org_name,
                    "account_type": account_type,
                    "is_org": (account_type == "Organization"),
                    "url": org_data.get("html_url", f"https://github.com/{org_name}"),
                    "message": f"{account_type} '{org_name}' is verified and active on GitHub!",
                    "details": {
                        "name": org_data.get("name"),
                        "plan": org_data.get("plan", {}).get("name", "free"),
                        "repos_url": org_data.get("repos_url"),
                    }
                })
                return

            # Step 2: Org does not exist. Test if API allows creating it
            api_attempt_result = {}
            if token:
                post_req = urllib.request.Request(
                    "https://api.github.com/user/orgs",
                    data=json.dumps({"login": org_name}).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "pSEO-Dashboard/2.0",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(post_req, timeout=10) as resp:
                        created_data = json.loads(resp.read().decode())
                        self.send_json({
                            "success": True,
                            "exists": True,
                            "created": True,
                            "org": org_name,
                            "message": f"Organization '{org_name}' successfully created via API!",
                            "details": created_data,
                        })
                        return
                except urllib.error.HTTPError as err:
                    api_attempt_result = {
                        "endpoint": "POST https://api.github.com/user/orgs",
                        "http_code": err.code,
                        "reason": err.reason,
                    }

            create_web_url = "https://github.com/account/organizations/new?plan=free"
            self.send_json({
                "success": False,
                "exists": False,
                "org": org_name,
                "create_web_url": create_web_url,
                "message": f"Organization '{org_name}' does not exist yet on GitHub.",
                "api_limitation": "GitHub API returned HTTP 404. Free organizations must be created once via GitHub web interface due to CAPTCHA/Terms of Service.",
                "api_details": api_attempt_result,
            })
            return

        # 8. API: Directly Create Repository & Enable Pages
        if path == "/api/github/create-repo":
            owner = (body.get("owner") or self.manager.config.github.owner or "").strip()
            repo = (body.get("repo") or self.manager.config.github.repo or "").strip()
            is_org = bool(body.get("is_org", self.manager.config.github.is_org))
            raw_token = (body.get("token") or "").strip()
            token = self.manager.config.github.token if (not raw_token or "****" in raw_token) else raw_token

            if not owner or not repo:
                self.send_json({"success": False, "error": "Both owner and repo are required."}, status=400)
                return

            from app.deployer.github import GitHubDeployer
            from app.config import GitHubConfig

            cfg = GitHubConfig(token=token, owner=owner, repo=repo, is_org=is_org)
            deployer = GitHubDeployer(config=cfg, logger=self.manager.log)

            try:
                repo_res = deployer.ensure_repository()
                pages_res = {}
                try:
                    pages_res = deployer.ensure_pages_enabled()
                except Exception as pe:
                    pages_res = {"warning": f"Pages will activate upon initial commit: {pe}"}

                self.send_json({
                    "success": True,
                    "repo": f"{owner}/{repo}",
                    "repo_url": f"https://github.com/{owner}/{repo}",
                    "pages_url": deployer.pages_url,
                    "created": repo_res.get("created", False),
                    "exists": repo_res.get("exists", True),
                    "pages": pages_res,
                    "message": f"Repository '{owner}/{repo}' is ready and configured for GitHub Pages!",
                })
            except Exception as e:
                self.send_json({"success": False, "error": f"Failed creating repository: {e}"}, status=500)
            return

        # 9. API: Detect Organizations from Token (POST)
        if path == "/api/github/orgs":
            raw_token = (body.get("token") or "").strip()
            token = self.manager.config.github.token if (not raw_token or "****" in raw_token) else raw_token
            if not token or "****" in token:
                self.send_json({
                    "success": False,
                    "error": "No GitHub Personal Access Token configured.",
                    "token_required": True,
                    "accounts": [],
                })
                return

            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": "pSEO-Dashboard/2.0",
                "Authorization": f"Bearer {token}",
            }

            accounts = []
            try:
                user_req = urllib.request.Request("https://api.github.com/user", headers=headers)
                with urllib.request.urlopen(user_req, timeout=10) as resp:
                    u_data = json.loads(resp.read().decode())
                    accounts.append({
                        "login": u_data.get("login"),
                        "type": "User",
                        "is_org": False,
                        "avatar_url": u_data.get("avatar_url"),
                    })
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    self.send_json({
                        "success": False,
                        "error": "Invalid GitHub token (HTTP 401 Unauthorized).",
                        "token_invalid": True,
                        "accounts": [],
                    })
                    return
            except Exception:
                pass

            try:
                orgs_req = urllib.request.Request("https://api.github.com/user/orgs", headers=headers)
                with urllib.request.urlopen(orgs_req, timeout=10) as resp:
                    orgs_data = json.loads(resp.read().decode())
                    for o in orgs_data:
                        accounts.append({
                            "login": o.get("login"),
                            "type": "Organization",
                            "is_org": True,
                            "avatar_url": o.get("avatar_url"),
                        })
            except Exception:
                pass

            self.send_json({"success": True, "accounts": accounts, "detected_from_token": True})
            return

        self.send_json({"error": f"Unknown POST endpoint: {path}"}, status=404)

    # -------------------------------------------------------------
    # PUT Endpoints
    # -------------------------------------------------------------
    def do_PUT(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        # Update Single Post & Mark custom_edited
        if path.startswith("/api/posts/"):
            slug = path[len("/api/posts/") :].strip("/")
            updated = self.manager.update_post(slug, body)
            if updated:
                self.send_json({"success": True, "post": updated})
            else:
                self.send_json({"error": f"Post '{slug}' not found"}, status=404)
            return

        self.send_json({"error": f"Unknown PUT endpoint: {path}"}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stdout clutter, keep logging tidy."""
        pass


class ThreadedDashboardServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Multi-threaded HTTP Server for responsive local dashboard interaction."""

    daemon_threads = True
    allow_reuse_address = True


def create_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    config_path: str = "pseo_config.json",
    manifest_path: str = "pseo_manifest.json",
) -> ThreadedDashboardServer:
    """Factory creating an initialized ThreadedDashboardServer instance."""
    manager = DashboardManager(config_path=config_path, manifest_path=manifest_path)
    handler_class = type(
        "ConfiguredDashboardHandler",
        (DashboardRequestHandler,),
        {"manager": manager},
    )
    server = ThreadedDashboardServer((host, port), handler_class)
    return server


def run_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    config_path: str = "pseo_config.json",
    manifest_path: str = "pseo_manifest.json",
) -> None:
    """Runs the dashboard web server until interrupted."""
    server = create_server(host=host, port=port, config_path=config_path, manifest_path=manifest_path)
    print(f"[pSEO Dashboard] Server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[pSEO Dashboard] Stopping server...")
    finally:
        server.server_close()
