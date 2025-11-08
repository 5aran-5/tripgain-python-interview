import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------------------------------------------------------
# Step 1: Load API key from .env
# -------------------------------------------------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)

# -------------------------------------------------------------------
# Step 2: Fetch and clean webpage data (Fixed version)
# -------------------------------------------------------------------
def fetch_and_clean(url: str) -> str:
    print(f"🌐 Fetching content from: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove irrelevant HTML sections
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "button"]):
        tag.decompose()

    text = " ".join(soup.stripped_strings)
    text = text[:10000]
    return text


# -------------------------------------------------------------------
# Step 3: Custom intelligent prompt
# -------------------------------------------------------------------
def create_prompt(content: str) -> str:
    return f"""
You are an AI analyst. Read the following webpage text and perform two tasks:

1️⃣ Summarize the main themes and key takeaways concisely.
2️⃣ Provide a short analytical insight — interpret trends, implications, or deeper meaning.

Keep your response structured and under 300 words.

--- Webpage Content Start ---
{content}
--- Webpage Content End ---
    """


# -------------------------------------------------------------------
# Step 4: Gemini Integration
# -------------------------------------------------------------------
def summarize_with_gemini(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text


# -------------------------------------------------------------------
# Step 5: Run everything
# -------------------------------------------------------------------
if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/Artificial_intelligence"

    try:
        webpage_text = fetch_and_clean(url)
        prompt = create_prompt(webpage_text)
        summary = summarize_with_gemini(prompt)

        print("\n================= 🧠 Gemini Summary & Insight =================\n")
        print(summary)
        print("\n===============================================================\n")

    except Exception as e:
        print(f"❌ Error: {e}")
