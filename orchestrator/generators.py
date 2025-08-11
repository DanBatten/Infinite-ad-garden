import random
from typing import Dict, Any, List

# ---- MOCK GENERATORS (works offline) ----
# Swap these with API-backed implementations (OpenAI, Anthropic, etc.)

def generate_claims(strategy: Dict[str, Any], formulation: Dict[str, Any], k:int=20) -> List[Dict[str, str]]:
    audience = strategy.get("audience", "All")
    angle = strategy.get("angle", "clean energy")
    ingredients = ", ".join(i["name"] for i in formulation.get("key_ingredients", []))
    bases = [
        "Steady focus without jitters",
        "Clean energy that lasts",
        "Dial in your flow state",
        "Energy plus calm clarity",
        "Feel locked-in and light",
        "Smooth focus for long sessions",
        "Stay sharp and composed",
        "Focus that feels natural",
        "Clarity for heavy lift days",
        "Energy that respects rest"
    ]
    out = []
    for i in range(k):
        base = bases[i % len(bases)]
        out.append({
            "text": base,
            "support_rationale": f"Angle: {angle}. Ingredients: {ingredients}."
        })
    return out

def expand_copy(brand: Dict[str, Any], claim_text: str, strategy: Dict[str, Any]) -> Dict[str, str]:
    tone = brand.get("tone", "confident, modern")
    audience = strategy.get("audience", "All")
    headline = f"{claim_text}."
    byline = f"Built for {audience}. {tone.title()} performance you can feel."
    cta = "Learn More"
    return {"headline": headline[:70], "byline": byline[:140], "cta": cta}

def image_brief(brand: Dict[str, Any], claim_text: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
    palette = brand.get("palette", ["#000000", "#FFFFFF"])
    style = brand.get("image_style", "studio-lit product on color backdrop")
    fmt = strategy.get("format", "1080x1440")
    prompt = f"{style}, product-forward, minimal graphics, palette {palette}, fits {fmt}, no text in image"
    return {"prompt": prompt, "negative_prompt": "no people, no hands, no text overlays", "seed": random.randint(1, 1_000_000)}

def generate_image_url(brief: Dict[str, Any], variant_id: str) -> str:
    # For the prototype we return a local placeholder image served by server.py
    return f"http://localhost:8001/static/images/product.png"
