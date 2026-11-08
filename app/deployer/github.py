"""
GitHub Pages & Git Data API Deployment Engine.
Handles repository creation, empty repository bootstrapping, Base64 image and UTF-8 text blobs,
Git tree construction, commit chaining, and atomic branch ref updates for pSEO static sites.
"""

from __future__ import annotations

import base64
import datetime
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Optional, Union

from app.config import GitHubConfig
from app.models import DeployJob


TEXT_EXTENSIONS = {
    ".html",
    ".htm",
    ".xml",
    ".txt",
    ".css",
    ".js",
    ".json",
    ".svg",
    ".map",
    ".webmanifest",
}


class GitHubDeployError(Exception):
    """Base exception for all GitHub deployment errors."""
    pass


class GitHubAPIError(GitHubDeployError):
    """Raised when GitHub API returns an HTTP error status code."""

    def __init__(
        self,
        status_code: int,
        reason: str,
        body: str = "",
        url: str = "",
        method: str = "GET",
    ):
        self.status_code = status_code
        self.reason = reason
        self.body = body
        self.url = url
        self.method = method
        msg = f"GitHub API {method} {url} returned HTTP {status_code}: {reason}"
        if body:
            msg += f" - Response: {body[:300]}"
        super().__init__(msg)


class GitHubNetworkError(GitHubDeployError):
    """Raised when a socket or network-level error occurs during communication."""
    pass


