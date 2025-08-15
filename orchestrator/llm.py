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
        primary = MODEL.split(":")[1] if ":" in MODEL else "gpt-4o-mini"
        fallbacks = ["gpt-4o-mini", "gpt-4.1-mini"]
        tried = []
        for m in [primary] + [fm for fm in fallbacks if fm != primary]:
            try:
                resp = client.chat.completions.create(
                    model=m,
                    temperature=0.7,
                    messages=[
                        {"role":"system","content":system},
                        {"role":"user","content":user}
                    ]
                )
                text = resp.choices[0].message.content
                return _parse_json(text)
            except Exception as e:
                tried.append((m, str(e)))
                last_err = e
                continue
        raise last_err
    elif PROVIDER.startswith("anthropic"):
        import anthropic
        client = anthropic.Anthropic()
        primary = MODEL.split(":")[1] if ":" in MODEL else "claude-3-7-sonnet"
        fallbacks = ["claude-3-7-sonnet", "claude-3-5-sonnet"]
        tried = []
        for m in [primary] + [fm for fm in fallbacks if fm != primary]:
            try:
                msg = client.messages.create(
                    model=m,
                    max_tokens=1200,
                    temperature=0.7,
                    system=system,
                    messages=[{"role":"user","content":user}]
                )
                text = "".join([b.text for b in msg.content if getattr(b,"type",None)=="text"])
                return _parse_json(text)
            except Exception as e:
                tried.append((m, str(e)))
                last_err = e
                continue
        raise last_err
    else:
        raise RuntimeError(f"Unknown PROVIDER={PROVIDER}")