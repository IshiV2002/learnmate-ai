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

    def generate_tutor_response(
        self,
        topic_focus: str,
        mode: str,
        pedagogical_directive: str | None,
        lecture_chunks: list[dict[str, Any]],
        history: list[dict[str, str]],
        student_message: str,
    ) -> tuple[str, list[str], str | None]:
        """Generate a pedagogical Socratic or step-by-step tutoring response grounded in lecture context.

        Returns:
            (reply_text, suggested_followups, concept_check_question)
        """
        # Format lecture context for grounding
        context_lines = []
        for i, chunk in enumerate(lecture_chunks, start=1):
            pg = chunk.get("page_number", "?")
            src = chunk.get("source", "Document")
            txt = chunk.get("text", "").strip()
            context_lines.append(f"[{i}] Page {pg} ({src}): {txt}")
        formatted_context = "\n\n".join(context_lines) if context_lines else "No specific lecture passages retrieved."

        # If LLM is available, call Gemini
        if self.is_available:
            history_str = "\n".join(
                f"{'Student' if h.get('role') == 'student' else 'AI Tutor'}: {h.get('content', '')}"
                for h in history[-6:]
            )
            mode_guidance = {
                "socratic": "Use the Socratic method: ask a probing, guided question to help the student derive the answer themselves. Do NOT give raw answers immediately.",
                "step_by_step": "Break down the concept into 2-3 clear, numbered steps with a simple analogy or concrete example.",
                "concept_check": "Provide a concise explanation (1-2 sentences) followed immediately by a quick comprehension check question.",
            }.get(mode, "Be an encouraging, clear, and step-by-step academic tutor.")

            prompt = (
                f"You are LearnMate AI, a patient, empathetic university AI Tutor grounded strictly in course materials.\n"
                f"Active Topic: {topic_focus or 'Course Concepts'}\n"
                f"Pedagogical Mode: {mode} ({mode_guidance})\n"
                f"Directive from Assessment Coach: {pedagogical_directive or 'Help student grasp fundamental principles.'}\n\n"
                f"--- Ground Truth Lecture Excerpts ---\n{formatted_context}\n\n"
                f"--- Recent Conversation History ---\n{history_str}\n\n"
                f"Student's Current Message: {student_message}\n\n"
                "Instructions:\n"
                "1. Ground your explanation in the lecture excerpts. Mention the page number when referencing course concepts (e.g. '[Page 3]').\n"
                "2. Maintain the chosen pedagogical mode.\n"
                "3. Provide your response in JSON format with three fields:\n"
                "   - 'reply': (string) Your complete conversational reply formatted in clean markdown.\n"
                "   - 'suggested_followups': (list of 2-3 strings) Short questions or phrases the student can click next.\n"
                "   - 'concept_check_question': (string or null) A brief question to check their understanding, if applicable.\n"
            )

            response_text = self._call_gemini(prompt)
            if response_text:
                try:
                    clean_text = response_text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    parsed = json.loads(clean_text)
                    reply = str(parsed.get("reply", "")).strip()
                    followups = [str(f) for f in parsed.get("suggested_followups", []) if f]
                    check_q = parsed.get("concept_check_question")
                    if reply:
                        return reply, followups[:3], (str(check_q) if check_q else None)
                except Exception:
                    pass

        # Deterministic pedagogical fallback
        return self._fallback_tutor_response(
            topic_focus=topic_focus,
            mode=mode,
            pedagogical_directive=pedagogical_directive,
            lecture_chunks=lecture_chunks,
            student_message=student_message,
        )

    def _fallback_tutor_response(
        self,
        topic_focus: str,
        mode: str,
        pedagogical_directive: str | None,
        lecture_chunks: list[dict[str, Any]],
        student_message: str,
    ) -> tuple[str, list[str], str | None]:
        """Generate structured deterministic pedagogical response grounded on retrieved excerpts."""
        primary_topic = topic_focus or "this topic"
        first_chunk = lecture_chunks[0] if lecture_chunks else None
        page_num = first_chunk.get("page_number", 1) if first_chunk else 1
        source_name = first_chunk.get("source", "the lecture slides") if first_chunk else "the lecture"
        excerpt = first_chunk.get("text", "")[:200].strip() if first_chunk else ""

        if mode == "socratic":
            if lecture_chunks:
                reply = (
                    f"Let's explore **{primary_topic}** step-by-step based on {source_name} (Page {page_num}).\n\n"
                    f"> *\"{excerpt}...\"* (Page {page_num})\n\n"
                    f"To build an intuitive grasp: When looking at your query *\"{student_message}\"*, "
                    f"what do you think is the fundamental reason we apply this principle rather than a naive approach?"
                )
            else:
                reply = (
                    f"Great question about **{primary_topic}**!\n\n"
                    f"Before we dive into technical definitions, how would you summarize the main goal of "
                    f"this concept in your own words based on what you've learned so far?"
                )
            followups = [
                f"Can you give me a simple real-world analogy for {primary_topic}?",
                "What are the main advantages of this approach?",
                "Can you show me a step-by-step calculation or example?",
            ]
            check_q = f"What is the key problem that {primary_topic} is designed to solve?"
            return reply, followups, check_q

        if mode == "step_by_step":
            if lecture_chunks:
                reply = (
                    f"Here is a structured, step-by-step breakdown of **{primary_topic}** based on {source_name} (Page {page_num}):\n\n"
                    f"1. **Core Definition**: {excerpt}...\n"
                    f"2. **Why It Matters**: It prevents distortions and normalizes measurements across different documents or inputs.\n"
                    f"3. **Practical Application**: When applied in practice, it ensures fair comparison without favoring outliers.\n\n"
                    f"Does this sequence make sense, or would you like to drill into step 1 or 2?"
                )
            else:
                reply = (
                    f"Here is how to approach **{primary_topic}** step-by-step:\n\n"
                    f"1. **Foundational Concept**: Identify the inputs and key vocabulary.\n"
                    f"2. **Mechanism**: Follow the transformation or computation rule.\n"
                    f"3. **Interpretation**: Evaluate what the result tells us.\n\n"
                    f"Would you like an example to see how this works in practice?"
                )
            followups = [
                "Walk me through a concrete numeric example.",
                "How does this relate to the previous lecture topic?",
                "Let's test my understanding with a practice question.",
            ]
            return reply, followups, None

        # Mode: concept_check
        if lecture_chunks:
            reply = (
                f"According to {source_name} (Page {page_num}), the key principle for **{primary_topic}** is that "
                f"*{excerpt}...*\n\n"
                f"Now let's check your understanding: If we double the input frequency or change document length, "
                f"how should our calculation adapt?"
            )
        else:
            reply = (
                f"For **{primary_topic}**, the core takeaway is ensuring accurate, normalized comparisons.\n\n"
                f"Quick check: What would happen if we skipped this normalization step entirely?"
            )
        followups = [
            "Explain the answer to this concept check.",
            "Switch to Step-by-Step explanation mode.",
            "Ask me another challenging question on this topic.",
        ]
        check_q = f"How would the system behave if {primary_topic} was omitted?"
        return reply, followups, check_q

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
                "maxOutputTokens": 600,
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as response:
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

