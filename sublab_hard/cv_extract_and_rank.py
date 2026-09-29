import json
import os
from common import call_llm_json, client, MODEL_NAME

SYSTEM_EXTRACTION_PROMPT = """
You are an expert CV extractor. Extract structured JSON from the application story following these STRICT RULES:
1. If a fact is NOT stated, return null. Never guess or estimate (No GPA stated -> gpa_4_scale = null).
2. GPA on other scales must be converted to a 4.0 scale, and original scale recorded.
3. Count ONLY published/accepted peer-reviewed papers. Submitted, under review, in prep, in press = 0 published outputs.
4. Contradictions must NOT be resolved or averaged. Set field to null and log contradiction in 'contradictions' array.

Schema to output:
{
  "candidate_id": "string",
  "full_name": "string",
  "degree": "string",
  "graduation_year": number or null,
  "gpa_4_scale": number or null,
  "original_gpa_scale": "string or null",
  "languages": ["list"],
  "published_papers_count": number,
  "relevant_experience_months": number,
  "contradictions": ["list of strings"],
  "evidence_quotes": {}
}
"""

SYSTEM_SCORING_PROMPT = """
Evaluate the extracted CV candidate JSON using the given criteria in Candidate Rubric.
Return ONLY scores (0 to 5) for each criterion in JSON format:
{
  "academic": number (0-5),
  "research": number (0-5),
  "experience": number (0-5)
}
"""

def extract_weights(rubric):
    weights = {"academic": 0.4, "research": 0.3, "experience": 0.3}
    criteria = rubric.get("criteria", [])
    if isinstance(criteria, list):
        for item in criteria:
            name = item.get("id") or item.get("name")
            if name in weights and "weight" in item:
                weights[name] = float(item["weight"])
    elif isinstance(criteria, dict):
        for name, item in criteria.items():
            if name in weights and "weight" in item:
                weights[name] = float(item["weight"])
    return weights

def run_hard():
    with open("data/candidate_rubric.json", encoding="utf-8") as f:
        rubric = json.load(f)

    weights = extract_weights(rubric)

    candidates_dir = "data/candidates"
    stories = sorted([f for f in os.listdir(candidates_dir) if f.endswith(".md")])

    results = []

    print("--- Part 1 & Part 2: Extracting & Scoring Candidates ---")
    for story_file in stories:
        path = os.path.join(candidates_dir, story_file)
        with open(path, encoding="utf-8") as f:
            story_text = f.read()

        extracted_cv, _ = call_llm_json(SYSTEM_EXTRACTION_PROMPT, f"Story File: {story_file}\nContent:\n{story_text}")
        
        user_score_prompt = f"RUBRIC:\n{json.dumps(rubric)}\n\nEXTRACTED CV:\n{json.dumps(extracted_cv)}"
        scores, _ = call_llm_json(SYSTEM_SCORING_PROMPT, user_score_prompt)

        s_acad = float(scores.get("academic", 0))
        s_res = float(scores.get("research", 0))
        s_exp = float(scores.get("experience", 0))

        total_score = round(s_acad * weights["academic"] + s_res * weights["research"] + s_exp * weights["experience"], 3)

        results.append({
            "file": story_file,
            "cv": extracted_cv,
            "scores": scores,
            "total": total_score
        })

        print(f"[{story_file}] Total Score: {total_score} | Scores: {scores}")

    winner = max(results, key=lambda x: x["total"])
    print(f"\nCOMPUTED WINNER BY CODE: {winner['file']} with score {winner['total']}")

    prose_prompt = "Here are all 6 applicant stories:\n"
    for r in results:
        prose_prompt += f"\n--- {r['file']} ---\n{json.dumps(r['cv'])}\n"
    prose_prompt += "\nWhich candidate should win the scholarship? Give a short prose explanation."

    prose_response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prose_prompt}]
    )
    print("\n--- LLM Prose Decision ---")
    print(prose_response.choices[0].message.content)

if __name__ == "__main__":
    run_hard()