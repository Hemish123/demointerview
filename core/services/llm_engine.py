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


    # =====================================================
    # INTERVIEW EVALUATION (STRICT SCORING)
    # =====================================================

    def evaluate_interview(self, role: str, turns: list[dict]) -> dict:
        """
        Evaluates the full interview transcript.
        Returns per-question scores, overall score, and confidence %.

        turns: list of {"question": str, "answer": str}
        """
        import json as _json

        # Build the transcript block for the prompt
        transcript_lines = []
        for i, t in enumerate(turns, 1):
            transcript_lines.append(
                f"Q{i}: {t['question']}\nA{i}: {t['answer']}"
            )
        transcript_text = "\n\n".join(transcript_lines)

        system = (
            "You are a STRICT technical interview evaluator. "
            "You must evaluate each answer against globally accepted standards for the given role. "
            "Do NOT be liberal or lenient. Score harshly but fairly. "
            "An empty or irrelevant answer must receive 0. "
            "A vague answer with no specifics should score no more than 3/10. "
            "Only genuinely strong, detailed, role-relevant answers should score 7+. "
            "Return ONLY valid JSON, no markdown, no explanation."
        )

        user = f"""
Role: {role}

Interview Transcript:
{transcript_text}

Evaluate EACH question-answer pair. Return JSON in this EXACT format:
{{
  "per_question": [
    {{
      "question_number": 1,
      "score": <0-10>,
      "remark": "<1 line reason for the score>"
    }}
  ],
  "overall_score": <0-100>,
  "confidence_percent": <0-100>,
  "confidence_remark": "<1 line about candidate's confidence level>",
  "knowledge_percent": <0-100>,
  "domain_percent": <0-100>,
  "communication_percent": <0-100>,
  "summary": "<2-3 line overall evaluation>"
}}

Scoring rules:
- score is 0-10 per question (0=no answer/irrelevant, 10=perfect expert answer)
- overall_score is 0-100 (weighted average, penalize unanswered questions heavily)
- confidence_percent is 0-100 (based on clarity, conviction, detail in answers)
- knowledge_percent is 0-100 (depth of technical/functional knowledge demonstrated)
- domain_percent is 0-100 (relevance and expertise in the specific role domain)
- communication_percent is 0-100 (articulation, structure, and clarity of responses)
- Skip greeting/intro questions (Q1 type) - give them score 5 (neutral)
- Be STRICT. Average candidates should score 40-55 overall, not 70+.
"""

        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.1,
                max_tokens=2000,
            )

            raw = resp.choices[0].message.content
            text = self._extract_text(raw)

            # Strip markdown fences if present
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            if text.startswith("json"):
                text = text[4:].strip()

            result = _json.loads(text)
            return result

        except Exception as e:
            logger.exception("Interview evaluation failed: %s", e)
            return {
                "per_question": [],
                "overall_score": 0,
                "confidence_percent": 0,
                "knowledge_percent": 0,
                "domain_percent": 0,
                "communication_percent": 0,
                "confidence_remark": "Evaluation failed",
                "summary": "Could not evaluate the interview. Please try again.",
            }


