from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from ..providers_base import BaseProvider
from ..types import ProviderResult, ResultStatus


class TumblrProvider(BaseProvider):
    name = "tumblr"
    timeout = 15
    ua_profile = "desktop_chrome"

    def build_url(self, username: str) -> str:
        # Primary format is subdirectory, but we check both.
        return f"https://www.tumblr.com/{username}"

    async def check(self, username: str, client, headers) -> ProviderResult:
        # Tumblr has two primary URL formats:
        # 1. Subdirectory: https://www.tumblr.com/username
        # 2. Subdomain:    https://username.tumblr.com
        # We need to check both to be certain.

        ts = datetime.now(timezone.utc).isoformat()
        start = time.monotonic()
        clean_user = username.strip().lower()

        urls_to_check = [
            f"https://www.tumblr.com/{clean_user}",
            f"https://{clean_user}.tumblr.com/",
        ]

        try:
            for url in urls_to_check:
                r = await client.get(
                    url, timeout=self.timeout, follow_redirects=True, headers=headers
                )
                text = (r.text or "").lower()

                # A 404 status is a definitive "not found".
                if r.status_code == 404:
                    continue  # Try the next URL format

                # Successful profiles usually contain the username in the title or body
                # and don't have "not found" messages.
                not_found_patterns = ["there's nothing here", "page not found"]
                if not any(p in text for p in not_found_patterns):
                    # Found a valid profile
                    return ProviderResult(
                        provider=self.name,
                        username=username,
                        url=str(r.url),
                        status=ResultStatus.FOUND,
                        http_status=r.status_code,
                        elapsed_ms=int((time.monotonic() - start) * 1000),
                        evidence={"checked_url": url},
                        profile={},
                        timestamp_iso=ts,
                    )

            # If we looped through both and found nothing
            return ProviderResult(
                provider=self.name,
                username=username,
                url=urls_to_check[0],  # Report the primary URL
                status=ResultStatus.NOT_FOUND,
                http_status=404,  # Simulate a 404 since neither worked
                elapsed_ms=int((time.monotonic() - start) * 1000),
                timestamp_iso=ts,
            )

        except Exception as e:
            # Handle network errors, SSL issues, etc.
            return ProviderResult(
                provider=self.name,
                username=username,
                url=self.build_url(username),
                status=ResultStatus.ERROR,
                error=str(e),
                profile={},
                timestamp_iso=ts,
            )


PROVIDERS = [TumblrProvider()]
