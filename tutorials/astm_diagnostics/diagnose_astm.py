"""
ASTM Store Diagnostics Script
Investigates why Tavily isn't finding .html links on https://store.astm.org/

Tests performed:
1. Raw HTTP response analysis
2. JavaScript/dynamic content detection  
3. BeautifulSoup link extraction
4. Tavily API method comparison
5. Anti-bot protection detection
"""

import os
import sys
import json
import logging
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Setup logging
LOG_DIR = Path(__file__).parent
LOG_FILE = LOG_DIR / "diagnostics.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / "agent-with-tavily-web-access" / ".env"
load_dotenv(env_path)

# Constants
TARGET_URL = "https://store.astm.org/"
KNOWN_HTML_PAGE = "https://store.astm.org/a0105_a0105m-21.html"

# Headers to mimic a real browser
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


def log_section(title: str):
    """Print a section header."""
    border = "=" * 70
    logger.info("")
    logger.info(border)
    logger.info(f"  {title}")
    logger.info(border)


def test_1_raw_http_response():
    """Test 1: Fetch homepage and analyze raw HTTP response."""
    log_section("TEST 1: Raw HTTP Response Analysis")
    
    try:
        # Test without browser headers
        logger.info("Fetching homepage WITHOUT browser headers...")
        resp_no_headers = requests.get(TARGET_URL, timeout=30)
        logger.info(f"  Status (no headers): {resp_no_headers.status_code}")
        logger.info(f"  Content-Length: {len(resp_no_headers.content)} bytes")
        
        # Test with browser headers
        logger.info("\nFetching homepage WITH browser headers...")
        resp_with_headers = requests.get(TARGET_URL, headers=BROWSER_HEADERS, timeout=30)
        logger.info(f"  Status (with headers): {resp_with_headers.status_code}")
        logger.info(f"  Content-Length: {len(resp_with_headers.content)} bytes")
        
        # Check for redirects
        if resp_with_headers.history:
            logger.info(f"  Redirects: {[r.url for r in resp_with_headers.history]}")
        
        # Save raw HTML for inspection
        html_file = LOG_DIR / "homepage_raw.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(resp_with_headers.text)
        logger.info(f"  Raw HTML saved to: {html_file}")
        
        return resp_with_headers
        
    except Exception as e:
        logger.error(f"  Error: {e}")
        return None


def test_2_javascript_detection(html_content: str):
    """Test 2: Detect JavaScript-based dynamic content loading."""
    log_section("TEST 2: JavaScript/Dynamic Content Detection")
    
    indicators = {
        'RequireJS': 'require.js' in html_content or 'requirejs' in html_content.lower(),
        'jQuery': 'jquery' in html_content.lower(),
        'Angular': 'ng-app' in html_content or 'angular' in html_content.lower(),
        'React': 'react' in html_content.lower() or '_reactRoot' in html_content,
        'Vue.js': 'vue' in html_content.lower() or 'v-app' in html_content,
        'AJAX patterns': 'XMLHttpRequest' in html_content or 'fetch(' in html_content,
        'data-* attributes': bool(re.search(r'data-[a-z]+=', html_content)),
        'Okta Auth': 'okta' in html_content.lower(),
        'Dynamic imports': 'import(' in html_content or 'define(' in html_content,
    }
    
    logger.info("JavaScript framework detection:")
    for name, detected in indicators.items():
        status = "✅ DETECTED" if detected else "❌ Not found"
        logger.info(f"  {name}: {status}")
    
    # Check for script tags
    soup = BeautifulSoup(html_content, 'html.parser')
    scripts = soup.find_all('script')
    logger.info(f"\nTotal <script> tags found: {len(scripts)}")
    
    external_scripts = [s.get('src') for s in scripts if s.get('src')]
    logger.info(f"External scripts: {len(external_scripts)}")
    for src in external_scripts[:10]:
        logger.info(f"  - {src}")
    
    return indicators


