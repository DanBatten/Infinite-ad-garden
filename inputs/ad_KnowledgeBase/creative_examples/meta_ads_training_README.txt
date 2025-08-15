Meta Ads Training Dataset
Generated: 2025-08-12T19:02:10.869170Z

FILES
- meta_ads_training_dataset.csv
- meta_ads_training_dataset.jsonl

SCHEMA (columns)
brand, product, angle, hook_type, headline, primary_text, cta, format_length, tone, audience, objective, platform, emojis_used, compliance_flags, notes

FIELD NOTES
- hook_type: Choose from [Problem (Negative), Question Hook, Social Proof, FOMO / Scarcity, Solution-First, Controversial / Pattern Interrupt, Offer].
- format_length: short/medium/long (guidance for copy length).
- compliance_flags: Add flags like “Restricted category on Meta—use education/landing page pre‑qual; avoid health/medical claims” where relevant.
- notes: Any clarifying info (e.g., preorder language).

USAGE
- Fine-tune or prompt an AI model to generate headlines + primary text by conditioning on brand, product, angle, hook_type, and format_length.
- Train to swap components modularly: keep headline and primary_text logically linked to hook_type.
- For Meta policy-sensitive verticals (supplements, CBD, medical), keep primary_text framed as general wellness or education and avoid explicit disease/medical claims.
