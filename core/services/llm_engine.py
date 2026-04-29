# core/services/llm_engine.py

from pathlib import Path
import os
import logging
import random

from dotenv import load_dotenv
from openai import AzureOpenAI


# -------------------------------------------------
# FORCE LOAD .env FROM PROJECT ROOT
# -------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


# -------------------------------------------------
# LOGGING
# -------------------------------------------------

logger = logging.getLogger(__name__)


# -------------------------------------------------
# ENV CONFIG
# -------------------------------------------------

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_OPENAI_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

API_VERSION = "2024-02-15-preview"

if not AZURE_ENDPOINT or not AZURE_KEY or not DEPLOYMENT:
    raise RuntimeError(
        "Azure OpenAI env missing.\n"
        "Check .env for:\n"
        "AZURE_OPENAI_ENDPOINT\n"
        "AZURE_OPENAI_KEY\n"
        "AZURE_OPENAI_DEPLOYMENT"
    )


# -------------------------------------------------
# CLIENT
# -------------------------------------------------

client = AzureOpenAI(
    api_key=AZURE_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    api_version=API_VERSION,
)


# -------------------------------------------------
# LLM ENGINE
# -------------------------------------------------

class LLMEngine:
    """
    Azure LLM wrapper for:
      • topic selection
      • familiarity questions
      • experience followups
      • HR screening
    """

    # =====================================================
    # INTERNAL CALL
    # =====================================================

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:

        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.35,
                max_tokens=160,
            )

            # ---- Extract Azure content safely ----
            raw = resp.choices[0].message.content

            text = self._extract_text(raw)

            try:
                return self._sanitize(text)

            except ValueError as e:
                logger.warning("LLM sanitize failed: %s", e)

                return "Can you describe your experience related to this area?"

        except Exception:
            logger.exception("Azure LLM call failed")
            return "Can you tell me more about your experience in this area?"

    # =====================================================
    # RESPONSE NORMALIZER
    # =====================================================

    def _extract_text(self, raw):

        if isinstance(raw, str):
            return raw

        # object with .text
        if hasattr(raw, "text"):
            return raw.text

        # dict response
        if isinstance(raw, dict):
            return raw.get("text") or raw.get("content") or str(raw)

        # list of blocks
        if isinstance(raw, list):
            parts = []
            for item in raw:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(item.get("text", ""))
                elif hasattr(item, "text"):
                    parts.append(item.text)
            return " ".join(parts)

        return str(raw)

    # =====================================================
    # TOPIC SELECTION
    # =====================================================

    def pick_next_topic(self, role: str, exclude: list[str]) -> str:

        system = (
            "You are an HR screening designer. "
            "Return ONLY one short topic label. "
            "No explanation."
        )

        user = f"""
Role: {role}

Topics already asked:
{exclude}

Suggest ONE new screening topic relevant to this role.

Return only the topic name.
"""

        topic = self._call_llm(system, user)

        if topic.lower() in [t.lower() for t in exclude]:
            topic = random.choice(
                [
                    "compliance",
                    "employee relations",
                    "recruitment",
                    "payroll basics",
                    "due diligence",
                    "financial analysis",
                ]
            )

        return topic.replace(".", "").strip()

    # =====================================================
    # FAMILIARITY QUESTION
    # =====================================================

    def generate_topic_familiarity_question(self, role: str, topic: str):

        system = (
            "You are a professional screening interviewer. "
            "Ask ONLY one short yes/no familiarity question."
        )

        user = f"""
Role: {role}
Topic: {topic}

Ask if the candidate is familiar with this topic.
One sentence only.
"""

        return self._call_llm(system, user)

    # =====================================================
    # EXPERIENCE FOLLOWUP
    # =====================================================

    def generate_topic_experience_question(self, role: str, topic: str):

        system = (
            "You are a professional interviewer. "
            "Ask ONLY one experience-based follow-up question."
        )

        user = f"""
Role: {role}
Topic: {topic}

Candidate said YES to familiarity.

Ask one experience-based question.
"""

        return self._call_llm(system, user)

    # =====================================================
    # HR BLOCK
    # =====================================================

    def generate_hr_screening_question(self, role: str):

        system = (
            "You are an HR interviewer. "
            "Ask one short screening question."
        )

        user = f"""
Role: {role}

Ask ONE HR question.
Topics: availability, notice period, salary, relocation,
shifts, travel, hobbies, joining date.
"""

        return self._call_llm(system, user)

    # =====================================================
    # SANITIZER
    # =====================================================

    def _sanitize(self, text: str):

        if not isinstance(text, str):
            text = str(text)

        text = text.replace("\n", " ").strip()

        banned_terms = [
            "religion",
            "caste",
            "politics",
            "marital",
            "children",
            "age",
            "pregnant",
        ]

        lowered = text.lower()

        for term in banned_terms:
            if term in lowered:
                raise ValueError("Unsafe LLM output detected")

        return text[:300]
