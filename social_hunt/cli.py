from __future__ import annotations

import argparse
import asyncio
import logging

from .banner import print_banner
from .engine import SocialHuntEngine
from .export import export_results
from .registry import build_registry
from .types import ResultStatus


def main() -> None:
    print_banner()

    parser = argparse.ArgumentParser(
        description="Social-Hunt: username presence checks (CLI+Web)"
    )
    parser.add_argument("username", help="Username to search")
    parser.add_argument(
        "--platforms", nargs="+", help="Specific platforms to search (space separated)"
    )
    parser.add_argument(
        "--format", choices=["csv", "json"], default="csv", help="Export format"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--max-concurrency", type=int, default=6, help="Max concurrent checks"
    )
    parser.add_argument(
        "--face-match", nargs="+", help="One or more paths to images for face matching"
    )
    args = parser.parse_args()

    dynamic_addons = []
    if args.face_match:
        from .addons.face_matcher import FaceMatcherAddon

        dynamic_addons.append(FaceMatcherAddon(target_image_paths=args.face_match))

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("social_hunt.log"), logging.StreamHandler()],
    )

    registry = build_registry("providers.yaml")
    engine = SocialHuntEngine(registry, max_concurrency=args.max_concurrency)

    print(f"\nSearching for username: {args.username}")
    print("=" * 60)

    results = asyncio.run(
        engine.scan_username(
            args.username, args.platforms, dynamic_addons=dynamic_addons
        )
    )

    for r in results:
        if r.status == ResultStatus.ERROR:
            mark = "?"
            msg = r.error or "error"
        else:
            mark = (
                "✓"
                if r.status == ResultStatus.FOUND
                else ("✗" if r.status == ResultStatus.NOT_FOUND else "~")
            )
            prof = r.profile or {}
            extra = []
            if prof.get("display_name"):
                extra.append(str(prof.get("display_name")))
            if prof.get("followers") is not None:
                extra.append(f"followers={prof.get('followers')}")
            if prof.get("following") is not None:
                extra.append(f"following={prof.get('following')}")
            if prof.get("created_at"):
                extra.append(f"created={prof.get('created_at')}")
            if prof.get("face_match"):
                match_info = prof["face_match"]
                if match_info.get("match"):
                    extra.append("FACE MATCH")
                else:
                    extra.append(
                        f"NO FACE MATCH (reason: {match_info.get('reason', 'unknown')})"
                    )
            prefix = (" | ".join(extra) + " | ") if extra else ""
            msg = f"{prefix}{r.url}"
        print(f"{r.provider:14} [{mark}] {r.status.value:10} {msg}")

    out = export_results(results, args.format)
    print(f"\nExported: {out}")
    print("Log: social_hunt.log")


if __name__ == "__main__":
    main()
