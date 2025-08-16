CLAIMS_SYSTEM = """You are a senior paid social copywriter for performance ads.
Return JSON only. Be creative yet compliant: avoid disease or drug-like claims (treat/cure/prevent); keep language truthful and testable."""

CLAIMS_USER = """You are a senior paid social copywriter. Generate creative ad claims for the brand {brand_name} using the following knowledge base.

- Brand Context:
  - Name: {brand_name}
  - Tagline: {tagline}
  - Mission: {mission}
  - Audience: {audience}
  - Personality/Tone: {tone}
  - Positioning: {positioning}
  - Compliance: Never use “treat,” “cure,” or “prevent” language; results may vary.

- Creative Guidelines (from training docs):
  - Headlines 4–8 words; punchy, curiosity-driven, emotional
  - Hook hard in first 3–5 words
  - Avoid jargon, all-caps spam, or fluff
  - Speak directly to one person (“you”)

- Claim Style Instructions (match to selected style):
  - Benefit-Focused: Highlight the main benefit clearly and aspirationally; show the win (“you get…”).
  - Problem–Solution: State a relatable problem, resolve with the brand as the obvious solution.
  - Social Proof: Use review language, volume, or authority (“Thousands trust…”, “Rated 4.9 stars”).
  - Urgency-Driven: Emphasize timeliness or scarcity (“Today only,” “Selling fast”).
  - Mixed Styles: Blend benefit, light problem, subtle proof, and urgency in one versatile claim.

- Angles to Rotate In:
  - {angle_name}

Primary style to follow for this batch: {style}
Style-specific guidance: {style_instruction}

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
- Ground each line in the brand positioning above; avoid generic claims.
- Use brand-compliant language only; avoid medical/disease claims.
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

VERIFY_SYSTEM = """You are a strict supplement claims reviewer. JSON only."""
VERIFY_USER = """Claim: "{claim}"
Ingredients: {ingredients}
Banned: {banned}
Reject disease, guarantees, “clinically proven” without proof, or non-plausible mechanisms.

JSON: {{"ok": true|false, "reason":"…", "rewrite":"…"}}"""