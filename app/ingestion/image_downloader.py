"""Image downloader and WebP optimizer with web-standard sizing (16:10 / 1200x750) and SVG fallback."""

from __future__ import annotations

import html as html_lib
import io
import json
import logging
import os
import shutil
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from app.models import PostItem

logger = logging.getLogger(__name__)

socket.setdefaulttimeout(10)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Web standards: 16:10 aspect ratio matching editorial hero cards and SVG badges
STANDARD_HERO_WIDTH = 1200
STANDARD_HERO_HEIGHT = 750
STANDARD_CARD_WIDTH = 600
STANDARD_CARD_HEIGHT = 375
DEFAULT_WEBP_QUALITY = 82


def detect_image_extension(url: str) -> str:
    """Infers the file extension (.jpg, .png, .webp) from an image URL path."""
    if not url:
        return ".jpg"

    parsed = urllib.parse.urlparse(url)
    clean_path = parsed.path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"):
        if clean_path.endswith(ext):
            return ext

    return ".jpg"


def optimize_image_to_webp(
    source: Union[str, bytes],
    output_path: str,
    max_width: int = STANDARD_HERO_WIDTH,
    max_height: int = STANDARD_HERO_HEIGHT,
    quality: int = DEFAULT_WEBP_QUALITY,
    crop_to_aspect: bool = False,
) -> Tuple[str, int, int]:
    """Resizes and converts image to standard web dimensions (16:10, max 1200x750) and WebP format.

    - Handles RGBA, LA, and P modes with transparency preserving alpha channel.
    - Converts CMYK or non-standard color modes to standard RGB for WebP.
    - If crop_to_aspect is True, crops the image to exact 16:10 aspect ratio centered.
    - Downscales proportionally within max_width x max_height using Lanczos resampling.
    - Saves with Pillow WEBP format, quality=82, method=6, optimize=True.
    - Returns (output_path, final_width, final_height).
    """
    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow is not installed. Writing raw source without optimization.")
        abs_output = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)
        if isinstance(source, bytes):
            with open(abs_output, "wb") as f:
                f.write(source)
        elif source != abs_output and os.path.exists(source):
            shutil.copy2(source, abs_output)
        return abs_output, max_width, max_height

    opened_img = None
    try:
        if isinstance(source, bytes):
            opened_img = Image.open(io.BytesIO(source))
        else:
            opened_img = Image.open(source)
        img = opened_img.copy()
    finally:
        if opened_img is not None:
            try:
                opened_img.close()
            except Exception:
                pass

    # Normalize color mode
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    orig_w, orig_h = img.size

    # Optional 16:10 center cropping for mismatched orientations
    if crop_to_aspect and orig_w > 0 and orig_h > 0:
        target_ratio = 16.0 / 10.0
        current_ratio = orig_w / float(orig_h)
        if current_ratio > target_ratio:
            new_w = int(orig_h * target_ratio)
            offset = (orig_w - new_w) // 2
            img = img.crop((offset, 0, offset + new_w, orig_h))
        elif current_ratio < target_ratio:
            new_h = int(orig_w / target_ratio)
            offset = (orig_h - new_h) // 2
            img = img.crop((0, offset, orig_w, offset + new_h))

    # Resize if exceeding maximum standard bounds
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    w, h = img.size
    abs_output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_output), exist_ok=True)
    img.save(abs_output, format="WEBP", quality=quality, method=6, optimize=True)
    return abs_output, w, h


def generate_svg_badge(
    title: str,
    slug: str,
    output_path: str,
    subtitle: str = "CURATED EDITORIAL GUIDE",
) -> str:
    """Generates a clean, 1200x750 high-resolution SVG fallback badge image."""
    abs_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    clean_title = (title or slug.replace("-", " ").title()).strip()
    if len(clean_title) > 52:
        safe_title = html_lib.escape(clean_title[:50] + "…")
    else:
        safe_title = html_lib.escape(clean_title)

    safe_subtitle = html_lib.escape(subtitle.upper())

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="750" viewBox="0 0 1200 750">
  <defs>
    <linearGradient id="bgGradient" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#F7F5F0"/>
      <stop offset="50%" stop-color="#EFECE4"/>
      <stop offset="100%" stop-color="#E4DDD1"/>
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="8" stdDeviation="16" flood-color="#000000" flood-opacity="0.06"/>
    </filter>
  </defs>
  <rect width="1200" height="750" fill="url(#bgGradient)"/>
  <rect x="48" y="48" width="1104" height="654" rx="20" fill="#FFFFFF" fill-opacity="0.65" stroke="#D8D0C2" stroke-width="2" filter="url(#shadow)"/>
  <rect x="520" y="240" width="160" height="4" rx="2" fill="#B45309"/>
  <text x="600" y="360" text-anchor="middle" font-family="'Playfair Display', Georgia, serif" font-size="44" font-weight="700" fill="#1C1917">{safe_title}</text>
  <text x="600" y="430" text-anchor="middle" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="20" font-weight="600" letter-spacing="4" fill="#78716C">{safe_subtitle}</text>
