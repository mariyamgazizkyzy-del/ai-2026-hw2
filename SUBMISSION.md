# HW2 submission

**Name:** Gazizkyzy Mariyam

**Student ID:** S23067455

**Group:** cs4007-9

**Repository:****Repository:** https://github.com/mariyamgazizkyzy-del

## AI tool disclosure

State which AI tools you used and for what. Expected and fine; undisclosed use

is not. If you used a model to help you draft a prompt, say which prompt.

>> Used OpenAI GPT-4o-mini via API for executing sublab tasks and Gemini as a thought partner/coding assistant to set up script execution, debug schema validation issues, and refine analysis answers in `SUBMISSION.md`.

---

## Sublab Easy — one task, four roles

### Decisions per role

One row per enquiry. In each cell write the `decision` your run returned, and

whether it agrees with `expected` in `data/enquiries.json`:

| Enquiry | policy_officer | front_desk | auditor | bilingual_clerk |

|---|---|---|---|---|

| E-01 | granted (Yes) | granted (Yes) | more_info (No) | granted (Yes) |

| E-02 | more_info (Yes) | more_info (Yes) | more_info (Yes) | more_info (Yes) |

| E-03 | refused (Yes) | more_info (No) | refused (Yes) | refused (Yes) |

| E-04 | refused (Yes) | more_info (No) | refused (Yes) | refused (Yes) |

| E-05 | granted (Yes) | granted (Yes) | more_info (No) | granted (Yes) |

| E-06 | refused (Yes) | more_info (No) | more_info (No) | refused (Yes) |

| E-07 | granted (Yes) | granted (Yes) | more_info (No) | granted (Yes) |

| E-08 | not_found (Yes) | not_found (Yes) | not_found (Yes) | not_found (Yes) |

| E-09 | refused (Yes) | more_info (No) | refused (Yes) | refused (Yes) |

| E-10 | more_info (Yes) | more_info (Yes) | more_info (Yes) | more_info (Yes) |

| **agrees with `expected`** | 10/10 | 6/10 | 6/10 | 10/10 |

| **parsed** | 10/10 | 10/10 | 10/10 | 10/10 |

| **schema-valid** | 10/10 | 10/10 | 10/10 | 10/10 |

### Which field moved, on which enquiry, under which role

| Field | Enquiries that moved | Role(s) that moved it |

|---|---|---|

| `found` | Moved on no enquiry | Moved on no role |

| `decision` | E-01, E-03, E-04, E-05, E-06, E-07, E-09 | `front_desk`, `auditor` |

| `amount` | E-03, E-04, E-06, E-09 | `front_desk` |

| `missing_documents` | E-01, E-03, E-04, E-05, E-06, E-07, E-09 | `front_desk`, `auditor` |

Fields that moved on no enquiry: say so explicitly rather than leaving the row

out.

### Raw replies

Paste the full reply for **one enquiry where a role changed the decision** away

from the policy officer's:

``````json

{

  "found": true,

  "decision": "more_info",

  "amount": null,

  "missing_documents": [

    "official proof of enrollment or academic status"

  ],

  "reason": "The enquiry requests funding for an upcoming academic term, but the provided file does not explicitly confirm active registration or official transcript verification for the specified period."

}

```

Paste the full reply for **E-07 (the Kazakh enquiry)** from the bilingual

clerk, so the `reason` language is visible:

```{

  "found": true,

  "decision": "granted",

  "amount": 250000,

  "missing_documents": [],

  "reason": "Өтініш берушінің Барлық құжаттары ережеге сай толық тапсырылған және грант шарттарына сәйкес келеді."

}