def test_3_beautifulsoup_links(html_content: str):
    """Test 3: Extract all links using BeautifulSoup."""
    log_section("TEST 3: BeautifulSoup Link Extraction")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all anchor tags
    all_links = soup.find_all('a', href=True)
    logger.info(f"Total <a> tags with href: {len(all_links)}")
    
    # Categorize links
    html_links = []
    internal_links = []
    external_links = []
    
    for a in all_links:
        href = a.get('href', '')
        if href.endswith('.html'):
            html_links.append(href)
        if href.startswith('/') or 'store.astm.org' in href:
            internal_links.append(href)
        elif href.startswith('http'):
            external_links.append(href)
    
    logger.info(f"\n.html links found: {len(html_links)}")
    for link in html_links[:20]:
        logger.info(f"  - {link}")
    
    logger.info(f"\nInternal links: {len(internal_links)}")
    logger.info(f"External links: {len(external_links)}")
    
    # Save all links to file
    links_file = LOG_DIR / "extracted_links.json"
    with open(links_file, 'w', encoding='utf-8') as f:
        json.dump({
            'html_links': html_links,
            'internal_links': internal_links[:50],
            'external_links': external_links[:20]
        }, f, indent=2)
    logger.info(f"\nAll links saved to: {links_file}")

    return html_links


def test_4_tavily_methods():
    """Test 4: Compare Tavily's different API methods."""
    log_section("TEST 4: Tavily API Method Comparison")

    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_key:
        logger.error("TAVILY_API_KEY not found!")
        return

    from tavily import TavilyClient
    client = TavilyClient(api_key=tavily_key)

    results = {}

    # Test 4a: Search for ASTM standards
    logger.info("\n4a. Testing tavily.search()...")
    try:
        search_result = client.search(
            query="ASTM A105 standard site:store.astm.org",
            max_results=10
        )
        results['search'] = search_result
        if 'results' in search_result:
            logger.info(f"  Found {len(search_result['results'])} results")
            for r in search_result['results'][:5]:
                logger.info(f"    - {r.get('url', 'N/A')}")
    except Exception as e:
        logger.error(f"  Search error: {e}")

    # Test 4b: Extract from known working URL
    logger.info("\n4b. Testing tavily.extract() on known .html page...")
    try:
        extract_result = client.extract(urls=[KNOWN_HTML_PAGE])
        results['extract'] = extract_result
        if 'results' in extract_result:
            logger.info(f"  Extracted {len(extract_result['results'])} pages")
            for r in extract_result['results']:
                content_preview = r.get('raw_content', '')[:200]
                logger.info(f"    URL: {r.get('url')}")
                logger.info(f"    Content preview: {content_preview}...")
    except Exception as e:
        logger.error(f"  Extract error: {e}")

    # Test 4c: Map the homepage
    logger.info("\n4c. Testing tavily.map() on homepage...")
    try:
        map_result = client.map(url=TARGET_URL)
        results['map'] = map_result

        # Handle different response formats
        urls = []
        if isinstance(map_result, dict) and 'results' in map_result:
            urls = map_result['results']
        elif isinstance(map_result, list):
            urls = map_result

        logger.info(f"  Found {len(urls)} URLs")
        html_urls = [u for u in urls if isinstance(u, str) and u.endswith('.html')]
        logger.info(f"  .html URLs: {len(html_urls)}")
        for u in html_urls[:10]:
            logger.info(f"    - {u}")
    except Exception as e:
        logger.error(f"  Map error: {e}")

    # Test 4d: Crawl with limited depth
    logger.info("\n4d. Testing tavily.crawl() with depth=1...")
    try:
        crawl_result = client.crawl(
            url=TARGET_URL,
            max_depth=1,
            max_breadth=20,
            limit=20
        )
        results['crawl'] = crawl_result

        if 'results' in crawl_result:
            logger.info(f"  Crawled {len(crawl_result['results'])} pages")
            for r in crawl_result['results'][:10]:
                logger.info(f"    - {r.get('url', 'N/A')}")
    except Exception as e:
        logger.error(f"  Crawl error: {e}")

    # Save all results
    tavily_file = LOG_DIR / "tavily_results.json"
    with open(tavily_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"\nTavily results saved to: {tavily_file}")

    return results