class GitHubDeployer:
    """
    Automates deployment of static site assets directly to GitHub Pages via Git Data APIs.
    Supports organization root domains (e.g. home-organization.github.io) and subpath repos.
    """

    def __init__(
        self,
        config: Optional[Union[GitHubConfig, dict[str, Any]]] = None,
        api_base_url: Optional[str] = None,
        logger: Optional[Callable[[str], None]] = None,
    ):
        if isinstance(config, dict):
            self.config = GitHubConfig.from_dict(config)
        elif config is not None:
            self.config = config
        else:
            self.config = GitHubConfig()

        if api_base_url:
            self.api_base_url = api_base_url.rstrip("/")
        elif os.environ.get("GITHUB_API_BASE"):
            self.api_base_url = os.environ["GITHUB_API_BASE"].rstrip("/")
        elif os.environ.get("GITHUB_API_URL"):
            self.api_base_url = os.environ["GITHUB_API_URL"].rstrip("/")
        else:
            self.api_base_url = "https://api.github.com"

        self.logger = logger
        self.logs: list[str] = []

    def log(self, message: str) -> None:
        """Appends to internal log buffer and notifies external logger if configured."""
        self.logs.append(message)
        if self.logger:
            try:
                self.logger(message)
            except Exception:
                pass

    @property
    def pages_url(self) -> str:
        """Calculates the canonical GitHub Pages URL for the repository."""
        repo = self.config.repo
        owner = self.config.owner
        if repo.endswith(".github.io"):
            return f"https://{repo}"
        if owner and repo:
            return f"https://{owner}.github.io/{repo}"
        return f"https://{owner or 'unknown'}.github.io"

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[dict[str, Any]] = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Performs an authenticated JSON HTTP request to the GitHub API."""
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = endpoint
        else:
            url = f"{self.api_base_url}/{endpoint.lstrip('/')}"

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "pSEO-GitHub-Deployer/2.0",
            "Connection": "close",
        }
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read()
                    if not raw:
                        return {}
                    try:
                        return json.loads(raw.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        return {"raw_body": raw.decode("utf-8", errors="replace")}
            except urllib.error.HTTPError as exc:
                err_body = ""
                try:
                    err_body = exc.read().decode("utf-8")
                except Exception:
                    pass
                raise GitHubAPIError(exc.code, exc.reason, err_body, url=url, method=method) from exc
            except urllib.error.URLError as exc:
                if attempt < max_retries:
                    self.log(f"[GITHUB] Transient network error connecting to {url} (attempt {attempt}/{max_retries}): {exc.reason}. Retrying in 0.5s...")
                    time.sleep(0.5)
                    continue
                raise GitHubNetworkError(f"Network error connecting to {url}: {exc.reason}") from exc
        return {}

    def check_repository(self) -> bool:
        """
        Checks whether the repository exists via GET /repos/{owner}/{repo}.
        Returns True if exists, False if 404, or raises GitHubAPIError for unexpected errors.
        """
        owner = self.config.owner
        repo = self.config.repo
        if not owner or not repo:
            raise ValueError("Both owner and repo must be configured to check repository.")

        try:
            self._request("GET", f"/repos/{owner}/{repo}")
            return True
        except GitHubAPIError as err:
            if err.status_code == 404:
                return False
            raise

    def ensure_repository(self) -> dict[str, Any]:
        """
        Ensures the repository exists. If not found:
        - If is_org: creates via POST /orgs/{org}/repos with auto_init and has_pages.
        - Else: creates via POST /user/repos with auto_init and has_pages.
        """
        owner = self.config.owner
        repo = self.config.repo
        if not owner or not repo:
            raise ValueError("Both owner and repo must be configured in GitHubConfig.")

        self.log(f"Checking repository existence for {owner}/{repo}...")
        if self.check_repository():
            self.log(f"Repository {owner}/{repo} exists.")
            return {"exists": True, "created": False}

        create_payload = {
            "name": repo,
            "description": f"Curated Editorial pSEO Hub ({repo})",
            "homepage": self.pages_url,
            "private": False,
            "auto_init": True,
            "has_pages": True,
        }

        if self.config.is_org:
            endpoint = f"/orgs/{owner}/repos"
            self.log(f"Creating Organization repository {owner}/{repo} via {endpoint}...")
        else:
            endpoint = "/user/repos"
            self.log(f"Creating User repository {owner}/{repo} via {endpoint}...")

        try:
            res = self._request("POST", endpoint, create_payload)
            self.log(f"Repository {owner}/{repo} created successfully.")
            return {"exists": True, "created": True, "data": res}
        except GitHubAPIError as err:
            # Handle potential 422 if created concurrently
            if err.status_code == 422 and "already exists" in err.body.lower():
                self.log(f"Repository {owner}/{repo} already exists (422 response).")
                return {"exists": True, "created": False}
            raise

    def ensure_pages_enabled(self, branch: Optional[str] = None) -> dict[str, Any]:
        """Ensures GitHub Pages is configured to serve from the specified branch root."""
        owner = self.config.owner
        repo = self.config.repo
        target_branch = branch or self.config.branch or "main"
        endpoint = f"/repos/{owner}/{repo}/pages"
        try:
            pages_info = self._request("GET", endpoint)
            return {"enabled": True, "info": pages_info}
        except GitHubAPIError as err:
            if err.status_code == 404:
                self.log(f"GitHub Pages not enabled on {owner}/{repo}; enabling from branch '{target_branch}'...")
                try:
                    payload = {"source": {"branch": target_branch, "path": "/"}}
                    pages_info = self._request("POST", endpoint, payload)
                    self.log(f"GitHub Pages successfully enabled on {owner}/{repo}.")
                    return {"enabled": True, "created": True, "info": pages_info}
                except Exception as exc:
                    self.log(f"Could not automatically enable GitHub Pages on {owner}/{repo}: {exc}")
                    return {"enabled": False, "error": str(exc)}
            return {"enabled": False, "error": str(err)}
        except Exception as exc:
            self.log(f"Could not verify GitHub Pages on {owner}/{repo}: {exc}")
            return {"enabled": False, "error": str(exc)}

    def bootstrap_empty_repo(self, branch: Optional[str] = None) -> tuple[str, str]:
        """
        Bootstraps an uninitialized or empty repository by creating an initial README.md blob,
        root tree, initial commit (with no parents), and setting the branch ref.
        Returns (commit_sha, tree_sha).
        """
        branch_name = branch or self.config.branch or "main"
        owner = self.config.owner
        repo = self.config.repo

        self.log(f"Bootstrapping empty repo {owner}/{repo} on branch {branch_name}...")
        readme_text = f"# {repo}\n\nAutomated static site deployment generated by pSEO Static Site Generator.\n"

        # 1. Create README blob
        blob_resp = self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/blobs",
            {"content": readme_text, "encoding": "utf-8"},
        )
        blob_sha = blob_resp["sha"]

        # 2. Create initial Tree
        tree_resp = self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/trees",
            {
                "tree": [
                    {
                        "path": "README.md",
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob_sha,
                    }
                ]
            },
        )
        tree_sha = tree_resp["sha"]

        # 3. Create initial Commit (parents: [])
        commit_resp = self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/commits",
            {
                "message": "Initial commit",
                "tree": tree_sha,
                "parents": [],
            },
        )
        commit_sha = commit_resp["sha"]

        # 4. Create or update branch ref
        try:
            self._request(
                "POST",
                f"/repos/{owner}/{repo}/git/refs",
                {
                    "ref": f"refs/heads/{branch_name}",
                    "sha": commit_sha,
                },
            )
        except GitHubAPIError as ref_err:
            if ref_err.status_code == 422:
                # Ref might have been created simultaneously; update it
                self._request(
                    "PATCH",
                    f"/repos/{owner}/{repo}/git/refs/heads/{branch_name}",
                    {"sha": commit_sha, "force": False},
                )
            else:
                raise

        self.log(f"Bootstrapped {owner}/{repo} branch {branch_name} with initial commit {commit_sha[:8]}")
        return commit_sha, tree_sha

    def ensure_branch_ref(self, branch: Optional[str] = None) -> tuple[str, str]:
        """
        Retrieves the latest commit SHA and base tree SHA for the given branch.
        If the ref returns 404 (or 409 empty repo), bootstraps the repo with an initial commit.
        Returns (parent_commit_sha, base_tree_sha).
        """
        branch_name = branch or self.config.branch or "main"
        owner = self.config.owner
        repo = self.config.repo
        endpoint = f"/repos/{owner}/{repo}/git/ref/heads/{branch_name}"

        try:
            ref_data = self._request("GET", endpoint)
            commit_sha = ref_data.get("object", {}).get("sha", "")
            commit_data = self._request("GET", f"/repos/{owner}/{repo}/git/commits/{commit_sha}")
            base_tree_sha = commit_data.get("tree", {}).get("sha", "")
            return commit_sha, base_tree_sha
        except GitHubAPIError as err:
            if err.status_code in (404, 409):
                self.log(f"Branch ref heads/{branch_name} not found ({err.status_code}). Bootstrapping empty repository...")
                return self.bootstrap_empty_repo(branch=branch_name)
            raise

    def create_blob(self, content: Union[str, bytes], is_binary: bool = False) -> str:
        """
        Creates a Git blob on GitHub.
        - Text content is submitted with utf-8 encoding.
        - Binary content is Base64 encoded and submitted with base64 encoding.
        Returns the SHA-1 of the created blob.
        """
        owner = self.config.owner
        repo = self.config.repo

        if is_binary:
            raw_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
            b64_str = base64.b64encode(raw_bytes).decode("ascii")
            payload = {"content": b64_str, "encoding": "base64"}
        else:
            text_str = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
            payload = {"content": text_str, "encoding": "utf-8"}

        resp = self._request("POST", f"/repos/{owner}/{repo}/git/blobs", payload)
        return resp["sha"]

    def create_tree(self, tree_items: list[dict[str, Any]], base_tree: Optional[str] = None) -> str:
        """
        Creates a Git tree from the assembled tree items and optional base_tree SHA.
        Returns the new tree SHA.
        """
        owner = self.config.owner
        repo = self.config.repo
        payload: dict[str, Any] = {"tree": tree_items}
        if base_tree:
            payload["base_tree"] = base_tree

        resp = self._request("POST", f"/repos/{owner}/{repo}/git/trees", payload)
        return resp["sha"]

    def create_commit(self, tree_sha: str, parents: list[str], message: str) -> str:
        """
        Creates a Git commit pointing to tree_sha with specified parent commit SHAs.
        Returns the new commit SHA.
        """
        owner = self.config.owner
        repo = self.config.repo
        payload = {
            "message": message,
            "tree": tree_sha,
            "parents": parents,
        }
        resp = self._request("POST", f"/repos/{owner}/{repo}/git/commits", payload)
        return resp["sha"]

    def update_ref(self, commit_sha: str, branch: Optional[str] = None, force: bool = False) -> dict[str, Any]:
        """
        Updates the branch reference to point to the new commit SHA via PATCH.
        Falls back to POST /git/refs if branch ref does not exist.
        """
        owner = self.config.owner
        repo = self.config.repo
        branch_name = branch or self.config.branch or "main"
        endpoint = f"/repos/{owner}/{repo}/git/refs/heads/{branch_name}"

        try:
            return self._request("PATCH", endpoint, {"sha": commit_sha, "force": force})
        except GitHubAPIError as err:
            if err.status_code == 404:
                self.log(f"Branch ref heads/{branch_name} not found during PATCH. Creating via POST /git/refs...")
                return self._request(
                    "POST",
                    f"/repos/{owner}/{repo}/git/refs",
                    {"ref": f"refs/heads/{branch_name}", "sha": commit_sha},
                )
            raise

    def deploy(
        self,
        output_dir: str,
        commit_message: Optional[str] = None,
        progress_callback: Optional[Callable[..., None]] = None,
        raise_on_error: bool = False,
        clean_tree: bool = False,
    ) -> DeployJob:
        """
        Executes the full Git Data API deployment pipeline:
        1. Ensures repository exists (creates Org or User repo if missing).
        2. Inspects branch ref or bootstraps empty repo.
        3. Scans output_dir for built static files.
        4. Uploads text files as UTF-8 blobs and binary files as Base64 blobs.
        5. Assembles Git tree with mode '100644'.
        6. Creates new commit referencing base tree and parent commit.
        7. Atomically updates branch ref.
        Returns DeployJob model with status, timestamps, commit SHA, and any errors.
        """
        start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        job = DeployJob(
            status="in_progress",
            started_at=start_time,
            total_files=0,
            deployed_files=0,
            commit_sha="",
            errors=[],
        )

        owner = self.config.owner
        repo = self.config.repo
        branch = self.config.branch or "main"

        try:
            if not owner or not repo:
                raise ValueError("Both owner and repo must be configured in GitHubConfig to deploy.")

            if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
                raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

            # 1. Discover all files to deploy
            files_to_deploy: list[str] = []
            for root_dir, _, filenames in os.walk(output_dir):
                for fname in filenames:
                    files_to_deploy.append(os.path.join(root_dir, fname))

            files_to_deploy.sort()
            total_files = len(files_to_deploy)
            job.total_files = total_files

            if total_files == 0:
                raise ValueError(f"No files found in output directory to deploy: {output_dir}")

            self.log(f"Starting GitHub Pages deployment for {owner}/{repo} (branch: {branch}, files: {total_files})")

            # 2. Ensure repository exists
            self.ensure_repository()

            # 3. Retrieve parent commit and base tree (bootstraps if empty)
            parent_commit_sha, base_tree_sha = self.ensure_branch_ref(branch)
            self.log(f"Parent commit SHA: {parent_commit_sha[:8] if parent_commit_sha else 'none'}, base tree: {base_tree_sha[:8] if base_tree_sha else 'none'}")

            # 4. Upload Blobs
            tree_items: list[dict[str, Any]] = []
            deployed_files = 0

            for full_path in files_to_deploy:
                rel_path = os.path.relpath(full_path, output_dir).replace("\\", "/").lstrip("/")
                _, ext = os.path.splitext(full_path)
                ext_lower = ext.lower()

                if ext_lower in TEXT_EXTENSIONS:
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            text_content = f.read()
                        payload = {"content": text_content, "encoding": "utf-8"}
                    except UnicodeDecodeError:
                        with open(full_path, "rb") as f:
                            raw_bytes = f.read()
                        payload = {
                            "content": base64.b64encode(raw_bytes).decode("ascii"),
                            "encoding": "base64",
                        }
                else:
                    with open(full_path, "rb") as f:
                        raw_bytes = f.read()
                    payload = {
                        "content": base64.b64encode(raw_bytes).decode("ascii"),
                        "encoding": "base64",
                    }

                blob_resp = self._request("POST", f"/repos/{owner}/{repo}/git/blobs", payload)
                blob_sha = blob_resp["sha"]

                tree_items.append({
                    "path": rel_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha,
                })

                deployed_files += 1
                job.deployed_files = deployed_files

                if progress_callback:
                    try:
                        progress_callback(deployed_files, total_files, rel_path)
                    except TypeError:
                        progress_callback(deployed_files, total_files)

                self.log(f"[GITHUB] Uploaded blob [{deployed_files}/{total_files}]: {rel_path} ({blob_sha[:8]})")

            # 5. Create Tree
            self.log(f"Assembling Git tree with {len(tree_items)} items (clean_tree={clean_tree})...")
            effective_base_tree = None if clean_tree else base_tree_sha
            new_tree_sha = self.create_tree(tree_items, base_tree=effective_base_tree)
            self.log(f"Git tree created: {new_tree_sha}")

            # 6. Create Commit
            default_msg = f"Deploy {len(tree_items)} pSEO pages, native images, robots.txt & sitemap.xml"
            msg = commit_message or default_msg
            parents = [parent_commit_sha] if parent_commit_sha else []
            new_commit_sha = self.create_commit(tree_sha=new_tree_sha, parents=parents, message=msg)
            self.log(f"Git commit created: {new_commit_sha}")

            # 7. Update Ref
            self.update_ref(commit_sha=new_commit_sha, branch=branch, force=False)
            self.log(f"[GITHUB] Successfully deployed commit {new_commit_sha} to {self.pages_url}")

            # 8. Ensure GitHub Pages is enabled (non-fatal if remote API is delayed or Pages unavailable)
            try:
                self.ensure_pages_enabled(branch=branch)
            except Exception as pages_exc:
                self.log(f"[GITHUB] Non-fatal Pages verification error: {pages_exc}")

            job.status = "success"
            job.commit_sha = new_commit_sha
            job.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return job

        except Exception as exc:
            job.status = "failed"
            job.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            job.errors.append(str(exc))
            self.log(f"[GITHUB] Deployment failed: {exc}")
            if raise_on_error:
                raise
            return job


def deploy_to_github_pages(
    output_dir: str,
    owner: str,
    repo: str,
    token: str = "",
    is_org: bool = True,
    branch: str = "main",
    base_path: str = "",
    commit_message: Optional[str] = None,
    api_base_url: Optional[str] = None,
    progress_callback: Optional[Callable[..., None]] = None,
    logger: Optional[Callable[[str], None]] = None,
    raise_on_error: bool = False,
) -> DeployJob:
    """
    Convenience functional interface for deploying static sites to GitHub Pages.
    Compatible with the reference pseo_github_deployer.py interface.
    """
    config = GitHubConfig(
        token=token,
        owner=owner,
        repo=repo,
        branch=branch,
        is_org=is_org,
        base_path=base_path,
    )
    deployer = GitHubDeployer(config=config, api_base_url=api_base_url, logger=logger)
    return deployer.deploy(
        output_dir=output_dir,
        commit_message=commit_message,
        progress_callback=progress_callback,
        raise_on_error=raise_on_error,
    )
