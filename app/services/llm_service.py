import google.generativeai as genai
from decouple import config
import os 
import json



GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Define your predefined healthcare schema columns
PREDEFINED_COLUMNS = [
    "member_id", "first_name", "last_name", "dob", "gender", "email", "phone", "address",
    "npi_number", "provider_name", "policy_number", "plan_name", "group_number",
    "policy_start_date", "policy_end_date", "claim_date", "admission_date", "discharge_date",
    "amount_claimed", "amount_approved", "claim_status", "rejection_reason", "diagnosis_code","diagnosis_description"
]

def generate_mapping_with_llm(headers: list, samples: list):
    prompt = f"""

You are a medical health insurance claim data integration assistant. Your task is to accurately map file headers to a predefined health claim insurance schema.

Given the following information:

**Predefined Health Claim Insurance Schema:**
{PREDEFINED_COLUMNS}

**File Headers:**
{headers}

**Sample Rows (first 5–7 for context):**
{samples}

For each `header` from the provided `File Headers`, identify the single most relevant `matched_column` from the `Predefined Health Claim Insurance Schema`. Assign a `confidence_score` between 0 and 1, indicating your certainty of the match.

**Important:** If a header does not have a suitable match within the `Predefined Health Claim Insurance Schema` with a `confidence_score` of at least **0.60** (you can adjust this threshold if needed), set its `matched_column` to `Unmapped` and its `confidence_score` to `0.0`. This threshold helps ensure only strong matches are returned.


Output format:
[
  {{
    "header": "<original_file_header>",
    "matched_column": "<schema_column>  or 'unmapped'>",
    "llm_suggestion": "<schema_column> or 'unmapped'>",
    "confidence_score": <float>,
    
    
  }},
  ...
]
"""

    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    raw_text = response.text.strip()
    
    if raw_text.startswith("```json"):
        raw_text = raw_text.strip("```json").strip("```").strip()
        
    try:
        mapping_result = json.loads(raw_text)
        return mapping_result
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Gemini: {e}\nRaw Output:\n{raw_text}")
    
