import json, time, uuid
from pathlib import Path

def save_job(variants, brand_name: str, product_name: str, fmt: str, out_dir: str = "out"):
    job = {
        "job_id": str(uuid.uuid4())[:8],
        "brand": brand_name,
        "product": product_name,
        "format": fmt,
        "variants": variants,
        "created_at": int(time.time())
    }
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    with open(f"{out_dir}/{job['job_id']}.json", "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)
    return job
