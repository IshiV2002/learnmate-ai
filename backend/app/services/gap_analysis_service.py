from collections import defaultdict
from typing import Any
import uuid

from app.database.models import (
    KnowledgeGap,
    QuestionMistakeDetail,
    StudyActionItem,
    TopicMastery,
)


class GapAnalysisService:
    """Intelligent Knowledge Gap Analyzer and Explainability Engine.
    
    Computes topic-level mastery percentages, difficulty-weighted severity metrics,
    and transparent pedagogical explanations for student misconceptions.
    """

    DIFFICULTY_WEIGHTS = {
        "easy": 1.0,      # Missing easy questions indicates fundamental concept gaps
        "medium": 1.5,
        "hard": 2.0,
    }

    def analyze(
        self,
        questions: list[QuestionMistakeDetail],
    ) -> tuple[float, str, str, list[TopicMastery], list[KnowledgeGap], list[StudyActionItem]]:
        """Perform comprehensive gap analysis on quiz submissions.
        
        Returns:
            overall_score_percentage,
            mastery_level,
            summary,
            topic_masteries,
            knowledge_gaps,
            action_items
        """
        if not questions:
            return 0.0, "No Assessment", "No quiz questions were submitted.", [], [], []

        total_questions = len(questions)
        total_correct = sum(1 for q in questions if q.is_correct)
        overall_score_percentage = round((total_correct / total_questions) * 100, 1)

        # 1. Group by Topic
        topic_groups: dict[str, list[QuestionMistakeDetail]] = defaultdict(list)
        for question in questions:
            topic_groups[question.topic].append(question)

        topic_masteries: list[TopicMastery] = []
        knowledge_gaps: list[KnowledgeGap] = []
        action_items: list[StudyActionItem] = []

        # 2. Analyze Each Topic
        for topic, topic_questions in topic_groups.items():
            t_total = len(topic_questions)
            t_correct = sum(1 for q in topic_questions if q.is_correct)
            t_accuracy = round((t_correct / t_total) * 100, 1)

            # Difficulty breakdown
            diff_breakdown: dict[str, dict[str, int]] = {
                "easy": {"correct": 0, "total": 0},
                "medium": {"correct": 0, "total": 0},
                "hard": {"correct": 0, "total": 0},
            }
            weighted_missed_score = 0.0
            missed_questions: list[QuestionMistakeDetail] = []

            for q in topic_questions:
                diff = q.difficulty if q.difficulty in diff_breakdown else "medium"
                diff_breakdown[diff]["total"] += 1
                if q.is_correct:
                    diff_breakdown[diff]["correct"] += 1
                else:
                    missed_questions.append(q)
                    weighted_missed_score += self.DIFFICULTY_WEIGHTS.get(diff, 1.5)

            # Mastery Status
            if t_accuracy >= 80.0:
                mastery_status = "Mastered"
            elif t_accuracy >= 50.0:
                mastery_status = "Review Needed"
            else:
                mastery_status = "Critical Gap"

            topic_masteries.append(
                TopicMastery(
                    topic=topic,
                    total_questions=t_total,
                    correct_count=t_correct,
                    accuracy_percentage=t_accuracy,
                    mastery_status=mastery_status,
                    weighted_severity_score=round(weighted_missed_score, 2),
                    difficulty_breakdown=diff_breakdown,
                )
            )

            # If there are mistakes, formulate Knowledge Gap
            if missed_questions:
                # Severity calculation
                if t_accuracy < 50.0 or diff_breakdown["easy"]["correct"] < diff_breakdown["easy"]["total"]:
                    severity = "CRITICAL"
                elif t_accuracy < 75.0:
                    severity = "MODERATE"
                else:
                    severity = "MINOR"

                # Confidence in gap diagnosis based on evidence count
                confidence = min(0.60 + (len(missed_questions) * 0.15), 0.98)

                # Transparent explainability justification
                explanation_parts = [
                    f"Student scored {t_accuracy}% ({t_correct}/{t_total} correct) on '{topic}'."
                ]
                if diff_breakdown["easy"]["total"] > 0 and diff_breakdown["easy"]["correct"] < diff_breakdown["easy"]["total"]:
                    explanation_parts.append("Missed fundamental/easy concept questions.")
                if diff_breakdown["hard"]["total"] > 0 and diff_breakdown["hard"]["correct"] < diff_breakdown["hard"]["total"]:
                    explanation_parts.append("Encountered difficulty with advanced application questions.")

                explanation_text = " ".join(explanation_parts)

                # Sample misconceptions from student mistakes
                misconceptions = [
                    f"Selected '{q.selected_answer}' instead of '{q.correct_answer}' for '{q.question_text}'"
                    for q in missed_questions[:3]
                ]

                knowledge_gaps.append(
                    KnowledgeGap(
                        gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                        topic=topic,
                        severity=severity,
                        confidence_score=round(confidence, 2),
                        explanation=explanation_text,
                        missed_questions_count=len(missed_questions),
                        sample_misconceptions=misconceptions,
                        suggested_prerequisites=[f"Core definitions of {topic}"],
                    )
                )

        # Sort Knowledge Gaps by severity (CRITICAL -> MODERATE -> MINOR)
        severity_order = {"CRITICAL": 0, "MODERATE": 1, "MINOR": 2}
        knowledge_gaps.sort(key=lambda g: (severity_order.get(g.severity, 3), -g.missed_questions_count))

        # 3. Overall Mastery Level & Summary
        if overall_score_percentage >= 85.0:
            mastery_level = "Advanced Proficiency"
            summary = (
                f"Excellent mastery demonstrated across topics ({overall_score_percentage}%). "
                f"Minor reinforcement on specialized details is recommended."
            )
        elif overall_score_percentage >= 70.0:
            mastery_level = "Proficient / Needs Minor Review"
            summary = (
                f"Solid foundational understanding ({overall_score_percentage}%). "
                f"A few focused topic reviews will solidify your comprehension."
            )
        elif overall_score_percentage >= 50.0:
            mastery_level = "Developing / Review Needed"
            summary = (
                f"Moderate performance ({overall_score_percentage}%). "
                f"Key conceptual knowledge gaps identified in {len(knowledge_gaps)} topic(s). Targeted review recommended."
            )
        else:
            mastery_level = "Critical Foundation Gaps"
            summary = (
                f"Significant conceptual gaps identified ({overall_score_percentage}%). "
                f"Step-by-step remedial tutoring is strongly recommended before advancing."
            )

        # 4. Generate Prioritized Action Items
        priority_idx = 1
        for gap in knowledge_gaps:
            if gap.severity == "CRITICAL":
                action_type = "Deep Conceptual Review"
                minutes = 20
                desc = f"Review fundamental lecture concepts for '{gap.topic}' with the AI Tutor and clarify identified misconceptions."
            elif gap.severity == "MODERATE":
                action_type = "Review Lecture"
                minutes = 15
                desc = f"Re-read key lecture sections on '{gap.topic}' and verify understanding of intermediate principles."
            else:
                action_type = "Practice Drills"
                minutes = 10
                desc = f"Complete quick flashcard or quiz drills on '{gap.topic}' to reinforce recall."

            action_items.append(
                StudyActionItem(
                    priority=priority_idx,
                    topic=gap.topic,
                    action_type=action_type,
                    title=f"Study Plan: {gap.topic}",
                    description=desc,
                    estimated_minutes=minutes,
                    lecture_citations=[],
                )
            )
            priority_idx += 1

        # If 100% score / no gaps, provide enrichment action item
        if not action_items:
            action_items.append(
                StudyActionItem(
                    priority=1,
                    topic="Advanced Mastery",
                    action_type="Practice Drills",
                    title="Deepen Concept Synthesis",
                    description="You answered all questions correctly! Challenge yourself with advanced application questions.",
                    estimated_minutes=15,
                    lecture_citations=[],
                )
            )

        return (
            overall_score_percentage,
            mastery_level,
            summary,
            topic_masteries,
            knowledge_gaps,
            action_items,
        )
