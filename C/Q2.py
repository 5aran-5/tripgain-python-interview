import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------------------------------------------------------
# Step 1: Load Gemini API Key
# -------------------------------------------------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)


# -------------------------------------------------------------------
# Step 2: Fetch and Clean Webpage Content
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

    # Remove unnecessary tags
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "button"]):
        tag.decompose()

    text = " ".join(soup.stripped_strings)
    text = text[:10000]  # keep it short for efficiency
    return text


# -------------------------------------------------------------------
# Step 3: Create Custom Prompt for Gemini
# -------------------------------------------------------------------
def create_prompt(content: str) -> str:
    return f"""
You are an advanced AI summarizer. Summarize the webpage content below.

Instructions:
1. Provide a concise summary in exactly 3–5 bullet points.
2. Then add ONE short analytical insight (1 line) that captures the overall theme, trend, or implication.
3. Do NOT include any introduction or conclusion. Output strictly in the following format:

Summary:
• <point 1>
• <point 2>
• <point 3>
• <point 4>
• <point 5>
Insight:
<single-line insight>

--- Webpage Content Start ---
{content}
--- Webpage Content End ---
    """


# -------------------------------------------------------------------
# Step 4: Call Gemini Model
# -------------------------------------------------------------------
def analyze_with_gemini(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text


# -------------------------------------------------------------------
# Step 5: Run the Integration
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Choose any one of the given URLs
    url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    # You can also test:
    # url = "https://www.bbc.com/news/technology"
    # url = "https://edition.cnn.com/business"

    try:
        # Step 1: Fetch webpage
        webpage_text = fetch_and_clean(url)

        # Step 2: Create prompt
        prompt = create_prompt(webpage_text)

        # Step 3: Get Gemini response
        result = analyze_with_gemini(prompt)

        # Step 4: Display formatted output
        print("\n================= 🧠 Gemini 2.5 Flash Output =================\n")
        print(result)
        print("\n===============================================================\n")

        # Step 5: Save output to file
        with open("summary_output.txt", "w", encoding="utf-8") as f:
            f.write(result.strip())

        print("✅ Output saved to summary_output.txt")

    except Exception as e:
        print(f"❌ Error: {e}")
