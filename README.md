# Ad Factory Prototype

End-to-end local prototype that:
1) Generates text + image briefs from inputs (mocked locally for now)
2) Saves a job JSON under `out/<job_id>.json`
3) Serves that JSON + placeholder image at `http://localhost:8000`
4) Figma plugin pulls the job, populates a template, and builds 30 frames.

## Quick start

### 1) Python env
```bash
cd ad-factory-prototype
python3 -m venv .venv && source .venv/bin/activate
pip install pillow
python orchestrator/main.py          # generates a job and prints JOB_ID
```

### 2) Start local server
```bash
python server.py
# -> Serving at http://localhost:8000
```

### 3) Figma template
- In your Figma file, create a frame named **Template/1080x1350** sized 1080×1350.
- Inside it, add:
  - Text layer named **#H1**
  - Text layer named **#BYLINE**
  - Text layer named **#CTA**
  - Rectangle named **#IMAGE_HERO** (this will get the image fill)
- Optional: set fonts to Inter (or your brand fonts installed locally).

### 4) Install the plugin
- In Figma desktop: `Plugins → Development → New Plugin... → Click "Link existing plugin"`.
- Choose the folder `ad-factory-prototype/figma-plugin` and select `manifest.json`.
- Open the plugin. Paste the **JOB_ID** printed earlier. Click **Run**.
- It will duplicate the template and build ~30 frames with mocked copy and a placeholder image.

## Switching to real models
- Replace functions in `orchestrator/generators.py` with API-backed calls.
- Keep the same return shapes:
  - `generate_claims(...) -> List[{"text": str, "support_rationale": str}]`
  - `expand_copy(...) -> {"headline": str, "byline": str, "cta": str}`
  - `image_brief(...) -> {"prompt": str, "negative_prompt": str, "seed": int}`
  - `generate_image_url(...) -> str (public URL)`
- If you host generated images on S3/GCS, update `figma-plugin/manifest.json` `allowedDomains`.

## Notes
- Compliance guardrails live in `orchestrator/compliance.py` (basic for now).
- The plugin currently builds frames; exporting files can be added (PNG/SVG naming, S3 upload).
- You can change inputs in `orchestrator/sample_input.json` to target other audiences, brands, or products.
