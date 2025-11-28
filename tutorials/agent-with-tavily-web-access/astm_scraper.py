"""
ASTM/ASME Standards Store Scraper using Tavily Search API

Uses Tavily's search() method to discover .html standard pages on store.astm.org.
This approach was chosen after diagnostics revealed that:
- crawl() and map() don't find .html pages (Next.js dynamic rendering)
- search() successfully discovers standard pages via indexed content

Supports both naming conventions:
- ASTM format: a0105_a0105m-21.html (lowercase 'a')
- ASME format: sa0105_sa0105m-21.html (lowercase 'sa')

Outputs:
- astm_directory_*.json: Complete catalog of all .html links found
- astm_extracted_*.json: Full content from first 10 pages only
"""

import os
import json
import re
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment variables
load_dotenv()

# Validate API keys
if not os.environ.get("TAVILY_API_KEY"):
    raise ValueError("TAVILY_API_KEY not found in environment variables")

# Initialize Tavily client
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Target site
TARGET_SITE = "store.astm.org"
TARGET_URL = f"https://{TARGET_SITE}/"

# Output directory
OUTPUT_DIR = Path(__file__).parent / "output"

# ASTM Series (A through G) - covers most engineering standards
ASTM_SERIES = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

# Common standard numbers to search for (covers a wide range)
STANDARD_PREFIXES = [
    # Common ASTM standards
    'A105', 'A106', 'A182', 'A193', 'A194', 'A216', 'A234', 'A312', 'A333', 'A350',
    'A351', 'A352', 'A403', 'A420', 'A479', 'A500', 'A513', 'A516', 'A519', 'A536',
    'B16', 'B31', 'B36', 'B61', 'B62', 'B148', 'B150', 'B151', 'B152', 'B209',
    'C150', 'C260', 'C270', 'C476', 'C595', 'C618', 'C1157',
    'D256', 'D638', 'D695', 'D790', 'D882', 'D1002', 'D1238', 'D2240',
    'E8', 'E10', 'E18', 'E21', 'E23', 'E45', 'E92', 'E94', 'E112', 'E140', 'E165',
    'F436', 'F593', 'F594', 'F788', 'F844', 'F1554', 'F3125',
    'G1', 'G4', 'G5', 'G31', 'G48', 'G61',
]

# Maximum pages to extract full content (to avoid long processing)
MAX_EXTRACT_PAGES = 10



def is_html_standard_page(url: str) -> bool:
    """Check if URL is a valid .html standard page."""
    if not url.endswith('.html'):
        return False
    if TARGET_SITE not in url:
        return False
    # Filter out non-standard pages
    exclude_patterns = ['products-services', 'bos-standards', 'checkout', 'customer', 'cart']
    return not any(p in url.lower() for p in exclude_patterns)


def extract_standard_info(url: str) -> dict:
    """
    Extract metadata from ASTM/ASME standard URL.
    Examples:
    - https://store.astm.org/a0105_a0105m-21.html (ASTM)
    - https://store.astm.org/sa0105_sa0105m-21.html (ASME)
    """
    filename = url.split('/')[-1].replace('.html', '')

    # Detect standard type and series
    if filename.lower().startswith('sa'):
        # ASME standard (SA prefix)
        pattern = re.match(r'^sa(\d+)', filename, re.IGNORECASE)
        std_type = "ASME"
        series = "SA"
    else:
        # ASTM standard (single letter prefix)
        pattern = re.match(r'^([a-z])(\d+)', filename, re.IGNORECASE)
        std_type = "ASTM"
        series = pattern.group(1).upper() if pattern else "Unknown"

    return {
        "url": url,
        "filename": filename,
        "standard_id": filename.upper().replace('_', '/'),
        "type": std_type,
        "series": series,
        "category": f"{std_type} {series} Series"
    }


def search_standards(query: str, max_results: int = 20) -> list[dict]:
    """
    Search for standards using Tavily search API.
    Returns list of search results with URL, title, and content snippet.
    """
    try:
        result = tavily_client.search(
            query=query,
            max_results=max_results,
            include_domains=[TARGET_SITE]
        )
        if result and 'results' in result:
            return result['results']
    except Exception as e:
        print(f"  ⚠️ Search error for '{query}': {e}")
    return []


