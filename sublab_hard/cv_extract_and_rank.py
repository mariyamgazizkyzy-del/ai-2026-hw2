import json
import os

from common import call_llm_json, client, MODEL_NAME


# ============================================================
# PART 1 — CV EXTRACTION
# ============================================================

SYSTEM_EXTRACTION_PROMPT = """
You are an expert CV extractor for a funded scholarship application.

Extract structured information from the applicant story.

STRICT RULES:

1. NEVER guess.
   If a fact is not explicitly stated, return null.
   Do not estimate GPA, graduation year, experience, or publications.

2. GPA:
   - If GPA is given on a 4.0 scale, keep the value.
   - If GPA is given on another scale, convert it to a 4.0 scale.
   - Always record the original GPA scale.
   - If no GPA is stated:
       gpa_4_scale = null
       original_gpa_scale = null
   - Never infer GPA from the university, degree, or general impression.

3. PUBLICATIONS:
   Count ONLY publications that are explicitly described as:
   - published
   - accepted
   - published peer-reviewed
   - accepted peer-reviewed

   Do NOT count:
   - in preparation
   - submitted
   - under review
   - planned
   - in press

   Record non-published outputs separately.

4. EXPERIENCE:
   Count relevant experience in MONTHS.
   - Count months, not number of jobs.
   - Overlapping periods count only once.
   - A period without enough dates cannot be counted.
   - Record uncountable experience separately.

5. CONTRADICTIONS:
   If the story gives contradictory information:
   - DO NOT choose one version.
   - DO NOT average the values.
   - Set the affected field to null.
   - Record the contradiction in the contradictions array.

6. EVIDENCE:
   For every non-null extracted field, provide a short direct quote
   from the applicant story supporting that field.

Return ONLY valid JSON.

Required structure:

{
  "candidate_id": "string or null",
  "full_name": "string or null",
  "degree": "string or null",
  "graduation_year": number or null,
  "gpa_4_scale": number or null,
  "original_gpa_scale": "string or null",
  "languages": ["list of languages"],
  "published_papers_count": number,
  "non_published_outputs": ["list"],
  "relevant_experience_months": number,
  "uncountable_experience": ["list"],
  "contradictions": ["list"],
  "evidence_quotes": {
    "candidate_id": "quote",
    "full_name": "quote",
    "degree": "quote",
    "graduation_year": "quote",
    "gpa": "quote",
    "languages": "quote",
    "published_papers": "quote",
    "experience": "quote"
  }
}
"""


# ============================================================
# PART 2 — SCORING
# ============================================================

SYSTEM_SCORING_PROMPT = """
You are scoring scholarship candidates using the supplied rubric.

Return ONLY JSON with exactly these three numeric fields:

{
  "academic": number,
  "research": number,
  "experience": number
}

Each score must be between 0 and 5.

Use ONLY the information in the extracted CV and the supplied rubric.

Do not calculate the weighted total.
Do not choose the winner.
Do not add explanations.

Important rubric rules:

ACADEMIC:
- Use the stated degree, grades and GPA.
- GPA must already be converted to the 4.0 scale.
- Missing GPA must not be guessed.
- If there is a contradiction in an academic field, use the extracted
  null value and do not resolve the contradiction.

RESEARCH:
- Count only published or accepted publications.
- Submitted, under review, in preparation, planned and in press
  are NOT published.

EXPERIENCE:
- Use only countable relevant months.
- Do not count overlapping periods twice.
- Do not invent dates or months.
"""


# ============================================================
# LOAD RUBRIC
# ============================================================

