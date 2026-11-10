"""Provider-boundary tests: no external calls or real API credentials."""
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import ai_service


class AssistanceTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"GEMINI_API_KEY": "test-not-a-real-key"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.catalog = [{"id": 8, "title": "Garrafa azul", "kind": "found", "demo": False}]

    def response(self, answer, finish="STOP"):
        return io.BytesIO(json.dumps({"candidates": [{"finishReason": finish,
            "content": {"parts": [{"text": json.dumps(answer)}]}}]}).encode())

    def test_missing_key_never_calls_provider(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}), patch.object(ai_service, "urlopen") as provider:
            with self.assertRaises(ai_service.AIUnavailable):
                ai_service.generate_assistance("search", "Perdi uma garrafa", "", [], "test-model")
            provider.assert_not_called()

    def test_filters_invented_duplicate_and_boolean_ids(self):
        answer = {"message": "Confira estes itens.", "matchIds": [999, True, 8, 8, "8"], "tips": ["Compare os detalhes."]}
        with patch.object(ai_service, "urlopen", return_value=self.response(answer)) as provider:
            result = ai_service.generate_assistance("search", "Perdi uma garrafa", "", self.catalog, "test-model")
        self.assertEqual(result["matches"], self.catalog)
        self.assertEqual(result["method"], "gemini")
        request = provider.call_args.args[0]
        self.assertEqual(request.get_header("X-goog-api-key"), "test-not-a-real-key")
        self.assertNotIn("test-not-a-real-key", request.full_url)

    def test_valid_empty_matches_stays_empty(self):
        with patch.object(ai_service, "urlopen", return_value=self.response({"message": "Nenhum item compatível.", "matchIds": [], "tips": []})):
            result = ai_service.generate_assistance("search", "Perdi um livro", "", self.catalog, "test-model")
        self.assertEqual(result["matches"], [])

    def test_photo_is_sent_for_draft_without_catalog(self):
        draft = {"title": "Garrafa azul", "description": "Garrafa de metal azul.", "category": "Acessórios", "location": "", "kind": "found", "unexpected": "discard"}
        with patch.object(ai_service, "urlopen", return_value=self.response({"message": "Revise o rascunho.", "matchIds": [], "tips": [], "draft": draft})) as provider:
            result = ai_service.generate_assistance("draft", "Encontrei esta garrafa", "data:image/png;base64,YQ==", self.catalog, "test-model")
        sent = json.loads(provider.call_args.args[0].data)
        parts = sent["contents"][0]["parts"]
        self.assertEqual(parts[1]["inlineData"]["mimeType"], "image/png")
        self.assertEqual(json.loads(parts[0]["text"])["catalogo"], [])
        self.assertNotIn("unexpected", result["draft"])
        self.assertEqual(result["draft"]["location"], "")

    def test_invalid_or_truncated_provider_output_is_rejected(self):
        for answer, finish in (([], "STOP"), ({"message": "x", "matchIds": "8", "tips": []}, "STOP"), ({"message": "x", "matchIds": [], "tips": []}, "MAX_TOKENS")):
            with self.subTest(answer=answer), patch.object(ai_service, "urlopen", return_value=self.response(answer, finish)):
                with self.assertRaises(ai_service.AIUnavailable):
                    ai_service.generate_assistance("search", "Perdi uma garrafa", "", self.catalog, "test-model")

    def test_provider_failures_do_not_leak_secrets(self):
        for error in (HTTPError("secret", 429, "secret key", {}, None), HTTPError("secret", 403, "secret key", {}, None), URLError("secret key")):
            with self.subTest(error=error), patch.object(ai_service, "urlopen", side_effect=error):
                with self.assertRaises(ai_service.AIUnavailable) as caught:
                    ai_service.generate_assistance("search", "Perdi uma garrafa", "", self.catalog, "test-model")
                self.assertNotIn("secret", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
