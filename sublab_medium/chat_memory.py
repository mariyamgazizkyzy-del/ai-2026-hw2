import json
import argparse

from common import client, MODEL_NAME
from jsonschema import validate, ValidationError


# ============================================================
# LOAD SCHEMA
# ============================================================

def load_schema():
    with open(
        "data/memory_state.schema.json",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ============================================================
# COMPRESSION PROMPT
# ============================================================

SYSTEM_COMPRESS_PROMPT = """
You are a conversation state summarizer for a grant office.

Your task is to compress the conversation into ONE JSON object.

The JSON MUST strictly match the provided schema.

Required fields:

- applicant_id:
  string or null.
  Preserve the applicant ID exactly if it was stated.

- topic:
  main topic of the conversation.

- facts:
  list of important facts stated BY THE APPLICANT.

- decisions:
  decisions or conclusions already made.

- constraints:
  constraints stated by the applicant.
  Examples: availability, deadlines, scheduling restrictions.

- open_questions:
  questions raised by the applicant that have not been answered.

- language:
  main language of the conversation.

Important rules:

1. Do NOT invent facts.
2. Do NOT guess missing information.
3. Preserve facts that were stated only once.
4. Preserve applicant identity.
5. Preserve financial information.
6. Preserve missing documents.
7. Preserve scheduling constraints.
8. Preserve unanswered questions.
9. If a question was asked but not answered, keep it in open_questions.
10. Output ONLY valid JSON.
"""


# ============================================================
# SEND NORMAL CHAT MESSAGE
# ============================================================

def send_message(messages):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages
    )

    answer = response.choices[0].message.content

    tokens = (
        response.usage.total_tokens
        if response.usage
        else 0
    )

    return answer, tokens


# ============================================================
# COMPRESS MEMORY
# ============================================================

def compress_memory(messages, schema):

    compression_messages = [
        {
            "role": "system",
            "content": SYSTEM_COMPRESS_PROMPT
        },
        {
            "role": "user",
            "content":
                "Here is the conversation history:\n\n"
                + json.dumps(
                    messages,
                    ensure_ascii=False,
                    indent=2
                )
        }
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=compression_messages,
        response_format={
            "type": "json_object"
        },
        temperature=0.0
    )

    content = response.choices[0].message.content

    # --------------------------------------------------------
    # JSON parsing
    # --------------------------------------------------------

    try:
        state = json.loads(content)

    except json.JSONDecodeError as e:

        print("\n[Compression Failed]")
        print("The model returned invalid JSON.")
        print(content)

        return None

    # --------------------------------------------------------
    # Schema validation
    # --------------------------------------------------------

    try:

        validate(
            instance=state,
            schema=schema
        )

    except ValidationError as e:

        print("\n[Compression Failed]")
        print(
            "The JSON did not pass schema validation:"
        )
        print(e.message)

        return None

    return state


# ============================================================
# RUN SCRIPTED CONVERSATION
# ============================================================

def run_medium(compressed_mode=False):

    # --------------------------------------------------------
    # Load chat script
    # --------------------------------------------------------

    with open(
        "data/chat_script.json",
        encoding="utf-8"
    ) as f:
        script = json.load(f)

    schema = load_schema()

    conversation = script.get(
        "conversation",
        []
    )

    # --------------------------------------------------------
    # Initial system message
    # --------------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": (
                "You are a grant office assistant. "
                "Answer the applicant clearly and accurately."
            )
        }
    ]

    mode_name = (
        "Compressed"
        if compressed_mode
        else "Uncompressed"
    )

    print("\n" + "=" * 70)
    print(f"RUNNING MODE: {mode_name}")
    print("=" * 70)

    token_results = []

    # --------------------------------------------------------
    # Process conversation
    # --------------------------------------------------------

    for turn_number, user_text in enumerate(
        conversation,
        start=1
    ):

        # ====================================================
        # COMPRESSION COMMAND
        # ====================================================

        if user_text == "<compress>":

            # -----------------------------------------------
            # Uncompressed run:
            # skip compression marker completely.
            # -----------------------------------------------

            if not compressed_mode:

                print(
                    f"\nTurn {turn_number}: "
                    "<compress> skipped"
                )

                continue

            # -----------------------------------------------
            # Compressed run:
            # compress the conversation.
            # -----------------------------------------------

            print(
                f"\nTurn {turn_number}: "
                "COMPRESSION"
            )

            state = compress_memory(
                messages,
                schema
            )

            # ------------------------------------------------
            # IMPORTANT:
            # If compression fails, KEEP the old history.
            # ------------------------------------------------

            if state is None:

                print(
                    "Compression failed."
                )

                print(
                    "Original conversation history "
                    "was kept."
                )

                continue

            # ------------------------------------------------
            # Compression successful
            # ------------------------------------------------

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a grant office assistant.\n\n"
                        "Current Conversation Memory State:\n"
                        + json.dumps(
                            state,
                            ensure_ascii=False,
                            indent=2
                        )
                    )
                }
            ]

            print(
                "Compression successful."
            )

            print(
                "\nSTATE OBJECT:"
            )

            print(
                json.dumps(
                    state,
                    ensure_ascii=False,
                    indent=2
                )
            )

            continue

        # ====================================================
        # NORMAL USER TURN
        # ====================================================

        messages.append(
            {
                "role": "user",
                "content": user_text
            }
        )

        answer, tokens = send_message(
            messages
        )

        messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        token_results.append(
            {
                "turn": turn_number,
                "tokens": tokens
            }
        )

        print(
            f"\nTurn {turn_number}"
        )

        print(
            f"User: {user_text}"
        )

        print(
            f"Tokens: {tokens}"
        )

        print(
            f"Assistant: {answer}"
        )

    # ========================================================
    # TOKEN SUMMARY
    # ========================================================

    print("\n" + "-" * 70)
    print(f"{mode_name} TOKEN TABLE")
    print("-" * 70)

    for row in token_results:

        print(
            f"Turn {row['turn']:>2}: "
            f"{row['tokens']} tokens"
        )

    if token_results:

        peak = max(
            row["tokens"]
            for row in token_results
        )

        total = sum(
            row["tokens"]
            for row in token_results
        )

        print("-" * 70)
        print(f"Peak tokens: {peak}")
        print(f"Total tokens: {total}")

    return messages, token_results