def test_5_antibot_detection():
    """Test 5: Check for anti-bot protections."""
    log_section("TEST 5: Anti-Bot Protection Detection")

    try:
        resp = requests.get(TARGET_URL, headers=BROWSER_HEADERS, timeout=30)

        # Check response headers
        logger.info("Response Headers Analysis:")
        suspicious_headers = ['cf-ray', 'cf-cache-status', 'x-sucuri', 'x-cdn',
                            'x-firewall', 'server', 'x-powered-by']

        for header in suspicious_headers:
            value = resp.headers.get(header)
            if value:
                logger.info(f"  {header}: {value}")

        # Check for Cloudflare
        if 'cf-ray' in resp.headers:
            logger.warning("  ⚠️ CLOUDFLARE DETECTED - May block automated requests")

        # Check for common anti-bot patterns in HTML
        html = resp.text.lower()
        antibot_patterns = {
            'Cloudflare challenge': 'cf-browser-verification' in html,
            'reCAPTCHA': 'recaptcha' in html,
            'hCaptcha': 'hcaptcha' in html,
            'Bot detection JS': 'bot-detection' in html or 'antibot' in html,
            'JavaScript challenge': 'javascript is required' in html,
            'Cookie consent blocking': 'cookie' in html and 'consent' in html,
        }

        logger.info("\nAnti-bot pattern detection:")
        for name, detected in antibot_patterns.items():
            status = "⚠️ DETECTED" if detected else "✅ Not found"
            logger.info(f"  {name}: {status}")

        # Check robots.txt
        logger.info("\nChecking robots.txt...")
        robots_resp = requests.get("https://store.astm.org/robots.txt",
                                   headers=BROWSER_HEADERS, timeout=10)
        if robots_resp.status_code == 200:
            logger.info("  robots.txt found:")
            for line in robots_resp.text.split('\n')[:15]:
                if line.strip():
                    logger.info(f"    {line}")
        else:
            logger.info(f"  robots.txt status: {robots_resp.status_code}")

    except Exception as e:
        logger.error(f"  Error: {e}")


def test_6_known_page_analysis():
    """Test 6: Analyze the known working .html page structure."""
    log_section("TEST 6: Known .html Page Analysis")

    try:
        logger.info(f"Fetching known page: {KNOWN_HTML_PAGE}")
        resp = requests.get(KNOWN_HTML_PAGE, headers=BROWSER_HEADERS, timeout=30)
        logger.info(f"  Status: {resp.status_code}")
        logger.info(f"  Content-Length: {len(resp.content)} bytes")

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Find links to other .html pages
            all_links = soup.find_all('a', href=True)
            html_links = [a['href'] for a in all_links if a['href'].endswith('.html')]

            logger.info(f"\n  Links to other .html pages: {len(html_links)}")
            for link in html_links[:10]:
                logger.info(f"    - {link}")

            # Save the page
            page_file = LOG_DIR / "known_page.html"
            with open(page_file, 'w', encoding='utf-8') as f:
                f.write(resp.text)
            logger.info(f"\n  Page saved to: {page_file}")

    except Exception as e:
        logger.error(f"  Error: {e}")


def generate_recommendations(js_indicators: dict, html_links: list):
    """Generate recommendations based on findings."""
    log_section("RECOMMENDATIONS")

    issues = []
    recommendations = []

    # Check for JavaScript rendering
    if js_indicators.get('RequireJS') or js_indicators.get('Dynamic imports'):
        issues.append("Site uses RequireJS/dynamic module loading")
        recommendations.append("Use a headless browser (Playwright/Selenium) to render JavaScript")

    if js_indicators.get('Okta Auth'):
        issues.append("Site uses Okta authentication")
        recommendations.append("May need to authenticate or use session cookies")

    if len(html_links) == 0:
        issues.append("No .html links found in initial HTML")
        recommendations.append("Links are likely loaded dynamically via JavaScript")
        recommendations.append("Try using Tavily search with 'site:store.astm.org .html' query")
        recommendations.append("Consider scraping sitemap.xml if available")

    # General recommendations
    recommendations.append("Use Tavily search() to find .html pages instead of crawl()")
    recommendations.append("Search for specific ASTM standards by name/number")
    recommendations.append("Check if store.astm.org/sitemap.xml exists")

    logger.info("IDENTIFIED ISSUES:")
    for i, issue in enumerate(issues, 1):
        logger.info(f"  {i}. {issue}")

    logger.info("\nRECOMMENDATIONS:")
    for i, rec in enumerate(recommendations, 1):
        logger.info(f"  {i}. {rec}")


def main():
    """Run all diagnostic tests."""
    logger.info("=" * 70)
    logger.info("  ASTM STORE DIAGNOSTICS")
    logger.info(f"  Started: {datetime.now().isoformat()}")
    logger.info("=" * 70)

    # Run tests
    response = test_1_raw_http_response()

    if response:
        html_content = response.text
        js_indicators = test_2_javascript_detection(html_content)
        html_links = test_3_beautifulsoup_links(html_content)
    else:
        js_indicators = {}
        html_links = []

    test_4_tavily_methods()
    test_5_antibot_detection()
    test_6_known_page_analysis()

    generate_recommendations(js_indicators, html_links)

    log_section("DIAGNOSTICS COMPLETE")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Run completed: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()

