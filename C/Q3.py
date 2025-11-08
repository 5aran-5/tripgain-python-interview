import os
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------------------------------------------------------
# ✅ Step 1: Load Gemini API Key
# -------------------------------------------------------------------
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    raise ValueError("❌ GEMINI_API_KEY not found. Check your .env file!")

# -------------------------------------------------------------------
# ✅ Step 2: Configure Gemini SDK
# -------------------------------------------------------------------
genai.configure(api_key=gemini_key)

# Choose your model
# Options: "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"
model_id = "gemini-2.5-flash"
model = genai.GenerativeModel(model_id)

# -------------------------------------------------------------------
# ✅ Step 3: Define the Creative Prompt (Q3 Requirement)
# -------------------------------------------------------------------
prompt = """
You are an expert AI analyst writing for a technology policy audience. 
Analyze the webpage content below and produce a precise, insight-driven summary.

Tone: professional, concise, and analytical (suitable for a technology policy brief).

Focus areas: technological advances, ethical/risk considerations, and broader business/societal impact.

Instructions (strict):
1. Generate **exactly five** concise bullet points that capture distinct, high-value themes or findings from the content. 
   If fewer than five distinct themes exist, synthesize related observations to produce five bullets.
2. Each bullet must be one sentence, start with the bullet character "• ", and be no longer than 25 words.
3. After the five bullets, provide **one single-line Insight** (no extra bullets, no paragraph breaks) 
   that interprets the overall trend or implication.
4. Do not include introductions, headings, metadata, or any additional text beyond the required format.
5. Preserve the exact output structure below (including punctuation and line breaks).

Output format (exactly):
Summary:
• <point 1>
• <point 2>
• <point 3>
• <point 4>
• <point 5>
Insight:
<single-line insight>

Webpage Content:
Artificial intelligence (AI) refers to the capability of machines to perform tasks that typically require human intelligence. 
These include reasoning, learning, planning, and perception. AI research has accelerated due to increased computational power 
and data availability, enabling systems like ChatGPT and self-driving vehicles. 
However, ethical concerns such as bias, transparency, and accountability remain crucial challenges for AI governance.
"""

# -------------------------------------------------------------------
# ✅ Step 4: Send Prompt to Gemini
# -------------------------------------------------------------------
print("🤖 Sending prompt to Gemini model...\n")

response = model.generate_content(prompt)

print("✅ Gemini Response:\n")
print(response.text)
