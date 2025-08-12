# orchestrator/claims.py
from typing import Dict, Any, List
from .llm import llm_json
from .prompt_templates import (
    CLAIMS_SYSTEM,
    CLAIMS_USER,
    EXPAND_SYSTEM,
    EXPAND_USER,
    VERIFY_SYSTEM,
    VERIFY_USER,
)

def _ing_str(formulation: Dict[str, Any]) -> str:
    parts: List[str] = []
    for i in formulation.get("key_ingredients", []):
        dose = f" {i.get('dose_mg','')}mg" if i.get("dose_mg") else ""
        parts.append(f"{i['name']}{dose} ({i.get('evidence_level','n/a')})")
    return ", ".join(parts)

def generate_claims_by_angle(cfg: Dict[str, Any], target_per_angle: int = 8, style: str = 'balanced') -> Dict[str, List[Dict[str, str]]]:
    """
    Returns {angle_id: [ {text, style, angle_id}, ... ] } with de-dupe per angle.
    Expects cfg to include "angles" list (see input example I provide below).
    """
    brand, strategy, formulation = cfg["brand"], cfg["strategy"], cfg["formulation"]
    angle_claims: Dict[str, List[Dict[str, str]]] = {}

    # Style-specific instructions for the LLM
    style_instructions = {
        'benefit': "Focus on specific product benefits and results. Use language that emphasizes what the customer will gain.",
        'balanced': "Balance benefits with emotional appeal. Mix functional benefits with aspirational messaging.",
        'problem': "Focus on pain points and problems the product solves. Use language that resonates with customer frustrations.",
        'lifestyle': "Emphasize lifestyle integration and daily usage. Focus on how the product fits into the customer's routine."
    }
    
    style_instruction = style_instructions.get(style, style_instructions['balanced'])

    for angle in cfg.get("angles", []):
        user = CLAIMS_USER.format(
            tone=brand.get("tone", ""),
            audience=strategy.get("audience", ""),
            angle_name=angle.get("name", ""),
            pain_point=angle.get("pain_point", ""),
            trigger=angle.get("trigger", ""),
            positioning=angle.get("positioning", ""),
            ingredients=_ing_str(formulation),
            dos=", ".join(brand.get("voice_guide", {}).get("dos", [])),
            donts=", ".join(brand.get("voice_guide", {}).get("donts", [])),
            prefer=", ".join(brand.get("voice_guide", {}).get("lexicon", {}).get("prefer", [])),
            avoid=", ".join(brand.get("voice_guide", {}).get("lexicon", {}).get("avoid", [])),
            examples="\n".join(f"- {ex}" for ex in angle.get("headline_examples", [])),
            target_count=target_per_angle,
            product_name=formulation.get("product_name", "the product"),
            style_instruction=style_instruction,  # Add style-specific instruction
        )

        out = llm_json(CLAIMS_SYSTEM, user) or {}
        seen: set = set()
        claims: List[Dict[str, str]] = []
        for c in out.get("claims", []):
            txt = (c.get("text") or "").strip()
            if not txt:
                continue
            k = txt.lower()
            if k in seen:
                continue
            seen.add(k)
            claims.append({
                "text": txt,
                "style": style,  # Use the requested style
                "angle_id": angle.get("id", angle.get("name", "angle"))
            })
        angle_claims[angle.get("id", angle.get("name", "angle"))] = claims

    return angle_claims

def expand_copy(brand: Dict[str, Any], claim: str, strategy: Dict[str, Any]) -> Dict[str, str]:
    """
    Returns {"headline","byline","cta"}; fills defaults if model omits keys.
    """
    user = EXPAND_USER.format(
        tone=brand.get("tone", ""),
        audience=strategy.get("audience", ""),
        claim=claim,
    )
    out = llm_json(EXPAND_SYSTEM, user) or {}
    headline = (out.get("headline") or "").strip() or claim
    byline   = (out.get("byline") or "").strip() or "Inside-out support for hydrated, healthy-looking skin."
    cta      = (out.get("cta") or "").strip() or "Learn More"
    return {"headline": headline, "byline": byline, "cta": cta}

def verify_or_rewrite(claim: str, formulation: Dict[str, Any], banned: List[str]) -> Dict[str, Any]:
    """
    Returns {"ok": bool, "reason": str, "rewrite": str}
    """
    user = VERIFY_USER.format(
        claim=claim,
        ingredients=_ing_str(formulation),
        banned=", ".join(banned or []),
    )
    out = llm_json(VERIFY_SYSTEM, user) or {}
    ok = bool(out.get("ok"))
    reason = (out.get("reason") or "").strip()
    rewrite = (out.get("rewrite") or "").strip()
    return {"ok": ok, "reason": reason, "rewrite": rewrite}