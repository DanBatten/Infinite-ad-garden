from pathlib import Path
from typing import List

SUPPORTED_EXTS = {".txt", ".md", ".markdown", ".json"}


def _safe_read_text(path: Path, max_chars: int) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if len(text) > max_chars:
            return text[:max_chars]
        return text
    except Exception:
        return ""


def _collect_from_dir(dir_path: Path, remaining: int) -> str:
    if not dir_path.exists() or not dir_path.is_dir() or remaining <= 0:
        return ""

    chunks: List[str] = []
    # deterministic order
    for file_path in sorted(dir_path.glob("**/*")):
        if remaining <= 0:
            break
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTS:
            header = f"\n\n=== FILE: {file_path.name} ===\n"
            header_len = len(header)
            file_budget = max(0, remaining - header_len)
            if file_budget <= 0:
                break
            body = _safe_read_text(file_path, file_budget)
            if body:
                chunks.append(header)
                chunks.append(body)
                remaining -= (header_len + len(body))
    return "".join(chunks)


def load_knowledge_texts(brand_name: str, brand_chars: int = 3000, global_chars: int = 3000) -> str:
    """
    Aggregate lightweight reference text from:
    - Global: inputs/ad_KnowledgeBase/creative_examples
    - Brand: inputs/{brand}/knowledge/creative_assets

    Character budgets are provided independently for brand and global.
    """
    brand_budget = max(0, int(brand_chars))
    global_budget = max(0, int(global_chars))

    global_dir = Path("inputs/ad_KnowledgeBase/creative_examples")
    brand_dir = Path(f"inputs/{brand_name}/knowledge/creative_assets")

    out_parts: List[str] = []

    # Brand knowledge (priority)
    if brand_budget > 0:
        brand_block = _collect_from_dir(brand_dir, brand_budget)
        if brand_block:
            out_parts.append("\n\n### BRAND KNOWLEDGE ###\n")
            out_parts.append(brand_block)

    # Global knowledge
    if global_budget > 0:
        global_block = _collect_from_dir(global_dir, global_budget)
        if global_block:
            out_parts.append("\n\n### GLOBAL KNOWLEDGE ###\n")
            out_parts.append(global_block)

    return "".join(out_parts).strip()


