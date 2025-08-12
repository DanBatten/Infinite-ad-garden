CLAIMS_SYSTEM = """You are a compliance-aware, but creative ad ideation partner for ingestible beauty supplements.
Return JSON only. Avoid disease or drug-like claims."""

CLAIMS_USER = """Brand tone: {tone}
Audience: {audience}

Angle:
- Name: {angle_name}
- Pain Point: {pain_point}
- Trigger: {trigger}
- Positioning: {positioning}

Ingredient context: {ingredients}

Voice guardrails:
- Do: {dos}
- Don't: {donts}
Lexicon:
- Prefer: {prefer}
- Avoid: {avoid}

Style guidance: {style_instruction}

Style anchors (examples, DO NOT copy verbatim):
{examples}

Task:
Generate AT LEAST {target_count} distinct, compliance-safe CLAIMS for {product_name}.
Each claim: 6–12 words, structure/function style. No disease, no "clinically proven", no guarantees.
Vary styles: mix first-person ("I… "), "why/explainer", and stat/price hooks.

JSON:
{{ "claims": [ {{ "text": "…", "style": "first_person|why|stat", "support": "1-line rationale" }} ] }}
"""

EXPAND_SYSTEM = """You write on-brand ad copy. JSON only."""

EXPAND_USER = """Tone: {tone}
Audience: {audience}
Claim: "{claim}"

Write:
- headline (40–70 chars, active)
- byline (80–140 chars, concrete benefit; no medical claims)
- cta (2–3 words)

JSON:
{{"headline":"…","byline":"…","cta":"…"}}
"""

VERIFY_SYSTEM = """You are a strict supplement claims reviewer. JSON only."""
VERIFY_USER = """Claim: "{claim}"
Ingredients: {ingredients}
Banned: {banned}
Reject disease, guarantees, “clinically proven” without proof, or non-plausible mechanisms.

JSON: {{"ok": true|false, "reason":"…", "rewrite":"…"}}"""