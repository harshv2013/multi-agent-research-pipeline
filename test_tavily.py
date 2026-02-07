# Research for new requirements for UPSC 2026

"""
Test Tavily search integration.
"""
from tools.web_search import web_search_tool, get_search_tool

def test_search():
    """Test basic search."""
    print("\n" + "="*60)
    print("TESTING TAVILY SEARCH")
    print("="*60 + "\n")
    
    # Test search
    results = web_search_tool("benefits of meditation in 2026, what are the latest trends?", num_results=3)

    print(results)
    
    # Get stats
    tool = get_search_tool()
    stats = tool.get_stats()
    print("\n" + "-"*60)
    print("SEARCH TOOL STATISTICS")
    print("-"*60)
    print(f"Provider: {stats['provider']}")
    print(f"Cache Size: {stats['cache_size']}")
    print(f"Rate Limit: {stats['rate_limit']} requests/minute")

if __name__ == "__main__":
    test_search()