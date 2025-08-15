# orchestrator/claims.py
from typing import Dict, Any, List
from .llm import llm_json
from .knowledge import load_knowledge_texts
import os
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
    # Style-specific instructions for the LLM, with creativity guardrails
    style_instructions = {
        'benefit-focused': "STYLE: Lead with the main benefit the audience cares about most. Use 'you' language and positive, aspirational tone. Frame as personal transformation. Creativity: avoid clichés (e.g., elevate/unlock/transform), use vivid but concise imagery, and vary verbs across claims. Example approach: 'You get [specific benefit] that [tangible outcome].'",
        
        'problem-solution': "STYLE: Start with a clear, relatable problem the audience recognizes. Then present the product as the natural solution. Use empathetic tone. Creativity: prefer concrete, sensory phrasing; avoid clichés. Example approach: 'Tired of [problem]? [Product] helps by [specific mechanism/benefit].'",
        
        'social-proof': "STYLE: Use credibility and validation to build trust. Include customer voices, expert endorsements, or review elements. Keep conversational and authentic. Creativity: avoid generic templates ('Join X others…'); use fresh constructs. Example approach: quote snippets or specific outcomes.",
        
        'urgency-driven': "STYLE: Create urgency with time/quantity triggers and clear calls to action. Use energetic, persuasive tone. Creativity: keep tasteful; avoid hype. Example approach: 'Limited drop—[benefit] starts now.'",
        
        'mixed-styles': "STYLE: Combine multiple approaches subtly—start with a hook, add a light pain point, include social proof, end with soft urgency. Creativity: rotate verbs and structure; avoid repetition across claims."
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

    # Lightweight RAG: attach concise brand/global knowledge as a prefix note
    brand_name = brand.get("name", "")
    # Knowledge influence budgets
    # Prefer separate brand vs ad influence if provided
    infl = os.getenv("KNOWLEDGE_INFLUENCE", os.getenv("KNOWLEDGE_AD_INFLUENCE", "medium")).lower()
    brand_infl = os.getenv("KNOWLEDGE_BRAND_INFLUENCE", infl).lower()
    budgets = {
        "low": (1000, 1000),
        "medium": (3000, 3000),
        "high": (6000, 6000),
    }
    brand_chars, global_chars = budgets.get(brand_infl, budgets["medium"]) 
    kb = load_knowledge_texts(brand_name, brand_chars=brand_chars, global_chars=global_chars)
    if kb:
        user = f"""[REFERENCE DOCS]\n{kb}\n\n[INSTRUCTION]\n{user}"""
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

def expand_copy(brand: Dict[str, Any], claim: str, strategy: Dict[str, Any], 
                template_requirements: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Returns dynamic structure based on template requirements.
    Completely template-driven - no hardcoded fields.
    """
    # Build dynamic prompt based on template requirements
    if template_requirements and template_requirements.get('elements'):
        # Template-specific generation
        elements = template_requirements.get('elements', [])
        element_info = []
        required_fields = []
        
        for element in elements:
            name = element.get('name', '')
            max_chars = element.get('max_chars', 100)
            element_info.append(f"- {name}: max {max_chars} characters")
            required_fields.append(name)
        
        # Get template prompt guidance if available
        template_guidance = ""
        if hasattr(template_requirements, 'metadata') and template_requirements.metadata:
            template_guidance = template_requirements.metadata.get('prompt_guidance', '')
        elif isinstance(template_requirements, dict) and template_requirements.get('metadata'):
            template_guidance = template_requirements['metadata'].get('prompt_guidance', '')
        
        # Include knowledge with independent budgets for brand/global
        infl = os.getenv("KNOWLEDGE_INFLUENCE", os.getenv("KNOWLEDGE_AD_INFLUENCE", "medium")).lower()
        brand_infl = os.getenv("KNOWLEDGE_BRAND_INFLUENCE", infl).lower()
        budgets = {"low": (800, 800), "medium": (2000, 2000), "high": (4000, 4000)}
        b_chars, g_chars = budgets.get(brand_infl, budgets["medium"]) 
        kb = load_knowledge_texts(brand.get("name",""), brand_chars=b_chars, global_chars=g_chars)
        prefix = f"[REFERENCE DOCS]\n{kb}\n\n" if kb else ""

        user = f"""{prefix}Tone: {brand.get("tone", "")}
Audience: {strategy.get("audience", "")}
Claim: "{claim}"

TEMPLATE REQUIREMENTS:
{chr(10).join(element_info)}

TEMPLATE GUIDANCE:
{template_guidance if template_guidance else "Generate engaging, brand-appropriate content for each text element."}

Generate ONLY the text elements specified above. Each element should respect the character limits and follow the template guidance.
Return JSON with exactly these fields: {chr(10).join(f'"{field}": "..."' for field in required_fields)}

JSON:"""
        
        out = llm_json(EXPAND_SYSTEM, user) or {}
        
        # Return only the fields that the template requires
        result = {}
        for field in required_fields:
            result[field] = (out.get(field) or "").strip() or f"Default {field}"
        
        return result
    else:
        # Fallback to default structure if no template requirements
        # Include knowledge
        infl = os.getenv("KNOWLEDGE_INFLUENCE", os.getenv("KNOWLEDGE_AD_INFLUENCE", "medium")).lower()
        brand_infl = os.getenv("KNOWLEDGE_BRAND_INFLUENCE", infl).lower()
        budgets = {"low": (800, 800), "medium": (2000, 2000), "high": (4000, 4000)}
        b_chars, g_chars = budgets.get(brand_infl, budgets["medium"]) 
        kb = load_knowledge_texts(brand.get("name",""), brand_chars=b_chars, global_chars=g_chars)
        prefix = f"[REFERENCE DOCS]\n{kb}\n\n" if kb else ""

        user = prefix + EXPAND_USER.format(
            tone=brand.get("tone", ""),
            audience=strategy.get("audience", ""),
            claim=claim,
        )
        
        out = llm_json(EXPAND_SYSTEM, user) or {}
        headline = (out.get("headline") or "").strip() or claim
        value_props = out.get("value_props", [])
        if not value_props or len(value_props) < 4:
            value_props = [
                "Natural ingredients",
                "Clinically formulated", 
                "Proven results",
                "Safe & effective"
            ]
        cta = (out.get("cta") or "").strip() or "Learn More"
        return {"headline": headline, "value_props": value_props, "cta": cta}

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