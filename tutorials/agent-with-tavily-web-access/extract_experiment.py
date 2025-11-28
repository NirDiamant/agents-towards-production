"""
Experiment: Extract structured content from ASTM standard pages.
Tests Tavily extract() and custom parsing approaches.
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Test URLs - known standard pages
TEST_URLS = [
    "https://store.astm.org/a0105_a0105m-21.html",
    "https://store.astm.org/a0106_a0106m-22.html",
    "https://store.astm.org/a0182_a0182m-23.html",
    "https://store.astm.org/a0193_a0193m-25.html",
    "https://store.astm.org/a0961_a0961m-25a.html",
]

# Content markers to identify sections
EXCLUDE_PATTERNS = [
    r"JavaScript seems to be disabled",
    r"ASTM License Agreement",
    r"IMPORTANT- READ THESE TERMS",
    r"Shipping and Handling",
    r"Domestic Shipping",
    r"International.*Shipping",
    r"Why Redline\?",
    r"Order Total.*Fee",
    r"Copyright © 1996",
    r"About ASTM Overview",
    r"Sign in to use Tracker",
    r"ASTM Compass",
    r"Not registered\?",
]


def parse_designation(filename: str) -> str:
    """
    Parse ASTM/ASME designation from filename.
    Examples:
      a0105_a0105m-21 -> A105/A105M-21
      sa0105_sa0105m-21 -> SA105/SA105M-21
    """
    # Pattern: prefix + number + underscore + prefix + number + hyphen + year
    match = re.match(r"([a-z]+)0*(\d+)_([a-z]+)0*(\d+[a-z]?)-(\d+[a-z]?)", filename, re.I)
    if match:
        p1, n1, p2, n2, year = match.groups()
        return f"{p1.upper()}{n1}/{p2.upper()}{n2}-{year}"
    return filename.upper()


def extract_structured_content(raw_content: str, url: str, tavily_title: str = "") -> dict:
    """Parse raw Tavily content into structured fields."""

    filename = url.split("/")[-1].replace(".html", "")

    result = {
        "url": url,
        "filename": filename,
        "designation": parse_designation(filename),
        "title": None,
        "standard_type": "ASTM" if not filename.lower().startswith("sa") else "ASME",
        "status_badge": "Active",  # Default assumption; could parse if available
        "abstract": None,
        "scope": None,
        "body_content": None,
        "raw_content_length": len(raw_content),
        "extraction_notes": [],
    }

    # Use Tavily's title - it's reliable
    if tavily_title:
        # Parse: "A105/A105M Standard Specification for Carbon Steel..."
        title_match = re.match(r"[\w/\-]+\s+(Standard\s+.+)", tavily_title, re.I)
        if title_match:
            result["title"] = title_match.group(1).strip()
        else:
            result["title"] = tavily_title

    # Clean content - remove navigation, footer, license
    lines = raw_content.split("\n")
    clean_lines = []
    in_excluded_section = False

    for line in lines:
        skip = False
        for pattern in EXCLUDE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                skip = True
                in_excluded_section = True
                break

        if "Abstract" in line or "Scope" in line:
            in_excluded_section = False

        if not skip and not in_excluded_section:
            clean_lines.append(line)

    clean_content = "\n".join(clean_lines)

    # Extract Abstract
    abstract_match = re.search(r"Abstract\s*\n(.+?)(?=\nScope|\n#|\n\*\*|\Z)", clean_content, re.DOTALL)
    if abstract_match:
        result["abstract"] = abstract_match.group(1).strip()

    # Extract Scope
    scope_match = re.search(r"Scope\s*\n(.+?)(?=\n####|\n#|\n\*\*Why|\Z)", clean_content, re.DOTALL)
    if scope_match:
        result["scope"] = scope_match.group(1).strip()

    # Store cleaned body content
    result["body_content"] = clean_content.strip()

    return result


def save_markdown_file(filename: str, body_content: str, designation: str, title: str, url: str) -> Path:
    """Save cleaned body content as a Markdown file with header."""
    md_path = OUTPUT_DIR / f"{filename}.md"

    # Create markdown with source URL comment and header
    source_comment = f"<!-- Source: {url} -->\n\n"
    header = f"# {designation}\n\n"
    if title:
        header += f"**{title}**\n\n---\n\n"

    md_content = source_comment + header + (body_content or "")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return md_path


def main():
    print("="*60)
    print("🧪 ASTM Content Extraction Experiment")
    print("="*60)

    # Limit to 5 pages as requested
    test_urls = TEST_URLS[:5]
    results = []
    errors = []  # Track failed extractions

    for i, url in enumerate(test_urls, 1):
        print(f"\n[{i}/{len(test_urls)}] Extracting: {url.split('/')[-1]}")

        try:
            response = tavily_client.extract(urls=[url])

            if response and "results" in response and len(response["results"]) > 0:
                for r in response["results"]:
                    raw = r.get("raw_content", "")
                    tavily_title = r.get("title", "")

                    if not raw or len(raw.strip()) < 100:
                        error_msg = "Empty or insufficient content returned"
                        print(f"  ✗ {error_msg}")
                        errors.append({"url": url, "error": error_msg})
                        continue

                    structured = extract_structured_content(raw, url, tavily_title)

                    # Save markdown file
                    md_path = save_markdown_file(
                        structured["filename"],
                        structured["body_content"],
                        structured["designation"],
                        structured["title"],
                        url
                    )
                    structured["markdown_file"] = f"output/{structured['filename']}.md"

                    results.append(structured)

                    # Print summary
                    print(f"  ✓ Designation: {structured['designation']}")
                    print(f"  ✓ Title: {structured['title'][:60]}..." if structured['title'] else "  ✗ No title")
                    print(f"  ✓ Abstract: {len(structured['abstract'] or '')} chars")
                    print(f"  ✓ Scope: {len(structured['scope'] or '')} chars")
                    print(f"  ✓ Body: {len(structured['body_content'] or '')} chars")
                    print(f"  ✓ Markdown: {md_path.name}")
            else:
                error_msg = "No results returned from Tavily"
                print(f"  ✗ {error_msg}")
                errors.append({"url": url, "error": error_msg})

        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ Exception: {error_msg}")
            errors.append({"url": url, "error": error_msg})

    # Save JSON results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"extraction_experiment_{timestamp}.json"

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_attempted": len(test_urls),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"  ✓ Successful: {len(results)}/{len(test_urls)}")
    print(f"  ✗ Failed: {len(errors)}/{len(test_urls)}")
    print(f"\n💾 JSON saved to: {output_file}")
    print(f"💾 Markdown files saved to: {OUTPUT_DIR}/")

    # Print error report
    if errors:
        print(f"\n{'='*60}")
        print(f"❌ ERROR REPORT")
        print(f"{'='*60}")
        for err in errors:
            print(f"  URL: {err['url']}")
            print(f"  Error: {err['error']}")
            print()

    return results, errors


if __name__ == "__main__":
    main()

