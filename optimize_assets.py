"""Standalone CLI script to batch-optimize project images to WebP format with web-standard dimensions."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from app.ingestion.image_downloader import (
    DEFAULT_WEBP_QUALITY,
    STANDARD_HERO_HEIGHT,
    STANDARD_HERO_WIDTH,
    batch_optimize_directory,
)


def format_bytes(num_bytes: int) -> str:
    """Formats bytes into human readable format."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    else:
        return f"{num_bytes / (1024 * 1024):.2f} MB"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch optimize project images to WebP with web-standard dimensions (16:10 / 1200x750)."
    )
    parser.add_argument(
        "--dir",
        default="assets/images",
        help="Path to images directory (default: assets/images)",
    )
    parser.add_argument(
        "--manifest",
        default="pseo_manifest.json",
        help="Path to manifest JSON file to update (default: pseo_manifest.json)",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=STANDARD_HERO_WIDTH,
        help=f"Standard maximum width in pixels (default: {STANDARD_HERO_WIDTH})",
    )
    parser.add_argument(
        "--max-height",
        type=int,
        default=STANDARD_HERO_HEIGHT,
        help=f"Standard maximum height in pixels (default: {STANDARD_HERO_HEIGHT})",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_WEBP_QUALITY,
        help=f"WebP quality factor 1-100 (default: {DEFAULT_WEBP_QUALITY})",
    )
    parser.add_argument(
        "--remove-source",
        action="store_true",
        help="Remove original source raster images after WebP conversion",
    )

    args = parser.parse_args()

    images_dir = os.path.abspath(args.dir)
    manifest_path = os.path.abspath(args.manifest) if args.manifest else None

    if not os.path.exists(images_dir):
        print(f"[ERROR] Directory does not exist: {images_dir}")
        return 1

    print("=" * 70)
    print("      pSEO ASSET OPTIMIZER: WebP & Web-Standard Dimensions")
    print("=" * 70)
    print(f" Target Directory : {images_dir}")
    print(f" Manifest Path    : {manifest_path if manifest_path and os.path.exists(manifest_path) else 'None'}")
    print(f" Web Bounds       : max {args.max_width}x{args.max_height} px (16:10 ratio)")
    print(f" WebP Quality     : {args.quality}")
    print(f" Remove Source    : {args.remove_source}")
    print("-" * 70)

    stats = batch_optimize_directory(
        images_dir=images_dir,
        manifest_path=manifest_path,
        max_width=args.max_width,
        max_height=args.max_height,
        quality=args.quality,
        remove_source_raster=args.remove_source,
    )

    print(f" Scanned Images   : {stats['total_scanned']}")
    print(f" Converted / Opt  : {stats['converted']}")
    print(f" Original Size    : {format_bytes(stats['original_bytes'])}")
    print(f" Optimized Size   : {format_bytes(stats['optimized_bytes'])}")
    print(f" Total Saved      : {format_bytes(stats['saved_bytes'])} ({stats['percent_reduction']}%)")
    print("=" * 70)
    print("[SUCCESS] Image optimization completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
