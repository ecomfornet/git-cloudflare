"""Incremental manifest diffing engine preserving custom user edits."""

from __future__ import annotations

import datetime
import logging
from typing import Dict, List, Optional, Set, Tuple

from app.models import DiffSummary, Manifest, PostItem

logger = logging.getLogger(__name__)


def parse_date_to_timestamp(date_str: str) -> float:
    """Parses an ISO or YYYY-MM-DD date string to a numeric UTC timestamp for comparison."""
    if not date_str:
        return 0.0

    clean = str(date_str).strip()
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"

    try:
        dt = datetime.datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError):
        pass

    try:
        dt = datetime.datetime.strptime(clean[:10], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError):
        pass

    return 0.0


def merge_post_preserving_edits(existing: PostItem, incoming: PostItem) -> PostItem:
    """Merges incoming post data into existing post, strictly preserving custom dashboard edits.

    If custom_edited is True:
    Preserves: title, excerpt, checklist, takeaways, custom_edited flag, local_image_path.
    Updates: modified date, content_html, raw_meta.
    """
    if not existing.custom_edited:
        # Not customized: replace with incoming, keeping existing local image if incoming lacks one
        merged = PostItem.from_dict(incoming.to_dict())
        if existing.local_image_path and not incoming.local_image_path:
            merged.local_image_path = existing.local_image_path
        return merged

    # User has custom edited this post: preserve custom fields strictly
    merged_raw_meta = dict(incoming.raw_meta or {})
    merged_raw_meta.update(existing.raw_meta or {})

    # Compute latest modified timestamp
    in_ts = parse_date_to_timestamp(incoming.modified)
    ex_ts = parse_date_to_timestamp(existing.modified)
    latest_modified = incoming.modified if in_ts > ex_ts else existing.modified

    return PostItem(
        slug=existing.slug,
        title=existing.title,  # PRESERVED custom title
        excerpt=existing.excerpt,  # PRESERVED custom excerpt
        content_html=incoming.content_html or existing.content_html,
        category=existing.category or incoming.category,
        category_slug=existing.category_slug or incoming.category_slug,
        parent_slug=existing.parent_slug or incoming.parent_slug,
        date=existing.date or incoming.date,
        modified=latest_modified,
        image_url=incoming.image_url or existing.image_url,
        local_image_path=existing.local_image_path or incoming.local_image_path,
        custom_edited=True,  # PRESERVED custom flag
        checklist=[dict(c) for c in existing.checklist],  # PRESERVED custom checklist
        takeaways=[str(t) for t in existing.takeaways],  # PRESERVED custom takeaways
        raw_meta=merged_raw_meta,
    )


def is_post_updated(existing: PostItem, incoming: PostItem) -> bool:
    """Determines whether an incoming post has newer content or modified date than existing."""
    in_ts = parse_date_to_timestamp(incoming.modified)
    ex_ts = parse_date_to_timestamp(existing.modified)

    # 1. Incoming modified date is strictly newer
    if in_ts > ex_ts:
        return True

    # 2. Content HTML has changed
    if incoming.content_html and existing.content_html and incoming.content_html != existing.content_html:
        return True

    # 3. If post has NOT been custom edited, check if upstream title or excerpt changed
    if not existing.custom_edited:
        if incoming.title and existing.title and incoming.title != existing.title:
            return True
        if incoming.excerpt and existing.excerpt and incoming.excerpt != existing.excerpt:
            return True

    # 4. Featured image URL changed upstream
    if incoming.image_url and existing.image_url and incoming.image_url != existing.image_url:
        return True

    return False


def diff_manifest(manifest: Manifest, incoming_posts: Union[List[PostItem], List[dict]]) -> DiffSummary:
    """Diffs incoming posts against existing manifest.

    Categorizes incoming posts into:
    - New: slug not in manifest
    - Updated: slug in manifest with newer modified date or changed content (and not custom_edited)
    - Synced: slug in manifest with custom_edited == True (preserving user custom edits)
    - Unchanged: slug in manifest with identical modified date / no changes
    """
    new_posts: List[PostItem] = []
    updated_posts: List[PostItem] = []
    synced_posts: List[PostItem] = []
    unchanged_posts: List[PostItem] = []

    incoming_items: List[PostItem] = []
    for item in incoming_posts:
        if isinstance(item, PostItem):
            incoming_items.append(item)
        elif isinstance(item, dict):
            incoming_items.append(PostItem.from_dict(item))

    for incoming in incoming_items:
        if not incoming.slug:
            continue

        slug = incoming.slug
        existing = manifest.get_post(slug)

        if existing is None:
            # 1. New Post
            new_posts.append(incoming)
        else:
            if existing.custom_edited:
                # 2. Custom edited post is preserved and categorized as synced
                merged = merge_post_preserving_edits(existing, incoming)
                synced_posts.append(merged)
            elif is_post_updated(existing, incoming):
                # 3. Post updated upstream
                updated = merge_post_preserving_edits(existing, incoming)
                updated_posts.append(updated)
            else:
                # 4. Unchanged post
                unchanged_posts.append(existing)

    return DiffSummary(
        new_posts=new_posts,
        updated_posts=updated_posts,
        synced_posts=synced_posts,
        unchanged_posts=unchanged_posts,
    )


def apply_diff_to_manifest(manifest: Manifest, diff: DiffSummary) -> Manifest:
    """Applies DiffSummary changes to manifest, upserting new, updated, and synced posts."""
    for post in diff.new_posts:
        manifest.upsert_post(post)

    for post in diff.updated_posts:
        manifest.upsert_post(post)

    for post in diff.synced_posts:
        manifest.upsert_post(post)

    return manifest


def update_manifest_with_posts(
    manifest: Manifest,
    incoming_posts: List[PostItem],
) -> Tuple[DiffSummary, Manifest]:
    """Diffs incoming posts against manifest and applies updates atomically."""
    diff = diff_manifest(manifest, incoming_posts)
    apply_diff_to_manifest(manifest, diff)
    return diff, manifest
