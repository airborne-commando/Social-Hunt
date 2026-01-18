from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

import httpx

from .addons_base import BaseAddon
from .addons_registry import build_addon_registry, load_enabled_addons
from .providers_base import BaseProvider
from .rate_limit import HostRateLimiter
from .types import ProviderResult
from .ua import UA_PROFILES, merge_headers


class SocialHuntEngine:
    def __init__(
        self,
        registry: Dict[str, BaseProvider],
        max_concurrency: int = 6,
        min_host_interval_sec: float = 1.2,
    ):
        self.registry = registry
        self.max_concurrency = int(max_concurrency)
        self.limiter = HostRateLimiter(min_interval_sec=min_host_interval_sec)
        self.addon_registry = build_addon_registry()
        self.enabled_addon_names = load_enabled_addons()

    async def scan_username(
        self,
        username: str,
        providers: Optional[List[str]] = None,
        dynamic_addons: Optional[List[BaseAddon]] = None,
    ) -> List[ProviderResult]:
        if providers:
            chosen = [p for p in providers if p in self.registry]
        else:
            chosen = list(self.registry.keys())

        sem = asyncio.Semaphore(self.max_concurrency)

        async with httpx.AsyncClient() as client:

            async def run_one(name: str) -> ProviderResult:
                prov = self.registry[name]
                url = prov.build_url(username)

                base_headers = UA_PROFILES.get("desktop_chrome", {})
                prof_headers = UA_PROFILES.get(
                    getattr(prov, "ua_profile", "desktop_chrome"), {}
                )
                headers = merge_headers(base_headers, prof_headers)

                await self.limiter.wait(url)

                async with sem:
                    return await prov.check(username, client, headers)

            tasks = [asyncio.create_task(run_one(p)) for p in chosen]
            results = await asyncio.gather(*tasks)

            # --- Addon Processing ---
            addons_to_run = [
                self.addon_registry[name]
                for name in self.enabled_addon_names
                if name in self.addon_registry
            ]
            if dynamic_addons:
                addons_to_run.extend(dynamic_addons)

            if addons_to_run:
                addon_tasks = [
                    asyncio.create_task(
                        addon.run(username, results, client, self.limiter)
                    )
                    for addon in addons_to_run
                ]
                await asyncio.gather(*addon_tasks)

        return sorted(results, key=lambda r: r.provider.lower())
