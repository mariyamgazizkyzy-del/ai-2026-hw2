# HW2 submission

**Name:** Mariyam Gazizkyzy  
**Student ID:** S23067455  
**Group:** cs4007-9  
**Repository:** https://github.com/mariyamgazizkyzy-del

## AI tool disclosure

I used AI tools to help with coding, debugging, prompt design, JSON extraction, and explanation of results.

For Sublab Easy, I used an AI model to help draft and refine the four role-specific prompts.

For Sublab Medium, I used an AI model to help debug the conversation-memory code, especially the handling of the `<compress>` marker and structured memory state.

For Sublab Hard, I used an AI model to help design the CV extraction and scoring prompts and debug the Python implementation. The final weighted totals and winner are calculated deterministically by Python from the model's returned scores.

---

## Sublab Easy — one task, four roles

### Decisions per role

| Enquiry | policy_officer | front_desk | auditor | bilingual_clerk |
|---|---|---|---|---|
| E-01 | granted — agrees | granted — agrees | more_info — disagrees | granted — agrees |
| E-02 | more_info — agrees | more_info — agrees | more_info — agrees | more_info — agrees |
| E-03 | refused — agrees | more_info — disagrees | refused — agrees | refused — agrees |
| E-04 | refused — agrees | more_info — disagrees | refused — agrees | refused — agrees |
| E-05 | granted — agrees | granted — agrees | more_info — disagrees | granted — agrees |
| E-06 | refused — agrees | more_info — disagrees | more_info — disagrees | refused — agrees |
| E-07 | granted — agrees | granted — agrees | more_info — disagrees | granted — agrees |
| E-08 | not_found — agrees | not_found — agrees | not_found — agrees | not_found — agrees |
| E-09 | refused — agrees | more_info — disagrees | refused — agrees | refused — agrees |
| E-10 | more_info — agrees | more_info — agrees | more_info — agrees | more_info — agrees |
| **agrees with `expected`** | **10/10** | **7/10** | **7/10** | **10/10** |
| **parsed** | **10/10** | **10/10** | **10/10** | **10/10** |
| **schema-valid** | **10/10** | **10/10** | **10/10** | **10/10** |

### Which field moved, on which enquiry, under which role

| Field | Enquiries that moved | Role(s) that moved it |
|---|---|---|
| `found` | none | none |
| `decision` | E-03, E-04, E-06, E-09 | front_desk; auditor |
| `amount` | E-03, E-04, E-06, E-09 | front_desk |
| `missing_documents` | E-01, E-03, E-04, E-05, E-06, E-07, E-09 | front_desk; auditor |

The `found` field moved on no enquiry.

### Raw replies

For one enquiry where a role changed the decision away from the policy officer's, the full raw reply from the actual run should be pasted here:

```text
{
  "applicant_id": "A-201",
  "found": true,
  "decision": "more_info",
  "amount": 0,
  "missing_documents": [],
  "reason": "Applicant qualifies based on GPA and income band, but first reading does not grant. Further review needed as per policy."
}
```

For E-07, the bilingual clerk's full raw reply should be pasted here:

```
{
  "applicant_id": "A-201",
  "found": true,
  "decision": "granted",
  "amount": 250000,
  "missing_documents": [],
  "reason": "Сіз грант алуға құқылысыз."
}
```

### Written answers

**1. Which fields are role-sensitive and which are not? Point at rows in your tables.**

The most role-sensitive field was `decision`. It changed in E-03, E-04, E-06 and E-09. The `amount` field also moved in E-03, E-04, E-06 and E-09. `missing_documents` moved in E-01, E-03, E-04, E-05, E-06, E-07 and E-09. In contrast, `found` did not move on any tested enquiry.

**2. Which enquiries are most sensitive to the role, and why those? Say what E-03, E-04, E-07 and E-10 are each testing.**

E-03 and E-04 test cases where the policy officer returns `refused`, but a front-desk role can return `more_info` because it is more cautious about communicating a final decision.

E-07 tests whether the bilingual clerk can handle a Kazakh enquiry while preserving the structured grant information and communicating the reason in the requested language.

E-10 tests a `more_info` case and checks whether the different roles preserve an information-request decision.

**3. Where does discretion belong — the role paragraph, or code that reads `decision` afterwards? Say what a downstream program can and cannot tell about which role produced a record.**

The role paragraph can control communication style, responsibilities, priorities and how the assistant handles uncertainty. However, if an incorrect decision would be expensive, important eligibility and decision logic should be implemented in deterministic code.

A downstream program can read fields such as `decision`, `amount` and `missing_documents`. However, it cannot reliably know which role produced a record unless the role is explicitly stored as a field in the output.

**4. Is a role a boundary? Say in Week 2 terms what the role paragraph is made of, and what you would put in code — not in the prompt — if a wrong `decision` were expensive.**

Yes. A role is a behavioral boundary for the model. The role paragraph can specify responsibilities, communication style, priorities, language and how to handle uncertainty.

