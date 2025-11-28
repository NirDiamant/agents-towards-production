"""
ASTM Grades and Materials Extractor using Gemini Flash

This module processes the master list of ASTM standards and extracts:
- Applicable grades for each standard
- Material types for each grade combination
- Additional metadata (scope, applications, etc.)

Uses Google's Gemini Flash model for efficient, cost-effective extraction.
Tavily is used to fetch the raw content from ASTM store pages.

Input: astm_standards_list.json (from astm-web-access module)
Output: astm_grades_materials.json (enriched with grades and materials)
"""

import os
import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from dotenv import load_dotenv
from tavily import TavilyClient
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure logging
LOG_DIR = Path(__file__).parent / "output"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "extraction.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Validate API keys
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in environment variables")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Initialize clients
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

# Use Gemini Flash for speed and cost efficiency
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Paths
INPUT_DIR = Path(__file__).parent.parent / "agent-with-tavily-web-access" / "output" / "astm_lists"
OUTPUT_DIR = Path(__file__).parent / "output"

# Rate limiting settings
TAVILY_DELAY = 0.5  # seconds between Tavily requests
GEMINI_DELAY = 0.2  # seconds between Gemini requests

# Processing limits (set to None for full processing)
MAX_STANDARDS_TO_PROCESS = 50  # Start with 50 for testing


@dataclass
class GradeInfo:
    """Information about a specific grade within a standard."""
    grade: str
    material: Optional[str] = None
    chemical_composition: Optional[str] = None
    mechanical_properties: Optional[str] = None
    applications: Optional[str] = None


@dataclass
class StandardInfo:
    """Complete information about an ASTM standard."""
    designation: str
    code: str
    series: str
    title: Optional[str] = None
    scope: Optional[str] = None
    grades: Optional[list[dict]] = None
    materials: Optional[list[str]] = None
    extraction_status: str = "pending"
    extraction_error: Optional[str] = None
    extracted_at: Optional[str] = None
    source_url: Optional[str] = None


def build_astm_url(code: str) -> str:
    """
    Build ASTM store URL from standard code.

    Examples:
        A0105-21 -> https://store.astm.org/a0105_a0105m-21.html
        B0148-18 -> https://store.astm.org/b0148_b0148m-18.html
    """
    # Parse the code: e.g., "A0105-21" or "A0105-21E01"
    match = re.match(r"([A-Z])(\d+)-(\d+[A-Z]?\d*)", code, re.IGNORECASE)
    if not match:
        # Try alternate format without hyphen
        match = re.match(r"([A-Z])(\d+)(\d{2}[A-Z]?\d*)", code, re.IGNORECASE)
        if not match:
            logger.warning(f"Could not parse code format: {code}")
            return None

    series = match.group(1).lower()
    number = match.group(2)
    year = match.group(3)

    # Pad number to 4 digits
    number_padded = number.zfill(4)

    # Build URL with metric variant (most common format)
    filename = f"{series}{number_padded}_{series}{number_padded}m-{year}"
    return f"https://store.astm.org/{filename}.html"


def fetch_standard_content(url: str) -> Optional[str]:
    """Fetch content from ASTM store page using Tavily extract."""
    try:
        response = tavily_client.extract(urls=[url])

        if response and "results" in response and len(response["results"]) > 0:
            result = response["results"][0]
            content = result.get("raw_content", "")

            if len(content.strip()) < 100:
                logger.warning(f"Insufficient content from {url}")
                return None

            return content
    except Exception as e:
        logger.error(f"Tavily extract error for {url}: {e}")

    return None


