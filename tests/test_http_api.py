"""HTTP integration tests using an isolated database and an ephemeral port."""

import hashlib
import json
import sys
import tempfile
import threading
import unittest
import uuid
from unittest.mock import patch
from datetime import date
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

import server as portal_server  # noqa: E402


class PortalApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="cesmac-sdd-test-")
        self.original_db_file = portal_server.DB_FILE
        portal_server.DB_FILE = Path(self.temp_dir.name) / "test.sqlite3"
        self._start_server()

    def tearDown(self):
        self._stop_server()
        portal_server.DB_FILE = self.original_db_file
        self.temp_dir.cleanup()

    def _start_server(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), portal_server.PortalHandler)
        self.httpd.daemon_threads = True
        self.base_url = "http://127.0.0.1:{}".format(self.httpd.server_address[1])
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def _stop_server(self):
        if getattr(self, "httpd", None) is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.thread.join(timeout=3)
            self.httpd = None

    def _request(self, path, method="GET", payload=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            with error:
                return error.code, error.read(), error.headers
        with response:
            return response.status, response.read(), response.headers

    def _new_listing(self, **overrides):
        data = {
            "kind": "lost",
            "title": "Item teste {}".format(uuid.uuid4().hex[:10]),
            "description": "Descrição fictícia para teste automatizado.",
            "category": "Chaves",
            "location": "Biblioteca",
            "eventDate": date.today().isoformat(),
            "contactName": "Pessoa de Teste",
            "contactEmail": "teste@example.invalid",
            "contactPhone": "",
            "urgent": False,
            "photo": "",
        }
        data.update(overrides)
        return data

    def test_health_and_openapi_route(self):
        status, body, _ = self._request("/api/v1/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"status": "ok"})

        status, body, headers = self._request("/openapi.yaml")
        self.assertEqual(status, 200)
        self.assertIn("application/yaml", headers.get("Content-Type", ""))
        self.assertIn(b"openapi: 3.0.3", body)

    def test_ai_status_does_not_expose_secret(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "private-test-secret"}):
            status, body, _ = self._request("/api/v1/ai/status")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["configured"])
        self.assertNotIn(b"private-test-secret", body)

    def test_direct_item_lookup_for_shared_links(self):
        status, body, _ = self._request("/api/v1/items", "POST", self._new_listing())
        created = json.loads(body)
        status, body, _ = self._request("/api/v1/items/{}".format(created["item"]["id"]))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["item"]["id"], created["item"]["id"])
        self.assertNotIn(created["managementToken"].encode(), body)
        self.assertNotIn(b"management_hash", body)
        status, _, _ = self._request("/api/v1/items/999999")
        self.assertEqual(status, 404)

    def test_ai_requires_valid_input_and_explicit_consent(self):
        portal_server._match_requests.clear()
        with patch.object(portal_server, "generate_assistance") as provider:
            for payload in ([], {"mode": "bad"}, {"mode": "search", "text": "Perdi um fone", "consent": False}):
                status, _, _ = self._request("/api/v1/ai/assist", "POST", payload)
                self.assertEqual(status, 422)
            provider.assert_not_called()

    def test_ai_excludes_contacts_descriptions_and_management_from_catalog(self):
        portal_server._match_requests.clear()
        self._request("/api/v1/items", "POST", self._new_listing())
        result = {"method": "gemini", "message": "Nenhum item compatível", "matches": [], "tips": []}
        with patch.object(portal_server, "generate_assistance", return_value=result) as provider:
            status, body, _ = self._request("/api/v1/ai/assist", "POST", {"mode": "search", "text": "Perdi um fone preto", "consent": True})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), result)
        for item in provider.call_args.args[3]:
            self.assertEqual(set(item), {"id", "title", "category", "kind", "location", "eventDate", "demo"})

    def test_ai_unconfigured_is_503_and_rate_limit_is_429(self):
        portal_server._match_requests.clear()
        payload = {"mode": "search", "text": "Perdi um fone preto", "consent": True}
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            status, _, _ = self._request("/api/v1/ai/assist", "POST", payload)
        self.assertEqual(status, 503)
        with patch.object(portal_server, "_allow_match_request", return_value=False):
            status, _, _ = self._request("/api/v1/ai/assist", "POST", payload)
        self.assertEqual(status, 429)
        portal_server._match_requests.clear()

    def test_radar_filters_opposite_type_and_demo_records_on_server(self):
        portal_server._match_requests.clear()
        for kind in ("lost", "found"):
            self._request("/api/v1/items", "POST", self._new_listing(kind=kind))
        payload = {"mode": "search", "text": "Perdi um objeto", "consent": True, "lookingFor": "found"}
        with patch.object(portal_server, "generate_assistance", return_value={"method": "gemini", "matches": [], "message": "Sem itens", "tips": []}) as provider:
            status, body, _ = self._request("/api/v1/ai/assist", "POST", payload)
        self.assertEqual(status, 200)
        candidates = provider.call_args.args[3]
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["kind"], "found")
        self.assertFalse(candidates[0]["demo"])
        self.assertEqual(json.loads(body)["catalogCount"], 1)
        self.assertFalse(json.loads(body)["includesExamples"])

    def test_radar_validates_options_without_server_errors(self):
        portal_server._match_requests.clear()
        payload = {"mode": "search", "text": "Perdi um objeto", "consent": True}
        for invalid in ({"lookingFor": []}, {"includeExamples": "true"}, {"mode": []}):
            with self.subTest(invalid=invalid):
                status, _, _ = self._request("/api/v1/ai/assist", "POST", {**payload, **invalid})
                self.assertEqual(status, 422)

    def test_publish_find_contact_and_persist_after_restart(self):
        listing = self._new_listing()
        status, body, _ = self._request("/api/v1/items", "POST", listing)
        self.assertEqual(status, 201)
        created = json.loads(body)
        self.assertTrue(created["managementToken"])
        item_id = created["item"]["id"]
        self.assertEqual(created["item"]["contactEmail"], listing["contactEmail"])
        with portal_server.db_session() as db:
            stored_hash = db.execute(
                "SELECT management_hash FROM listings WHERE id = ?", (item_id,)
            ).fetchone()["management_hash"]
        self.assertEqual(
            stored_hash,
            hashlib.sha256(created["managementToken"].encode("utf-8")).hexdigest(),
        )

        query = urlencode({"q": listing["title"]})
        status, body, _ = self._request("/api/v1/items?{}".format(query))
        self.assertEqual(status, 200)
        results = json.loads(body)["items"]
        self.assertTrue(any(item["id"] == item_id for item in results))
        self.assertNotIn("managementToken", results[0])

        self._stop_server()
        self._start_server()
        status, body, _ = self._request("/api/v1/items?{}".format(query))
        self.assertEqual(status, 200)
        self.assertTrue(any(item["id"] == item_id for item in json.loads(body)["items"]))

    def test_rejects_invalid_creation(self):
        status, body, _ = self._request(
            "/api/v1/items", "POST", self._new_listing(category="Inválida")
        )
        self.assertEqual(status, 422)
        self.assertIn("error", json.loads(body))

    def test_rejects_invalid_status_kind_and_category_filters(self):
        for query in (
            "status=unknown",
            "kind=unknown",
            "category=Categoria%20inexistente",
        ):
            with self.subTest(query=query):
                status, body, _ = self._request("/api/v1/items?" + query)
                self.assertEqual(status, 400)
                self.assertIn("error", json.loads(body))

    def test_valid_kind_and_category_filters_return_matching_items(self):
        listing = self._new_listing(kind="found", category="Eletrônicos")
        status, body, _ = self._request("/api/v1/items", "POST", listing)
        self.assertEqual(status, 201)
        item_id = json.loads(body)["item"]["id"]

        query = urlencode({"kind": "found", "category": "Eletrônicos"})
        status, body, _ = self._request("/api/v1/items?{}".format(query))
        self.assertEqual(status, 200)
        self.assertTrue(any(item["id"] == item_id for item in json.loads(body)["items"]))

    def test_search_with_no_matches_returns_empty_list(self):
        query = urlencode({"q": "termo-inexistente-" + uuid.uuid4().hex})
        status, body, _ = self._request("/api/v1/items?{}".format(query))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["items"], [])

    def test_list_order_prioritizes_open_urgent_and_newer_items(self):
        marker = "ordem-" + uuid.uuid4().hex
        for title, urgent, status_value, created_at in (
            (marker + "-normal-recente", False, "open", "2026-01-03T00:00:00+00:00"),
            (marker + "-urgente-antigo", True, "open", "2026-01-01T00:00:00+00:00"),
            (marker + "-resolvido", True, "resolved", "2026-01-04T00:00:00+00:00"),
        ):
            status, body, _ = self._request(
                "/api/v1/items",
                "POST",
                self._new_listing(title=title, description=marker, urgent=urgent),
            )
            self.assertEqual(status, 201)
            item_id = json.loads(body)["item"]["id"]
            with portal_server.db_session() as db:
                db.execute(
                    "UPDATE listings SET status=?, created_at=? WHERE id=?",
                    (status_value, created_at, item_id),
                )
        query = urlencode({"q": marker, "status": "all"})
        status, body, _ = self._request("/api/v1/items?{}".format(query))
        self.assertEqual(status, 200)
        titles = [item["title"] for item in json.loads(body)["items"]]
        self.assertEqual(
            titles,
            [marker + "-urgente-antigo", marker + "-normal-recente", marker + "-resolvido"],
        )

    def test_missing_item_returns_404_for_resolve_and_delete(self):
        missing_id = 999999
        status, body, _ = self._request(
            "/api/v1/items/{}".format(missing_id),
            "PATCH",
            {"managementToken": "token-ficticio", "status": "recovered"},
        )
        self.assertEqual(status, 404)
        self.assertIn("error", json.loads(body))

        status, body, _ = self._request(
            "/api/v1/items/{}".format(missing_id),
            "DELETE",
            {"managementToken": "token-ficticio"},
        )
        self.assertEqual(status, 404)
        self.assertIn("error", json.loads(body))

    def test_counters_include_all_records_and_update_after_resolution(self):
        status, body, _ = self._request("/api/v1/items")
        self.assertEqual(status, 200)
        baseline = json.loads(body)["stats"]

        status, body, _ = self._request(
            "/api/v1/items", "POST", self._new_listing(kind="lost")
        )
        self.assertEqual(status, 201)
        lost = json.loads(body)
        status, body, _ = self._request(
            "/api/v1/items", "POST", self._new_listing(kind="found")
        )
        self.assertEqual(status, 201)

        status, body, _ = self._request(
            "/api/v1/items/{}".format(lost["item"]["id"]),
            "PATCH",
            {"managementToken": lost["managementToken"], "status": "recovered"},
        )
        self.assertEqual(status, 200)

        status, body, _ = self._request("/api/v1/items?status=all")
        self.assertEqual(status, 200)
        stats = json.loads(body)["stats"]
        self.assertEqual(stats["total"], baseline["total"] + 2)
        self.assertEqual(stats["lost"], baseline["lost"])
        self.assertEqual(stats["found"], baseline["found"] + 1)
        self.assertEqual(stats["resolved"], baseline["resolved"] + 1)

    def test_wrong_management_code_cannot_resolve_item(self):
        status, body, _ = self._request("/api/v1/items", "POST", self._new_listing())
        self.assertEqual(status, 201)
        item_id = json.loads(body)["item"]["id"]

        status, body, _ = self._request(
            "/api/v1/items/{}".format(item_id),
            "PATCH",
            {"managementToken": "token-incorreto", "status": "recovered"},
        )
        self.assertEqual(status, 403)
        self.assertIn("error", json.loads(body))

        status, body, _ = self._request(
            "/api/v1/items/{}".format(item_id),
            "DELETE",
            {"managementToken": "token-incorreto"},
        )
        self.assertEqual(status, 403)

    def test_valid_management_code_resolves_lost_and_found_items(self):
        for kind, resolution in (("lost", "recovered"), ("found", "returned")):
            with self.subTest(kind=kind):
                status, body, _ = self._request(
                    "/api/v1/items", "POST", self._new_listing(kind=kind)
                )
                self.assertEqual(status, 201)
                created = json.loads(body)
                item_id = created["item"]["id"]
                status, body, _ = self._request(
                    "/api/v1/items/{}".format(item_id),
                    "PATCH",
                    {"managementToken": created["managementToken"], "status": resolution},
                )
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body)["item"]["status"], "resolved")

    def test_photo_route_returns_uploaded_image(self):
        listing = self._new_listing(photo="data:image/png;base64,aGVsbG8=")
        status, body, _ = self._request("/api/v1/items", "POST", listing)
        self.assertEqual(status, 201)
        item_id = json.loads(body)["item"]["id"]
        status, body, headers = self._request("/api/v1/items/{}/photo".format(item_id))
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Content-Type"), "image/png")
        self.assertEqual(body, b"hello")

    def test_oversized_request_returns_413(self):
        listing = self._new_listing(description="x" * 1_000_001)
        status, body, _ = self._request("/api/v1/items", "POST", listing)
        self.assertEqual(status, 413)
        self.assertIn("error", json.loads(body))


if __name__ == "__main__":
    unittest.main()

