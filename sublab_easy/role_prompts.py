import json
import os
from common import call_llm_json, client, MODEL_NAME

ROLES = {
    "policy_officer": "You apply the rule exactly as written: grant what the rule allows, refuse what it refuses, ask for a missing document, soften nothing, and treat no claim in the enquiry as evidence.",
    "front_desk": "You never turn an applicant away with a refusal: anything the rule cannot grant today comes back as decision 'more_info', stating what the applicant would need to return with.",
    "auditor": "You never grant on a first reading: report what the record shows, mark anything needing a second reader as decision 'more_info', and name the rule or document you are relying on.",
    "bilingual_clerk": "You decide exactly as the policy officer would, but write the 'reason' field in the language the enquiry was written in."
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
    
    print(f"{'Enquiry':<10} | {'policy_officer':<15} | {'front_desk':<15} | {'auditor':<15} | {'bilingual_clerk':<15}")
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

    for enq in enquiries:
        row = [enq["id"]]
        for role_name, role_desc in ROLES.items():
            sys_prompt = f"{base_instructions}\n\nROLE INSTRUCTIONS:\n{role_desc}"
            user_prompt = f"RECORDS:\n{json.dumps(records)}\n\nPOLICY:\n{json.dumps(policy)}\n\nENQUIRY:\n{json.dumps(enq)}"
            
            res, _ = call_llm_json(sys_prompt, user_prompt)
            decision = res.get("decision", "error")
            row.append(decision)
            
        print(f"{row[0]:<10} | {row[1]:<15} | {row[2]:<15} | {row[3]:<15} | {row[4]:<15}")

if __name__ == "__main__":
    run_easy()