def extract_grades_with_gemini(content: str, designation: str) -> dict:
    """
    Use Gemini Flash to extract grades and materials from standard content.

    Returns a dict with:
        - title: Standard title
        - scope: Brief scope description
        - grades: List of grade objects with materials
        - materials: List of all materials covered
    """
    prompt = f"""Analyze the following ASTM standard content for {designation} and extract structured information.

CONTENT:
{content[:15000]}  # Limit content to avoid token limits

EXTRACT THE FOLLOWING (respond in JSON format only):
{{
    "title": "Full title of the standard (e.g., 'Standard Specification for Carbon Steel...')",
    "scope": "Brief 1-2 sentence scope description",
    "grades": [
        {{
            "grade": "Grade designation (e.g., 'Grade A', 'Grade B', 'Type 304')",
            "material": "Material type (e.g., 'Carbon Steel', 'Stainless Steel 304')",
            "applications": "Typical applications if mentioned"
        }}
    ],
    "materials": ["List of all distinct material types covered by this standard"]
}}

IMPORTANT:
- If no specific grades are defined, return an empty grades array
- For the materials array, list ALL distinct materials mentioned
- Keep responses concise
- Return ONLY valid JSON, no markdown formatting"""

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)

        # Extract JSON from response
        response_text = response.text.strip()

        # Handle markdown code blocks
        if response_text.startswith("```"):
            # Remove markdown code block markers
            response_text = re.sub(r"^```(?:json)?\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        result = json.loads(response_text)
        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error for {designation}: {e}")
        logger.debug(f"Raw response: {response.text[:500]}")
        return {"error": f"JSON parse error: {e}"}
    except Exception as e:
        logger.error(f"Gemini extraction error for {designation}: {e}")
        return {"error": str(e)}


def load_standards_list(filepath: Path) -> list[dict]:
    """Load the master list of ASTM standards."""
    logger.info(f"Loading standards from {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    standards = data.get("standards", [])
    logger.info(f"Loaded {len(standards)} standards")

    return standards


def process_standard(standard: dict) -> StandardInfo:
    """Process a single standard: fetch content and extract grades."""
    designation = standard.get("designation", "Unknown")
    code = standard.get("code", "")
    series = standard.get("series", "")

    info = StandardInfo(
        designation=designation,
        code=code,
        series=series
    )

    # Build URL and fetch content
    url = build_astm_url(code)
    if not url:
        info.extraction_status = "failed"
        info.extraction_error = "Could not build URL from code"
        return info

    info.source_url = url
    logger.info(f"Fetching: {designation} from {url}")

    content = fetch_standard_content(url)
    time.sleep(TAVILY_DELAY)

    if not content:
        info.extraction_status = "failed"
        info.extraction_error = "Could not fetch content"
        return info

    # Extract grades using Gemini
    logger.info(f"Extracting grades for: {designation}")
    extracted = extract_grades_with_gemini(content, designation)
    time.sleep(GEMINI_DELAY)

    if "error" in extracted:
        info.extraction_status = "partial"
        info.extraction_error = extracted["error"]
    else:
        info.extraction_status = "success"
        info.title = extracted.get("title")
        info.scope = extracted.get("scope")
        info.grades = extracted.get("grades", [])
        info.materials = extracted.get("materials", [])

    info.extracted_at = datetime.now().isoformat()

    return info


def save_results(results: list[StandardInfo], filename: str) -> Path:
    """Save extraction results to JSON file."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / filename

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "model_used": GEMINI_MODEL,
        "total_processed": len(results),
        "successful": sum(1 for r in results if r.extraction_status == "success"),
        "failed": sum(1 for r in results if r.extraction_status == "failed"),
        "partial": sum(1 for r in results if r.extraction_status == "partial"),
        "standards": [asdict(r) for r in results]
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to: {output_path}")
    return output_path


def save_checkpoint(results: list[StandardInfo], checkpoint_num: int) -> Path:
    """Save intermediate checkpoint during long runs."""
    filename = f"checkpoint_{checkpoint_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return save_results(results, filename)


def main():
    """Main entry point for the grades extractor."""
    print("\n" + "=" * 60)
    print("ASTM Grades & Materials Extractor")
    print(f"Using: {GEMINI_MODEL}")
    print("=" * 60 + "\n")

    # Load standards list
    input_file = INPUT_DIR / "astm_standards_list.json"
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.info("Run the astm_scraper.py first to generate the standards list")
        return

    standards = load_standards_list(input_file)

    # Apply processing limit if set
    if MAX_STANDARDS_TO_PROCESS:
        standards = standards[:MAX_STANDARDS_TO_PROCESS]
        logger.info(f"Processing limited to first {MAX_STANDARDS_TO_PROCESS} standards")

    # Process standards
    results = []
    checkpoint_interval = 25  # Save checkpoint every 25 standards

    for i, standard in enumerate(standards, 1):
        print(f"\n[{i}/{len(standards)}] Processing: {standard.get('designation', 'Unknown')}")

        try:
            result = process_standard(standard)
            results.append(result)

            # Print summary
            if result.extraction_status == "success":
                grade_count = len(result.grades) if result.grades else 0
                material_count = len(result.materials) if result.materials else 0
                print(f"  Success: {grade_count} grades, {material_count} materials")
            else:
                print(f"  {result.extraction_status.upper()}: {result.extraction_error}")

            # Save checkpoint
            if i % checkpoint_interval == 0:
                save_checkpoint(results, i)

        except KeyboardInterrupt:
            logger.warning("Interrupted by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error processing {standard}: {e}")
            continue

    # Save final results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"astm_grades_materials_{timestamp}.json"
    output_path = save_results(results, output_file)

    # Print summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r.extraction_status == 'success')}")
    print(f"Failed: {sum(1 for r in results if r.extraction_status == 'failed')}")
    print(f"Partial: {sum(1 for r in results if r.extraction_status == 'partial')}")
    print(f"\nOutput: {output_path}")

    # Sample output
    successful = [r for r in results if r.extraction_status == "success"]
    if successful:
        print("\nSample extractions:")
        for r in successful[:3]:
            print(f"\n  {r.designation}:")
            print(f"    Title: {r.title[:60] if r.title else 'N/A'}...")
            print(f"    Grades: {len(r.grades) if r.grades else 0}")
            print(f"    Materials: {', '.join(r.materials[:3]) if r.materials else 'N/A'}")


if __name__ == "__main__":
    main()
