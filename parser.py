import os
import json
from openai import OpenAI

# This is the "brain" of the app. It turns a plain English instruction like
# "warm up the colours" into a structured JSON object the editor code can use.
# We use Groq because it gives you a free API key with a generous free tier,
# and it speaks the same "OpenAI style" API, so the code below looks familiar
# no matter which provider you use later.

SYSTEM_PROMPT = """You are an image editing instruction parser.
Given a user's natural language instruction, output ONLY a single JSON object (no markdown, no explanation, no code fences).

The JSON must have exactly these keys:
- "op": one of ["tone", "remove_bg", "enhance"]
- "region": one of ["full", "sky", "background", "foreground"]
- "params": an object with numeric values between -1.0 and 1.0 for any of: "warmth", "contrast", "saturation", "brightness"

Rules:
- If the instruction asks to remove or delete the background, use op "remove_bg", region "background", params {}
- If the instruction is vague like "make it better" or "enhance this", use op "enhance", region "full", with small positive contrast and saturation boosts
- Only include params that are actually relevant to the instruction
- Positive numbers increase the effect, negative numbers decrease it
- Always return valid JSON and nothing else

Examples:

Instruction: "warm up the colours"
Output: {"op": "tone", "region": "full", "params": {"warmth": 0.5}}

Instruction: "make the sky more dramatic"
Output: {"op": "tone", "region": "sky", "params": {"contrast": 0.4, "saturation": 0.3}}

Instruction: "remove the background"
Output: {"op": "remove_bg", "region": "background", "params": {}}

Instruction: "increase contrast a lot"
Output: {"op": "tone", "region": "full", "params": {"contrast": 0.7}}

Instruction: "make it darker and less saturated"
Output: {"op": "tone", "region": "full", "params": {"brightness": -0.4, "saturation": -0.3}}

Instruction: "enhance this photo"
Output: {"op": "enhance", "region": "full", "params": {"contrast": 0.2, "saturation": 0.15}}

Instruction: "cool it down a bit"
Output: {"op": "tone", "region": "full", "params": {"warmth": -0.3}}
"""


def get_client():
    api_key = os.environ.get("AQ.Ab8RN6LlghdYum6LsseJ8Bv298JsxSat8b76Qe6EkrzEjfr3fw")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is not set. "
            "Get a free key at console.groq.com and set it before running the app."
        )
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")


def parse_instruction(instruction: str, history=None) -> dict:
    """
    Sends the user's instruction (plus recent chat history for context) to the
    LLM and returns a dict like:
    {"op": "tone", "region": "sky", "params": {"contrast": 0.4}}
    """
    client = get_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        # keep only the last few turns so the prompt stays small and fast
        for turn in history[-6:]:
            if turn.get("role") in ("user", "assistant"):
                messages.append({"role": turn["role"], "content": str(turn["content"])})

    messages.append({"role": "user", "content": instruction})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # if the model ever returns something malformed, fall back to a safe default
        parsed = {"op": "enhance", "region": "full", "params": {"contrast": 0.1}}

    parsed.setdefault("op", "enhance")
    parsed.setdefault("region", "full")
    parsed.setdefault("params", {})
    return parsed
