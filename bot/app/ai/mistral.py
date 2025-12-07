import json
from typing import Dict, Any

import httpx
from mistralai import Mistral
from mistralai.models import MistralError

MISTRAL_API_KEY = "S2Iyc9vq3JiKdCKNGTrViTrItk7H5Umo"

# лучше пока использовать tiny, small у тебя уже давал 429
MODEL_NAME = "mistral-tiny-latest"

if not MISTRAL_API_KEY:
    raise RuntimeError("MISTRAL_API_KEY is not set in environment")

# Кастомный HTTP-клиент с таймаутом (например, 15 секунд)
http_client = httpx.Client(timeout=15.0)

client = Mistral(
    api_key=MISTRAL_API_KEY,
    client=http_client,  # важная строчка
)

SYSTEM_PROMPT = """
You are an experienced auto mechanic with deep practical expertise.
Your task is to estimate the typical service life of car parts and consumables
in MONTHS for an average driver.

Rules:
- Part names must be strictly in Russian, everything else must be strictly in English.
- All lifetimes must be INTEGER MONTHS.
- Assume an average driver and mixed city/highway usage.
- No Markdown, no code fences, no ``` blocks.
- The JSON MUST be flat: no hierarchical structure.
- "parts_lifetime" MUST be a flat dictionary where each key is a part name and each value is the lifetime in months.
- Include major assemblies AND individual components in the same flat list (e.g. "engine", "transmission", "engine oil", "brake pads", "tires", "battery", "spark plugs", "suspension parts", "engine components", etc.)
- Add any other important parts that a professional mechanic would include.

STRICT JSON FORMAT ONLY:

{
  "car": "<car_name>",
  "units": "months",
  "parts_lifetime": {
    "<part_name_1>": <integer_months>,
    "<part_name_2>": <integer_months>,
    ...
  }
}

No text before or after.
"""

def _extract_json(raw_content: str) -> str:
    content = raw_content.strip()

    if content.startswith("```"):
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1 :].strip()
        if content.endswith("```"):
            content = content[:-3].strip()

    return content


def get_parts_lifetime(car_name: str) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Estimate the service life of main parts and consumables for "
                f"the car \"{car_name}\" in MONTHS."
            ),
        },
    ]

    print(">> Sending request to Mistral...")

    try:
        response = client.chat.complete(
            model=MODEL_NAME,
            messages=messages,
        )
    except MistralError as e:
        # Здесь ты хотя бы увидишь, что именно прилетело (429, 401, 403 и т.д.)
        print("!! Mistral API error:")
        print("   message:", e.message)
        print("   status_code:", e.status_code)
        print("   body:", e.body)
        raise

    print(">> Got response, parsing JSON...")

    raw_content = response.choices[0].message.content
    content = _extract_json(raw_content)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print("!! Raw content from model:")
        print(raw_content)
        raise ValueError("Model returned invalid JSON") from e

    return data


if __name__ == "__main__":
    result = get_parts_lifetime("Toyota Camry 2015")
    print(">> Final result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
