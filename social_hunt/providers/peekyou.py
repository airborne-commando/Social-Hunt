from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from ..providers_base import BaseProvider
from ..types import ProviderResult, ResultStatus


class PeekYouProvider(BaseProvider):
    name = "peekyou"
    timeout = 15
    ua_profile = "desktop_chrome"
    
    def __init__(self, state: Optional[str] = None):
        """
        Initialize PeekYou provider.
        
        Args:
            state: Optional US state abbreviation (e.g., 'pennsylvania', 'new-york')
        """
        super().__init__()
        self.state = state.lower().replace(" ", "_") if state else None
    
    def build_url(self, name: str) -> str:
        """
        Build PeekYou URL from a full name.
        
        Args:
            
        Returns:
            URL string
        """
        # Format name as lowercase with underscores
        name_formatted = name.lower().replace(" ", "_")
        
        if self.state:
            # State-specific URL: https://www.peekyou.com/usa/{state}/{name}
            return f"https://www.peekyou.com/usa/{self.state}/{name_formatted}"
        else:
            # General URL: https://www.peekyou.com/{name}
            return f"https://www.peekyou.com/{name_formatted}"
    
    async def check(self, name: str, client, headers) -> ProviderResult:
        """
        Check for a person on PeekYou.
        
        Args:
            client: HTTP client
            headers: Request headers
            
        Returns:
            ProviderResult object
        """
        url = self.build_url(name)
        start = time.monotonic()
        ts = datetime.now(timezone.utc).isoformat()
        
        try:
            r = await client.get(
                url,
                timeout=self.timeout,
                follow_redirects=True,
                headers=headers
            )
            text = (r.text or "").lower()
            
            # Determine status based on response
            if r.status_code == 404:
                status = ResultStatus.NOT_FOUND
            elif "this peekyou profile has been removed" in text:
                status = ResultStatus.NOT_FOUND
            elif "no results found" in text:
                status = ResultStatus.NOT_FOUND
            elif "profile not found" in text:
                status = ResultStatus.NOT_FOUND
            elif "privacy settings" in text:
                status = ResultStatus.FOUND
            elif "profile preview" in text:
                status = ResultStatus.FOUND
            elif name.lower().replace(" ", "_") in url.lower():
                # Name appears in URL (profile exists)
                status = ResultStatus.FOUND
            elif "age" in text and "location" in text:
                status = ResultStatus.FOUND
            else:
                status = ResultStatus.UNKNOWN
            
            # Extract profile information
            profile = {}
            if status == ResultStatus.FOUND:
                profile = self._extract_profile_info(text, name)
            
            return ProviderResult(
                provider=self.name,
                username=name,  # Using the full name
                url=url,
                status=status,
                http_status=r.status_code,
                elapsed_ms=int((time.monotonic() - start) * 1000),
                evidence={
                    "len": len(text),
                    "state": self.state,
                    "has_privacy_notice": "privacy settings" in text
                },
                profile=profile,
                timestamp_iso=ts,
            )
            
        except Exception as e:
            return ProviderResult(
                provider=self.name,
                username=name,
                url=url,
                status=ResultStatus.ERROR,
                error=str(e),
                elapsed_ms=int((time.monotonic() - start) * 1000),
                profile={},
                timestamp_iso=ts,
            )
    
    def _extract_profile_info(self, text: str, name: str) -> dict:
        """
        Extract basic profile information from PeekYou page.
        
        Args:
            text: HTML text content
            name: Full name
            
        Returns:
            Dictionary with extracted profile info
        """
        profile = {}
        
        # Split name if possible
        name_parts = name.split()
        if len(name_parts) >= 2:
            profile["first_name"] = name_parts[0]
            profile["last_name"] = " ".join(name_parts[1:])
        
        # Look for age pattern
        import re
        
        age_patterns = [
            r'(\d{1,3})\s+years?\s+old',
            r'age\s*:\s*(\d{1,3})',
            r'(\d{1,3})\s+yrs?',
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                profile["age"] = match.group(1)
                break
        
        # Try to find location
        location_patterns = [
            r'lives?\s+in\s+([^<>.]+?)(?:<|\.|$)',
            r'location\s*:\s*([^<>.]+?)(?:<|\.|$)',
            r'from\s+([^<>.]+?)(?:<|\.|$)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) < 100:
                    profile["location"] = location
                break
        
        return profile


PROVIDERS = [PeekYouProvider()]