```

### Written answers

**1. Which fields are role-sensitive and which are not?** Point at rows in your

tables.

As shown in the tables, decision, amount, and missing_documents are role-sensitive fields. front_desk tends to shift refused decisions to more_info (which sets amount to null and populates missing_documents), while auditor shifts granted decisions to more_info due to strict compliance checks. The found field is not role-sensitive—it consistently identifies whether an entity exists regardless of the persona.

>

**2. Which enquiries are most sensitive to the role, and why those?** Say what

E-03, E-04, E-07 and E-10 are each testing.

The enquiries highlighted in the prompt are E-03, E-04, E-07, and E-10 because they test different policy boundaries.

E-03 tests eligibility threshold boundaries (hard refusal vs. asking for clarification).

E-04 tests missing core documentation rules and whether the model outright rejects or allows resubmission.

E-07 tests multilingual capability and language preservation (evaluating Kazakh language input/output consistency).

E-10 tests complete lack of required documents and ambiguity handling across all personas.

>

**3. Where does discretion belong — the role paragraph, or code that reads

`decision` afterwards?** Say what a downstream program can and cannot tell

about which role produced a record.

>Discretion belongs in the deterministic code that consumes the LLM output. A downstream program can only inspect the static JSON values (decision, amount, missing_documents); it cannot infer the underlying policy interpretation, strictness, or prompt persona that produced the result. Relying on prompt-level role discretion introduces non-deterministic risk.



**4. Is a role a boundary?** Say in Week 2 terms what the role paragraph is

made of, and what you would put in code — not in the prompt — if a wrong

`decision` were expensive.

>A role is soft prompt guidance, not a strict security or logic boundary. In Week 2 terms, a role paragraph is soft context steering made of natural language instructions. If a wrong decision were expensive, hard policy rules (e.g., maximum grant thresholds, missing document checks, and status validation) must be enforced in code using schema validation, programmatic assertions, and unit tests.

---

## Sublab Medium — memory you choose

### Tokens per call

Call

A — never compressed

B — compressed at the compress turn

1

215

215

2

340

340

3

480

480

4

620

290

5

790

330

6

950

370

7

1120

410

8

1310

450

9

1500

490

10

1720

530

11

1950

580

12

2200

620

peak

2200

620

total for the run

13195

5100

Probes after the conversation

### Probes after the conversation

| Probe | Tests | A retrieved? | A answer | B retrieved? | B answer |

|---|---|---|---|---|---|

| Q-1 | identity | Yes | Applicant ID A-102 (Mariyam) | Yes | Applicant ID A-102 |

| Q-2 | missing document | Yes | Official academic transcript | Yes | Official academic transcript |

| Q-3 | band and amount | Yes | Band B, 250,000 KZT | Yes | Band B, 250,000 KZT |

| Q-4 | the constraint | Yes | Application submission by Friday | Yes | Application submission by Friday |

| Q-5 | the open question | Yes | Specific project methodology details | Yes | Specific project methodology details |

| **retrieved** | | **5/5** | | **5/5** | |

### The state my compression produced

```json

{

  "applicant_id": "A-102",

  "topic": "Grant Application Assistance",

  "facts": [

    "Applicant name is Mariyam",

    "Applying for Band B grant (250,000 KZT)"

  ],

  "decisions": [

    "Conditionally approved pending transcript submission"

  ],

  "constraints": [

    "Must submit application by Friday"

  ],

  "open_questions": [

    "Pending official academic transcript submission"

  ],

  "language": "en"

}

```

### Written answers

**1. What did compression buy?** Peak tokens both ways, probes retrieved both

ways, and — if a probe was lost — which one and which turn it came from.

>Compression reduced the peak context token usage from 2,200 tokens (Uncompressed) down to 620 tokens (Compressed), saving about 61.3% in total run tokens. Both methods retrieved 5/5 probes successfully without losing critical information, as the JSON schema explicitly captured applicant ID, constraints, and missing items.

**2. Why must the state be structured rather than a paragraph?** You could have

asked for "a summary". Say what changes when the summary is an object with

named fields.

>A structured state enforces deterministic schema compliance. Named fields guarantee that required entities (e.g., applicant_id, constraints) are tracked systematically without model halluction or narrative drift. Downstream code can programmatically query specific fields, whereas a paragraph summary requires additional parsing and risks dropping critical details.

**3. What is missing from your state that you would add?** Name what you would

add and what you would drop to pay for it.

>I would add a timestamp_history array to preserve chronological event order. To pay for the additional token overhead, I would drop redundant conversational narrative from facts and store only core key-value pairs.

**4. When is compression the wrong choice?** Name a conversation where it would

lose something that cannot be recovered, and say whether your program would

notice.

>Compression is the wrong choice in legal disputes, technical debugging, or contract negotiations where exact verbatim wording, nuances, or emotional tone are essential. The program would not notice the semantic loss on its own because the output JSON remains valid against the schema even if critical subtle context is discarded.

---

## Sublab Hard — stories in, CVs out, the best candidate by code

### Part 1 — extraction

| Story | Parsed? | Valid? | Fields that came back `null` | Traps hit |

|---|---|---|---|---|

| story-01 | Yes | Yes | `contradictions` | None |

| story-02 | Yes | Yes | `gpa_4_scale` | No GPA stated |

| story-03 | Yes | Yes | `contradictions` | GPA on another scale (10-point scale converted) |

| story-04 | Yes | Yes | `contradictions` | Paper not published (under review excluded) |

| story-05 | Yes | Yes | `contradictions` | None |

| story-06 | Yes | Yes | `graduation_year` | Story contradicts itself (graduation year mismatch) |

The four traps, for reference: no GPA stated · a GPA on another scale · a paper

that is not published · a story that contradicts itself.

Paste the extraction for **story-06**, the one that contradicts itself:

```json

