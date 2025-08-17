# orchestrator/claims.py
from typing import Dict, Any, List
from .llm import llm_json
from .knowledge import load_knowledge_texts
from .brand_profile import load_brand_profile
import os
from .prompt_templates import (
    CLAIMS_SYSTEM,
    CLAIMS_USER,
    EXPAND_SYSTEM,
    EXPAND_USER,
)
from pathlib import Path
import datetime
def _debug_enabled() -> bool:
    return os.getenv("DEBUG_PROMPTS", "false").lower() in ("1", "true", "yes")


def _debug_write(block: str, text: str):
    if not _debug_enabled():
        return
    try:
        p = Path(os.getenv("PROMPT_DEBUG_FILE", "logs/prompts.log"))
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            # Write only the raw text with a minimal newline separator
            f.write(f"\n{text}\n")
    except Exception:
        pass

def _extract_prompt_sections(user_text: str) -> Dict[str, str]:
    """Return {attachments, instruction} split using [REFERENCE DOCS] and [INSTRUCTION] markers.
    If markers are absent, treat entire text as instruction."""
    attachments = ""
    instruction = user_text or ""
    if not user_text:
        return {"attachments": attachments, "instruction": instruction}

    marker_docs = "[REFERENCE DOCS]"
    marker_instr = "[INSTRUCTION]"
    idx_docs = user_text.find(marker_docs)
    idx_instr = user_text.find(marker_instr)
    if idx_docs != -1:
        start_docs = idx_docs + len(marker_docs)
        end_docs = idx_instr if idx_instr != -1 else len(user_text)
        attachments = user_text[start_docs:end_docs].strip()
        if idx_instr != -1:
            instruction = user_text[idx_instr + len(marker_instr):].strip()
        else:
            # No explicit instruction marker; take everything before docs as instruction
            instruction = user_text[:idx_docs].strip()
    return {"attachments": attachments, "instruction": instruction}

