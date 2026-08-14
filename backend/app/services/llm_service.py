import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.database.models import KnowledgeGap


class LLMService:
    """Service for generating LLM-powered explainable recommendations and Socratic tutor prompts.
    
    Uses Google Gemini API when GEMINI_API_KEY is configured in the environment,
    with a robust deterministic fallback for offline development and testing.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def is_available(self) -> bool:
        """Return True if an API key is configured."""
        return bool(self.api_key)

    def generate_pedagogical_summary(
        self,
        quiz_title: str,
        score_percentage: float,
        gaps: list[KnowledgeGap],
    ) -> str:
        """Generate a personalized, encouraging learning summary with growth-mindset feedback."""
        if not self.is_available or not gaps:
            # Deterministic pedagogical fallback
            if score_percentage >= 80.0:
                return (
                    f"Strong conceptual grasp demonstrated on '{quiz_title}'. "
                    f"Continue reinforcing key definitions to maintain mastery."
                )
            if score_percentage >= 50.0:
                top_topics = ", ".join(f"'{g.topic}'" for g in gaps[:2])
                return (
                    f"Good foundation on '{quiz_title}', with opportunities to strengthen understanding in {top_topics}. "
                    f"Reviewing the cited lecture sections with the AI Tutor will help solidify these areas."
                )
            critical_topics = ", ".join(f"'{g.topic}'" for g in gaps[:2])
            return (
                f"On '{quiz_title}', foundational misconceptions were identified in {critical_topics}. "
                f"We recommend a step-by-step Socratic review with the AI Tutor before attempting the next assessment."
            )

        prompt = (
            f"You are a supportive educational AI coach. A student completed a quiz on '{quiz_title}' "
            f"scoring {score_percentage}%. Identified knowledge gaps: "
            f"{json.dumps([{'topic': g.topic, 'severity': g.severity, 'explanation': g.explanation} for g in gaps])}. "
            "Write a concise (2-3 sentences), encouraging, growth-oriented summary highlighting what they did well "
            "and what specific concept they should focus on next."
        )

        llm_response = self._call_gemini(prompt)
        if llm_response:
            return llm_response.strip()

        # Fallback if API response is empty
        top_topics = ", ".join(f"'{g.topic}'" for g in gaps[:2])
        return (
            f"Completed assessment for '{quiz_title}' ({score_percentage}%). "
            f"Targeted review is recommended for {top_topics} to close conceptual gaps."
        )

    def generate_socratic_tutor_package(
        self,
        quiz_title: str,
        weak_topics: list[str],
        sample_misconceptions: list[str],
    ) -> tuple[str, str]:
        """Synthesize pedagogical guidance and an opening prompt for the Tutor Agent.
        
        Returns:
            (pedagogical_instruction, suggested_opening_prompt)
        """
        if not weak_topics:
            instruction = (
                "The student has achieved full mastery on this quiz. "
                "Engage them with advanced synthesis questions and real-world edge cases."
            )
            opening = (
                f"Congratulations on your outstanding performance on '{quiz_title}'! "
                "Would you like to explore advanced application scenarios or move to the next chapter?"
            )
            return instruction, opening

        topics_str = ", ".join(f"'{t}'" for t in weak_topics)
        first_topic = weak_topics[0]

        default_instruction = (
            f"You are an empathetic, step-by-step Socratic tutor. The student struggled with {topics_str}. "
            "Do not provide direct answers immediately. Instead, break down the core concept into simple intuitive steps, "
            "ask guided questions to identify their mental model, and validate their understanding before moving forward."
        )

        if sample_misconceptions:
            default_opening = (
                f"Hello! I noticed you encountered some challenging questions on {first_topic} during the '{quiz_title}' quiz. "
                "Let's explore this together step by step. To start, how would you describe the core purpose of this concept in your own words?"
            )
        else:
            default_opening = (
                f"Hello! Let's review the key principles behind {first_topic}. "
                "What aspect of this topic felt least clear to you during the quiz?"
            )

        if not self.is_available:
            return default_instruction, default_opening

        prompt = (
            f"You are an expert pedagogical designer. A student needs remedial tutoring on '{quiz_title}' for topics: {topics_str}. "
            f"Misconceptions noted: {json.dumps(sample_misconceptions)}. "
            "Generate JSON with two keys: 'instruction' (guiding the AI Tutor on how to teach) and "
            "'opening_prompt' (the first warm, friendly Socratic question the AI Tutor will say to the student)."
        )

        response_text = self._call_gemini(prompt)
        if response_text:
            try:
                # Try parsing json if LLM returned json format
                clean_text = response_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                parsed = json.loads(clean_text)
                if "instruction" in parsed and "opening_prompt" in parsed:
                    return str(parsed["instruction"]), str(parsed["opening_prompt"])
            except Exception:
                pass

        return default_instruction, default_opening

    def _call_gemini(self, prompt: str) -> str | None:
        """Perform a REST request to Gemini API if key is present."""
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 300,
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    response_data = json.loads(response.read().decode("utf-8"))
                    candidates = response_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
        except Exception:
            # On any network or API error, gracefully fall back
            return None

        return None
