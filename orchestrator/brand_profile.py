from pathlib import Path
from typing import Dict, Any
import json


def _safe_load_json(p: Path) -> Dict[str, Any]:
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def load_brand_profile(brand_name: str) -> Dict[str, Any]:
    """
    Load a structured brand profile used to guide prompts.
    Priority: inputs/<brand>/brand_profile.json → synthesize from <brand>_enhanced.json
    """
    base = Path(f"inputs/{brand_name}")
    # 1) Explicit brand profile (manual/curated overrides)
    profile_path = base / "brand_profile.json"
    profile = _safe_load_json(profile_path)
    if profile:
        return profile

    # 2) Synthesize from enhanced JSON
    enhanced = _safe_load_json(base / f"{brand_name.lower()}_enhanced.json")
    brand = enhanced.get("brand", {})
    strategy = enhanced.get("strategy", {})
    formulation = enhanced.get("formulation", {})

    key_ings = formulation.get("key_ingredients", []) or []
    ing_summaries = []
    for i in key_ings:
        name = i.get("name") or "Ingredient"
        details = []
        if i.get("dose_mg"):
            details.append(f"{i['dose_mg']}mg")
        if i.get("evidence_level"):
            details.append(i['evidence_level'])
        ing_summaries.append(f"- {name} ({', '.join(details)})")

    voice = brand.get("voice_guide", {})
    lex = (voice.get("lexicon") or {}) if isinstance(voice, dict) else {}

    profile = {
        "product_ingredients": {
            "product_name": formulation.get("product_name") or brand.get("name"),
            "ingredients": ing_summaries,
        },
        "positioning_statement": strategy.get("positioning") or brand.get("positioning") or "",
        "audience_persona": {
            "audience": strategy.get("audience", ""),
            "persona": strategy.get("persona", ""),
        },
        "voice_lexicon": {
            "dos": voice.get("dos", []),
            "donts": voice.get("donts", []),
            "prefer": lex.get("prefer", []),
            "avoid": lex.get("avoid", []),
        },
        "proof_assets": {
            "testimonials": strategy.get("testimonials", []),
            "experts": strategy.get("experts", []),
        },
        "ctas_offers": strategy.get("ctas", []),
    }
    return profile