def _debug_log_prompt(tag: str, system_text: str, user_text: str):
    """Write ONLY the prompt (instruction) text to the log, no headers or attachments."""
    if not _debug_enabled():
        return
    try:
        sections = _extract_prompt_sections(user_text)
        prompt_only = sections.get("instruction", "").strip()
        if prompt_only:
            _debug_write(tag, prompt_only)
    except Exception:
        pass

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
        'benefit-focused': "ONLY BENEFIT-FOCUSED: Lead with the single most important benefit. Use 'you' language. No problem statements, no urgency, no proof.",
        'problem-solution': "ONLY PROBLEM–SOLUTION: Start with the problem in 3–6 words, then present Metra as the solution. No social proof, no urgency, no generic benefits-only lines.",
        'social-proof': "ONLY SOCIAL PROOF: Center the line on validation—ratings, experts, review snippets, or volume. Use explicit signals like 'Rated 4.9★', 'Trusted by 10,000+', 'Dermatologist-approved', '4.9/5 from 2,431 reviews'. No problem framing, no urgency.",
        'urgency-driven': "ONLY URGENCY-DRIVEN: Time/quantity triggers + action. Keep tasteful, avoid hype. No proof language, no problem framing.",
        'mixed-styles': "BLENDED: Hook + light problem + subtle proof + soft urgency, balanced in one line."
    }
    
    style_instruction = style_instructions.get(style, style_instructions['mixed-styles'])

    # Get all available angles for context
    angles = cfg.get("angles", [])
    angle_context = ""
    if angles:
        angle_context = f"Available angles: {', '.join([a.get('name', '') for a in angles])}"
    
    # Generate claims for the specific style, using angles as context but not as the primary driver
    brand_profile = load_brand_profile(brand.get("name", ""))
    # Build angles text for prompt readability
    angles_text = ", ".join([a.get('name','') for a in angles]) if angles else "beauty-from-within, busy-lifestyle, scientific-backing"

    # We will ask for exactly target_per_angle claims total
    # Extract proof assets summary for social-proof grounding
    proof_assets = ""
    try:
        pa = (brand_profile.get('proof_assets') or {})
        testis = ", ".join(pa.get('testimonials', [])[:3]) if isinstance(pa.get('testimonials'), list) else ""
        experts = ", ".join(pa.get('experts', [])[:3]) if isinstance(pa.get('experts'), list) else ""
        parts = []
        if testis:
            parts.append(f"Testimonials: {testis}")
        if experts:
            parts.append(f"Experts: {experts}")
        proof_assets = "; ".join(parts)
    except Exception:
        proof_assets = ""

    user = CLAIMS_USER.format(
        brand_name=brand.get("name",""),
        tagline=brand.get("tagline",""),
        positioning=brand.get("positioning","Holistic beauty from within; clinically supported ingredients; avoids exaggerated or medical claims"),
        mission=brand.get("mission","Empower individuals to enhance natural beauty with scientifically-backed holistic supplements"),
        tone=brand.get("tone", ""),
        audience=strategy.get("audience", ""),
        angle_name=angles_text,
        proof_assets=proof_assets,
        target_count=target_per_angle,
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
    # Build brand profile reference text and attach as reference docs (not inline prompt)
    profile_lines = []
    ings = brand_profile.get('product_ingredients',{}).get('ingredients',[])
    if ings:
        profile_lines.append("Product & Ingredients:\n" + "\n".join(ings))
    pos = brand_profile.get('positioning_statement','')
    if pos:
        profile_lines.append("Positioning:\n" + pos)
    aud = brand_profile.get('audience_persona',{}).get('audience','')
    if aud:
        profile_lines.append("Audience:\n" + aud)
    profile_text = "\n\n".join(profile_lines)

    ref_docs = profile_text
    if kb:
        ref_docs = (ref_docs + "\n\n" if ref_docs else "") + kb
    if ref_docs:
        user = f"""[REFERENCE DOCS]\n{ref_docs}\n\n[INSTRUCTION]\n{user}"""
    if _debug_enabled():
        # Log the prompt plus an explicit resolved style instruction block for easy debugging
        _debug_log_prompt("CLAIMS", CLAIMS_SYSTEM, user)
        try:
            resolved = f"\n-- RESOLVED STYLE --\n{style_instruction}\n-- END STYLE --\n"
            _debug_write("CLAIMS_STYLE", resolved)
        except Exception:
            pass
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
    # Helper: banned headline verbs we want to avoid (too common)
    banned_verbs = [
        "elevate", "unlock", "discover", "transform", "reveal", "experience", "boost"
    ]

    def _needs_rewrite(text: str) -> bool:
        lower = (text or "").lower()
        return any(w in lower for w in banned_verbs)

    def _rewrite_headline(text: str) -> str:
        try:
            system = "You are a concise, on-brand headline writer. Return JSON only."
            user = (
                f"Tone: {brand.get('tone','')}\n"
                f"Audience: {strategy.get('audience','')}\n"
                f"Current: '{text}'\n\n"
                f"Rewrite this as a single fresh headline (40-70 chars) WITHOUT using these verbs or their direct variants: {', '.join(banned_verbs)}.\n"
                f"Keep meaning and legality; avoid hype.\n\n"
                "JSON:{\"headline\":\"…\"}"
            )
            out = llm_json(system, user) or {}
            new_h = (out.get("headline") or "").strip()
            return new_h or text
        except Exception:
            return text

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
        # Include concise brand profile in attachments so the LLM has brand-specific context
        bp = load_brand_profile(brand.get("name",""))
        profile_lines = []
        ings = bp.get('product_ingredients',{}).get('ingredients',[])
        if ings:
            profile_lines.append("Product & Ingredients:\n" + "\n".join(ings))
        pos = bp.get('positioning_statement','')
        if pos:
            profile_lines.append("Positioning:\n" + pos)
        audp = bp.get('audience_persona',{}).get('audience','')
        if audp:
            profile_lines.append("Audience:\n" + audp)
        profile_text = "\n\n".join(profile_lines)
        attachments = "\n\n".join([t for t in [profile_text, kb] if t])

        body = f"""Brand: {brand.get("name", "")}
Tone: {brand.get("tone", "")}
Audience: {strategy.get("audience", "")}
Claim: "{claim}"

TEMPLATE REQUIREMENTS:
{chr(10).join(element_info)}

TEMPLATE GUIDANCE:
{template_guidance if template_guidance else "Generate engaging, brand-appropriate content for each text element."}

Generate ONLY the text elements specified above. Each element should respect the character limits and follow the template guidance.
Return JSON with exactly these fields: {chr(10).join(f'"{field}": "..."' for field in required_fields)}

JSON:"""
        user = f"""[REFERENCE DOCS]\n{attachments}\n\n[INSTRUCTION]\n{body}"""
        if _debug_enabled():
            _debug_log_prompt("EXPAND(template)", EXPAND_SYSTEM, user)
        out = llm_json(EXPAND_SYSTEM, user) or {}
        
        # Return only the fields that the template requires
        result = {}
        for field in required_fields:
            val = (out.get(field) or "").strip() or f"Default {field}"
            # If this field looks like a headline, optionally rewrite to avoid banned words
            if field.strip().replace('#','').upper().startswith('HEADLINE') and _needs_rewrite(val):
                val = _rewrite_headline(val)
            result[field] = val
        
        return result
    else:
        # Fallback to default structure if no template requirements
        # Include knowledge
        infl = os.getenv("KNOWLEDGE_INFLUENCE", os.getenv("KNOWLEDGE_AD_INFLUENCE", "medium")).lower()
        brand_infl = os.getenv("KNOWLEDGE_BRAND_INFLUENCE", infl).lower()
        budgets = {"low": (800, 800), "medium": (2000, 2000), "high": (4000, 4000)}
        b_chars, g_chars = budgets.get(brand_infl, budgets["medium"]) 
        kb = load_knowledge_texts(brand.get("name",""), brand_chars=b_chars, global_chars=g_chars)
        bp = load_brand_profile(brand.get("name",""))
        profile_lines = []
        ings = bp.get('product_ingredients',{}).get('ingredients',[])
        if ings:
            profile_lines.append("Product & Ingredients:\n" + "\n".join(ings))
        pos = bp.get('positioning_statement','')
        if pos:
            profile_lines.append("Positioning:\n" + pos)
        audp = bp.get('audience_persona',{}).get('audience','')
        if audp:
            profile_lines.append("Audience:\n" + audp)
        profile_text = "\n\n".join(profile_lines)
        attachments = "\n\n".join([t for t in [profile_text, kb] if t])

        body = EXPAND_USER.format(
            tone=brand.get("tone", ""),
            audience=strategy.get("audience", ""),
            claim=claim,
        )
        user = f"""[REFERENCE DOCS]\n{attachments}\n\n[INSTRUCTION]\n{body}"""
        
        if _debug_enabled():
            _debug_log_prompt("EXPAND(generic)", EXPAND_SYSTEM, user)
        out = llm_json(EXPAND_SYSTEM, user) or {}
        headline = (out.get("headline") or "").strip() or claim
        if _needs_rewrite(headline):
            headline = _rewrite_headline(headline)
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

## Compliance verification removed per request