# core/services/evaluator.py

import re


# -------------------------------------------------
# YES / NO ROLE KNOWLEDGE CHECK (Q2)
# -------------------------------------------------

NEGATIVE_PATTERNS = [
    r"\bno\b",
    r"\bnot\b",
    r"\bnever\b",
    r"\bdon't\b",
    r"\bdont\b",
    r"\bnone\b",
]

POSITIVE_PATTERNS = [
    r"\byes\b",
    r"\byep\b",
    r"\byeah\b",
    r"\bsure\b",
    r"\bof course\b",
    r"\bi do\b",
    r"\bi have\b",
]


YES_WORDS = [
    "yes", "yeah", "yup", "yep", "sure",
    "i have", "i did", "i do",
    "worked", "experience", "experienced",
    "familiar", "know", "knowledge"
]

NO_WORDS = [
    "no", "nope", "nah",
    "not really", "don't", "do not",
    "haven't", "have not",
    "not familiar", "no idea"
]


def is_positive(text: str | None) -> bool:

    if not text:
        return False

    t = text.lower()

    if any(w in t for w in YES_WORDS):
        return True

    if any(w in t for w in NO_WORDS):
        return False

    # default: treat unknown as NO
    return False


def evaluate_role_confirmation(answer: str) -> bool:
    """
    Returns:
        True  -> candidate knows role
        False -> candidate does NOT know role
    """

    if not answer:
        return False

    a = answer.lower()

    for pat in NEGATIVE_PATTERNS:
        if re.search(pat, a):
            return False

    for pat in POSITIVE_PATTERNS:
        if re.search(pat, a):
            return True

    # default safe assumption → continue
    return True


# -------------------------------------------------
# WEAK SKILL HEURISTIC
# -------------------------------------------------

WEAK_HINTS = [
    r"\bnot sure\b",
    r"\bmaybe\b",
    r"\blittle\b",
    r"\bbasic\b",
    r"\bbeginner\b",
    r"\blearning\b",
    r"\bno experience\b",
    r"\bnot much\b",
]


def detect_weak_skill(answer: str, skill_tag: str | None = None):
    """
    Returns skill_tag if weakness detected.
    """

    if not answer:
        return None

    text = answer.lower()

    for pat in WEAK_HINTS:
        if re.search(pat, text):
            return skill_tag or "general"

    return None
