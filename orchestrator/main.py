# orchestrator/main.py
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

import json, uuid, sys, traceback
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

    # point to your current enhanced input file (processed from input docs)
    cfg = load_json("inputs/Metra/metra_enhanced.json")

    strategy, brand, formulation = cfg["strategy"], cfg["brand"], cfg["formulation"]
    
    # Read parameters from environment variables (set by the API)
    import os
    claim_count = int(os.environ.get('CLAIM_COUNT', 30))
    claim_style = os.environ.get('CLAIM_STYLE', 'balanced')
    
    # Override config values with API parameters
    n = claim_count  # Use the actual requested count instead of hardcoded 30
    per_angle = max(claim_count // 4, 2)  # Distribute claims across angles
    
    print(f"[IAG] Requested: {claim_count} claims, style: {claim_style}", flush=True)
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
    tmpl_name = f"Template/{strategy['format']}"  # e.g. Template/1080x1440

    for idx, claim in enumerate(claims):
        try:
            if use_llm:
                try:
                    copy = expand_copy(brand, claim, strategy)
                except Exception:
                    copy = {
                        "headline": f"{claim}.",
                        "byline": f"Built for {strategy.get('audience','')}.",
                        "cta": "Learn More",
                    }
            else:
                copy = {
                    "headline": f"{claim}.",
                    "byline": f"Built for {strategy.get('audience','')}.",
                    "cta": "Learn More",
                }

            brief = image_brief(brand, claim, strategy)
            img_url = generate_image_url(brief, variant_id=str(idx))

            variants.append({
                "id": str(uuid.uuid4())[:8],
                "layout": tmpl_name,
                "claim": claim,
                "headline": copy["headline"],
                "byline": copy["byline"],
                "cta": copy["cta"],
                "image_url": img_url,
                "logo_url": brand["logo_url"],
                "palette": brand["palette"],
                "type": brand["type"],
            })
        except Exception as e:
            print("[IAG] Variant build error:", e, file=sys.stderr)
            traceback.print_exc()

        if len(variants) >= n: break

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