</svg>"""

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    return abs_path


def download_image_to_repo(
    img_url: str,
    slug: str,
    output_dir: str,
    timeout: int = 15,
    user_agent: str = DEFAULT_USER_AGENT,
    convert_to_webp: bool = False,
    max_width: int = STANDARD_HERO_WIDTH,
    max_height: int = STANDARD_HERO_HEIGHT,
    quality: int = DEFAULT_WEBP_QUALITY,
) -> str:
    """Downloads remote image to <output_dir>/assets/images/<slug>.<ext> or creates SVG fallback.

    If convert_to_webp is True, converts/optimizes the image into WebP format with standard sizing.
    Returns the web path '/assets/images/<slug>.<ext>'.
    """
    clean_slug = slug or "editorial-guide"
    assets_dir = os.path.join(output_dir, "assets", "images")
    os.makedirs(assets_dir, exist_ok=True)

    if convert_to_webp:
        ext = ".webp"
    else:
        ext = detect_image_extension(img_url) if img_url else ".jpg"

    filename = f"{clean_slug}{ext}"
    local_file_path = os.path.join(assets_dir, filename)
    web_path = f"/assets/images/{filename}"

    if img_url and img_url.startswith(("http://", "https://")):
        try:
            req = urllib.request.Request(img_url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            if data and len(data) > 64:
                if convert_to_webp:
                    optimize_image_to_webp(
                        data,
                        local_file_path,
                        max_width=max_width,
                        max_height=max_height,
                        quality=quality,
                    )
                else:
                    with open(local_file_path, "wb") as f:
                        f.write(data)
                return web_path
        except Exception as exc:
            logger.warning("Error downloading image %s: %s", img_url, exc)

    # Fallback to SVG badge
    svg_filename = f"{clean_slug}.svg"
    svg_file_path = os.path.join(assets_dir, svg_filename)
    svg_web_path = f"/assets/images/{svg_filename}"
    generate_svg_badge(
        title=clean_slug.replace("-", " ").title(),
        slug=clean_slug,
        output_path=svg_file_path,
    )
    return svg_web_path


def download_post_image(
    post: PostItem,
    output_dir: str = ".",
    timeout: int = 15,
    force: bool = False,
    fetcher: Optional[Callable[[str], bytes]] = None,
    convert_to_webp: bool = True,
    max_width: int = STANDARD_HERO_WIDTH,
    max_height: int = STANDARD_HERO_HEIGHT,
    quality: int = DEFAULT_WEBP_QUALITY,
    domain: Optional[str] = None,
) -> str:
    """Downloads and optimizes post featured image to assets/images/<slug>.webp with standard sizing.

    If domain is specified, organizes into assets/<domain>/images/<slug>.webp.
    If download fails, HTTP error occurs, or image_url is missing:
    Generates a fallback SVG badge at assets/[domain/]images/<slug>.svg.
    Updates post.local_image_path, post.image_width, and post.image_height.
    """
    slug = post.slug or "editorial-guide"
    post_domain = domain or getattr(post, "domain", None)
    archive_dir = None
    if post_domain:
        clean_domain = str(post_domain).strip().lower()
        if "://" in clean_domain:
            clean_domain = urllib.parse.urlparse(clean_domain).hostname or clean_domain
        if clean_domain.startswith("www."):
            clean_domain = clean_domain[4:]
        if clean_domain.endswith(".workers.dev"):
            clean_domain = clean_domain.split(".")[0]
        images_dir = os.path.join(output_dir, "assets", clean_domain, "images")
        archive_dir = os.path.join(output_dir, "scraped_data", clean_domain, "assets", "images")
        os.makedirs(archive_dir, exist_ok=True)
        webp_filename = f"{slug}.webp"
        webp_target_file = os.path.join(images_dir, webp_filename)
        webp_relative_path = f"assets/{clean_domain}/images/{webp_filename}"
        svg_filename = f"{slug}.svg"
        svg_target_file = os.path.join(images_dir, svg_filename)
        svg_relative_path = f"assets/{clean_domain}/images/{svg_filename}"
    else:
        images_dir = os.path.join(output_dir, "assets", "images")
        webp_filename = f"{slug}.webp"
        webp_target_file = os.path.join(images_dir, webp_filename)
        webp_relative_path = f"assets/images/{webp_filename}"
        svg_filename = f"{slug}.svg"
        svg_target_file = os.path.join(images_dir, svg_filename)
        svg_relative_path = f"assets/images/{svg_filename}"
    os.makedirs(images_dir, exist_ok=True)

    # 1. Check if optimized WebP already exists on disk and is valid
    if not force and os.path.exists(webp_target_file) and os.path.getsize(webp_target_file) > 64:
        post.local_image_path = webp_relative_path
        post.image_width = max_width
        post.image_height = max_height
        return webp_relative_path

    # 2. Check if any raster image exists; optimize to WebP on-the-fly if convert_to_webp is True
    if not force:
        for possible_ext in (".jpg", ".jpeg", ".png"):
            cand_file = os.path.join(images_dir, f"{slug}{possible_ext}")
            if os.path.exists(cand_file) and os.path.getsize(cand_file) > 64:
                if convert_to_webp:
                    try:
                        _, w, h = optimize_image_to_webp(
                            cand_file,
                            webp_target_file,
                            max_width=max_width,
                            max_height=max_height,
                            quality=quality,
                        )
                        post.local_image_path = webp_relative_path
                        post.image_width = w
                        post.image_height = h
                        return webp_relative_path
                    except Exception as opt_err:
                        logger.warning("Could not optimize existing %s: %s", cand_file, opt_err)
                cand_rel = f"assets/images/{slug}{possible_ext}"
                post.local_image_path = cand_rel
                return cand_rel

    # 3. Check for existing SVG fallback
    svg_filename = f"{slug}.svg"
    svg_target_file = os.path.join(images_dir, svg_filename)
    svg_relative_path = f"assets/images/{svg_filename}"
    img_url = (post.image_url or "").strip()
    if not force and not img_url and os.path.exists(svg_target_file):
        post.local_image_path = svg_relative_path
        post.image_width = STANDARD_HERO_WIDTH
        post.image_height = STANDARD_HERO_HEIGHT
        return svg_relative_path

    # 4. Attempt remote download and WebP optimization
    if img_url and img_url.startswith(("http://", "https://")):
        try:
            if fetcher:
                data = fetcher(img_url)
            else:
                req = urllib.request.Request(img_url, headers={"User-Agent": DEFAULT_USER_AGENT})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = resp.read()

            if data and len(data) > 64:
                if convert_to_webp:
                    try:
                        _, w, h = optimize_image_to_webp(
                            data,
                            webp_target_file,
                            max_width=max_width,
                            max_height=max_height,
                            quality=quality,
                        )
                        logger.info("Optimized and saved WebP image for '%s': %dx%d -> %s", slug, w, h, webp_target_file)
                        if archive_dir and os.path.exists(archive_dir):
                            try:
                                shutil.copy2(webp_target_file, os.path.join(archive_dir, webp_filename))
                            except Exception:
                                pass
                        post.local_image_path = webp_relative_path
                        post.image_width = w
                        post.image_height = h
                        return webp_relative_path
                    except Exception as conv_exc:
                        logger.warning("WebP encoding failed for %s: %s; saving raw format", slug, conv_exc)

                # Fallback to saving raw format if WebP conversion fails or is disabled
                ext = detect_image_extension(img_url)
                raw_filename = f"{slug}{ext}"
                raw_file_path = os.path.join(images_dir, raw_filename)
                with open(raw_file_path, "wb") as f:
                    f.write(data)
                if archive_dir and os.path.exists(archive_dir):
                    try:
                        shutil.copy2(raw_file_path, os.path.join(archive_dir, raw_filename))
                    except Exception:
                        pass
                raw_relative_path = f"assets/images/{raw_filename}"
                post.local_image_path = raw_relative_path
                return raw_relative_path
        except Exception as exc:
            logger.warning("Failed to download image from %s: %s; falling back to SVG", img_url, exc)

    # 5. Remote download failed or no URL provided: generate clean SVG fallback
    generate_svg_badge(
        title=post.title,
        slug=slug,
        output_path=svg_target_file,
        subtitle=post.category or "CURATED EDITORIAL GUIDE",
    )
    if archive_dir and os.path.exists(archive_dir):
        try:
            generate_svg_badge(
                title=post.title,
                slug=slug,
                output_path=os.path.join(archive_dir, svg_filename),
                subtitle=post.category or "CURATED EDITORIAL GUIDE",
            )
        except Exception:
            pass
    logger.info("Generated SVG badge for '%s' at %s", slug, svg_target_file)
    post.local_image_path = svg_relative_path
    post.image_width = STANDARD_HERO_WIDTH
    post.image_height = STANDARD_HERO_HEIGHT
    return svg_relative_path


def download_images_for_posts(
    posts: List[PostItem],
    output_dir: str = ".",
    timeout: int = 15,
    force: bool = False,
    fetcher: Optional[Callable[[str], bytes]] = None,
    convert_to_webp: bool = True,
    max_width: int = STANDARD_HERO_WIDTH,
    max_height: int = STANDARD_HERO_HEIGHT,
    quality: int = DEFAULT_WEBP_QUALITY,
    domain: Optional[str] = None,
) -> Dict[str, str]:
    """Batch downloads and optimizes featured images for multiple posts."""
    results: Dict[str, str] = {}
    for post in posts:
        if not post.slug:
            continue
        local_path = download_post_image(
            post=post,
            output_dir=output_dir,
            timeout=timeout,
            force=force,
            fetcher=fetcher,
            convert_to_webp=convert_to_webp,
            max_width=max_width,
            max_height=max_height,
            quality=quality,
            domain=domain,
        )
        results[post.slug] = local_path
    return results


def batch_optimize_directory(
    images_dir: str = "assets/images",
    manifest_path: Optional[str] = "pseo_manifest.json",
    max_width: int = STANDARD_HERO_WIDTH,
    max_height: int = STANDARD_HERO_HEIGHT,
    quality: int = DEFAULT_WEBP_QUALITY,
    remove_source_raster: bool = False,
) -> Dict[str, Any]:
    """Scans images_dir, converts all raster images to WebP with web standards, and updates manifest."""
    abs_images_dir = os.path.abspath(images_dir)
    if not os.path.exists(abs_images_dir):
        return {
            "total_scanned": 0,
            "converted": 0,
            "original_bytes": 0,
            "optimized_bytes": 0,
            "saved_bytes": 0,
            "percent_reduction": 0.0,
        }

    total_scanned = 0
    converted = 0
    original_bytes = 0
    optimized_bytes = 0
    slug_to_webp: Dict[str, str] = {}
    rel_prefix = os.path.relpath(abs_images_dir, os.path.abspath(".")).replace("\\", "/")

    for fname in os.listdir(abs_images_dir):
        full_path = os.path.join(abs_images_dir, fname)
        if not os.path.isfile(full_path):
            continue

        lower = fname.lower()
        if lower.endswith(".svg"):
            continue

        total_scanned += 1
        stem, ext = os.path.splitext(fname)
        target_webp = os.path.join(abs_images_dir, f"{stem}.webp")
        orig_size = os.path.getsize(full_path)
        original_bytes += orig_size

        is_oversized_webp = lower.endswith(".webp") and orig_size > 250_000
        needs_conversion = lower.endswith((".png", ".jpg", ".jpeg")) or is_oversized_webp

        if needs_conversion:
            try:
                # If modifying in-place for oversized webp, use temp file
                if lower.endswith(".webp"):
                    temp_out = os.path.join(abs_images_dir, f"{stem}_opt.tmp.webp")
                    _, w, h = optimize_image_to_webp(full_path, temp_out, max_width, max_height, quality)
                    os.replace(temp_out, full_path)
                    new_size = os.path.getsize(full_path)
                else:
                    _, w, h = optimize_image_to_webp(full_path, target_webp, max_width, max_height, quality)
                    new_size = os.path.getsize(target_webp)
                    if remove_source_raster and os.path.exists(full_path):
                        os.remove(full_path)

                optimized_bytes += new_size
                converted += 1
                slug_to_webp[stem] = f"{rel_prefix}/{stem}.webp"
            except Exception as exc:
                logger.warning("Failed optimizing %s: %s", fname, exc)
                optimized_bytes += orig_size
        else:
            optimized_bytes += orig_size
            if lower.endswith(".webp"):
                slug_to_webp[stem] = f"{rel_prefix}/{fname}"

    # Update manifest if provided
    if manifest_path and os.path.exists(manifest_path) and slug_to_webp:
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)

            updated = False
            posts_obj = manifest_data.get("posts")
            if isinstance(posts_obj, dict):
                for slug, post_dict in posts_obj.items():
                    if slug in slug_to_webp:
                        post_dict["local_image_path"] = slug_to_webp[slug]
                        post_dict["image_width"] = max_width
                        post_dict["image_height"] = max_height
                        updated = True
            elif isinstance(posts_obj, list):
                for post_dict in posts_obj:
                    s = post_dict.get("slug")
                    if s in slug_to_webp:
                        post_dict["local_image_path"] = slug_to_webp[s]
                        post_dict["image_width"] = max_width
                        post_dict["image_height"] = max_height
                        updated = True

            if updated:
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("Error updating manifest with WebP paths: %s", exc)

    saved_bytes = max(0, original_bytes - optimized_bytes)
    reduction = (saved_bytes / original_bytes * 100.0) if original_bytes > 0 else 0.0

    return {
        "total_scanned": total_scanned,
        "converted": converted,
        "original_bytes": original_bytes,
        "optimized_bytes": optimized_bytes,
        "saved_bytes": saved_bytes,
        "percent_reduction": round(reduction, 2),
    }