def build_directory() -> dict:
    """
    Build comprehensive directory of all .html standard pages.
    Uses multiple search queries to discover as many pages as possible.
    """
    print(f"\n{'='*60}")
    print("🔍 Building Standards Directory using Tavily Search")
    print(f"Target: {TARGET_URL}")
    print(f"{'='*60}\n")

    discovered_urls = {}  # url -> metadata dict
    search_count = 0

    # Strategy 1: Search by ASTM series
    print("📂 Searching by ASTM series (A-G)...")
    for series in ASTM_SERIES:
        query = f"site:{TARGET_SITE} ASTM {series} standard .html"
        print(f"  Searching: ASTM {series} Series...")
        results = search_standards(query, max_results=20)

        for r in results:
            url = r.get('url', '')
            if is_html_standard_page(url) and url not in discovered_urls:
                discovered_urls[url] = {
                    **extract_standard_info(url),
                    "title": r.get('title', ''),
                    "snippet": r.get('content', '')[:200] if r.get('content') else ''
                }
        search_count += 1
        time.sleep(0.3)  # Rate limiting

    print(f"  Found {len(discovered_urls)} unique .html pages so far\n")

    # Strategy 2: Search by specific standard numbers
    print("📂 Searching by specific standard numbers...")
    for prefix in STANDARD_PREFIXES:
        # Search both ASTM and ASME variants
        for variant in [f"ASTM {prefix}", f"ASME SA{prefix[1:]}" if prefix[0] == 'A' else None]:
            if variant is None:
                continue
            query = f"site:{TARGET_SITE} {variant} .html"
            results = search_standards(query, max_results=10)

            for r in results:
                url = r.get('url', '')
                if is_html_standard_page(url) and url not in discovered_urls:
                    discovered_urls[url] = {
                        **extract_standard_info(url),
                        "title": r.get('title', ''),
                        "snippet": r.get('content', '')[:200] if r.get('content') else ''
                    }
            search_count += 1

        # Progress indicator every 10 searches
        if search_count % 20 == 0:
            print(f"  Progress: {search_count} searches, {len(discovered_urls)} unique pages found")
        time.sleep(0.2)  # Rate limiting

    print(f"\n✅ Directory complete: {len(discovered_urls)} unique .html pages")
    print(f"   Total searches performed: {search_count}")

    return {
        "timestamp": datetime.now().isoformat(),
        "target_site": TARGET_SITE,
        "total_searches": search_count,
        "total_pages": len(discovered_urls),
        "pages": list(discovered_urls.values())
    }


def extract_page_content(urls: list[str], limit: int = MAX_EXTRACT_PAGES) -> dict:
    """
    Extract full content from .html pages using Tavily extract.
    Limited to first N pages to avoid long processing times.
    """
    print(f"\n{'='*60}")
    print(f"📄 Extracting Content from First {limit} Pages")
    print(f"{'='*60}\n")

    urls_to_extract = urls[:limit]
    extracted = []

    for i, url in enumerate(urls_to_extract, 1):
        print(f"  [{i}/{len(urls_to_extract)}] Extracting: {url.split('/')[-1]}")
        try:
            result = tavily_client.extract(urls=[url])
            if result and 'results' in result:
                for r in result['results']:
                    extracted.append({
                        "url": r.get('url', url),
                        "title": r.get('title', ''),
                        "content": r.get('raw_content', ''),
                        "extracted_at": datetime.now().isoformat()
                    })
            time.sleep(0.5)  # Rate limiting for extract
        except Exception as e:
            print(f"    ⚠️ Error: {e}")
            extracted.append({
                "url": url,
                "title": "",
                "content": "",
                "error": str(e),
                "extracted_at": datetime.now().isoformat()
            })

    print(f"\n✅ Extracted content from {len(extracted)} pages")

    return {
        "timestamp": datetime.now().isoformat(),
        "total_extracted": len(extracted),
        "max_limit": limit,
        "pages": extracted
    }



def save_json(data: dict, filename: str) -> Path:
    """Save data to JSON file in output/ directory."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved: {output_path}")
    return output_path


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("🔬 ASTM/ASME Standards Scraper")
    print("="*60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 1: Build directory of all .html pages
    directory = build_directory()

    # Save directory
    dir_file = f"astm_directory_{timestamp}.json"
    save_json(directory, dir_file)

    # Step 2: Extract content from first N pages
    if directory['pages']:
        urls = [p['url'] for p in directory['pages']]
        extracted = extract_page_content(urls, limit=MAX_EXTRACT_PAGES)

        # Save extracted content
        ext_file = f"astm_extracted_{timestamp}.json"
        save_json(extracted, ext_file)
    else:
        print("\n⚠️ No .html pages found to extract.")
        extracted = None

    # Print summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"Target site: {TARGET_SITE}")
    print(f"Total searches: {directory['total_searches']}")
    print(f"Total .html pages found: {directory['total_pages']}")
    print(f"Pages with content extracted: {extracted['total_extracted'] if extracted else 0}")
    print(f"\nOutput files:")
    print(f"  📁 Directory: output/{dir_file}")
    if extracted:
        print(f"  📄 Extracted: output/{ext_file}")

    # Show sample pages
    if directory['pages']:
        print(f"\n📄 Sample pages found:")
        for i, page in enumerate(directory['pages'][:10], 1):
            print(f"  {i}. [{page['type']} {page['series']}] {page['filename']}")
        if directory['total_pages'] > 10:
            print(f"  ... and {directory['total_pages'] - 10} more")

    return directory, extracted


if __name__ == "__main__":
    main()
