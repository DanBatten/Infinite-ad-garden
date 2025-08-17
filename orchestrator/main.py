# orchestrator/main.py
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

import json, uuid, sys, traceback, os
from typing import Dict, Any, List

from orchestrator.storage import save_job

def load_json(p: str) -> Dict[str, Any]:
    return json.load(open(p, "r", encoding="utf-8"))

def _split_family_and_style(raw: str):
    """Split a font string like 'Inter Bold' -> ('Inter', 'Bold').
    If only family provided, default style to 'Regular'.
    Accepts 'Semi Bold' and other spaced styles.
    """
    if not raw:
        return (None, None)
    value = str(raw).strip()
    # Known styles, longer first
    known_styles = [
        "Extra Black", "ExtraBold", "Extra Bold",
        "SemiBold", "Semi Bold", "DemiBold", "Demi Bold",
        "Black", "Bold", "Medium", "Light", "Thin", "Regular", "Book", "Roman"
    ]
    # Try exact suffix match
    for style in known_styles:
        if value.lower().endswith(style.lower()):
            family = value[:-len(style)].strip()
            # Normalize style spacing (e.g., 'Semi Bold' -> 'SemiBold')
            normalized_style = style.replace(" ", "") if style in ["Semi Bold", "Demi Bold", "Extra Bold", "Extra Black"] else style
            return (family or value, normalized_style)
    # Fallback: only treat last token as style if it's a known style token
    parts = value.split()
    if len(parts) > 1:
        last_token = parts[-1]
        if last_token.lower() in [s.lower() for s in known_styles]:
            return (" ".join(parts[:-1]).strip(), last_token)
        # Otherwise, the entire value is the family; default style Regular
        return (value, "Regular")
    return (value, "Regular")

