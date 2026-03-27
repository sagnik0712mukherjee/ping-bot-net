import os
import json
import requests
from datetime import datetime, timedelta
from langchain_community.tools import DuckDuckGoSearchRun
from crewai.tools import tool
from typing import List, Dict, Optional
from urllib.parse import quote

@tool("MultiSourceSearch")
def multi_source_search(query: str, hours_back: int = 96, top_k: int = 10) -> str:
    """
    Search for information across multiple sources including DuckDuckGo, Bing, and Reddit.
    Returns the latest articles about the query from the last N hours.
    
    Args:
        query (str): The search query (e.g., "Pritam Chakraborty")
        hours_back (int): How many hours back to search (default: 96)
        top_k (int): Maximum number of results per source (default: 10)
        
    Return:
        JSON string containing structured search results with URLs and metadata
    """
    try:
        all_results = []
        
        # 1. DuckDuckGo Search
        print(f"[SEARCH] Searching DuckDuckGo for: {query}")
        ddg_results = _search_duckduckgo(query, top_k)
        all_results.extend(ddg_results)
        
        # 2. Bing Search (basic web search)
        print(f"[SEARCH] Searching Bing for: {query}")
        bing_results = _search_bing(query, top_k)
        all_results.extend(bing_results)
        
        # 3. Reddit Search
        print(f"[SEARCH] Searching Reddit for: {query}")
        reddit_results = _search_reddit(query, top_k, hours_back)
        all_results.extend(reddit_results)
        
        # Remove duplicates and sort by date
        unique_results = _deduplicate_results(all_results)
        sorted_results = sorted(unique_results, key=lambda x: x.get("published_date", ""), reverse=True)
        
        # Keep only top_k results
        final_results = sorted_results[:top_k]
        
        result_json = json.dumps(final_results, indent=2, default=str)
        return result_json
        
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})


def _search_duckduckgo(query: str, top_k: int) -> List[Dict]:
    """Search using DuckDuckGo API"""
    try:
        ddg = DuckDuckGoSearchRun()
        results_text = ddg.run(f"{query} last 96 hours")
        
        # Parse DuckDuckGo results
        results = []
        lines = results_text.split('\n')
        
        for line in lines[:top_k * 3]:  # Process more lines than needed
            if line.strip():
                results.append({
                    "source": "DuckDuckGo",
                    "title": line[:100],
                    "snippet": line,
                    "url": "",  # DDG doesn't return direct URLs in this format
                    "published_date": datetime.now().isoformat(),
                    "search_quality": "snippet_only"
                })
        
        return results[:top_k]
    except Exception as e:
        print(f"[DuckDuckGo Error] {str(e)}")
        return []


def _search_bing(query: str, top_k: int) -> List[Dict]:
    """Search using Bing Search API (public endpoint)"""
    try:
        # Using Bing search via public endpoint (no API key required)
        search_url = "https://www.bing.com/search"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        params = {
            'q': f"{query} last 96 hours",
            'count': top_k
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        results = []
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find search results
            for result in soup.find_all('li', class_='b_algo')[:top_k]:
                try:
                    title_elem = result.find('h2')
                    link_elem = result.find('a')
                    snippet_elem = result.find('p')
                    
                    if title_elem and link_elem:
                        results.append({
                            "source": "Bing",
                            "title": title_elem.get_text()[:100],
                            "url": link_elem.get('href', ''),
                            "snippet": snippet_elem.get_text()[:200] if snippet_elem else "",
                            "published_date": datetime.now().isoformat(),
                            "search_quality": "full_result"
                        })
                except:
                    continue
        
        return results[:top_k]
    except Exception as e:
        print(f"[Bing Error] {str(e)}")
        return []


def _search_reddit(query: str, top_k: int, hours_back: int = 96) -> List[Dict]:
    """Search Reddit for discussions (free endpoint, no API key needed)"""
    try:
        # Using Reddit's pushshift equivalent or direct search
        search_url = "https://reddit.com/search"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Search with JSON response
        json_url = f"https://reddit.com/search.json"
        params = {
            'q': query,
            'sort': 'new',
            'time': 'day' if hours_back <= 96 else 'week',
            'limit': top_k
        }
        
        response = requests.get(json_url, headers=headers, params=params, timeout=10)
        results = []
        
        if response.status_code == 200:
            data = response.json()
            for post in data.get('data', {}).get('children', [])[:top_k]:
                try:
                    post_data = post.get('data', {})
                    results.append({
                        "source": "Reddit",
                        "title": post_data.get('title', '')[:100],
                        "url": f"https://reddit.com{post_data.get('permalink', '')}",
                        "snippet": post_data.get('selftext', '')[:200],
                        "subreddit": post_data.get('subreddit', ''),
                        "upvotes": post_data.get('ups', 0),
                        "published_date": datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
                        "search_quality": "full_result"
                    })
                except:
                    continue
        
        return results[:top_k]
    except Exception as e:
        print(f"[Reddit Error] {str(e)}")
        return []


def _deduplicate_results(results: List[Dict]) -> List[Dict]:
    """Remove duplicate results based on title/URL similarity"""
    seen_urls = set()
    seen_titles = set()
    unique = []
    
    for result in results:
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        
        # Skip if URL or title already seen
        if url and url in seen_urls:
            continue
        if title and title in seen_titles:
            continue
        
        unique.append(result)
        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)
    
    return unique
