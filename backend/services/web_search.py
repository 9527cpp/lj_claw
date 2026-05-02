"""
Web search service using Bing (cn.bing.com).
No API key required, uses curl subprocess for reliable results.
"""
import asyncio
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import quote

DATA_DIR = Path(__file__).parent.parent / "data"


class WebSearchService:
    """Search using Bing via curl (no API key required)."""

    def __init__(self):
        self._html_clean = re.compile(r"<[^>]+>")

    async def search(
        self,
        query: str,
        num_results: int = 5,
    ) -> List[Dict[str, str]]:
        """
        Search using Bing and return results with title, url, and snippet.
        Falls back to httpx if curl is unavailable.
        """
        try:
            return await self._search_via_curl(query, num_results)
        except Exception as e:
            print(f"[web_search] curl failed: {e}, trying httpx...")
            try:
                return await self._search_via_httpx(query, num_results)
            except Exception as e2:
                print(f"[web_search] httpx also failed: {e2}")
                return []

    async def _search_via_curl(
        self,
        query: str,
        num_results: int,
    ) -> List[Dict[str, str]]:
        """Search using Bing via curl subprocess (shell mode for proper URL encoding)."""
        encoded_q = quote(query, safe="")
        cmd = (
            f'curl -s --max-time 10 '
            f'-A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" '
            f'-H "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8" '
            f'-L "https://cn.bing.com/search?q={encoded_q}&setlang=zh-CN"'
        )

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=12.0)
        html = stdout.decode("utf-8", errors="replace")

        return self._parse_bing_html(html, num_results)

    async def _search_via_httpx(
        self,
        query: str,
        num_results: int,
    ) -> List[Dict[str, str]]:
        """Fallback search using httpx directly."""
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml",
            }
            resp = await client.get(
                f"https://cn.bing.com/search?q={quote(query, safe='')}&setlang=zh-CN",
                headers=headers,
                follow_redirects=True,
            )
            return self._parse_bing_html(resp.text, num_results)

    def _parse_bing_html(self, html: str, num_results: int) -> List[Dict[str, str]]:
        """Parse Bing search results from HTML."""
        results: List[Dict[str, str]] = []

        # Split by result blocks
        parts = html.split('li class="b_algo"')
        if len(parts) < 2:
            return results

        for block in parts[1:num_results + 1]:
            # Extract title and URL from <h2><a href="...">title</a></h2>
            h2_links = re.findall(
                r'<h2[^>]*><a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a></h2>',
                block,
                re.DOTALL,
            )
            if not h2_links:
                continue

            url = h2_links[0][0]
            title = self._clean_html(h2_links[0][1])

            # Skip CSS/asset URLs
            if not url or "://" not in url or url.startswith("https://r.bing.com"):
                continue

            # Clean URL: strip CSS/analytics params
            url = re.sub(r"\?.*", "", url)

            # Extract snippet from <p class="b_lineclamp...">...</p>
            p_snippets = re.findall(
                r'<p[^>]*class="[^"]*b_lineclamp[234][^"]*"[^>]*>(.*?)</p>',
                block,
                re.DOTALL,
            )
            snippet = ""
            if p_snippets:
                snippet = self._clean_html(p_snippets[0])

            results.append({
                "title": title,
                "url": url,
                "snippet": snippet,
            })

        return results

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and decode entities from text."""
        if not text:
            return ""
        # Remove HTML tags
        text = self._html_clean.sub("", text)
        # Decode common HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&ensp;", " ")
        text = text.replace("&#0183;", "·")
        text = text.replace("&hellip;", "…")
        return text.strip()

    async def close(self):
        pass  # curl subprocess handles its own lifecycle


# Singleton
_search_service: Optional[WebSearchService] = None


def get_search_service() -> WebSearchService:
    global _search_service
    if _search_service is None:
        _search_service = WebSearchService()
    return _search_service