def load_rubric():
    with open(
        "data/candidate_rubric.json",
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ============================================================
# EXTRACT WEIGHTS FROM RUBRIC
# ============================================================

def extract_weights(rubric):
    """
    Read the weights directly from candidate_rubric.json.

    Current rubric:
        academic   = 0.5
        research   = 0.3
        experience = 0.2
    """

    weights = {
        "academic": 0.5,
        "research": 0.3,
        "experience": 0.2
    }

    criteria = rubric.get("criteria", [])

    if isinstance(criteria, list):
        for item in criteria:
            criterion_id = item.get("id")

            if criterion_id in weights and "weight" in item:
                weights[criterion_id] = float(item["weight"])

    elif isinstance(criteria, dict):
        for criterion_id, item in criteria.items():
            if criterion_id in weights and "weight" in item:
                weights[criterion_id] = float(item["weight"])

    return weights


# ============================================================
# VALIDATE EXTRACTED CV
# ============================================================

def validate_extracted_cv(cv):
    """
    Basic programmatic validation of the LLM extraction.
    """

    required_fields = [
        "candidate_id",
        "full_name",
        "degree",
        "graduation_year",
        "gpa_4_scale",
        "original_gpa_scale",
        "languages",
        "published_papers_count",
        "non_published_outputs",
        "relevant_experience_months",
        "uncountable_experience",
        "contradictions",
        "evidence_quotes"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in cv
    ]

    if missing_fields:
        return False, f"Missing fields: {missing_fields}"

    # Numeric validation
    if cv["graduation_year"] is not None:
        if not isinstance(cv["graduation_year"], (int, float)):
            return False, "graduation_year must be numeric or null"

    if cv["gpa_4_scale"] is not None:
        if not isinstance(cv["gpa_4_scale"], (int, float)):
            return False, "gpa_4_scale must be numeric or null"

        if not 0 <= float(cv["gpa_4_scale"]) <= 4:
            return False, "gpa_4_scale must be between 0 and 4"

    if not isinstance(cv["published_papers_count"], (int, float)):
        return False, "published_papers_count must be numeric"

    if cv["published_papers_count"] < 0:
        return False, "published_papers_count cannot be negative"

    if not isinstance(cv["relevant_experience_months"], (int, float)):
        return False, "relevant_experience_months must be numeric"

    if cv["relevant_experience_months"] < 0:
        return False, "relevant_experience_months cannot be negative"

    # List validation
    list_fields = [
        "languages",
        "non_published_outputs",
        "uncountable_experience",
        "contradictions"
    ]

    for field in list_fields:
        if not isinstance(cv[field], list):
            return False, f"{field} must be a list"

    if not isinstance(cv["evidence_quotes"], dict):
        return False, "evidence_quotes must be an object"

    return True, "Valid"


# ============================================================
# VALIDATE SCORES
# ============================================================

def validate_scores(scores):
    required = ["academic", "research", "experience"]

    for field in required:
        if field not in scores:
            return False, f"Missing score: {field}"

        try:
            value = float(scores[field])
        except (TypeError, ValueError):
            return False, f"{field} must be numeric"

        if not 0 <= value <= 5:
            return False, f"{field} must be between 0 and 5"

    return True, "Valid"


# ============================================================
# CALCULATE WEIGHTED SCORE
# ============================================================

def calculate_total(scores, weights):
    """
    IMPORTANT:
    The LLM does NOT calculate the final ranking.

    Python calculates:

    0.5 * academic
    + 0.3 * research
    + 0.2 * experience
    """

    total = (
        float(scores["academic"]) * weights["academic"]
        + float(scores["research"]) * weights["research"]
        + float(scores["experience"]) * weights["experience"]
    )

    return round(total, 2)


# ============================================================
# READ STORIES
# ============================================================

def load_stories():
    candidates_dir = "data/candidates"

    story_files = sorted(
        file_name
        for file_name in os.listdir(candidates_dir)
        if file_name.endswith(".md")
    )

    stories = []

    for story_file in story_files:
        path = os.path.join(candidates_dir, story_file)

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            story_text = f.read()

        stories.append({
            "file": story_file,
            "text": story_text
        })

    return stories


# ============================================================
# MAIN HARD SUBLAB
# ============================================================

def run_hard():

    print("=" * 70)
    print("SUBLAB HARD — CV EXTRACTION AND RANKING")
    print("=" * 70)

    # --------------------------------------------------------
    # Load rubric
    # --------------------------------------------------------

    rubric = load_rubric()
    weights = extract_weights(rubric)

    print("\nRubric weights:")
    print(f"Academic   = {weights['academic']}")
    print(f"Research   = {weights['research']}")
    print(f"Experience = {weights['experience']}")

    print(
        "\nFormula:"
        " 0.5 * academic + 0.3 * research + 0.2 * experience"
    )

    # --------------------------------------------------------
    # Load stories
    # --------------------------------------------------------

    stories = load_stories()

    results = []

    # --------------------------------------------------------
    # Process every candidate
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PART 1 — EXTRACTION AND PART 2 — SCORING")
    print("=" * 70)

    for story in stories:

        story_file = story["file"]
        story_text = story["text"]

        print(f"\nProcessing {story_file}...")

        # ====================================================
        # EXTRACTION CALL
        # ====================================================

        extraction_user_prompt = f"""
Story File: {story_file}

Applicant Story:
{story_text}
"""

        extracted_cv, extraction_raw = call_llm_json(
            SYSTEM_EXTRACTION_PROMPT,
            extraction_user_prompt
        )

        # ----------------------------------------------------
        # Validate extraction
        # ----------------------------------------------------

        extraction_valid, extraction_message = validate_extracted_cv(
            extracted_cv
        )

        print(f"Extraction validation: {extraction_valid}")

        if not extraction_valid:
            print(f"Validation message: {extraction_message}")

        # ====================================================
        # SCORING CALL
        # ====================================================

        scoring_user_prompt = f"""
CANDIDATE RUBRIC:

{json.dumps(rubric, ensure_ascii=False, indent=2)}

EXTRACTED CV:

{json.dumps(extracted_cv, ensure_ascii=False, indent=2)}
"""

        scores, scoring_raw = call_llm_json(
            SYSTEM_SCORING_PROMPT,
            scoring_user_prompt
        )

        # ----------------------------------------------------
        # Validate scores
        # ----------------------------------------------------

        scores_valid, scores_message = validate_scores(scores)

        print(f"Score validation: {scores_valid}")

        if not scores_valid:
            print(f"Validation message: {scores_message}")

            # Do not silently continue with invalid scores.
            raise ValueError(
                f"Invalid scores for {story_file}: {scores_message}"
            )

        # ====================================================
        # CODE CALCULATES WEIGHTED TOTAL
        # ====================================================

        total_score = calculate_total(
            scores,
            weights
        )

        result = {
            "file": story_file,
            "cv": extracted_cv,
            "scores": scores,
            "total": total_score,
            "extraction_valid": extraction_valid,
            "score_valid": scores_valid
        }

        results.append(result)

        print(
            f"[{story_file}] "
            f"Academic={scores['academic']} | "
            f"Research={scores['research']} | "
            f"Experience={scores['experience']} | "
            f"Total={total_score:.2f}"
        )

    # ========================================================
    # PART 3 — DETERMINISTIC WINNER
    # ========================================================

    print("\n" + "=" * 70)
    print("PART 3 — CODE-COMPUTED RANKING")
    print("=" * 70)

    # Sort by total score, highest first
    ranking = sorted(
        results,
        key=lambda item: item["total"],
        reverse=True
    )

    print("\nRanking:")

    for position, result in enumerate(
        ranking,
        start=1
    ):
        print(
            f"{position}. "
            f"{result['file']} — "
            f"{result['total']:.2f}"
        )

    winner = ranking[0]

    print(
        f"\nCOMPUTED WINNER BY CODE: "
        f"{winner['file']} "
        f"with score {winner['total']:.2f}"
    )

    # ========================================================
    # TOP TWO GAP
    # ========================================================

    if len(ranking) >= 2:

        second = ranking[1]

        gap = round(
            winner["total"] - second["total"],
            2
        )

        print(
            f"TOP TWO GAP: "
            f"{winner['total']:.2f} - "
            f"{second['total']:.2f} = "
            f"{gap:.2f}"
        )

        if gap <= 0.05:
            print(
                "The top two candidates are within 0.05."
            )
        else:
            print(
                "The top two candidates are NOT within 0.05."
            )

    # ========================================================
    # SHOW EXTRACTION DETAILS
    # ========================================================

    print("\n" + "=" * 70)
    print("EXTRACTION DETAILS")
    print("=" * 70)

    for result in results:

        cv = result["cv"]

        print(f"\n--- {result['file']} ---")

        print(
            f"Candidate ID: "
            f"{cv.get('candidate_id')}"
        )

        print(
            f"Name: "
            f"{cv.get('full_name')}"
        )

        print(
            f"Degree: "
            f"{cv.get('degree')}"
        )

        print(
            f"Graduation year: "
            f"{cv.get('graduation_year')}"
        )

        print(
            f"GPA 4.0: "
            f"{cv.get('gpa_4_scale')}"
        )

        print(
            f"Original GPA scale: "
            f"{cv.get('original_gpa_scale')}"
        )

        print(
            f"Languages: "
            f"{cv.get('languages')}"
        )

        print(
            f"Published papers: "
            f"{cv.get('published_papers_count')}"
        )

        print(
            f"Non-published outputs: "
            f"{cv.get('non_published_outputs')}"
        )

        print(
            f"Relevant experience months: "
            f"{cv.get('relevant_experience_months')}"
        )

        print(
            f"Uncountable experience: "
            f"{cv.get('uncountable_experience')}"
        )

        print(
            f"Contradictions: "
            f"{cv.get('contradictions')}"
        )

    # ========================================================
    # PART 4 — SEPARATE LLM PROSE CALL
    # ========================================================

    print("\n" + "=" * 70)
    print("PART 4 — SEPARATE LLM PROSE DECISION")
    print("=" * 70)

    prose_prompt = """
You are reviewing six scholarship applicants.

Below are the original applicant stories and the scholarship rubric.

Give a short prose explanation of how the applicants compare.

You may describe which candidate the model would select,
but DO NOT calculate the weighted total yourself.

Do not invent facts.

Pay special attention to:
- GPA
- published research
- relevant experience
- contradictions
- missing information

Applicant stories:

"""

    for story in stories:
        prose_prompt += (
            f"\n\n--- {story['file']} ---\n"
            f"{story['text']}"
        )

    prose_prompt += (
        "\n\n--- RUBRIC ---\n"
        + json.dumps(
            rubric,
            ensure_ascii=False,
            indent=2
        )
    )

    prose_response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prose_prompt
            }
        ]
    )

    prose_text = (
        prose_response
        .choices[0]
        .message
        .content
    )

    print("\nLLM PROSE DECISION:")
    print(prose_text)

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(
        f"Code winner: "
        f"{winner['file']} — "
        f"{winner['total']:.2f}"
    )

    if len(ranking) >= 2:
        print(
            f"Second place: "
            f"{ranking[1]['file']} — "
            f"{ranking[1]['total']:.2f}"
        )

        print(
            f"Gap: "
            f"{round(winner['total'] - ranking[1]['total'], 2):.2f}"
        )

    print(
        "\nThe final weighted ranking is calculated by Python, "
        "not by the LLM."
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_hard()