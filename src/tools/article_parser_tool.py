import requests
from crewai.tools import tool
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
from typing import Dict, Optional
import json
import re

# Pritam's famous works that can be tracked even without his name
PRITAM_FAMOUS_WORKS = {
    "songs": [
        "Tu Hi Disda"
    ],
    "albums": ["Bhoot Bangla", "Ae Dil Hai Mushkil"],
    "movies": ["Bhoot Bangla", "Ae Dil Hai Mushkil"]
}

@tool("ArticleParser")
def parse_article_metadata(url: str) -> str:
    """
    Fetch and extract article metadata including title, publish date, content snippet,
    and keywords from a given URL.
    
    Args:
        url (str): The URL to parse
        
    Return:
        JSON string containing extracted metadata
    """
    try:
        if not url or not url.startswith(('http://', 'https://')):
            return json.dumps({"error": f"Invalid URL: {url}"})
        
        metadata = _extract_article_metadata(url)
        return json.dumps(metadata, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to parse URL {url}: {str(e)}"})


def _extract_article_metadata(url: str) -> Dict:
    """Extract metadata from article URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = _extract_title(soup)
        
        # Extract publish date
        publish_date = _extract_publish_date(soup, url)
        
        # Extract content snippet
        content = _extract_content(soup)
        
        # Extract image (optional)
        image_url = _extract_image(soup)
        
        # Detect if article contains controversy keywords
        is_controversial = _detect_controversy(soup, title + " " + content)
        
        # Detect if article is about one of Pritam's works (songs/albums/movies) even without his name
        is_pritam_work = _is_pritam_work_mentioned(title + " " + content)
        
        return {
            "url": url,
            "title": title,
            "publish_date": publish_date,
            "publish_date_formatted": publish_date.strftime("%Y-%m-%d %H:%M:%S") if publish_date else "Unknown",
            "content_snippet": content[:300],
            "full_content": content[:1000],
            "image_url": image_url,
            "is_controversial": is_controversial,
            "is_pritam_work": is_pritam_work,  # NEW: Track if about Pritam's works even without name
            "extraction_success": True
        }
        
    except Exception as e:
        print(f"[Parser Error] {str(e)}")
        return {
            "url": url,
            "error": str(e),
            "extraction_success": False
        }


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract article title from various possible locations"""
    
    # Try meta og:title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title.get('content')
    
    # Try meta description as fallback
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        return meta_desc.get('content')
    
    # Try h1 tag
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)
    
    # Try title tag
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text(strip=True)
    
    return "No title found"


def _extract_publish_date(soup: BeautifulSoup, url: str) -> Optional[datetime]:
    """Extract publish date from various sources in HTML"""
    
    # Try meta article:published_time
    published_meta = soup.find('meta', attrs={'property': 'article:published_time'})
    if published_meta and published_meta.get('content'):
        try:
            return date_parser.parse(published_meta.get('content'))
        except:
            pass
    
    # Try meta datePublished
    date_published = soup.find('meta', attrs={'itemprop': 'datePublished'})
    if date_published and date_published.get('content'):
        try:
            return date_parser.parse(date_published.get('content'))
        except:
            pass
    
    # Try time tag with datetime attribute
    time_tag = soup.find('time', attrs={'datetime': True})
    if time_tag and time_tag.get('datetime'):
        try:
            return date_parser.parse(time_tag.get('datetime'))
        except:
            pass
    
    # Try common date patterns in text
    date_patterns = [
        r'Published.*?(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        r'Updated.*?(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        r'(\d{1,2}-\d{1,2}-\d{4})',
        r'(\d{4}-\d{1,2}-\d{1,2})',
    ]
    
    page_text = soup.get_text()
    for pattern in date_patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            try:
                return date_parser.parse(match.group(1))
            except:
                pass
    
    return None


def _extract_content(soup: BeautifulSoup) -> str:
    """Extract main article content"""
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Try article tag
    article = soup.find('article')
    if article:
        return article.get_text(separator=' ', strip=True)[:500]
    
    # Try div with id or class containing 'content', 'article', 'post'
    for div_class in ['content', 'article', 'post', 'entry', 'main']:
        div = soup.find('div', class_=re.compile(div_class, re.I))
        if div:
            return div.get_text(separator=' ', strip=True)[:500]
    
    # Try paragraphs
    paragraphs = soup.find_all('p')
    if paragraphs:
        return ' '.join([p.get_text(strip=True) for p in paragraphs[:3]])
    
    # Fallback to body text
    body = soup.find('body')
    if body:
        return body.get_text(separator=' ', strip=True)[:500]
    
    return "No content found"


def _extract_image(soup: BeautifulSoup) -> Optional[str]:
    """Extract featured image URL"""
    
    # Try og:image
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        return og_image.get('content')
    
    # Try article image
    img_meta = soup.find('meta', attrs={'itemprop': 'image'})
    if img_meta and img_meta.get('content'):
        return img_meta.get('content')
    
    # Try first large image in article
    images = soup.find_all('img')
    if images:
        for img in images:
            if img.get('src'):
                return img.get('src')
    
    return None


def _detect_controversy(text: str, additional_text: str = "") -> bool:
    """Detect if article contains controversy-related keywords"""
    
    controversy_keywords = [
        'controversy', 'scandal', 'controversy', 'allegation', 'accused',
        'criticize', 'criticism', 'plagiarism', 'plagiarized', 'exposed',
        'controversy', 'dispute', 'conflict', 'arrest', 'legal',
        'lawsuit', 'complaint', 'negative', 'failed', 'controversy',
        'controversy', 'backlash', 'outrage', 'banned', 'banned',
        'controversial', 'controversial', 'controversial'
    ]
    
    combined_text = (text + " " + additional_text).lower()
    
    for keyword in controversy_keywords:
        if keyword.lower() in combined_text:
            return True
    
    return False


def _is_pritam_work_mentioned(text: str) -> bool:
    """
    Detect if article is about one of Pritam's famous works (songs, albums, movies)
    even if his name is not explicitly mentioned.
    
    Returns:
        bool: True if any of Pritam's works are mentioned in the text
    """
    text_lower = text.lower()
    
    # Check all songs, albums, and movies
    all_works = (
        PRITAM_FAMOUS_WORKS["songs"] + 
        PRITAM_FAMOUS_WORKS["albums"] + 
        PRITAM_FAMOUS_WORKS["movies"]
    )
    
    for work in all_works:
        # Case-insensitive search for the work name
        if work.lower() in text_lower:
            return True
    
    return False
