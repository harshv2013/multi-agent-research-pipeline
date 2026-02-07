"""
Web search tool using Tavily API.

Tavily provides AI-optimized search results designed for LLMs.
"""
from typing import List, Dict, Optional
import time
from dataclasses import dataclass, asdict
from datetime import datetime

from tavily import TavilyClient
from config import get_settings


@dataclass
class WebSearchResult:
    """Structured search result."""
    title: str
    url: str
    snippet: str
    source_domain: str
    timestamp: datetime
    relevance_score: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def __str__(self) -> str:
        return f"[{self.source_domain}] {self.title}\n{self.snippet}\n{self.url}"


class WebSearchTool:
    """
    Web search tool using Tavily API.
    
    Features:
    - Real-time web search
    - AI-powered relevance ranking
    - Clean, structured results
    - Automatic caching
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.tavily_api_key
        
        # Initialize Tavily client
        try:
            self.client = TavilyClient(api_key=self.api_key)
            print("✓ Tavily search initialized successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Tavily: {e}")
        
        # Cache and rate limiting
        self.cache: Dict[str, List[WebSearchResult]] = {}
        self.last_request_time = 0
        self.rate_limit = 10  # requests per minute
    
    def search(self, query: str, num_results: int = 5) -> List[WebSearchResult]:
        """
        Perform web search using Tavily.
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 10)
            
        Returns:
            List of WebSearchResult objects
        """
        # Check cache first
        cache_key = f"{query}:{num_results}"
        if cache_key in self.cache:
            print(f"✓ Using cached results for: '{query}'")
            return self.cache[cache_key]
        
        # Rate limiting
        self._enforce_rate_limit()
        
        print(f"🔍 Searching Tavily: '{query}'")
        
        try:
            # Call Tavily API
            response = self.client.search(
                query=query,
                max_results=min(num_results, 10),  # Tavily max is 10
                search_depth="advanced",  # or "basic" for faster results
                include_answer=False,  # Set True to get AI-generated answer
                include_raw_content=False,  # Set True for full page content
                include_images=False
            )
            
            # Parse results
            results = []
            for item in response.get('results', []):
                url = item.get('url', '')
                
                # Extract domain from URL
                try:
                    domain = url.split('/')[2] if len(url.split('/')) > 2 else 'unknown'
                except:
                    domain = 'unknown'
                
                result = WebSearchResult(
                    title=item.get('title', 'No title'),
                    url=url,
                    snippet=item.get('content', '')[:500],  # Limit snippet
                    source_domain=domain,
                    timestamp=datetime.now(),
                    relevance_score=item.get('score', 0.0)
                )
                results.append(result)
            
            # Cache results
            self.cache[cache_key] = results
            
            print(f"✓ Found {len(results)} results from Tavily")
            return results
            
        except Exception as e:
            print(f"❌ Tavily search failed: {e}")
            raise
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        min_interval = 60.0 / self.rate_limit
        
        if time_since_last_request < min_interval:
            sleep_time = min_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def clear_cache(self):
        """Clear search cache."""
        self.cache.clear()
        print("✓ Search cache cleared")
    
    def get_stats(self) -> Dict:
        """Get search tool statistics."""
        return {
            'cache_size': len(self.cache),
            'rate_limit': self.rate_limit,
            'provider': 'Tavily'
        }


# Singleton instance
_search_tool_instance: Optional[WebSearchTool] = None


def get_search_tool(api_key: Optional[str] = None) -> WebSearchTool:
    """Get or create search tool singleton."""
    global _search_tool_instance
    if _search_tool_instance is None:
        _search_tool_instance = WebSearchTool(api_key=api_key)
    return _search_tool_instance


def web_search_tool(query: str, num_results: int = 5) -> str:
    """
    Perform web search and return formatted results.
    
    This is the function called by agents.
    
    Args:
        query: Search query
        num_results: Number of results (default 5)
        
    Returns:
        Formatted search results as string
    """
    search_tool = get_search_tool()
    results = search_tool.search(query, num_results)
    
    if not results:
        return "No search results found."
    
    # Format results for LLM
    output = f"\nSearch Results for: '{query}'\n"
    output += f"Found {len(results)} results\n"
    output += f"Provider: Tavily (AI-optimized search)\n"
    
    for i, result in enumerate(results, 1):
        output += f"\n--- Result {i} ---\n"
        output += f"Title: {result.title}\n"
        output += f"Source: {result.source_domain}\n"
        output += f"URL: {result.url}\n"
        output += f"Summary: {result.snippet}\n"
        output += f"Relevance: {result.relevance_score:.2f}\n"
    
    return output


def fetch_webpage_content(url: str, max_length: int = 5000) -> str:
    """
    Fetch webpage content using Tavily's extract feature.
    
    Args:
        url: URL to fetch
        max_length: Maximum content length
        
    Returns:
        Extracted text content
    """
    search_tool = get_search_tool()
    
    try:
        print(f"📄 Extracting content from: {url}")
        
        # Use Tavily's extract endpoint
        response = search_tool.client.extract(urls=[url])
        
        if response and len(response.get('results', [])) > 0:
            content = response['results'][0].get('raw_content', '')
            
            if len(content) > max_length:
                content = content[:max_length] + "...[truncated]"
            
            print(f"✓ Extracted {len(content)} characters")
            return content
        else:
            return f"Could not extract content from {url}"
            
    except Exception as e:
        print(f"❌ Content extraction failed: {e}")
        return f"Error extracting content: {str(e)}"