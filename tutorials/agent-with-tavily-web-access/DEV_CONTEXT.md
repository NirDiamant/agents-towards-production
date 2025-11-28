# ASTM/ASME Standards Scraper - Development Context

## Project Overview

This project scrapes ASTM and ASME standard pages from `https://store.astm.org/` using the Tavily API.

**Goal**: Build a comprehensive directory of all available .html standard pages and extract content from them.

**Target URLs**:
- ASTM format: `https://store.astm.org/a0105_a0105m-21.html`
- ASME format: `https://store.astm.org/sa0105_sa0105m-21.html`

---

## Diagnostic Findings (2025-11-28)

### Why crawl() and map() Failed

The ASTM Store is a **Next.js/React application** with:
- Server-side rendering (SSR) with client hydration
- Dynamic content loading via JavaScript
- 92 `<script>` tags, 22 external JS files
- No `.html` links in initial HTML response

| Tavily Method | Result |
|---------------|--------|
| `map()` | Found 21 URLs, **0 .html pages** - only navigation pages |
| `crawl()` | Redirected to `www.astm.org` instead of `store.astm.org` |
| **`search()`** | ✅ **WORKS!** Found `.html` pages via indexed content |
| `extract()` | ✅ Successfully extracts content from known URLs |

### Key Insight
The `.html` pages exist and are indexed by search engines, but they're not discoverable through traditional crawling because:
1. Links are rendered dynamically via JavaScript
2. The site uses Next.js client-side routing
3. Standard pages are behind search/filter interfaces

### Anti-Bot Status
- No Cloudflare protection
- No CAPTCHA
- No rate limiting detected
- Cookie consent popup present but not blocking

---

## Current Implementation

### Approach: Search-Based Discovery

Instead of crawling, we use **Tavily search()** to discover pages:

1. **Series-based search**: `"site:store.astm.org ASTM A standard .html"`
2. **Standard-number search**: `"site:store.astm.org ASTM A105 .html"`
3. **ASME variant search**: `"site:store.astm.org ASME SA105 .html"`

### Output Files

| File | Description |
|------|-------------|
| `astm_directory_*.json` | Complete catalog of all discovered .html URLs |
| `astm_extracted_*.json` | Full content from first 10 pages only |

### Standard Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| ASTM | `[a-g]NNNN_[a-g]NNNNm-YY.html` | `a0105_a0105m-21.html` |
| ASME | `saNNNN_saNNNNm-YY.html` | `sa0105_sa0105m-21.html` |

---

## Known Limitations

1. **Search API limits**: Tavily search returns max 20 results per query
2. **Discovery gaps**: Some standards may not be indexed or may require exact queries
3. **Rate limiting**: 200-500ms delays between API calls to avoid throttling
4. **Extract costs**: Content extraction is slower and more expensive than search

---

## Files Structure

```
tutorials/agent-with-tavily-web-access/
├── .env                 # API keys (TAVILY_API_KEY, OPENAI_API_KEY)
├── astm_scraper.py      # Main scraper script
├── DEV_CONTEXT.md       # This file
└── output/              # Generated JSON files
    ├── astm_directory_*.json
    └── astm_extracted_*.json

tutorials/astm_diagnostics/
├── diagnose_astm.py     # Diagnostic script
├── diagnostics.log      # Log output
├── homepage_raw.html    # Saved homepage
├── known_page.html      # Saved sample standard page
├── extracted_links.json # Links from BeautifulSoup
└── tavily_results.json  # Raw Tavily API responses
```

---

## Next Steps / Future Improvements

1. **Expand search coverage**: Add more standard prefixes to STANDARD_PREFIXES list
2. **Sitemap parsing**: Check if `store.astm.org/sitemap.xml` exists
3. **Incremental updates**: Track previously discovered URLs to avoid duplicates
4. **Content parsing**: Extract structured data (scope, abstract, price) from extracted content
5. **Database storage**: Store results in SQLite or PostgreSQL for querying
6. **Caching**: Cache search results to reduce API costs on re-runs

---

## Running the Scraper

```bash
cd tutorials/agent-with-tavily-web-access
.venv\Scripts\activate  # Windows
python astm_scraper.py
```

Or use VS Code: **F5** → **"ASTM Scraper"**

