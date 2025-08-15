import os, json, re
from typing import Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

PROVIDER = os.getenv("PROVIDER", "openai").lower()
MODEL = os.getenv("MODEL", "openai:gpt-5")

def _parse_json(text: str) -> Dict[str, Any]:
    # Try plain JSON, then try to extract from code fences
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        return json.loads(m.group(1))
    raise ValueError("Model did not return valid JSON.")

@retry(stop=stop_after_attempt(1), wait=wait_exponential(min=0.25, max=0.5))
def llm_json(system: str, user: str) -> Dict[str, Any]:
    if PROVIDER.startswith("openai"):
        from openai import OpenAI
        client = OpenAI()
        # responses API or chat completions both work; using chat for simplicity
        resp = client.chat.completions.create(
            model=MODEL.split(":")[1] if ":" in MODEL else "gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":user}
            ]
        )
        text = resp.choices[0].message.content
        return _parse_json(text)
    elif PROVIDER.startswith("anthropic"):
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=MODEL.split(":")[1] if ":" in MODEL else "claude-3-7-sonnet",
            max_tokens=1200,
            temperature=0.7,
            system=system,
            messages=[{"role":"user","content":user}]
        )
        # anthropic returns a list of content blocks
        text = "".join([b.text for b in msg.content if getattr(b,"type",None)=="text"])
        return _parse_json(text)
    else:
        raise RuntimeError(f"Unknown PROVIDER={PROVIDER}")