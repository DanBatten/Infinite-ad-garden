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
    Now style-first approach to avoid angle/style conflicts.
    """
    brand, strategy, formulation = cfg["brand"], cfg["strategy"], cfg["formulation"]
    angle_claims: Dict[str, List[Dict[str, str]]] = {}

    # Style-specific instructions for the LLM
    style_instructions = {
        'benefit-focused': "STYLE: Lead with the main benefit the audience cares about most. Use 'you' language and positive, aspirational tone. Frame as personal transformation. Example approach: 'You get [specific benefit] that [transformation outcome].'",
        
        'problem-solution': "STYLE: Start with a clear, relatable problem the audience recognizes. Then present the product as the natural solution. Use empathetic tone. Example approach: 'Tired of [problem]? [Product] solves this by [solution].'",
        
        'social-proof': "STYLE: Use credibility and validation to build trust. Include customer voices, expert endorsements, or review elements. Keep conversational and authentic. Example approach: 'Join [X] others who [benefit]' or 'Experts recommend [product] for [reason].'",
        
        'urgency-driven': "STYLE: Create urgency with time/quantity triggers and clear calls to action. Use energetic, persuasive tone. Include words like 'today,' 'limited,' 'only,' 'now.' Example approach: 'Only [X] left - [benefit] today!'",
        
        'mixed-styles': "STYLE: Combine multiple approaches subtly - start with a hook, add light pain point, include social proof, end with soft urgency. Keep balanced and versatile. Example approach: '[Hook] + [Light problem] + [Social proof] + [Soft urgency].'"
    }
    
    style_instruction = style_instructions.get(style, style_instructions['mixed-styles'])

    # Get all available angles for context
    angles = cfg.get("angles", [])
    angle_context = ""
    if angles:
        angle_context = f"Available angles: {', '.join([a.get('name', '') for a in angles])}"
    
    # Generate claims for the specific style, using angles as context but not as the primary driver
    user = CLAIMS_USER.format(
        tone=brand.get("tone", ""),
        audience=strategy.get("audience", ""),
        angle_name=f"All angles: {angle_context}",
        pain_point="Various pain points across angles",
        trigger="Multiple triggers",
        positioning="Overall brand positioning",
        ingredients=_ing_str(formulation),
        dos=", ".join(brand.get("voice_guide", {}).get("dos", [])),
        donts=", ".join(brand.get("voice_guide", {}).get("donts", [])),
        prefer=", ".join(brand.get("voice_guide", {}).get("lexicon", {}).get("prefer", [])),
        avoid=", ".join(brand.get("voice_guide", {}).get("lexicon", {}).get("avoid", [])),
        examples="\n".join(f"- {ex}" for ex in angles[0].get("headline_examples", []) if angles),
        target_count=target_per_angle * len(angles) if angles else target_per_angle,
        product_name=formulation.get("product_name", "the product"),
        style_instruction=style_instruction,
        style=style,
    )

    out = llm_json(CLAIMS_SYSTEM, user) or {}
    seen: set = set()
    all_claims: List[Dict[str, str]] = []
    
    for c in out.get("claims", []):
        txt = (c.get("text") or "").strip()
        if not txt:
            continue
        k = txt.lower()
        if k in seen:
            continue
        seen.add(k)
        all_claims.append({
            "text": txt,
            "style": style,
            "angle_id": "style_generated"  # Mark as style-generated, not angle-specific
        })
    
    # Distribute claims across angles if we have them
    if angles and all_claims:
        claims_per_angle = len(all_claims) // len(angles)
        for i, angle in enumerate(angles):
            start_idx = i * claims_per_angle
            end_idx = start_idx + claims_per_angle if i < len(angles) - 1 else len(all_claims)
            angle_claims[angle.get("id", angle.get("name", f"angle_{i}"))] = all_claims[start_idx:end_idx]
    else:
        # Fallback: put all claims under a general angle
        angle_claims["general"] = all_claims

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