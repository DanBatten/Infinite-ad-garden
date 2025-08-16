CLAIMS_SYSTEM = """You are a senior paid social copywriter for performance ads.
Return JSON only. Be creative yet compliant: avoid disease or drug-like claims (treat/cure/prevent); keep language truthful and testable."""

CLAIMS_USER = """You are a senior paid social copywriter. Use the attached reference docs for brand and creative context.

STYLE TO FOLLOW:
{style_instruction}

BRAND SNAPSHOT (orientation only):
- Brand: {brand_name}
- Tone: {tone}
- Audience: {audience}
- Angles context: {angle_name}

TASK
Generate EXACTLY {target_count} distinct ad claims in the selected style: {style}.
Each claim must be a single strong line (4–14 words) suitable as a Meta ad hook/headline.

OUTPUT FORMAT (JSON object):
{{
  "claims": [
    {{
      "style": "{style}",
      "claim": "…",
      "angle": "beauty-from-within | busy-lifestyle | scientific-backing",
      "hook_type": "Solution-First | Problem (Negative) | Social Proof | FOMO/Scarcity | Question | Pattern Interrupt | Offer",
      "voice_variant": "first_person | why_explainer | stat_hook",
      "compliance_note": ""
    }}
  ]
}}

CONSTRAINTS
- Use brand-compliant language only; avoid medical/disease claims.
- No duplicates across claims.
- Balance voice variants across the batch (~40% first_person, 30% why_explainer, 30% stat_hook).
- Prefer concrete, specific phrasing; avoid fluff.
- Avoid using cliches like elevate, unlock, or transform (and similar).
"""

EXPAND_SYSTEM = """You write on-brand ad copy. JSON only."""

EXPAND_USER = """Tone: {tone}
Audience: {audience}
Claim: "{claim}"

Write:
- headline (40–70 chars, active, compelling)
- value_props (array of 4 short benefit statements, 15-25 chars each, no medical claims)
- cta (2–3 words, action-oriented)

Creativity guidelines:
- Use fresh, surprising verbs and concrete imagery
- Avoid cliché openings and overused verbs: elevate, unlock, transform, discover, reveal, experience, boost
- Prefer specificity over generic phrasing; avoid repeating words across outputs
- Keep on-brand and human, not robotic; no exclamation points unless essential

JSON:
{{"headline":"…","value_props":["…","…","…","…"],"cta":"…"}}
"""

VERIFY_SYSTEM = """You are a strict supplement claims reviewer. JSON only."""
VERIFY_USER = """Claim: "{claim}"
Ingredients: {ingredients}
Banned: {banned}
Reject disease, guarantees, “clinically proven” without proof, or non-plausible mechanisms.

JSON: {{"ok": true|false, "reason":"…", "rewrite":"…"}}"""