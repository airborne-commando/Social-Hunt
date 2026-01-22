from __future__ import annotations

import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

from ..providers_base import BaseProvider
from ..types import ProviderResult, ResultStatus


class RobloxProvider(BaseProvider):
    name = "roblox"
    timeout = 15
    ua_profile = "desktop_chrome"

    def build_url(self, username: str) -> str:
        # Roblox uses a search redirect to find the user by name, as the final
        # URL is ID-based (e.g., /users/12345/profile).
        return f"https://www.roblox.com/search/users?keyword={quote_plus(username)}"

    async def check(self, username: str, client, headers) -> ProviderResult:
        search_url = self.build_url(username)
        ts = datetime.now(timezone.utc).isoformat()
        start = time.monotonic()

        try:
            r = await client.get(
                search_url, timeout=self.timeout, follow_redirects=True, headers=headers
            )
            text = (r.text or "").lower()

            # If the search page contains "no results found", the user doesn't exist.
            if "no results were found for" in text or "page not found" in text:
                return ProviderResult(
                    provider=self.name,
                    username=username,
                    url=search_url,
                    status=ResultStatus.NOT_FOUND,
                    http_status=r.status_code,
                    timestamp_iso=ts,
                )

            # A successful search redirects to the user's profile.
            # e.g., https://www.roblox.com/users/1234567/profile
            final_url = str(r.url)
            if "/users/" in final_url and "/profile" in final_url:
                status = ResultStatus.FOUND
            else:
                # If we land on the search page but there are multiple results,
                # we can't be sure which one is correct. Mark as NOT_FOUND for a specific match.
                status = ResultStatus.NOT_FOUND

            return ProviderResult(
                provider=self.name,
                username=username,
                url=final_url,
                status=status,
                http_status=r.status_code,
                elapsed_ms=int((time.monotonic() - start) * 1000),
                evidence={"final_url": final_url, "note": "Found via user search."},
                profile={},
                timestamp_iso=ts,
            )
        except Exception as e:
            return ProviderResult(
                provider=self.name,
                username=username,
                url=search_url,
                status=ResultStatus.ERROR,
                error=str(e),
                profile={},
                timestamp_iso=ts,
            )


PROVIDERS = [RobloxProvider()]