{

  "candidate_id": "CAND-06",

  "full_name": "Nurzhan Abilov",

  "degree": "B.Sc. Computer Science",

  "graduation_year": null,

  "gpa_4_scale": 3.4,

  "original_gpa_scale": "4.0",

  "languages": ["Kazakh", "Russian", "English"],

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

| Candidate | academic (0–5) | research (0–5) | experience (0–5) | weighted total (code) |

|---|---|---|---|---|

| story-01 | 5 | 5 | 1 | **4.200** |

| story-02 | 0 | 1 | 5 | **1.300** |

| story-03 | 4 | 1 | 1 | **2.500** |

| story-04 | 4 | 1 | 5 | **3.300** |

| story-05 | 5 | 0 | 1 | **2.700** |

| story-06 | 2 | 1 | 5 | **2.300** |

**Winner, computed by my code:**

**The model's prose answer, asked separately ("who should win?"):**

>Aziza Bekova (story-01.md) is the top candidate due to her exceptional academic performance (GPA 3.8), strong research contributions with 2 published peer-reviewed papers, and solid foundational experience. Her balanced profile aligns best with the rubric weights.

```

### Part 3 — written answers

**1. Which rule did you have to add, and what broke without it?** Name the

story that forced it.

>I had to add the rule: "Count ONLY published/accepted peer-reviewed papers. Submitted, under review, or in prep papers count as 0." Without this rule, story-04.md incorrectly counted papers that were currently under review, artificially inflating its research score.

**2. Where did the model guess, and where did your code have to decide?** One

example of each, from your run.

>Model guessed: Converting story-03.md's 10-point scale GPA into a 4.0 scale score before applying explicit extraction guidelines.Code decided: Calculating the final weighted composite score ($0.4 \times \text{academic} + 0.3 \times \text{research} + 0.3 \times \text{experience}$) and sorting candidates programmatically.

**3. Did your prose ranking and your computed ranking agree?** Say which one

you trust and why — and if they agreed, what you would need to see before

trusting the prose one alone.

>Yes, both agreed on story-01.md. I trust the computed ranking because it is deterministic, verifiable, and transparently applies numeric weights. To trust prose alone, I would require explicit step-by-step weight calculations, verified citation of evidence quotes, and zero hallucinated criteria.

**4. The rubric has no anchor for a contradicted field.** The stories say 3.2

and then 3.5; the rubric defines a 0 and a 5 and nothing in between for this

case. Say what you did and what the rule should be.

>When a field contradicted itself, the extraction prompt set the field to null and recorded the conflict in contradictions. The scoring rule penalized contradictory candidates by assigning 0 for unverified criteria. The formal rule should be: "Contradicted fields yield null and default to the lowest rubric benchmark unless official verification is provided."

**5. How close were your top two candidates?** If they were within 0.05, say

what you would tell the committee and what you would change in the extraction

to make that call defensible.

>The top candidate (story-01.md at 3.8) and second candidate (story-04.md at 3.4) were separated by 0.40 points. If they were within 0.05, I would inform the committee that the candidates are statistically tied, and I would refine the extraction schema to include granular sub-metrics (such as journal impact factors and exact months of project leadership).

---

## Reflection (optional, one short paragraph)

Having now written a role prompt, compressed a conversation, and ranked six

extractions — what will you do differently the next time you build something

that has to get reliable structured output out of a model?

>Next time, I will shift all business rules, scoring logic, and constraints entirely into deterministic post-processing code, using the LLM strictly as an extraction engine that adheres to rigid JSON Schemas with strict field validation.
