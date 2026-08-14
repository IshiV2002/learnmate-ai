"""Live demonstration of the LearnMate AI Recommendation Agent.

Simulates a real student quiz attempt, triggers the Recommendation Agent
to perform gap analysis, and displays the explainable recommendations,
topic mastery breakdown, and the Tutor Agent Socratic handoff package.
"""

import sys

# Ensure UTF-8 output on Windows terminal if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.database.database import DocumentDatabase
from app.database.models import DocumentRecord, QuestionMistakeDetail, QuizSubmissionRequest
from app.agents.recommendation_agent import RecommendationAgent


def run_demo() -> None:
    print("=" * 80)
    print(" [*] LearnMate AI - Recommendation Agent Live Demonstration")
    print("=" * 80)

    # 1. Initialize SQLite Database
    db = DocumentDatabase()
    db.initialize()

    # Ensure demo lecture document exists in DB
    demo_doc_id = "doc_demo_ir_01"
    existing_doc = db.get_document(demo_doc_id)
    if not existing_doc:
        db.create_document(
            DocumentRecord(
                document_id=demo_doc_id,
                original_filename="Lecture_4_Vector_Space_Model.pdf",
                stored_filename="Lecture_4_Vector_Space_Model.stored.pdf",
                page_count=18,
                pages_with_text=18,
                chunk_count=35,
                file_size_bytes=1048576,
                created_at="2026-08-14T21:00:00+00:00",
            )
        )
        print(f"[+] Registered lecture document: 'Lecture_4_Vector_Space_Model.pdf' (ID: {demo_doc_id})")
    else:
        print(f"[i] Using registered lecture document: '{existing_doc.original_filename}'")

    # 2. Instantiate Recommendation Agent
    agent = RecommendationAgent(database=db)

    # 3. Simulate a realistic Quiz Submission from Quiz Agent / Frontend
    # Scenario: Student took a 5-question quiz on Information Retrieval.
    # Strengths: Term Frequency (TF) definition, Skip pointers.
    # Weaknesses: Inverted Index Postings Lists, Term Weighting log scaling, Vector Space Normalization.
    submission = QuizSubmissionRequest(
        student_id="student_ravin_2026",
        document_id=demo_doc_id,
        quiz_id="quiz_vsm_101",
        quiz_title="IR Module 4: Vector Space & Scoring",
        time_spent_seconds=210,
        questions=[
            QuestionMistakeDetail(
                question_id="q1",
                topic="Term Weighting",
                difficulty="easy",
                cognitive_level="recall",
                question_text="What does TF stand for in TF-IDF?",
                selected_answer="Term Frequency",
                correct_answer="Term Frequency",
                is_correct=True,
                explanation="TF measures how frequently a term occurs in a document.",
            ),
            QuestionMistakeDetail(
                question_id="q2",
                topic="Term Weighting",
                difficulty="medium",
                cognitive_level="understanding",
                question_text="Why do we use logarithmic scaling for Term Frequency (log(1 + tf))?",
                selected_answer="To give 10 occurrences tenfold importance over 1 occurrence",
                correct_answer="To reflect diminishing returns of repeated term occurrences",
                is_correct=False,
                explanation="Sublinear scaling prevents high term frequency from dominating relevance scores.",
            ),
            QuestionMistakeDetail(
                question_id="q3",
                topic="Inverted Index",
                difficulty="easy",
                cognitive_level="recall",
                question_text="In an inverted index, what does a postings list contain for a term?",
                selected_answer="All words in alphabetical order",
                correct_answer="A list of document IDs (and positions) where the term occurs",
                is_correct=False,
                explanation="Postings lists store occurrences of a term across documents.",
            ),
            QuestionMistakeDetail(
                question_id="q4",
                topic="Inverted Index",
                difficulty="medium",
                cognitive_level="understanding",
                question_text="How do skip pointers optimize postings list intersection?",
                selected_answer="By skipping ahead without inspecting every posting element",
                correct_answer="By skipping ahead without inspecting every posting element",
                is_correct=True,
                explanation="Skip pointers allow O(sqrt(P)) comparisons during merge.",
            ),
            QuestionMistakeDetail(
                question_id="q5",
                topic="Vector Space Scoring",
                difficulty="hard",
                cognitive_level="application",
                question_text="Why is Euclidean length normalization (L2 norm) applied to document vectors?",
                selected_answer="To shorten long queries",
                correct_answer="To neutralize the unfair advantage long documents have due to high word counts",
                is_correct=False,
                explanation="Length normalization ensures long documents with repeated terms do not dominate.",
            ),
        ],
    )

    print("\n[>] Analyzing Student Quiz Performance with Recommendation Agent...")
    response = agent.analyze_and_recommend(submission)

    # 4. Display Results
    print("\n" + "=" * 80)
    print(f" [REPORT] OVERALL PERFORMANCE (Score: {response.overall_score}/{response.total_questions} - {response.score_percentage}%)")
    print("=" * 80)
    print(f" * Student ID         : {response.student_id}")
    print(f" * Quiz Title         : {submission.quiz_title}")
    print(f" * Mastery Level      : {response.mastery_level}")
    print(f" * Recommendation ID  : {response.recommendation_id}")
    print(f" * Attempt ID         : {response.attempt_id}")
    print(f"\n [Feedback Summary]:\n   \"{response.summary}\"")

    print("\n" + "-" * 80)
    print(" [TOPIC MASTERY BREAKDOWN]")
    print("-" * 80)
    for tm in response.topic_mastery:
        bar_filled = int(tm.accuracy_percentage / 10)
        bar = "#" * bar_filled + "." * (10 - bar_filled)
        print(f"  - {tm.topic:<22} : [{bar}] {tm.accuracy_percentage:>5.1f}% ({tm.correct_count}/{tm.total_questions}) | Status: {tm.mastery_status:<15} | Severity Score: {tm.weighted_severity_score}")

    print("\n" + "-" * 80)
    print(" [IDENTIFIED CONCEPTUAL KNOWLEDGE GAPS & EXPLAINABILITY]")
    print("-" * 80)
    for idx, gap in enumerate(response.knowledge_gaps, 1):
        print(f"\n {idx}. [{gap.severity}] Topic: '{gap.topic}' (Diagnosis Confidence: {int(gap.confidence_score * 100)}%)")
        print(f"    * Pedagogical Reasoning : {gap.explanation}")
        print(f"    * Missed Count          : {gap.missed_questions_count} question(s)")
        print(f"    * Misconceptions Logged :")
        for m in gap.sample_misconceptions:
            print(f"      - {m}")

    print("\n" + "-" * 80)
    print(" [PRIORITIZED ACTIONABLE STUDY PLAN]")
    print("-" * 80)
    for item in response.action_items:
        print(f"\n  [Priority #{item.priority}] - {item.action_type} ({item.estimated_minutes} mins)")
        print(f"  * Action Title : {item.title}")
        print(f"  * Guidance     : {item.description}")

    print("\n" + "=" * 80)
    print(" [TUTOR AGENT SOCRATIC HANDOFF PACKAGE - Inter-Agent Contract]")
    print("=" * 80)
    th = response.tutor_handoff
    print(f" * Target Remedial Topics : {', '.join(th.target_topics)}")
    print(f" * Overall Gap Severity   : {th.gap_severity}")
    print(f" * Pedagogical Directive  : {th.pedagogical_instruction}")
    print(f"\n [Suggested Socratic Opening Prompt for Tutor Agent]:")
    print(f"   \"{th.suggested_opening_prompt}\"")
    print("=" * 80)
    print("[+] Live demonstration complete. All records successfully persisted to SQLite.")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
