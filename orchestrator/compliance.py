BANNED_PHRASES = {
    "cure", "treat", "prevent disease", "clinically proven", "guaranteed",
    "diagnose", "mitigate", "heal", "medicine", "prescription"
}

def validate_claim(text: str, formulation) -> bool:
    low = text.lower()
    if any(p in low for p in BANNED_PHRASES):
        return False
    if any(p.lower() in low for p in formulation.banned_claims):
        return False
    return True
