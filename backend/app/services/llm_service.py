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

            response_text = self._call_gemini(prompt, max_tokens=600)
            if response_text:
                try:
                    clean_text = response_text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    if clean_text.startswith("```"):
                        clean_text = clean_text[3:]
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

    def generate_quiz_questions(
        self,
        context_chunks: list[dict[str, Any]],
        topic: str | None = None,
        num_questions: int = 5,
        difficulty: str = "mixed",
        question_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Synthesize educational assessment questions grounded in lecture context."""
        question_types = question_types or ["mcq"]
        context_text = "\n\n".join(
            f"[Page {c.get('page_number', 1)}]: {c.get('text', '')}"
            for c in context_chunks[:8]
        )

        if self.is_available and context_text.strip():
            prompt = (
                f"You are an expert university professor creating a formative assessment.\n"
                f"Topic focus: {topic or 'Core Concepts in the Lecture'}\n"
                f"Difficulty distribution: {difficulty}\n"
                f"Question types: {', '.join(question_types)}\n"
                f"Number of questions required: {num_questions}\n\n"
                f"Lecture Context Source:\n{context_text}\n\n"
                "Generate a JSON array of questions strictly based on the provided lecture context. "
                "Each object in the array MUST contain:\n"
                "- 'question_id': 'q1', 'q2', etc.\n"
                "- 'topic': Specific concept name (e.g. 'Inverted Index', 'Term Weighting', etc.)\n"
                "- 'difficulty': 'easy', 'medium', or 'hard'\n"
                "- 'cognitive_level': 'recall', 'understanding', 'application', or 'analysis'\n"
                "- 'question_type': 'mcq', 'short_answer', or 'true_false'\n"
                "- 'question_text': Clear, unambiguous question\n"
                "- 'options': Array of 4 distinct choices for MCQ, or ['True', 'False'] for true_false, or [] for short_answer\n"
                "- 'correct_answer': The exact correct choice or concise model answer\n"
                "- 'explanation': Educational explanation clarifying why this answer is correct\n"
                "- 'rubric': Essential keywords or criteria required in an answer\n"
                "- 'source_page': Page number integer from the context citations\n"
                "- 'source_chunk_index': Chunk index integer\n\n"
                "Return ONLY a valid JSON array. Do not include markdown preamble."
            )

            response_text = self._call_gemini(prompt, max_tokens=2000)
            if response_text:
                try:
                    clean_text = response_text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    if clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    parsed = json.loads(clean_text)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return parsed[:num_questions]
                except Exception:
                    pass

        # Deterministic fallback question generator when offline or if LLM unavailable
        return self._generate_fallback_questions(
            context_chunks=context_chunks,
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
            question_types=question_types,
        )

    def _generate_fallback_questions(
        self,
        context_chunks: list[dict[str, Any]],
        topic: str | None,
        num_questions: int,
        difficulty: str,
        question_types: list[str],
    ) -> list[dict[str, Any]]:
        """Deterministic heuristic question generator for offline, CI, and fallback use."""
        target_topic = topic or "Course Fundamentals"
        extracted_facts: list[tuple[str, int, int]] = []

        for chunk in context_chunks:
            text = chunk.get("text", "").strip()
            page = chunk.get("page_number", 1)
            chunk_idx = chunk.get("chunk_index", 0)
            sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 30]
            for sentence in sentences:
                extracted_facts.append((sentence, page, chunk_idx))

        questions: list[dict[str, Any]] = []
        difficulties = ["easy", "medium", "hard"] if difficulty == "mixed" else [difficulty]
        cognitive_levels = ["recall", "understanding", "application", "analysis"]

        for i in range(num_questions):
            q_id = f"q{i + 1}"
            diff = difficulties[i % len(difficulties)]
            cog = cognitive_levels[i % len(cognitive_levels)]
            q_type = question_types[i % len(question_types)] if question_types else "mcq"

            if extracted_facts:
                fact, page_num, c_idx = extracted_facts[i % len(extracted_facts)]
                words = [w for w in fact.split() if len(w) > 4 and w.isalpha()]
                key_term = words[0] if words else target_topic

                if q_type == "true_false":
                    is_true = (i % 2 == 0)
                    statement = fact if is_true else f"{fact} (Note: this is universally inverted)."
                    questions.append({
                        "question_id": q_id,
                        "topic": target_topic,
                        "difficulty": diff,
                        "cognitive_level": cog,
                        "question_type": "true_false",
                        "question_text": f"True or False: {statement}",
                        "options": ["True", "False"],
                        "correct_answer": "True" if is_true else "False",
                        "explanation": f"Based on lecture page {page_num}: '{fact}'.",
                        "rubric": key_term,
                        "source_page": page_num,
                        "source_chunk_index": c_idx,
                    })
                elif q_type == "short_answer":
                    questions.append({
                        "question_id": q_id,
                        "topic": target_topic,
                        "difficulty": diff,
                        "cognitive_level": cog,
                        "question_type": "short_answer",
                        "question_text": f"Explain the significance of '{key_term}' according to the lecture context.",
                        "options": [],
                        "correct_answer": fact,
                        "explanation": f"Page {page_num} states that {fact}.",
                        "rubric": key_term,
                        "source_page": page_num,
                        "source_chunk_index": c_idx,
                    })
                else:
                    # MCQ
                    correct_opt = f"{fact[:90]}..." if len(fact) > 90 else fact
                    distractors = [
                        f"It is unrelated to {target_topic} and only affects network bandwidth",
                        f"It reduces computational complexity by random parameter shuffling",
                        f"It is an obsolete technique superseded by unindexed linear scanning",
                    ]
                    options = [correct_opt] + distractors
                    # Deterministically shuffle based on index
                    shift = i % 4
                    rotated_options = options[shift:] + options[:shift]

                    questions.append({
                        "question_id": q_id,
                        "topic": target_topic,
                        "difficulty": diff,
                        "cognitive_level": cog,
                        "question_type": "mcq",
                        "question_text": f"Regarding '{target_topic}', which statement accurately reflects the concept of {key_term}?",
                        "options": rotated_options,
                        "correct_answer": correct_opt,
                        "explanation": f"According to page {page_num}: {fact}.",
                        "rubric": key_term,
                        "source_page": page_num,
                        "source_chunk_index": c_idx,
                    })
            else:
                # Generic fallback if no context chunks provided
                questions.append({
                    "question_id": q_id,
                    "topic": target_topic,
                    "difficulty": diff,
                    "cognitive_level": cog,
                    "question_type": "mcq",
                    "question_text": f"What is the primary objective of studying {target_topic} in this curriculum?",
                    "options": [
                        f"To understand and apply foundational principles of {target_topic}",
                        "To bypass algorithmic optimization completely",
                        "To store arbitrary unstructured metadata without index support",
                        "To eliminate the need for data verification",
                    ],
                    "correct_answer": f"To understand and apply foundational principles of {target_topic}",
                    "explanation": f"Understanding foundational principles of {target_topic} is essential for mastery.",
                    "rubric": target_topic,
                    "source_page": 1,
                    "source_chunk_index": 0,
                })

        return questions

    def evaluate_conceptual_answer(
        self,
        question_text: str,
        reference_answer: str,
        student_answer: str,
        rubric: str = "",
    ) -> tuple[bool, float, str]:
        """Evaluate an open-ended student answer using LLM or rubric heuristics.

        Returns:
            (is_correct, score_fraction (0.0 to 1.0), pedagogical_feedback)
        """
        clean_student = student_answer.strip()
        if not clean_student:
            return False, 0.0, "No answer was provided."

        if self.is_available:
            prompt = (
                "You are an objective academic evaluator.\n"
                f"Question: {question_text}\n"
                f"Ground Truth Reference: {reference_answer}\n"
                f"Key Rubric Concepts: {rubric}\n"
                f"Student Answer: {clean_student}\n\n"
                "Evaluate the student's conceptual correctness. Return a JSON object with:\n"
                "- 'score': A float between 0.0 and 1.0 (1.0 = fully correct, 0.5 = partial credit, 0.0 = incorrect)\n"
                "- 'is_correct': boolean (true if score >= 0.6)\n"
                "- 'feedback': 1-2 constructive sentences explaining what was correct and any missing concepts."
            )
            resp = self._call_gemini(prompt, max_tokens=300)
            if resp:
                try:
                    clean = resp.strip()
                    if clean.startswith("```json"):
                        clean = clean[7:]
                    if clean.startswith("```"):
                        clean = clean[3:]
                    if clean.endswith("```"):
                        clean = clean[:-3]
                    parsed = json.loads(clean)
                    score = max(0.0, min(1.0, float(parsed.get("score", 0.0))))
                    is_correct = bool(parsed.get("is_correct", score >= 0.6))
                    feedback = str(parsed.get("feedback", ""))
                    return is_correct, score, feedback
                except Exception:
                    pass

        # Heuristic Rubric & Token Overlap Fallback
        ref_words = set(w.lower() for w in reference_answer.split() if len(w) > 3)
        rubric_words = set(w.lower() for w in rubric.split() if len(w) > 3)
        student_words = set(w.lower() for w in clean_student.split() if len(w) > 3)

        overlap = len(ref_words.intersection(student_words))
        rubric_overlap = len(rubric_words.intersection(student_words))
        total_target = max(1, len(ref_words) + len(rubric_words))

        matched = overlap + (rubric_overlap * 2)
        score_ratio = min(1.0, matched / max(2, min(6, total_target)))

        if score_ratio >= 0.6:
            return True, score_ratio, f"Good explanation! Your answer touches on the key concepts: {reference_answer[:80]}..."
        elif score_ratio >= 0.3:
            return False, score_ratio, f"Partially correct, but missing critical points. Key idea: {reference_answer[:80]}..."
        else:
            return False, 0.0, f"Incorrect concept. The correct understanding is: {reference_answer[:100]}..."

    def _call_gemini(self, prompt: str, max_tokens: int = 300) -> str | None:
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
                "maxOutputTokens": max_tokens,
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

