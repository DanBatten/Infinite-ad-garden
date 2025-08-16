CLAIMS_SYSTEM = """You are a compliance-aware, but creative ad ideation partner for ingestible beauty supplements.
Return JSON only. Avoid disease or drug-like claims."""

CLAIMS_USER = """🎯 PRIMARY INSTRUCTION - FOLLOW THIS STYLE EXACTLY:
{style_instruction}

⚠️  IMPORTANT: The STYLE above is your PRIMARY directive. Everything else is context.

📋 CONTEXT (for reference only):
Brand tone: {tone}
Audience: {audience}
Available angles: {angle_name}
Ingredients: {ingredients}
Voice rules: {dos} | Avoid: {donts}
Lexicon: Prefer {prefer} | Avoid {avoid}

Examples (DO NOT copy, just understand the brand voice):
{examples}

📝 TASK:
Generate EXACTLY {target_count} claims for {product_name}.
Structure and diversity:
- Use varied opening patterns across the batch (questions, direct benefits, defamiliarization, proof-led).
- Keep lines specific and concrete; avoid generic templates.
- Avoid these overused verbs in headlines: elevate, unlock, transform, discover, reveal, experience, boost.
- Keep 1–2 sentences; aim for 8–18 words per sentence.

CRITICAL: Each claim MUST embody the specific style approach, tone, and the above constraints.

JSON:
{{ "claims": [ {{ "text": "…", "style": "{style}", "support": "How this claim follows the style guidance" }} ] }}"""

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