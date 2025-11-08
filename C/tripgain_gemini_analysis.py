#!/usr/bin/env python3
"""
tripgain_gemini_analysis.py
---------------------------------
Fetches live webpage content, cleans it, sends to Gemini 2.5 Flash model via API,
and prints + saves an intelligent summary and insight.
"""

import os
import sys
import argparse
import requests
from bs4 import BeautifulSoup
import re
import json
from textwrap import dedent
from dotenv import load_dotenv

# ------------------------------------------
# Load environment variables from .env
# ------------------------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file.")
    sys.exit(1)

# ------------------------------------------
# Configuration
# ------------------------------------------
MODEL_NAME = "gemini-2.5-flash"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
MAX_CHARS = 30000
OUTPUT_FILE = "summary_output.txt"

ALLOWED_URLS = {
    "wikipedia_ai": "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "bbc_tech": "https://www.bbc.com/news/technology",
    "cnn_business": "https://edition.cnn.com/business"
}


# ------------------------------------------
# Helper Functions
# ------------------------------------------
def fetch_url(url, timeout=15):
    headers = {"User-Agent": "Tripgain-Gemini-Integration/1.0"}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def clean_html(html):
    """Remove scripts, styles, nav, etc., and return cleaned text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup.body
    text = article.get_text(separator=" ", strip=True) if article else soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text[:MAX_CHARS]


def build_prompt(cleaned_text):
    """Create a structured and clear prompt for Gemini."""
    prompt = dedent(f"""
    You are an expert analyst. Analyze the following webpage content and produce output EXACTLY in the format below.

    Requirements:
    - Summarize into 3–5 bullet points focusing on the technology and societal impact of the topic.
    - Each bullet must be concise and factually derived.
    - Then provide exactly one line labeled "Insight:" explaining what the content suggests about the trend or theme.
    - Use a professional, analytical tone.
    - Follow this format exactly:

    Summary:
    • <point 1>
    • <point 2>
    • <point 3>
    • <point 4>
    • <point 5>
    Insight:
    <single-line insight>

    Content:
    {cleaned_text}
    """).strip()
    return prompt


def call_gemini(prompt):
    """Send cleaned content to Gemini 2.5 Flash API."""
    url = f"{API_BASE}/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    response = requests.post(url, headers=headers, json=body, timeout=60)
    if response.status_code != 200:
        print("❌ Gemini API Error:", response.text)
        sys.exit(1)

    data = response.json()
    # Extract text safely
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        return json.dumps(data, indent=2)


def format_output(text):
    """Ensure output follows exact structure required."""
    if "Summary:" not in text:
        text = "Summary:\n• " + text.replace(". ", ".\n• ")
    if "Insight:" not in text:
        text += "\nInsight:\n(No clear insight provided)"
    return text


def save_output(final_text):
    print(final_text)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"\n✅ Saved summary and insight to '{OUTPUT_FILE}'")


# ------------------------------------------
# Main
# ------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Tripgain Gemini 2.5 Flash Integration")
    parser.add_argument("--url", type=str, default=ALLOWED_URLS["wikipedia_ai"],
                        help="URL to analyze (choose from allowed list)")
    args = parser.parse_args()
    url = args.url.strip()

    if url not in ALLOWED_URLS.values():
        print("❌ Invalid URL. Choose from:")
        for v in ALLOWED_URLS.values():
            print(" -", v)
        sys.exit(1)

    print("🔹 Fetching webpage...")
    html = fetch_url(url)

    print("🔹 Cleaning content...")
    cleaned = clean_html(html)

    print("🔹 Building prompt for Gemini...")
    prompt = build_prompt(cleaned)

    print("🔹 Sending request to Gemini 2.5 Flash...")
    response_text = call_gemini(prompt)

    print("🔹 Formatting output...")
    final_text = format_output(response_text)

    save_output(final_text)


if __name__ == "__main__":
    main()
