CLAIMS_SYSTEM = """You are a senior paid social copywriter for performance ads.
Return JSON only. Write claims in the specified style AND DO NOT blend styles."""

CLAIMS_USER = """You are a senior paid social copywriter. Generate creative ad claims for the brand {brand_name} using the following knowledge base.

- Brand Context:
  - Name: {brand_name}
  - Tagline: {tagline}
  - Mission: {mission}
  - Audience: {audience}
  - Personality/Tone: {tone}
  - Positioning: {positioning}
  - Proof assets (for Social Proof style): {proof_assets}
  - Compliance: Never use “treat,” “cure,” or “prevent” language; results may vary.

- Creative Guidelines (from training docs):
  - Headlines 4–8 words; punchy, curiosity-driven, emotional
  - Hook hard in first 3–5 words
  - Avoid jargon, all-caps spam, or fluff
  - Speak directly to one person (“you”)

- Selected Style: {style}
- Style Instruction: {style_instruction}

- Angles to Rotate In:
  - {angle_name}

Primary style to follow for this batch: {style}

Task
Generate EXACTLY {target_count} distinct ad claims in the selected style.
Each claim should be one strong, memorable line (4–14 words). Suitable for a Meta ad hook or headline.

Output Format (single JSON object):
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

Constraints
- No duplicates across claims.
- Balance voice types across the batch (~40% first_person, 30% why_explainer, 30% stat_hook).
- Each claim should be testable as a headline.
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

# Compliance prompt templates removed per request