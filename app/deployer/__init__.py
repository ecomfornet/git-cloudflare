"""
Deployer package for automated static site deployment to GitHub Pages via Git Data APIs.
"""

from app.deployer.github import (
    GitHubDeployer,
    GitHubDeployError,
    GitHubAPIError,
    GitHubNetworkError,
    deploy_to_github_pages,
)

__all__ = [
    "GitHubDeployer",
    "GitHubDeployError",
    "GitHubAPIError",
    "GitHubNetworkError",
    "deploy_to_github_pages",
]
