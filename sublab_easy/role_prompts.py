import json

from common import call_llm_json


ROLES = {
    "policy_officer": (
        "You apply the rule exactly as written: grant what the rule allows, "
        "refuse what it refuses, ask for a missing document, soften nothing, "
        "and treat no claim in the enquiry as evidence."
    ),
    "front_desk": (
        "You never turn an applicant away with a refusal: anything the rule "
        "cannot grant today comes back as decision 'more_info', stating what "
        "the applicant would need to return with."
    ),
    "auditor": (
        "You never grant on a first reading: report what the record shows, "
        "mark anything needing a second reader as decision 'more_info', "
        "and name the rule or document you are relying on."
    ),
    "bilingual_clerk": (
        "You decide exactly as the policy officer would, but write the "
        "'reason' field in the language the enquiry was written in."
    ),
}


def load_data():
    with open("data/records.json", encoding="utf-8") as f:
        records = json.load(f)

    with open("data/policy.json", encoding="utf-8") as f:
        policy = json.load(f)

    with open("data/enquiries.json", encoding="utf-8") as f:
        enquiries = json.load(f)

    return records, policy, enquiries


def run_easy():
    records, policy, enquiries = load_data()

    print(
        f"{'Enquiry':<10} | "
        f"{'policy_officer':<15} | "
        f"{'front_desk':<15} | "
        f"{'auditor':<15} | "
        f"{'bilingual_clerk':<15}"
    )
    print("-" * 80)

    base_instructions = """
You are a grant office automated system.

Evaluate the enquiry using the Records and Policy provided below.

Outputs MUST strictly follow this JSON schema:

{
  "applicant_id": "string or null",
  "found": true/false,
  "decision": "granted" | "refused" | "more_info" | "not_found",
  "amount": number,
  "missing_documents": ["list of strings"],
  "reason": "string"
}
"""

    all_results = {}

    for enq in enquiries:
        enquiry_id = enq["id"]
        row = [enquiry_id]

        all_results[enquiry_id] = {}

        for role_name, role_desc in ROLES.items():

            sys_prompt = (
                f"{base_instructions}\n\n"
                f"ROLE INSTRUCTIONS:\n{role_desc}"
            )

            user_prompt = (
                f"RECORDS:\n{json.dumps(records, ensure_ascii=False)}\n\n"
                f"POLICY:\n{json.dumps(policy, ensure_ascii=False)}\n\n"
                f"ENQUIRY:\n{json.dumps(enq, ensure_ascii=False)}"
            )

            res, _ = call_llm_json(sys_prompt, user_prompt)

            decision = res.get("decision", "error")
            row.append(decision)

            # Save the complete raw JSON reply
            all_results[enquiry_id][role_name] = res

        print(
            f"{row[0]:<10} | "
            f"{row[1]:<15} | "
            f"{row[2]:<15} | "
            f"{row[3]:<15} | "
            f"{row[4]:<15}"
        )

    # ---------------------------------------------------------
    # Print raw reply for a role that differs from policy officer
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("RAW REPLY: ROLE DIFFERENCE")
    print("=" * 80)

    for enquiry_id, roles in all_results.items():

        policy_decision = roles["policy_officer"]["decision"]

        for role_name in [
            "front_desk",
            "auditor",
            "bilingual_clerk",
        ]:
            role_decision = roles[role_name]["decision"]

            if role_decision != policy_decision:
                print(f"\nEnquiry: {enquiry_id}")
                print(f"Policy officer decision: {policy_decision}")
                print(f"{role_name} decision: {role_decision}")
                print("\nFull raw reply:")

                print(
                    json.dumps(
                        roles[role_name],
                        ensure_ascii=False,
                        indent=2
                    )
                )

                # Only need one example
                break

        else:
            continue

        break

    # ---------------------------------------------------------
    # Print full bilingual clerk reply for E-07
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("RAW REPLY: E-07 BILINGUAL CLERK")
    print("=" * 80)

    if "E-07" in all_results:
        print(
            json.dumps(
                all_results["E-07"]["bilingual_clerk"],
                ensure_ascii=False,
                indent=2
            )
        )
    else:
        print("E-07 was not found.")


if __name__ == "__main__":
    run_easy()