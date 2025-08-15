# orchestrator/main.py
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

import json, uuid, sys, traceback, os
from typing import Dict, Any, List

from orchestrator.storage import save_job
from orchestrator.compliance import validate_claim
from orchestrator.generators import image_brief, generate_image_url

def load_json(p: str) -> Dict[str, Any]:
    return json.load(open(p, "r", encoding="utf-8"))

# ---- LLM availability (module scope, no rebinding inside main)
HAS_LLM = False
try:
    # NOTE: import the new angle-aware generator
    from orchestrator.claims import generate_claims_by_angle, expand_copy, verify_or_rewrite
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
    per_angle = max(claim_count // 4, 2)  # Distribute claims across angles
    
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
            angle_map = generate_claims_by_angle(cfg, target_per_angle=max(per_angle, 8), style=claim_style)

            # verify / rewrite with compliance
            allowed_pool: List[Dict[str, str]] = []
            for angle_id, items in angle_map.items():
                for c in items:
                    txt = (c.get("text") or "").strip()
                    if not txt:
                        continue
                    if not validate_claim(txt, type("F", (), formulation)):
                        continue
                    verdict = verify_or_rewrite(txt, formulation, formulation.get("banned_claims", []))
                    use_txt = txt if verdict.get("ok") else (verdict.get("rewrite") or "").strip()
                    if use_txt and validate_claim(use_txt, type("F", (), formulation)):
                        allowed_pool.append({"text": use_txt, "angle_id": angle_id})

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
        bases = [
            "Steady focus without jitters","Clean energy that lasts","Dial in your flow state",
            "Energy plus calm clarity","Feel locked-in and light","Smooth focus for long sessions",
            "Stay sharp and composed","Focus that feels natural","Clarity for heavy lift days",
            "Energy that respects rest"
        ]
        for b in bases:
            if len(claims) >= n: break
            if b not in claims:
                claims.append(b)

    # ---- full mock fallback (if LLM produced nothing)
    if not claims:
        print("[IAG] Mock claims fallback", flush=True)
        bases = [
            "Steady focus without jitters","Clean energy that lasts","Dial in your flow state",
            "Energy plus calm clarity","Feel locked-in and light","Smooth focus for long sessions",
            "Stay sharp and composed","Focus that feels natural","Clarity for heavy lift days",
            "Energy that respects rest"
        ]
        claims = (bases * ((n//len(bases))+1))[:n]

    print("[IAG] Claims:", len(claims), flush=True)

    # ---- VARIANTS
    variants = []
    
    # Determine template name for variants
    if template_name:
        tmpl_name = template_name
        print(f"[IAG] Using specified template: {tmpl_name}", flush=True)
    else:
        tmpl_name = f"Template/{strategy['format']}"  # e.g. Template/1080x1440
        print(f"[IAG] Using default template: {tmpl_name}", flush=True)

    # Get template requirements for copy expansion
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
                
            print(f"[IAG] Template requirements loaded: {len(template_requirements.get('elements', []))} elements", flush=True)
        except ImportError:
            print("[IAG] Template manager not available, proceeding without template requirements", flush=True)

    for idx, claim in enumerate(claims):
        try:
            if use_llm:
                try:
                    copy = expand_copy(brand, claim, strategy, template_requirements)
                    print(f"[IAG] DEBUG: expand_copy returned: {copy}", flush=True)
                except Exception as e:
                    print(f"[IAG] DEBUG: expand_copy failed: {e}", flush=True)
                    copy = {
                        "headline": f"{claim}.",
                        "value_props": ["Natural ingredients", "Clinically formulated", "Proven results", "Safe & effective"],
                        "cta": "Learn More",
                    }
            else:
                copy = {
                    "headline": f"{claim}.",
                    "value_props": ["Natural ingredients", "Clinically formulated", "Proven results", "Safe & effective"],
                    "cta": "Learn More",
                }

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
                        "claim": claim,
                        "logo_url": brand["logo_url"],
                        "palette": brand["palette"],
                        "type": brand["type"],
                        "template_name": template_name,
                        "template_variation": variation.name,
                        "aspect_ratio": variation.aspect_ratio,
                        "dimensions": variation.dimensions
                    }
                    
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
                    "claim": claim,
                    "logo_url": brand["logo_url"],
                    "palette": brand["palette"],
                    "type": brand["type"],
                    "template_name": template_name,
                    "template_variation": template_variation,
                }
                
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