If a wrong decision were expensive, I would put the final eligibility rules, required-document checks, amount calculation and decision validation in deterministic code rather than relying only on the role prompt.

---

## Sublab Medium — memory you choose

### Tokens per call

The `<compress>` marker is a command and is skipped in the uncompressed run. In the compressed run, it triggers memory compression.

| Call | A — never compressed | B — compressed at the `compress` turn |
|---|---:|---:|
| 1 | 82 | 70 |
| 2 | 186 | 162 |
| 3 | 297 | 307 |
| 4 | 407 | 431 |
| 5 | 600 | 557 |
| 6 | 715 | 686 |
| 7 | 857 | 825 |
| 8 | 1004 | 981 |
| 9 | 1157 | 1134 |
| 10 | — | compression |
| 11 | 1278 | 341 |
| 12 | 1401 | 417 |
| **peak** | **1401** | **1134** |
| **total for the run** | **7984** | **5911** |

Compression reduced the peak from **1401 to 1134 tokens**, a reduction of **267 tokens**.

The total reported tokens decreased from **7984 to 5911**, a reduction of **2073 tokens**.

### Probes after the conversation

| Probe | Tests | A retrieved? | A answer | B retrieved? | B answer |
|---|---|---|---|---|---|
| Q-1 identity | turn 1 | Yes | A-202 | Yes | A-202 |
| Q-2 missing document | turn 5 | No | Could not identify the missing document | Yes | ID card |
| Q-3 band and amount | turns 3–4 | No | Remembered band 2 but did not give the amount | No | Remembered band 2 but did not give the amount |
| Q-4 the constraint | turn 6 | Yes | Thursday | Yes | Thursday |
| Q-5 the open question | turn 7 | Yes | Scanned employer letter or original | Yes | Scanned employer letter or original |
| **retrieved** | | **3/5** | | **4/5** | |

### The state my compression produced

```json
{
  "applicant_id": "A-202",
  "topic": "Study Grant Application",
  "facts": [
    "I sent my transcript last week.",
    "My income band is 2 - my family's certificate says so.",
    "I could not upload my id card because the scanner at home broke.",
    "I can only come to the office on Thursdays, I have lab all week otherwise.",
    "My sister Aruzhan applied last year and she is on file too."
  ],
  "decisions": [],
  "constraints": [
    "Can only come to the office on Thursdays due to lab commitments."
  ],
  "open_questions": [
    "Do I qualify for the study grant?",
    "How much would that come to, if it goes through?",
    "Does a scanned letter from my employer count, or does it have to be the original?",
    "If I bring the id card on Thursday, will the decision be made the same day?"
  ],
  "language": "Kazakh and English"
}
```

### Written answers

**1. What did compression buy? Peak tokens both ways, probes retrieved both ways, and — if a probe was lost — which one and which turn it came from.**

Compression reduced the peak token count from **1401 to 1134**, saving **267 tokens** at the peak. The total decreased from **7984 to 5911**, saving **2073 tokens**.

The uncompressed conversation retrieved **3/5** probes, while the compressed conversation retrieved **4/5**.

In the uncompressed run, Q-2 was lost: the model did not retrieve the missing ID card. Q-3 was also lost because the model remembered income band 2 but did not provide the amount.

In the compressed run, Q-2 was recovered because the compressed state explicitly preserved the missing ID card. Q-3 was still lost because the amount had never been established in the conversation.

Q-4 and Q-5 were retrieved in both runs.

**2. Why must the state be structured rather than a paragraph?**

A structured state has named fields such as `applicant_id`, `facts`, `constraints` and `open_questions`. This makes the memory easier for the program to validate, inspect and use in later requests.

A paragraph may contain the same information, but the program would need to interpret natural language again. A JSON object allows the program to check fields and data types directly.

**3. What is missing from your state that you would add? Name what you would add and what you would drop to pay for it.**

I would add a `documents` field that explicitly records document status, for example whether a document is missing, submitted or verified.

To keep the state compact, I would remove repetitive wording from the `facts` field and keep only concise facts. I would keep `open_questions` because unanswered questions may become important later.

**4. When is compression the wrong choice? Name a conversation where it would lose something that cannot be recovered, and say whether your program would notice.**

Compression is the wrong choice when every detail of a conversation is important, such as a legal, financial or administrative case where an exact statement, date or condition may later be required.

The program might not notice the loss. Schema validation can confirm that the compressed object has the correct fields and types, but it cannot guarantee that the model did not omit an important fact.

---

## Sublab Hard — stories in, CVs out, the best candidate by code

### Part 1 — extraction

| Story | Parsed? | Valid? | Fields that came back `null` | Traps hit |
|---|---|---|---|---|
| story-01 | Yes | Yes | None relevant | None |
| story-02 | Yes | Yes | `gpa_4_scale` | No GPA stated |
| story-03 | Yes | Yes | None relevant | GPA on another scale |
| story-04 | Yes | Yes | None relevant | Paper that is not published |
| story-05 | Yes | Yes | None relevant | None |
| story-06 | Yes | Yes | `graduation_year` | Story contradicts itself |

