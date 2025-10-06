import google.generativeai as genai
import os

API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDbBSku2PcCPfIH0SvJ36CT_dW-mLs3zqY")
MODEL = "gemini-2.5-flash"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL)

def analyze_mood(text: str):
    prompt = f"""You are MoodMapper AI, an empathetic assistant specialized in emotional intelligence.
Your role is to analyze mood entries and provide supportive, actionable guidance.
Always respond with valid JSON only, no additional text.
    
    
analyze user text and returns a recommendation for a scripture(book,chapter,verse/verses) to help/aid the user

return only json format: 
{{"mood": "happy",
"confidence": 0.95,
  "book": "Psalms",
  "chapter": "100",
  "verse": "1-5",
  "scripture_text": "Make a joyful noise to the Lord, all the earth! Serve the Lord with gladness! Come into his presence with singing! Know that the Lord, he is God! It is he who made us, and we are his; we are his people, and the sheep of his pasture. Enter his gates with thanksgiving, and his courts with praise! Give thanks to him; bless his name! For the Lord is good; his steadfast love endures forever, and his faithfulness to all generations."

}}

User entry: "{text}"

Return ONLY the JSON object, no additional text."""
    resp = model.generate_content(prompt)
    return resp.text

