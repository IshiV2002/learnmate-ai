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
