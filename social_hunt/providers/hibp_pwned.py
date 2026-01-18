from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ..providers_base import BaseProvider
from ..types import ProviderResult, ResultStatus
from ..settings import get_setting


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_email(s: str) -> bool:
    return bool(_EMAIL_RE.match(s or ""))


class HIBPProvider(BaseProvider):
    """Have I Been Pwned breach + paste check.

    - If the input looks like an email, checks:
        * /breachedaccount/{account} (breaches)
        * /pasteaccount/{account} (pastes)  (email-only per docs)

    - If the input is not an email, it will *only* attempt /breachedaccount/{account}
      (HIBP documents this as "account"; pastes are explicitly email-only).

    Requires:
      - settings: hibp_api_key
      - settings: hibp_user_agent (optional, but HIBP requires a User-Agent header)
    """

    name = "hibp"
    timeout = 12
    ua_profile = "desktop_chrome"

    def build_url(self, username: str) -> str:
        # HIBP is not a profile URL; return docs page as a reference
        return "https://haveibeenpwned.com/"

    async def _call(self, client, url: str, headers: Dict[str, str]) -> Any:
        r = await client.get(url, timeout=self.timeout, follow_redirects=True, headers=headers)
        return r

    async def check(self, username: str, client, headers: Dict[str, str]) -> ProviderResult:
        start = time.monotonic()
        ts = datetime.now(timezone.utc).isoformat()

        acct = (username or "").strip()
        if not acct:
            return ProviderResult(
                provider=self.name,
                username=username,
                url=self.build_url(username),
                status=ResultStatus.ERROR,
                http_status=None,
                elapsed_ms=0,
                evidence={"hibp": True},
                profile={},
                error="empty input",
                timestamp_iso=ts,
            )

        api_key = str(get_setting("hibp_api_key") or "").strip()
        ua = str(get_setting("hibp_user_agent") or "social-hunt/2.2 (OSINT)").strip()
        allow_non_email = str(get_setting("hibp_allow_non_email") or "").strip().lower() in ("1", "true", "yes", "y")

        if not api_key:
            elapsed = int((time.monotonic() - start) * 1000)
            return ProviderResult(
                provider=self.name,
                username=username,
                url=self.build_url(username),
                status=ResultStatus.UNKNOWN,
                http_status=None,
                elapsed_ms=elapsed,
                evidence={"hibp": True, "configured": False},
                profile={"note": "HIBP API key not configured (set hibp_api_key in Settings)"},
                timestamp_iso=ts,
            )

        # HIBP is primarily email-based. By default we skip non-email inputs to avoid
        # unnecessary queries; you can override with hibp_allow_non_email=1 in Settings.
        if not _is_email(acct) and not allow_non_email:
            elapsed = int((time.monotonic() - start) * 1000)
            return ProviderResult(
                provider=self.name,
                username=username,
                url=self.build_url(username),
                status=ResultStatus.UNKNOWN,
                http_status=None,
                elapsed_ms=elapsed,
                evidence={"hibp": True, "configured": True, "skipped": True},
                profile={
                    "account": acct,
                    "note": "HIBP search is email-based; skipped (set hibp_allow_non_email=1 to force non-email)"
                },
                timestamp_iso=ts,
            )

        # HIBP requires a User-Agent header and hibp-api-key header.
        hibp_headers = dict(headers)
        hibp_headers["User-Agent"] = ua
        hibp_headers["hibp-api-key"] = api_key
        hibp_headers.setdefault("Accept", "application/json")

        from urllib.parse import quote

        encoded = quote(acct, safe="")
        base = "https://haveibeenpwned.com/api/v3"

        breaches_url = f"{base}/breachedaccount/{encoded}"
        pastes_url = f"{base}/pasteaccount/{encoded}"

        profile: Dict[str, Any] = {"account": acct}
        evidence: Dict[str, Any] = {"hibp": True, "breaches": True}

        try:
            rb = await self._call(client, breaches_url, hibp_headers)
            elapsed = int((time.monotonic() - start) * 1000)

            # Breaches
            if rb.status_code == 200:
                data = rb.json() if rb.text else []
                breach_names: List[str] = []
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("Name"):
                            breach_names.append(str(item["Name"]))
                profile["breach_count"] = len(breach_names)
                profile["breaches"] = breach_names
            elif rb.status_code == 404:
                profile["breach_count"] = 0
                profile["breaches"] = []
            elif rb.status_code in (401, 403, 429):
                return ProviderResult(
                    provider=self.name,
                    username=username,
                    url=self.build_url(username),
                    status=ResultStatus.BLOCKED,
                    http_status=rb.status_code,
                    elapsed_ms=elapsed,
                    evidence=evidence,
                    profile=profile,
                    error=(rb.text or "").strip() or "HIBP request blocked",
                    timestamp_iso=ts,
                )
            else:
                return ProviderResult(
                    provider=self.name,
                    username=username,
                    url=self.build_url(username),
                    status=ResultStatus.UNKNOWN,
                    http_status=rb.status_code,
                    elapsed_ms=elapsed,
                    evidence=evidence,
                    profile=profile,
                    error=f"Unexpected response ({rb.status_code})",
                    timestamp_iso=ts,
                )

            # Pastes (email-only per docs)
            if _is_email(acct):
                evidence["pastes"] = True
                rp = await self._call(client, pastes_url, hibp_headers)
                if rp.status_code == 200:
                    pdata = rp.json() if rp.text else []
                    # Keep it light: include source + id + date + emailcount
                    pastes: List[Dict[str, Any]] = []
                    if isinstance(pdata, list):
                        for p in pdata:
                            if isinstance(p, dict):
                                pastes.append({
                                    "Source": p.get("Source"),
                                    "Id": p.get("Id"),
                                    "Date": p.get("Date"),
                                    "EmailCount": p.get("EmailCount"),
                                })
                    profile["paste_count"] = len(pastes)
                    profile["pastes"] = pastes
                elif rp.status_code == 404:
                    profile["paste_count"] = 0
                    profile["pastes"] = []
                elif rp.status_code in (401, 403, 429):
                    profile["pastes_error"] = (rp.text or "").strip() or "HIBP pastes blocked"
                else:
                    profile["pastes_error"] = f"Unexpected response ({rp.status_code})"
            else:
                profile["pastes_note"] = "Pastes API is email-only; skipped"

            # Determine status
            breach_count = int(profile.get("breach_count") or 0)
            paste_count = int(profile.get("paste_count") or 0)
            status = ResultStatus.FOUND if (breach_count > 0 or paste_count > 0) else ResultStatus.NOT_FOUND

            return ProviderResult(
                provider=self.name,
                username=username,
                url=self.build_url(username),
                status=status,
                http_status=rb.status_code,
                elapsed_ms=elapsed,
                evidence=evidence,
                profile={k: v for k, v in profile.items() if v not in (None, "")},
                timestamp_iso=ts,
            )

        except Exception as e:
            elapsed = int((time.monotonic() - start) * 1000)
            return ProviderResult(
                provider=self.name,
                username=username,
                url=self.build_url(username),
                status=ResultStatus.ERROR,
                http_status=None,
                elapsed_ms=elapsed,
                evidence=evidence,
                profile=profile,
                error=str(e),
                timestamp_iso=ts,
            )


PROVIDERS = [HIBPProvider()]
