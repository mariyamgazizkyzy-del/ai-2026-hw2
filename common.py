import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Модель для OpenRouter
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
)

def call_llm_json(system_prompt: str, user_prompt: str, schema: dict = None) -> tuple[dict, int]:
    messages = [
        {"role": "system", "content": system_prompt + "\n\nYou MUST reply ONLY with valid JSON. Do not include markdown codeblocks (```json ... ```) or any extra text."},
        {"role": "user", "content": user_prompt}
    ]
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    content = response.choices[0].message.content
    tokens = response.usage.total_tokens if response.usage else 0
    
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        clean_content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_content)
        
    return data, tokens