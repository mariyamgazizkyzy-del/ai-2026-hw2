import json
import os
import argparse
from common import client, MODEL_NAME
from jsonschema import validate, ValidationError

def load_schema():
    with open("data/memory_state.schema.json", encoding="utf-8") as f:
        return json.load(f)

SYSTEM_COMPRESS_PROMPT = """
You are a conversation state summarizer. Summarize the chat history into a single valid JSON object that strictly matches this schema.

REQUIRED JSON FIELDS:
- "applicant_id": string or null (null if not mentioned)
- "topic": string (main topic of discussion)
- "facts": list of strings (facts stated BY THE APPLICANT only)
- "decisions": list of strings
- "constraints": list of strings
- "open_questions": list of strings
- "language": string (e.g. "en", "kk", "ru")

Output ONLY valid JSON.
"""

def run_medium(compressed_mode=False):
    with open("data/chat_script.json", encoding="utf-8") as f:
        script = json.load(f)
        
    schema = load_schema()
    messages = [{"role": "system", "content": "You are a grant office assistant."}]

    print(f"\n--- Running Mode: {'Compressed' if compressed_mode else 'Uncompressed'} ---")

    for i, turn in enumerate(script.get("turns", []), 1):
        user_text = turn["text"]
        
        if user_text == "compress" and compressed_mode:
            prompt_compress = [
                {"role": "system", "content": SYSTEM_COMPRESS_PROMPT},
                {"role": "user", "content": f"History to compress:\n{json.dumps(messages)}"}
            ]
            comp_res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=prompt_compress,
                response_format={"type": "json_object"}
            )
            state_json = json.loads(comp_res.choices[0].message.content)
            
            try:
                validate(instance=state_json, schema=schema)
                messages = [
                    {"role": "system", "content": f"Current Conversation Memory State: {json.dumps(state_json)}"}
                ]
                print(f"Turn {i}: Compressed successfully!")
            except ValidationError as e:
                print(f"Turn {i}: Compression validation failed: {e.message}")
            continue

        messages.append({"role": "user", "content": user_text})
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        
        tokens = response.usage.total_tokens if response.usage else 0
        print(f"Turn {i} ({turn.get('speaker', 'user')}): Tokens: {tokens}")

def interactive_mode():
    print("Interactive Chat Started. Type 'compress' to compress memory or 'exit' to quit.")
    messages = [{"role": "system", "content": "You are a helpful grant office assistant."}]
    schema = load_schema()

    while True:
        user_inp = input("\nYou: ")
        if user_inp.strip().lower() == "exit":
            break
            
        if user_inp.strip().lower() == "compress":
            prompt_compress = [
                {"role": "system", "content": SYSTEM_COMPRESS_PROMPT},
                {"role": "user", "content": f"History to compress:\n{json.dumps(messages)}"}
            ]
            comp_res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=prompt_compress,
                response_format={"type": "json_object"}
            )
            try:
                state_json = json.loads(comp_res.choices[0].message.content)
                validate(instance=state_json, schema=schema)
                messages = [{"role": "system", "content": f"State: {json.dumps(state_json)}"}]
                print("[Memory Compressed Successfully]")
            except Exception as e:
                print(f"[Compression Failed]: {e}")
            continue

        messages.append({"role": "user", "content": user_inp})
        res = client.chat.completions.create(model=MODEL_NAME, messages=messages)
        ans = res.choices[0].message.content
        messages.append({"role": "assistant", "content": ans})
        print(f"Assistant: {ans}")
        print(f"(Tokens used: {res.usage.total_tokens if res.usage else 'N/A'})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    else:
        run_medium(compressed_mode=False)
        run_medium(compressed_mode=True)