from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.retrieval_agent import RetrievalAgent

from app.database.models import (
    KnowledgeGap,
    StudyActionItem,
    TutorHandoffPackage,
)
from app.services.llm_service import LLMService


class TutorHandoffService:
    """Service that enriches recommendations with ground-truth lecture context
    from the Retrieval Agent and synthesizes the handoff package for the Tutor Agent.
    """

    def __init__(
        self,
        retrieval_agent: RetrievalAgent | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self.retrieval_agent = retrieval_agent
        self.llm_service = llm_service or LLMService()

    def enrich_citations_and_build_handoff(
        self,
        recommendation_id: str,
        student_id: str,
        document_id: str,
        quiz_title: str,
        gaps: list[KnowledgeGap],
        action_items: list[StudyActionItem],
        mastered_topics: list[str] | None = None,
        mistake_details: list[dict[str, Any]] | None = None,
    ) -> tuple[list[StudyActionItem], TutorHandoffPackage]:
        """Fetch lecture references via RetrievalAgent and assemble the Tutor Handoff package."""
        all_retrieved_chunks: list[dict[str, Any]] = []
        weak_topics = [gap.topic for gap in gaps]
        mastered = mastered_topics or []
        mistakes = mistake_details or []

        # 1. Fetch relevant lecture chunks for weak topics if Retrieval Agent is available
        if self.retrieval_agent and document_id:
            doc_ids = [d.strip() for d in document_id.split(",") if d.strip()]
            for item in action_items:
                try:
                    if len(doc_ids) > 1 and hasattr(self.retrieval_agent, "search_documents"):
                        search_results = self.retrieval_agent.search_documents(
                            document_ids=doc_ids,
                            query=item.topic,
                            top_k=2,
                        )
                    else:
                        search_results = self.retrieval_agent.search(
                            document_id=doc_ids[0] if doc_ids else document_id,
                            query=item.topic,
                            top_k=2,
                        )
                    citations = [
                        {
                            "page_number": res.get("page_number", 1),
                            "chunk_index": res.get("chunk_index", 0),
                            "source": res.get("source", ""),
                            "text_preview": (res.get("text", "")[:180] + "...")
                            if len(res.get("text", "")) > 180
                            else res.get("text", ""),
                        }
                        for res in search_results
                    ]
                    item.lecture_citations = citations
                    all_retrieved_chunks.extend(citations)
                except Exception:
                    # Retrieval is best-effort enrichment; do not crash recommendations if document has no chunks
                    item.lecture_citations = []

        # 2. Extract sample misconceptions
        misconceptions: list[str] = []
        for gap in gaps:
            misconceptions.extend(gap.sample_misconceptions[:2])

        # 3. Synthesize Socratic instruction, personalized opening prompt, and cognitive bridge via LLM or fallback
        instruction, opening_prompt, cognitive_bridge = self.llm_service.generate_socratic_tutor_package(
            quiz_title=quiz_title,
            weak_topics=weak_topics,
            sample_misconceptions=misconceptions,
            mastered_topics=mastered,
            mistake_details=mistakes,
        )

        # 4. Determine overall gap severity
        if any(g.severity == "CRITICAL" for g in gaps):
            gap_severity = "CRITICAL"
        elif any(g.severity == "MODERATE" for g in gaps):
            gap_severity = "MODERATE"
        elif any(g.severity == "MINOR" for g in gaps):
            gap_severity = "MINOR"
        else:
            gap_severity = "NONE"

        # 5. Assemble Tutor Handoff Package
        tutor_package = TutorHandoffPackage(
            recommendation_id=recommendation_id,
            student_id=student_id,
            document_id=document_id,
            target_topics=weak_topics,
            gap_severity=gap_severity,
            pedagogical_instruction=instruction,
            suggested_opening_prompt=opening_prompt,
            relevant_lecture_chunks=all_retrieved_chunks[:4],
            mastered_topics=mastered,
            cognitive_bridge_analogy=cognitive_bridge,
        )

        return action_items, tutor_package
