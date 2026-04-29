from core.services.llm_engine import LLMEngine
import json
import re
import unicodedata

llm = LLMEngine()


SYSTEM = """
You are an HR analyst.

Extract:
1) Domain
2) Role titles
3) Seniority

Return ONLY valid JSON:

{
  "domain": "...",
  "roles": [
    {"label": "...", "level": "junior/senior/manager"}
  ]
}
"""


# -------------------------------------------------
# INTERNAL HELPERS (SAFE ADDITIONS)
# -------------------------------------------------

ROLE_KEYWORDS = [
    "associate",
    "senior associate",
    "manager",
    "lead",
    "executive",
    "officer",
    "analyst",
    "engineer",
    "developer",
    "hr",
    "payroll",
    "talent acquisition",
    "people function",
]

DOMAIN_HINTS = {
    "HR": ["payroll", "recruitment", "hr", "human resources", "ta"],
    "IT": ["developer", "engineer", "software"],
    "Education": ["teacher", "faculty", "trainer"],
}


def _normalize(text: str):
    text = unicodedata.normalize("NFKD", text)
    return text.replace("–", "-").replace("—", "-")


def _guess_domain(text: str):

    scores = {}

    for domain, kws in DOMAIN_HINTS.items():
        for kw in kws:
            if re.search(rf"\b{kw}\b", text, re.I):
                scores[domain] = scores.get(domain, 0) + 1

    if not scores:
        return "General"

    return max(scores, key=scores.get)


def _extract_roles_rules(text: str):

    roles = []

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:

        if 4 <= len(line) <= 90:

            for kw in ROLE_KEYWORDS:
                if re.search(rf"\b{kw}\b", line, re.I):

                    level = None
                    lline = line.lower()

                    if "senior" in lline:
                        level = "senior"
                    elif "manager" in lline or "lead" in lline:
                        level = "manager"
                    elif "associate" in lline or "junior" in lline:
                        level = "junior"

                    roles.append({
                        "label": line,
                        "level": level,
                    })
                    break

    # Deduplicate
    seen = set()
    unique = []

    for r in roles:
        key = r["label"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique


# -------------------------------------------------
# EXISTING JSON PARSER (UNCHANGED)
# -------------------------------------------------

def _safe_json(text: str):

    match = re.search(r"\{.*\}", text, re.S)

    if not match:
        raise ValueError("No JSON found from LLM")

    return json.loads(match.group())


# -------------------------------------------------
# MAIN ENTRY (ENHANCED BUT SAFE)
# -------------------------------------------------

def detect_domains_and_roles(text):

    text = _normalize(text)

    # ---------- RULE-BASED PASS FIRST ----------
    roles = _extract_roles_rules(text)
    domain = _guess_domain(text)

    if roles:
        return {
            "domain": domain,
            "roles": roles,
            "seniority": list(
                {r["level"] for r in roles if r.get("level")}
            ),
        }

    # ---------- FALLBACK TO LLM ----------
    user = f"""
JOB DESCRIPTION TEXT:

{text[:12000]}
"""

    raw = llm._call_llm(SYSTEM, user)

    return _safe_json(raw)
