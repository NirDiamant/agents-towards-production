"""
Fetch ASTM standards list from la.astm.org using Tavily and save as JSON + Markdown.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

SOURCE_URL = "https://la.astm.org/standards/astm-standards-list/"

def parse_standard(line: str) -> dict:
    """Parse a single ASTM standard designation."""
    line = line.strip()
    if not line or not line.startswith("ASTM"):
        return None

    # Remove "ASTM " prefix
    code = line.replace("ASTM ", "")

    # Extract series letter (A, B, C, D, E, F, G, R, SI, ANS, ANSI, ISO)
    series_match = re.match(r"([A-Z]+)", code)
    series = series_match.group(1) if series_match else None

    # Check if it has metric designation (_XxxxxM)
    has_metric = "_" in code and "M-" in code

    return {
        "designation": line,
        "code": code,
        "series": series,
        "has_metric": has_metric,
    }


def main():
    output_dir = Path("output/astm_lists")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("🔍 Fetching ASTM standards list from Tavily...")
    response = tavily_client.extract(urls=[SOURCE_URL])

    if not response or "results" not in response or len(response["results"]) == 0:
        print("✗ Failed to fetch content from Tavily")
        return

    raw_content = response["results"][0].get("raw_content", "")
    print(f"✓ Received {len(raw_content)} characters of content")

    # Extract ASTM standard designations using regex
    # Pattern: ASTM followed by letter(s), numbers, optional underscore variant, hyphen, year
    pattern = r"ASTM [A-Z][A-Z0-9_]+(?:M)?-\d{2}[A-Z0-9]*"
    matches = re.findall(pattern, raw_content)

    # Remove duplicates and sort
    unique_standards = sorted(set(matches))
    print(f"✓ Found {len(unique_standards)} unique standards")

    # Parse each standard
    standards = []
    for line in unique_standards:
        parsed = parse_standard(line)
        if parsed:
            standards.append(parsed)

    # Count by series
    series_counts = {}
    for s in standards:
        series = s["series"]
        series_counts[series] = series_counts.get(series, 0) + 1

    timestamp = datetime.now().isoformat()

    # Build JSON structure
    json_data = {
        "source_url": SOURCE_URL,
        "scraped_at": timestamp,
        "total_count": len(standards),
        "series_breakdown": series_counts,
        "standards": standards
    }

    # Save JSON
    json_path = output_dir / "astm_standards_list.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print(f"✓ Saved JSON: {json_path}")

    # Build Markdown
    md_lines = [
        f"<!-- Source: {SOURCE_URL} -->",
        f"<!-- Scraped: {timestamp} -->",
        "",
        "# ASTM Standards List",
        "",
        f"**Source:** [{SOURCE_URL}]({SOURCE_URL})",
        f"**Total Standards:** {len(standards)}",
        "",
        "## Series Breakdown",
        "",
    ]
    for series, count in sorted(series_counts.items()):
        md_lines.append(f"- **{series}**: {count} standards")

    md_lines.extend([
        "",
        "## Full List",
        "",
        "| Designation | Code | Series | Has Metric |",
        "|-------------|------|--------|------------|",
    ])
    for s in standards:
        md_lines.append(f"| {s['designation']} | {s['code']} | {s['series']} | {'Yes' if s['has_metric'] else 'No'} |")

    # Save Markdown
    md_path = output_dir / "astm_standards_list.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"✓ Saved Markdown: {md_path}")

    print(f"\n📊 Summary:")
    print(f"   Total: {len(standards)} standards")
    for series, count in sorted(series_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"   {series}: {count}")


if __name__ == "__main__":
    main()

