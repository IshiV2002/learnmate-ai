import json
import unittest
from unittest.mock import patch

from app.services.llm_service import LLMService


class FakeGeminiResponse:
    """Small context-manager response used without making a network request."""

    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "grounded reply"}]}}]}
        ).encode("utf-8")


class LLMServiceTests(unittest.TestCase):
    def test_offline_fallback_creates_five_distinct_grounded_mcqs(self) -> None:
        service = LLMService(api_key="")
        context_chunks = [
            {
                "page_number": 2,
                "chunk_index": 0,
                "text": (
                    "An inverted index is a database index that maps terms to document positions. "
                    "TF-IDF weighting calculates a product of term frequency and inverse document frequency to measure term importance. "
                    "Cosine similarity measures the angle between two document vectors. "
                    "Tokenization converts text into individual tokens before indexing. "
                    "Stop-word removal excludes common terms that contribute little meaning."
                ),
            }
        ]

        questions = service.generate_quiz_questions(
            context_chunks=context_chunks,
            topic="Information Retrieval",
            num_questions=5,
            question_types=["mcq"],
        )

        self.assertEqual(len(questions), 5)
        self.assertEqual(len({question["question_text"] for question in questions}), 5)
        self.assertEqual(len({question["correct_answer"] for question in questions}), 5)
        for question in questions:
            self.assertTrue(question["question_text"].endswith("?"))
            self.assertEqual(len(question["options"]), 4)
            self.assertEqual(len(set(question["options"])), 4)
            self.assertIn(question["correct_answer"], question["options"])
            self.assertEqual(question["source_page"], 2)
            self.assertEqual(question["source_chunk_index"], 0)

    def test_offline_fallback_refuses_to_pad_with_generic_questions(self) -> None:
        service = LLMService(api_key="")
        with self.assertRaisesRegex(ValueError, "supports only 1 distinct questions"):
            service.generate_quiz_questions(
                context_chunks=[
                    {
                        "page_number": 1,
                        "chunk_index": 0,
                        "text": "An inverted index is a structure that maps terms to document positions.",
                    }
                ],
                num_questions=2,
                question_types=["mcq"],
            )

    def test_gemini_request_uses_current_model_header_key_and_system_instruction(
        self,
    ) -> None:
        service = LLMService(
            api_key="test-api-key",
            model_name="gemini-2.5-flash",
        )

        with patch(
            "app.services.llm_service.urllib.request.urlopen",
            return_value=FakeGeminiResponse(),
        ) as urlopen_mock:
            result = service._call_gemini("Student content")

        self.assertEqual(result, "grounded reply")
        request = urlopen_mock.call_args.args[0]
        self.assertIn("models/gemini-2.5-flash:generateContent", request.full_url)
        self.assertNotIn("test-api-key", request.full_url)
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(headers["x-goog-api-key"], "test-api-key")

        request_payload = json.loads(request.data.decode("utf-8"))
        system_text = request_payload["system_instruction"]["parts"][0]["text"]
        self.assertIn("untrusted data", system_text)
        self.assertIn("Do not reveal", system_text)
        self.assertEqual(
            request_payload["contents"][0]["parts"][0]["text"],
            "Student content",
        )


if __name__ == "__main__":
    unittest.main()
