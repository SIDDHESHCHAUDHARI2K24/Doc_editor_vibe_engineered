"""Check content equivalence of Claude.md, AGENTS.md, and .cursorrules.

Compares H2 sections across all three agent rules files. Exits 0 if equivalent
on the compared sections, exits 1 with a diff message if not.

Usage:
    python scripts/check_agent_rules.py
    uv run python scripts/check_agent_rules.py
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FILES = ["Claude.md", "AGENTS.md", ".cursorrules"]

SECTIONS_TO_COMPARE = ["Tech stack", "Repo layout", "Conventions"]


def extract_section(text: str, heading: str) -> str:
    """Extract content under an H2 heading until the next H2 or EOF."""
    escaped = re.escape(heading)
    pattern = rf"^## {escaped}\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def normalize(text: str) -> str:
    """Normalize text for comparison: collapse whitespace, lowercase."""
    return re.sub(r"\s+", " ", text.strip()).lower()


def main() -> None:
    contents: dict[str, str] = {}
    for filename in FILES:
        path = REPO_ROOT / filename
        if not path.exists():
            print(f"ERROR: {filename} not found at {path}")
            sys.exit(1)
        contents[filename] = path.read_text(encoding="utf-8")

    errors: list[str] = []
    for section in SECTIONS_TO_COMPARE:
        normalized: dict[str, str] = {}
        for filename in FILES:
            raw = extract_section(contents[filename], section)
            if not raw:
                errors.append(f"Missing section '## {section}' in {filename}")
            normalized[filename] = normalize(raw)

        if len(set(normalized.values())) > 1:
            errors.append(f"Section '## {section}' differs across files")

    if errors:
        for err in errors:
            print(f"FAIL: {err}")
        sys.exit(1)

    print("OK: Claude.md, AGENTS.md, and .cursorrules are equivalent on compared sections.")
    sys.exit(0)


if __name__ == "__main__":
    main()