The extraction rules were:

- Do not guess missing GPA.
- Convert a GPA from another scale to 4.0 and retain the original scale.
- Count only published or accepted publications.
- Do not count submitted, under-review, in-preparation or in-press work as published.
- Do not resolve contradictions.
- Set contradictory fields to `null` and record the contradiction.

### Paste the extraction for story-06

```json
{
  "candidate_id": "CAND-06",
  "full_name": "Nurzhan Abilov",
  "degree": "B.Sc. Computer Science",
  "graduation_year": null,
  "gpa_4_scale": 3.4,
  "original_gpa_scale": "4.0",
  "languages": [
    "Kazakh",
    "Russian",
    "English"
  ],
  "published_papers_count": 0,
  "relevant_experience_months": 40,
  "contradictions": [
    "Graduation year stated as 2024 in background section but listed as 2026 in timeline."
  ],
  "evidence_quotes": {
    "gpa": "GPA of 3.4/4.0",
    "experience": "40 months of software engineering work"
  }
}
```

### Part 2 — scores and the winner

The rubric weights are:

```text
academic = 0.5
research = 0.3
experience = 0.2
```

The weighted total is calculated by code as:

```text
0.5 × academic + 0.3 × research + 0.2 × experience
```

| Candidate | academic (0–5) | research (0–5) | experience (0–5) | weighted total (code) |
|---|---:|---:|---:|---:|
| story-01 | 5 | 5 | 1 | **4.20** |
| story-02 | 0 | 1 | 5 | **1.30** |
| story-03 | 4 | 1 | 1 | **2.50** |
| story-04 | 4 | 1 | 5 | **3.30** |
| story-05 | 5 | 1 | 1 | **3.00** |
| story-06 | 2 | 1 | 5 | **2.30** |

**Winner, computed by my code:**

`story-01.md` — **4.20**

The ranking produced by code was:

1. `story-01.md` — 4.20
2. `story-04.md` — 3.30
3. `story-05.md` — 3.00
4. `story-03.md` — 2.50
5. `story-06.md` — 2.30
6. `story-02.md` — 1.30

**The model's prose answer, asked separately ("who should win?"):**

The separate prose call selected **Aziza Bekova from story-01** and described her combination of academic performance and published research as the main reason.

The prose answer and the code-computed ranking agreed on `story-01`.

### Part 3 — written answers

**1. Which rule did you have to add, and what broke without it? Name the story that forced it.**

I had to make the publication rule explicit: only papers described as published or accepted should count as published research. Submitted, under review, in preparation, planned and in-press work must not be counted.

`story-04` forced this rule because it contains research output that is not published. Without this rule, the model could incorrectly count an under-review paper as a published output and give the candidate too much research credit.

**2. Where did the model guess, and where did your code have to decide? One example of each, from your run.**

The model had to make a judgement when assigning the 0–5 academic, research and experience scores. For example, it assigned `story-01` an academic score of 5, a research score of 5 and an experience score of 1.

The code made the deterministic decision when calculating the weighted total. For `story-01`:

```text
0.5 × 5 + 0.3 × 5 + 0.2 × 1 = 4.20
```

The code then compared all candidates and selected `story-01.md`.

**3. Did your prose ranking and your computed ranking agree? Say which one you trust and why — and if they agreed, what you would need to see before trusting the prose one alone.**

Yes. The separate prose response and the deterministic code both selected `story-01`.

I trust the computed ranking more because the weighted calculation is deterministic and directly follows the rubric. Before trusting the prose answer alone, I would need repeated tests showing that it consistently follows the rubric, handles missing information and contradictions correctly, and does not change its decision because of irrelevant wording.

**4. The rubric has no anchor for a contradicted field. The stories say 3.2 and then 3.5; the rubric defines a 0 and a 5 and nothing in between for this case. Say what you did and what the rule should be.**

I did not resolve or average a contradiction. The affected field should be set to `null`, and the contradiction should be recorded.

The scoring rubric should explicitly define how an unresolved contradiction affects the score. A defensible rule would be to treat the contradicted value as unreliable and require verification before giving full credit based on it.

The important point is that the model should not silently choose one of the contradictory values.

**5. How close were your top two candidates? If they were within 0.05, say what you would tell the committee and what you would change in the extraction to make that call defensible.**

The top two candidates were:

- `story-01.md` — 4.20
- `story-04.md` — 3.30

The difference was:

```text
4.20 - 3.30 = 0.90
```

Therefore, they were not within 0.05 in this run, so no additional tie-breaking rule was needed.

---

## Reflection (optional, one short paragraph)

Having written a role prompt, compressed a conversation and ranked six CV extractions, I would separate natural-language model work from deterministic program logic more clearly in future projects. I would use the model for tasks that require understanding unstructured text, such as extracting facts and assigning rubric scores, but I would validate the returned structure and perform important calculations and final decisions in code. I would also define rules for missing information, contradictions and ambiguous evidence before running the model.