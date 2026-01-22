from __future__ import annotations

import time
from datetime import datetime, timezone

from ..providers_base import BaseProvider
from ..types import ProviderResult, ResultStatus


class LiveJournalProvider(BaseProvider):
    name = "livejournal"
    timeout = 15
    ua_profile = "desktop_chrome"

    def build_url(self, username: str) -> str:
        # LiveJournal uses a subdomain format.
        return f"https://{username.strip().lower()}.livejournal.com/"

    async def check(self, username: str, client, headers) -> ProviderResult:
        url = self.build_url(username)
        ts = datetime.now(timezone.utc).isoformat()
        start = time.monotonic()

        try:
            r = await client.get(
                url, timeout=self.timeout, follow_redirects=True, headers=headers
            )
            text = (r.text or "").lower()

            # Invalid or deleted journals have a specific title or message.
            not_found_patterns = [
                "journal deleted",
                "journal purged",
                "no such user",
                "account suspended",
            ]
            if any(p in text for p in not_found_patterns):
                status = ResultStatus.NOT_FOUND
            elif r.status_code == 200:
                # A 200 OK without an error message is a strong indicator of a valid journal.
                status = ResultStatus.FOUND
            else:
                status = ResultStatus.NOT_FOUND

            return ProviderResult(
                provider=self.name,
                username=username,
                url=url,
                status=status,
                http_status=r.status_code,
                elapsed_ms=int((time.monotonic() - start) * 1000),
                profile={},
                timestamp_iso=ts,
            )
        except Exception as e:
            # DNS errors (NXDOMAIN) are common for invalid subdomains
            if "name or service not known" in str(e).lower():
                return ProviderResult(
                    provider=self.name,
                    username=username,
                    url=url,
                    status=ResultStatus.NOT_FOUND,
                    error="DNS resolution failed (NXDOMAIN)",
                    timestamp_iso=ts,
                )

            return ProviderResult(
                provider=self.name,
                username=username,
                url=url,
                status=ResultStatus.ERROR,
                error=str(e),
                profile={},
                timestamp_iso=ts,
            )


PROVIDERS = [LiveJournalProvider()]
