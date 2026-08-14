import unittest

from app.database.models import QuestionMistakeDetail
from app.services.gap_analysis_service import GapAnalysisService


def create_question(
    q_id: str,
    topic: str,
    difficulty: str = "medium",
    is_correct: bool = True,
    selected: str = "A",
    correct: str = "A",
) -> QuestionMistakeDetail:
    return QuestionMistakeDetail(
        question_id=q_id,
        topic=topic,
        difficulty=difficulty,  # type: ignore[arg-type]
        cognitive_level="understanding",
        question_text=f"Question text for {q_id}",
        selected_answer=selected,
        correct_answer=correct,
        is_correct=is_correct,
        explanation="Standard explanation",
    )


class GapAnalysisServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = GapAnalysisService()

    def test_empty_questions_handled_gracefully(self) -> None:
        score, level, summary, masteries, gaps, actions = self.service.analyze([])
        self.assertEqual(score, 0.0)
        self.assertEqual(masteries, [])
        self.assertEqual(gaps, [])
        self.assertEqual(actions, [])

    def test_perfect_score_yields_advanced_mastery(self) -> None:
        questions = [
            create_question("q1", "Vector Space Models", "easy", True),
            create_question("q2", "Vector Space Models", "medium", True),
            create_question("q3", "TF-IDF Weighting", "hard", True),
        ]
        score, level, summary, masteries, gaps, actions = self.service.analyze(questions)

        self.assertEqual(score, 100.0)
        self.assertEqual(level, "Advanced Proficiency")
        self.assertEqual(len(gaps), 0)
        self.assertEqual(len(masteries), 2)
        self.assertEqual(masteries[0].mastery_status, "Mastered")
        self.assertEqual(masteries[1].mastery_status, "Mastered")
        self.assertEqual(len(actions), 1)
        self.assertIn("Deepen Concept Synthesis", actions[0].title)

    def test_failed_easy_questions_trigger_critical_gap_severity(self) -> None:
        questions = [
            create_question("q1", "PageRank", "easy", False, selected="B", correct="A"),
            create_question("q2", "PageRank", "medium", True, selected="C", correct="C"),
            create_question("q3", "Inverted Index", "easy", True, selected="D", correct="D"),
        ]
        score, level, summary, masteries, gaps, actions = self.service.analyze(questions)

        self.assertAlmostEqual(score, 66.7, places=1)
        self.assertEqual(len(gaps), 1)
        pagerank_gap = gaps[0]
        self.assertEqual(pagerank_gap.topic, "PageRank")
        self.assertEqual(pagerank_gap.severity, "CRITICAL")
        self.assertIn("fundamental/easy concept", pagerank_gap.explanation)
        self.assertEqual(pagerank_gap.missed_questions_count, 1)

    def test_multi_topic_prioritization_orders_critical_before_moderate(self) -> None:
        questions = [
            # Topic A: 0/2 correct (Critical)
            create_question("q1", "Topic A", "easy", False),
            create_question("q2", "Topic A", "medium", False),
            # Topic B: 1/2 correct (Moderate, 50%)
            create_question("q3", "Topic B", "medium", True),
            create_question("q4", "Topic B", "medium", False),
            # Topic C: 3/4 correct (Minor, 75%, only hard missed)
            create_question("q5", "Topic C", "easy", True),
            create_question("q6", "Topic C", "medium", True),
            create_question("q7", "Topic C", "medium", True),
            create_question("q8", "Topic C", "hard", False),
        ]
        score, level, summary, masteries, gaps, actions = self.service.analyze(questions)

        self.assertEqual(len(gaps), 3)
        # Topics must be ordered: CRITICAL -> MODERATE -> MINOR
        self.assertEqual(gaps[0].topic, "Topic A")
        self.assertEqual(gaps[0].severity, "CRITICAL")
        self.assertEqual(gaps[1].topic, "Topic B")
        self.assertEqual(gaps[1].severity, "MODERATE")
        self.assertEqual(gaps[2].topic, "Topic C")
        self.assertEqual(gaps[2].severity, "MINOR")

        # Action items should correspond in priority order
        self.assertEqual(actions[0].priority, 1)
        self.assertEqual(actions[0].topic, "Topic A")
        self.assertEqual(actions[0].action_type, "Deep Conceptual Review")

        self.assertEqual(actions[1].priority, 2)
        self.assertEqual(actions[1].topic, "Topic B")
        self.assertEqual(actions[1].action_type, "Review Lecture")

        self.assertEqual(actions[2].priority, 3)
        self.assertEqual(actions[2].topic, "Topic C")
        self.assertEqual(actions[2].action_type, "Practice Drills")