# ============================================================
# RUN PROBES
# ============================================================

def run_probes(messages, probes):

    print("\n" + "=" * 70)
    print("PROBE RESULTS")
    print("=" * 70)

    results = []

    for probe in probes:

        question = probe["question"]
        expected_strings = probe["expect_contains"]

        # -----------------------------------------------
        # Copy conversation so probe does not change
        # the original conversation state.
        # -----------------------------------------------

        probe_messages = list(messages)

        probe_messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        answer, tokens = send_message(
            probe_messages
        )

        answer_lower = answer.lower()

        retrieved = any(
            expected.lower() in answer_lower
            for expected in expected_strings
        )

        results.append(
            {
                "id": probe["id"],
                "question": question,
                "retrieved": retrieved,
                "answer": answer,
                "tokens": tokens
            }
        )

        print(
            f"\n{probe['id']}"
        )

        print(
            f"Question: {question}"
        )

        print(
            f"Retrieved: "
            f"{'Yes' if retrieved else 'No'}"
        )

        print(
            f"Answer: {answer}"
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    retrieved_count = sum(
        1
        for r in results
        if r["retrieved"]
    )

    print("\n" + "-" * 70)

    print(
        f"Retrieved: "
        f"{retrieved_count}/{len(results)}"
    )

    return results


# ============================================================
# INTERACTIVE MODE
# ============================================================

def interactive_mode():

    print("=" * 70)
    print("INTERACTIVE GRANT OFFICE CHAT")
    print("=" * 70)

    print(
        "Type your message."
    )

    print(
        "Type 'compress' to compress memory."
    )

    print(
        "Type 'exit' to quit."
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful grant office assistant."
            )
        }
    ]

    schema = load_schema()

    while True:

        user_input = input("\nYou: ").strip()

        # ====================================================
        # EXIT
        # ====================================================

        if user_input.lower() == "exit":

            print(
                "Interactive chat ended."
            )

            break

        # ====================================================
        # COMPRESS
        # ====================================================

        if user_input.lower() == "compress":

            print(
                "\nCompressing memory..."
            )

            state = compress_memory(
                messages,
                schema
            )

            # -----------------------------------------------
            # Failed compression:
            # keep history.
            # -----------------------------------------------

            if state is None:

                print(
                    "[Compression failed]"
                )

                print(
                    "Conversation history was kept."
                )

                continue

            # -----------------------------------------------
            # Successful compression
            # -----------------------------------------------

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful grant office assistant.\n\n"
                        "Current Conversation Memory State:\n"
                        + json.dumps(
                            state,
                            ensure_ascii=False,
                            indent=2
                        )
                    )
                }
            ]

            print(
                "\n[Memory Compressed Successfully]"
            )

            print(
                json.dumps(
                    state,
                    ensure_ascii=False,
                    indent=2
                )
            )

            continue

        # ====================================================
        # NORMAL CHAT
        # ====================================================

        messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        answer, tokens = send_message(
            messages
        )

        messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        print(
            f"\nAssistant: {answer}"
        )

        print(
            f"Tokens: {tokens}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--interactive",
        action="store_true"
    )

    args = parser.parse_args()

    # ========================================================
    # INTERACTIVE
    # ========================================================

    if args.interactive:

        interactive_mode()

        return

    # ========================================================
    # SCRIPTED RUNS
    # ========================================================

    with open(
        "data/chat_script.json",
        encoding="utf-8"
    ) as f:
        script = json.load(f)

    probes = script.get(
        "probes",
        []
    )

    # --------------------------------------------------------
    # UNCOMPRESSED
    # --------------------------------------------------------

    messages_a, tokens_a = run_medium(
        compressed_mode=False
    )

    probes_a = run_probes(
        messages_a,
        probes
    )

    # --------------------------------------------------------
    # COMPRESSED
    # --------------------------------------------------------

    messages_b, tokens_b = run_medium(
        compressed_mode=True
    )

    probes_b = run_probes(
        messages_b,
        probes
    )

    # ========================================================
    # FINAL COMPARISON
    # ========================================================

    peak_a = (
        max(r["tokens"] for r in tokens_a)
        if tokens_a
        else 0
    )

    peak_b = (
        max(r["tokens"] for r in tokens_b)
        if tokens_b
        else 0
    )

    total_a = sum(
        r["tokens"]
        for r in tokens_a
    )

    total_b = sum(
        r["tokens"]
        for r in tokens_b
    )

    retrieved_a = sum(
        1
        for r in probes_a
        if r["retrieved"]
    )

    retrieved_b = sum(
        1
        for r in probes_b
        if r["retrieved"]
    )

    print("\n" + "=" * 70)
    print("FINAL COMPARISON")
    print("=" * 70)

    print(
        f"Uncompressed peak: {peak_a}"
    )

    print(
        f"Compressed peak:   {peak_b}"
    )

    print(
        f"Uncompressed total: {total_a}"
    )

    print(
        f"Compressed total:   {total_b}"
    )

    print(
        f"Uncompressed probes: "
        f"{retrieved_a}/{len(probes)}"
    )

    print(
        f"Compressed probes:   "
        f"{retrieved_b}/{len(probes)}"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()