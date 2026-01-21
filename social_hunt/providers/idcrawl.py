from __future__ import annotations

import time
import re
from datetime import datetime, timezone
from typing import Optional, Literal
from urllib.parse import quote_plus

from ..providers_base import BaseProvider
from ..types import ProviderResult, ResultStatus


class IDCrawlProvider(BaseProvider):
    name = "idcrawl"
    timeout = 15
    ua_profile = "desktop_chrome"
    
    def __init__(self, state: Optional[str] = None):
        """
        Initialize IDCrawl provider.
        
        Args:
            state: Optional US state for people search (e.g., 'pennsylvania', 'new-york')
        """
        super().__init__()
        self.state = state.lower().replace(" ", "-") if state else None
    
    def _detect_query_type(self, query: str) -> Literal["email", "username", "people"]:
        """
        Detect whether the query is an email, username, or name.
        
        Args:
            query: Search query
            
        Returns:
            Query type
        """
        # Check if it's an email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, query):
            return "email"
        
        # Check if it looks like a username (no spaces, might have dots, underscores, etc.)
        username_pattern = r'^[a-zA-Z0-9._-]+$'
        if re.match(username_pattern, query) and " " not in query:
            # Additional check to avoid mistaking single names
            if len(query.split(".")) <= 2 and not query.endswith(('.com', '.org', '.net')):
                return "username"
        
        # Default to people search
        return "people"
    
    def build_url(self, query: str, query_type: Optional[str] = None) -> str:
        """
        Build IDCrawl URL based on detected query type.
        
        Args:
            query: Search query
            query_type: Optional override for query type detection
            
        Returns:
            URL string
        """
        if query_type is None:
            query_type = self._detect_query_type(query)
        
        if query_type == "people":
            # Format name with dashes
            name_formatted = query.lower().replace(" ", "-")
            
            if self.state:
                return f"https://www.idcrawl.com/{name_formatted}/{self.state}"
            else:
                return f"https://www.idcrawl.com/{name_formatted}"
        
        elif query_type == "username":
            # Username search: https://www.idcrawl.com/username-search?username=username
            encoded_username = quote_plus(query)
            return f"https://www.idcrawl.com/username-search?username={encoded_username}"
        
        elif query_type == "email":
            # Email lookup: https://www.idcrawl.com/email-lookup?email=email@example.com
            encoded_email = quote_plus(query)
            return f"https://www.idcrawl.com/email-lookup?email={encoded_email}"
        
        else:
            raise ValueError(f"Unknown query type: {query_type}")
    
    async def check(self, query: str, client, headers) -> ProviderResult:
        """
        Check for information on IDCrawl.
        
        Args:
            query: Search query (automatically detected as name, username, or email)
            client: HTTP client
            headers: Request headers
            
        Returns:
            ProviderResult object
        """
        # Detect query type
        query_type = self._detect_query_type(query)
        
        url = self.build_url(query, query_type)
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
            
            # Determine status based on response and query type
            status = self._determine_status(r.status_code, text, query, query_type)
            
            # Extract profile information if found
            profile = {}
            evidence_info = {}
            
            if status == ResultStatus.FOUND:
                if query_type == "people":
                    profile = self._extract_people_profile_info(text, query)
                elif query_type == "username":
                    profile = self._extract_username_info(text, query)
                    evidence_info["results_count"] = self._count_search_results(text)
                elif query_type == "email":
                    profile = self._extract_email_info(text, query)
                    evidence_info["results_count"] = self._count_search_results(text)
            
            # Build evidence dictionary
            evidence = {
                "len": len(text),
                "query_type": query_type,
                "state": self.state,
                **evidence_info
            }
            
            return ProviderResult(
                provider=self.name,
                username=query,
                url=url,
                status=status,
                http_status=r.status_code,
                elapsed_ms=int((time.monotonic() - start) * 1000),
                evidence=evidence,
                profile=profile,
                timestamp_iso=ts,
            )
            
        except Exception as e:
            return ProviderResult(
                provider=self.name,
                username=query,
                url=url,
                status=ResultStatus.ERROR,
                error=str(e),
                elapsed_ms=int((time.monotonic() - start) * 1000),
                profile={},
                timestamp_iso=ts,
            )
    
    def _determine_status(self, status_code: int, text: str, query: str, query_type: str) -> ResultStatus:
        """
        Determine the result status based on response.
        
        Args:
            status_code: HTTP status code
            text: Response text
            query: Original search query
            query_type: Type of query
            
        Returns:
            ResultStatus enum value
        """
        if status_code == 404:
            return ResultStatus.NOT_FOUND
        
        # Check for no results messages
        no_results_indicators = [
            "no results found",
            "0 results found",
            "could not find",
            "no matches found",
            "try another search",
            "search again",
        ]
        
        for indicator in no_results_indicators:
            if indicator in text:
                return ResultStatus.NOT_FOUND
        
        # Check for found indicators
        if query_type == "people":
            # People search specific indicators
            found_indicators = [
                "age",
                "location",
                "current city",
                "associated with",
                "social profiles",
                "public records",
            ]
            
            for indicator in found_indicators:
                if indicator in text:
                    return ResultStatus.FOUND
            
            # Check if name appears on page
            name_parts = query.lower().split()
            if all(part in text for part in name_parts):
                return ResultStatus.FOUND
        
        elif query_type in ["username", "email"]:
            # Username/email search specific indicators
            if "search results" in text or "results for" in text:
                return ResultStatus.FOUND
            
            # Check for result count
            results_pattern = r'(\d+)\s+results? found'
            match = re.search(results_pattern, text)
            if match and int(match.group(1)) > 0:
                return ResultStatus.FOUND
        
        return ResultStatus.UNKNOWN
    
    # The _extract_people_profile_info, _extract_username_info, 
    # _extract_email_info, and _count_search_results methods 
    # remain the same as in the first version above...


PROVIDERS = [IDCrawlProvider()]