def _load_brand_txt_fonts(brand_folder: Path) -> Dict[str, str]:
    """Parse brand font overrides from text files.
    Looks for:
      - inputs/{brand}/brand.txt
      - inputs/{brand}/brand_docs/brand.txt
    Recognizes lines like 'Heading Font: FreightDisp Pro' or 'Body Copy Font: Parabolica'.
    Returns keys: heading_font, body_font, cta_font.
    Later files override earlier ones.
    """
    result: Dict[str, str] = {}
    candidates = [
        brand_folder / "brand.txt",
        brand_folder / "brand_docs" / "brand.txt",
    ]

    def apply_from_text(text: str):
        nonlocal result
        for raw_line in text.splitlines():
            lower = raw_line.strip().lower()
            if not lower:
                continue
            val = raw_line.split(":", 1)[1].strip() if ":" in raw_line else None
            heading_keys = ["heading font", "headline font", "heading_typography", "headline", "title", "heading"]
            body_keys    = ["body copy font", "body font", "body_typography", "body copy", "body"]
            cta_keys     = ["cta font", "cta_typography", "cta", "button font", "button"]
            if any(k in lower for k in heading_keys) and val:
                result["heading_font"] = val
            elif any(k in lower for k in body_keys) and val:
                result["body_font"] = val
            elif any(k in lower for k in cta_keys) and val:
                result["cta_font"] = val

    for path in candidates:
        try:
            if path.exists():
                apply_from_text(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue

    return result

# ---- Fallback claim helpers
def _fallback_claims_from_brand(brand: Dict[str, Any]) -> List[str]:
    """Generate safe, brand-appropriate fallback lines when LLM output is empty.
    Prefers beauty/ritual/glow language drawn from brand positioning and lexicon.
    """
    name = brand.get("name", "The brand")
    positioning = brand.get("positioning") or brand.get("value_prop") or "Beauty from within"
    lex = (brand.get("voice_guide", {}) or {}).get("lexicon", {})
    prefer = [w for w in lex.get("prefer", []) if isinstance(w, str)]
    # Seed words
    words = prefer or ["glow", "ritual", "balance", "skin", "inner beauty", "calm clarity"]
    lines = [
        f"Visible {words[0] if words else 'glow'} from within",
        f"Make {name} your daily beauty ritual",
        f"Nourish skin for a smoother, healthier look",
        f"Beauty that starts inside—simple, steady, consistent",
        f"Clean ingredients for confident, natural radiance",
        f"Support skin’s {words[1] if len(words)>1 else 'balance'} every day",
        f"A calmer routine for clearer, brighter-looking skin",
        f"Small daily steps, noticeable {words[0] if words else 'glow'}",
        f"Backed by science, made for everyday beauty",
        f"Your inside-out approach to modern beauty"
    ]
    # De-duplicate and cap
    out: List[str] = []
    for l in lines:
        if l not in out:
            out.append(l)
    return out

# ---- LLM availability (module scope, no rebinding inside main)
HAS_LLM = False
try:
    # NOTE: import the new angle-aware generator
    from orchestrator.claims import generate_claims_by_angle, expand_copy
    HAS_LLM = True
except Exception:
    HAS_LLM = False

# flip to True if you want to force mock while testing
FORCE_MOCK = False

def main():
    print("[IAG] Start", flush=True)

    # Read brand file from environment variable (set by the API)
    brand_file = os.environ.get('BRAND_FILE', 'Metra')
    
    # point to your current enhanced input file (processed from input docs)
    cfg = load_json(f"inputs/{brand_file}/{brand_file.lower()}_enhanced.json")

    strategy, brand, formulation = cfg["strategy"], cfg["brand"], cfg["formulation"]
    
    # Read parameters from environment variables (set by the API)
    claim_count = int(os.environ.get('CLAIM_COUNT', 30))
    claim_style = os.environ.get('CLAIM_STYLE', 'balanced')
    
    # New: Read template information
    template_name = os.environ.get('TEMPLATE_NAME')
    template_variation = os.environ.get('TEMPLATE_VARIATION')
    
    # Override config values with API parameters
    n = claim_count  # Use the actual requested count instead of hardcoded 30
    per_angle = max(claim_count // 4, 2)  # legacy calc (not used for target now)
    
    print(f"[IAG] Requested: {claim_count} claims, style: {claim_style}", flush=True)
    if template_name:
        print(f"[IAG] Template: {template_name}", flush=True)
        if template_variation:
            print(f"[IAG] Variation: {template_variation}", flush=True)
    print(f"[IAG] Will generate {per_angle} claims per angle", flush=True)

    use_llm = HAS_LLM and (not FORCE_MOCK)

    # ---- CLAIMS (angle-aware + balanced sampling)
    claims: List[str] = []
    if use_llm:
        try:
            print("[IAG] LLM claims by angle…", flush=True)
            # Request exactly claim_count total claims from the generator, including template fields
            angle_map = generate_claims_by_angle(cfg, target_per_angle=claim_count, style=claim_style, template_requirements=None)

            # accept all non-empty claims without compliance filtering/rewrite
            allowed_pool: List[Dict[str, str]] = []
            for angle_id, items in angle_map.items():
                for c in items:
                    txt = (c.get("text") or "").strip()
                    if not txt:
                        continue
                    allowed_pool.append({"text": txt, "angle_id": angle_id})

            # even sampling across angles
            by_angle: Dict[str, List[str]] = {}
            for item in allowed_pool:
                by_angle.setdefault(item["angle_id"], []).append(item["text"])

            while len(claims) < n and any(by_angle.values()):
                for aid in list(by_angle.keys()):
                    if by_angle[aid]:
                        claims.append(by_angle[aid].pop(0))
                        if len(claims) >= n:
                            break

        except Exception as e:
            print("[IAG] LLM failed — using mock claims.", file=sys.stderr)
            traceback.print_exc()

    # ---- BACKFILL to guarantee n claims (if LLM path left us short)
    if use_llm and len(claims) < n:
        # light, safe stock lines to top up
        bases = _fallback_claims_from_brand(brand)
        for b in bases:
            if len(claims) >= n: break
            if b not in claims:
                claims.append(b)

    # ---- full mock fallback (if LLM produced nothing)
    if not claims:
        print("[IAG] Mock claims fallback", flush=True)
        bases = _fallback_claims_from_brand(brand)
        claims = (bases * ((n//len(bases))+1))[:n]

    print("[IAG] Claims:", len(claims), flush=True)

    # ---- VARIANTS
    variants = []
    
    # Determine template name for variants (always use tmpl_name subsequently)
    if template_name:
        tmpl_name = template_name
        print(f"[IAG] Using specified template: {tmpl_name}", flush=True)
    else:
        tmpl_name = f"Template/{strategy['format']}"  # e.g. Template/1080x1440
        print(f"[IAG] Using default template: {tmpl_name}", flush=True)

    # Get template requirements for prompt (single-pass)
    template_requirements = None
    template_variations = []
    if template_name:
        try:
            from orchestrator.templates import template_manager
            template_requirements = template_manager.get_claims_requirements(template_name, template_variation)
            
            # Get all variations (portrait, square) for the selected version
            if template_variation:
                template_variations = template_manager.get_variations_by_version(template_name, template_variation)
                print(f"[IAG] Template version {template_variation} has {len(template_variations)} variations (portrait/square)", flush=True)
            else:
                # If no version specified, get all variations
                template_variations = template_manager.get_all_variations_for_template(template_name)
                print(f"[IAG] All template variations loaded: {len(template_variations)} total", flush=True)
                
            elems_count = len(template_requirements.get('elements', [])) if template_requirements else 0
            print(f"[IAG] Template requirements loaded: {elems_count} elements", flush=True)
        except ImportError:
            print("[IAG] Template manager not available, proceeding without template requirements", flush=True)

    # If a template was specified but we failed to load any requirements, use a safe headline-only fallback
    if template_name and (not template_requirements or not template_requirements.get('elements')):
        print(f"[IAG] No requirements found for '{template_name}'. Using headline-only fallback (no CTA/value props).", flush=True)
        template_requirements = {
            "template_name": template_name,
            "variation_name": template_variation or "01",
            "elements": [
                {"name": "#HEADLINE", "max_chars": 70, "description": "Primary headline"}
            ],
            "metadata": {"prompt_guidance": "Produce a single impactful headline only. No CTA or value props."}
        }

    # Derive brand fonts from enhanced JSON, with optional overrides from brand.txt
    brand_folder = Path(f"inputs/{brand_file}")
    brand_txt_fonts = _load_brand_txt_fonts(brand_folder)
    # Base from enhanced JSON
    # Prefer structured typography if available
    heading_dict = (brand.get("typography", {}) or {}).get("heading") or (brand.get("visual", {}).get("typography", {}) or {}).get("heading")
    body_dict    = (brand.get("typography", {}) or {}).get("body")    or (brand.get("visual", {}).get("typography", {}) or {}).get("body")
    # Fallbacks from older schema
    if not heading_dict:
        heading_dict = brand.get("type", {}).get("heading")
    if not body_dict:
        body_dict = brand.get("type", {}).get("body")

    # Extract family/style from structured objects when present
    heading_family_json = heading_dict.get("family") if isinstance(heading_dict, dict) else heading_dict
    body_family_json    = body_dict.get("family")    if isinstance(body_dict, dict)    else body_dict
    heading_style_json  = heading_dict.get("style")  if isinstance(heading_dict, dict) else None
    body_style_json     = body_dict.get("style")     if isinstance(body_dict, dict)    else None
    # Allow brand.txt overrides if present
    heading_raw = brand_txt_fonts.get("heading_font", heading_family_json)
    body_raw    = brand_txt_fonts.get("body_font", body_family_json)
    cta_raw     = brand_txt_fonts.get("cta_font", heading_raw)
    heading_family, heading_style = _split_family_and_style(heading_raw)
    body_family, body_style       = _split_family_and_style(body_raw)
    # If JSON explicitly provided styles, prefer them over parsed styles
    if heading_style_json:
        heading_style = heading_style_json
    if body_style_json:
        body_style = body_style_json
    _, cta_style                  = _split_family_and_style(cta_raw)

    # Re-run first call with template requirements now that we have them
    if use_llm:
        try:
            print("[IAG] Regenerating claims with template requirements (single-pass)…", flush=True)
            angle_map = generate_claims_by_angle(cfg, target_per_angle=claim_count, style=claim_style, template_requirements=template_requirements)
            # Flatten to list preserving counts
            claims_structured = []
            for items in angle_map.values():
                for it in items:
                    # Ensure template metadata propagated if present
                    it["template_name"] = tmpl_name
                    claims_structured.append(it)
            claims_structured = claims_structured[:n]
        except Exception:
            claims_structured = []
    else:
        claims_structured = []

    for idx, item in enumerate(claims_structured or []):
        try:
            # Build copy dict directly from structured claim item
            copy = {}
            if template_requirements and template_requirements.get("elements"):
                for el in template_requirements.get("elements", []):
                    name = el.get("name")
                    if not name:
                        continue
                    copy[name] = item.get(name) or item.get(name.lower()) or item.get(name.strip('#').lower()) or ""
            else:
                # headline-only fallback
                copy["#HEADLINE"] = item.get("#HEADLINE") or item.get("headline") or (item.get("claim") or "")

            # If we have template variations, create variants for each variation
            print(f"[IAG] DEBUG: template_variations count: {len(template_variations) if template_variations else 0}", flush=True)
            if template_variations and len(template_variations) > 1:
                print(f"[IAG] DEBUG: Creating variants for {len(template_variations)} variations", flush=True)
                # Create variants for each template variation (portrait, square, etc.)
                for variation in template_variations:
                    print(f"[IAG] DEBUG: Processing variation: {variation.name}", flush=True)
                    # Create dynamic variant based on template requirements
                    variant = {
                        "id": str(uuid.uuid4())[:8],
                        "layout": f"{tmpl_name}-{variation.name}",
                        "claim": item.get("claim") or "",
                        "logo_url": brand["logo_url"],
                        "palette": brand["palette"],
                        "type": {
                            "heading": heading_family or brand.get("type", {}).get("heading"),
                            "body": body_family or brand.get("type", {}).get("body"),
                            "headingStyle": heading_style or "Regular",
                            "bodyStyle": body_style or "Regular",
                            "ctaStyle": cta_style or "Bold",
                        },
                        # Always set the template name we actually used
                        "template_name": tmpl_name,
                        "template_variation": variation.name,
                        "aspect_ratio": variation.aspect_ratio,
                        "dimensions": variation.dimensions
                    }
                    if item.get("style"):
                        variant["style"] = item.get("style")
                    
                    # Add all fields from copy (template-specific)
                    for key, value in copy.items():
                        variant[key] = value
                    
                    variants.append(variant)
                    print(f"[IAG] DEBUG: Added variant {variant['id']}", flush=True)
                
                print(f"[IAG] Created {len(template_variations)} variants for claim {idx + 1}", flush=True)
            else:
                # Standard single variant
                variant = {
                    "id": str(uuid.uuid4())[:8],
                    "layout": tmpl_name,
                    "claim": item.get("claim") or "",
                    "logo_url": brand["logo_url"],
                    "palette": brand["palette"],
                    "type": {
                        "heading": heading_family or brand.get("type", {}).get("heading"),
                        "body": body_family or brand.get("type", {}).get("body"),
                        "headingStyle": heading_style or "Regular",
                        "bodyStyle": body_style or "Regular",
                        "ctaStyle": cta_style or "Bold",
                    },
                    # Always set the template name we actually used
                    "template_name": tmpl_name,
                    "template_variation": template_variation,
                }
                if item.get("style"):
                    variant["style"] = item.get("style")
                
                # Add all fields from copy (template-specific)
                for key, value in copy.items():
                    variant[key] = value
                
                variants.append(variant)

        except Exception as e:
            print("[IAG] Variant build error:", e, file=sys.stderr)
            traceback.print_exc()

        # Limit total variants if we're generating multiple per claim
        if template_variations and len(template_variations) > 1:
            # For templates with variations, we want to limit the total number of claims
            # to avoid overwhelming output
            if len(variants) >= n * len(template_variations):
                break
        else:
            # Standard single variant limit
            if len(variants) >= n:
                break

    print("[IAG] Variants:", len(variants), flush=True)

    job = save_job(
        variants,
        brand_name=brand["name"],
        product_name=formulation["product_name"],
        fmt=strategy["format"],
        out_dir="out"
    )
    print(f"[IAG] JOB_ID: {job['job_id']}")
    print(f"[IAG] WROTE out/{job['job_id']}.json", flush=True)
    return job

if __name__ == "__main__":
    main()