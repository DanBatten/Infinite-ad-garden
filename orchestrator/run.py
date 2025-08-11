import argparse, json, os
from orchestrator.main import generate_variants

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="orchestrator/sample_input.json", help="Path to input JSON")
args = parser.parse_args()

cfg = json.load(open(args.config, "r", encoding="utf-8"))
job = generate_variants(cfg)
print(job["job_id"])
