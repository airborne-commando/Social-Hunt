from __future__ import annotations

import re
import time
from datetime import datetime, timezone

from ..providers_base import BaseProvider
from ..types import ProviderResult, ResultStatus


class ThreemaProvider(BaseProvider):
    name = "threema"
    timeout = 15
    ua_profile = "desktop_chrome"

    def build_url(self, username: str) -> str:
        return f"https://threema.id/{username}"

    async def check(self, username: str, client, headers) -> ProviderResult:
        # Threema IDs are 8 alphanumeric characters.
        # If input is not a valid ID format, we mark it as NOT_FOUND immediately
        # to avoid false positives or redirects.
        clean_id = username.strip().upper()

        # Basic validation: 8 chars, alphanumeric
        if not re.match(r"^[A-Z0-9]{8}$", clean_id):
            return ProviderResult(
                provider=self.name,
                username=username,
                url=f"https://threema.id/{username}",
                status=ResultStatus.NOT_FOUND,
                error="Invalid Threema ID format (must be 8 alphanumeric chars)",
                elapsed_ms=0,
                profile={},
                timestamp_iso=datetime.now(timezone.utc).isoformat(),
            )

        url = f"https://threema.id/{clean_id}"
        start = time.monotonic()
        ts = datetime.now(timezone.utc).isoformat()

        try:
            # We follow redirects. Invalid IDs often redirect to the main site (threema.ch).
            r = await client.get(
                url, timeout=self.timeout, follow_redirects=True, headers=headers
            )
            text = (r.text or "").lower()
            final_url = str(r.url)

            # 1. Check for redirect to homepage
            # Valid: https://threema.id/ECHOECHO -> stays on threema.id
            # Invalid: https://threema.id/INVALID1 -> redirects to https://threema.ch/en
            if "threema.ch" in final_url:
                status = ResultStatus.NOT_FOUND

            # 2. Check content for specific success markers
            elif "add to threema" in text or f"threema id: {clean_id.lower()}" in text:
                status = ResultStatus.FOUND

            # 3. Check for specific error markers
            elif "invalid id" in text:
                status = ResultStatus.NOT_FOUND

            else:
                # Ambiguous result
                status = ResultStatus.UNKNOWN

            return ProviderResult(
                provider=self.name,
                username=clean_id,
                url=url,
                status=status,
                http_status=r.status_code,
                elapsed_ms=int((time.monotonic() - start) * 1000),
                evidence={"final_url": final_url, "len": len(text)},
                profile={},
                timestamp_iso=ts,
            )

        except Exception as e:
            return ProviderResult(
                provider=self.name,
                username=username,
                url=url,
                status=ResultStatus.ERROR,
                error=str(e),
                elapsed_ms=int((time.monotonic() - start) * 1000),
                profile={},
                timestamp_iso=ts,
            )


PROVIDERS = [ThreemaProvider()]
