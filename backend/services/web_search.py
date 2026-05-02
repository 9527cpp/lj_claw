"""
Web search service using DuckDuckGo HTML (no API key required).
Falls back to Brave Search if API key is available.
"""
import asyncio
import html
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

import httpx

DATA_DIR = Path(__file__).parent.parent / "data"

# Brave Search (free tier: 2000 queries/month)
BRAVE_API_KEY_FILE = DATA_DIR / "brave_search_key"


def get_brave_api_key() -> Optional[str]:
    if BRAVE_API_KEY_FILE.exists():
        return BRAVE_API_KEY_FILE.read_text().strip()
    return None


class WebSearchService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.brave_key = get_brave_api_key()

    async def search(
        self,
        query: str,
        num_results: int = 5,
    ) -> List[Dict[str, str]]:
        """
        Search the web and return a list of results with title, url, and snippet.

        Uses Brave Search API if API key is configured, otherwise falls back to
        DuckDuckGo HTML (no API key needed, but rate-limited and less reliable).
        """
        if self.brave_key:
            return await self._brave_search(query, num_results)
        else:
            return await self._duckduckgo_search(query, num_results)

    async def _brave_search(
        self, query: str, num_results: int
    ) -> List[Dict[str, str]]:
        """Search using Brave Search API."""
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_key,
        }
        params = {
            "q": query,
            "count": min(num_results, 10),
            "safesearch": "moderate",
        }
        try:
            resp = await self.client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("web", {}).get("results", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", ""),
                })
            return results
        except Exception as e:
            print(f"[web_search] Brave search failed: {e}, falling back to DDG")
            return await self._duckduckgo_search(query, num_results)

    async def _duckduckgo_search(
        self, query: str, num_results: int
    ) -> List[Dict[str, str]]:
        """Search using DuckDuckGo HTML (no API key required)."""
        try:
            # DuckDuckGo HTML Lite results
            url = "https://lite.duckduckgo.com/lite/"
            params = {"q": query, "kl": "wt-wt"}
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()

            html_content = resp.text
            results = []

            # Parse result blocks
            # Format: <a class="result-link" href="...">title</a>
            #         <span class="result-snippet">snippet</span>
            link_pattern = re.compile(
                r'<a\s+class="result-link"\s+href="([^"]+)"[^>]*>([^<]*)</a>'
            )
            snippet_pattern = re.compile(
                r'<span\s+class="result-snippet"[^>]*>([^<]*)</span>'
            )

            links = link_pattern.findall(html_content)
            snippets = snippet_pattern.findall(html_content)

            for i, (url, title) in enumerate(links[:num_results]):
                snippet = ""
                if i < len(snippets):
                    snippet = html.unescape(snippets[i])
                    # Clean up HTML tags
                    snippet = re.sub(r'<[^>]+>', '', snippet).strip()

                title = html.unescape(title).strip()
                results.append({
                    "title": title,
                    "url": url.strip(),
                    "snippet": snippet,
                })

            return results

        except Exception as e:
            print(f"[web_search] DDG search failed: {e}")
            return []

    async def close(self):
        await self.client.aclose()


# Singleton
_search_service: Optional[WebSearchService] = None


def get_search_service() -> WebSearchService:
    global _search_service
    if _search_service is None:
        _search_service = WebSearchService()
    return _search_service