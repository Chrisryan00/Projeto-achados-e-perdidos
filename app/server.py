"""Local HTTP API and static-file server for CESMAC Achados & Perdidos."""

from __future__ import annotations

import hashlib
import argparse
import base64
from contextlib import contextmanager
import json
import os
import re
import secrets
import sqlite3
import unicodedata
from datetime import date, datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlsplit
from urllib.request import Request, urlopen

from domain import CATEGORIES, KINDS, ValidationError, validate_listing, validate_photo


APP_DIR = Path(__file__).resolve().parent
DB_FILE = Path(os.environ.get(
    "LOST_FOUND_DB",
    Path(os.environ.get("LOCALAPPDATA", APP_DIR)) / "CESMAC-AchadosPerdidos" / "items.sqlite3",
))
MAX_BODY_BYTES = 1_000_000
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
_match_rate_lock = Lock()
_match_requests = {}
_WORD_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)
_SEARCH_STOPWORDS = {
    "a", "ao", "aos", "as", "com", "da", "das", "de", "do", "dos", "e", "em", "eu",
    "foi", "me", "na", "nas", "no", "nos", "o", "os", "para", "perdi", "perto", "por",
    "que", "um", "uma", "uns", "umas", "vi", "perdi", "encontrei", "achei", "meu", "minha",
}


def connect_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_FILE, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL CHECK(kind IN ('lost','found')),
        title TEXT NOT NULL, description TEXT NOT NULL, category TEXT NOT NULL,
        location TEXT NOT NULL, event_date TEXT NOT NULL,
        contact_name TEXT NOT NULL, contact_email TEXT NOT NULL DEFAULT '',
        contact_phone TEXT NOT NULL DEFAULT '', urgent INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'open',
        management_hash TEXT NOT NULL,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        is_demo INTEGER NOT NULL DEFAULT 0,
        photo_data TEXT NOT NULL DEFAULT ''
    )""")
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(listings)")}
    if "is_demo" not in columns:
        connection.execute("ALTER TABLE listings ADD COLUMN is_demo INTEGER NOT NULL DEFAULT 0")
    if "photo_data" not in columns:
        connection.execute("ALTER TABLE listings ADD COLUMN photo_data TEXT NOT NULL DEFAULT ''")
    connection.execute("CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_listings_status_date ON listings(status, created_at)")
    # Upgrade titles created by earlier versions while preserving the old DB column.
    connection.execute("""UPDATE listings
        SET title=CASE
            WHEN title LIKE 'DEMO ·%' THEN substr(title, 8)
            WHEN title LIKE 'EXEMPLO ·%' THEN substr(title, 11)
            ELSE title END,
        description=replace(replace(replace(replace(replace(description,
            ' O item é um exemplo fictício para demonstrar o mural.', ''),
            ' Exemplo fictício.', ''),
            ' não há documentos ou dados pessoais neste anúncio fictício.', ''),
            'Carregador branco encontrado e devolvido no exemplo de demonstração.',
            'Carregador branco encontrado e já devolvido ao dono.'),
            'Exemplo fictício.', ''),
        is_demo=1
        WHERE title LIKE 'DEMO ·%' OR title LIKE 'EXEMPLO ·%' OR is_demo=1""")
    connection.execute("""UPDATE listings SET contact_name=CASE title
        WHEN 'Fone bluetooth preto' THEN 'Mariana Alves'
        WHEN 'Chaveiro azul com três chaves' THEN 'Lucas Rocha'
        WHEN 'Caderno de Cálculo I' THEN 'Beatriz Lima'
        WHEN 'Garrafa térmica verde' THEN 'Rafael Costa'
        WHEN 'Carteira pequena marrom' THEN 'Camila Santos'
        WHEN 'Carregador USB-C branco' THEN 'Pedro Nunes'
        ELSE contact_name END
        WHERE is_demo=1""")
    seed_demo_data(connection)
    return connection


@contextmanager
def db_session():
    """Commit or roll back a database operation, then always release SQLite's file handle."""
    connection = connect_db()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def seed_demo_data(db):
    """Add clearly fictional examples once, preserving any real announcements."""
    if not db.execute("SELECT 1 FROM app_meta WHERE key = 'demo_seeded'").fetchone():
        has_examples = db.execute(
            "SELECT 1 FROM listings WHERE is_demo = 1 OR title LIKE 'DEMO ·%' OR title LIKE 'EXEMPLO ·%' LIMIT 1"
        ).fetchone()
        if not has_examples:
            base_examples = [
                ("lost", "Fone bluetooth preto", "Estojo preto fosco, sem identificação.", "Eletrônicos", "Biblioteca — térreo", 1, True, "open", "Mariana Alves"),
                ("found", "Chaveiro azul com três chaves", "Chaveiro de tecido azul encontrado perto da entrada.", "Chaves", "Bloco C — recepção", 2, False, "open", "Lucas Rocha"),
                ("lost", "Caderno de Cálculo I", "Caderno universitário com capa verde, sem nome visível.", "Material de estudo", "Cantina — mesas externas", 3, False, "open", "Beatriz Lima"),
                ("found", "Garrafa térmica verde", "Garrafa verde sem adesivos encontrada em uma sala de aula.", "Acessórios", "Bloco A — sala 204", 4, False, "open", "Rafael Costa"),
                ("lost", "Carteira pequena marrom", "Carteira pequena com alguns cartões.", "Acessórios", "Estacionamento — portaria", 5, True, "open", "Camila Santos"),
                ("found", "Carregador USB-C branco", "Carregador branco encontrado e já devolvido ao dono.", "Eletrônicos", "Laboratório de informática", 8, False, "resolved", "Pedro Nunes"),
            ]
            _insert_demo_examples(db, base_examples)
        db.execute("INSERT OR IGNORE INTO app_meta(key,value) VALUES('demo_seeded','1')")

    if not db.execute("SELECT 1 FROM app_meta WHERE key = 'demo_seeded_v2'").fetchone():
        additional_examples = [
            ("lost", "Mochila azul-marinho", "Mochila com caderno e estojo no bolso da frente.", "Acessórios", "Bloco B — sala 105", 2, False, "open", "Felipe Martins"),
            ("found", "Óculos de grau com armação preta", "Armação preta encontrada sobre uma carteira da sala.", "Acessórios", "Biblioteca — segundo andar", 3, False, "open", "Ana Clara Souza"),
            ("lost", "Garrafa lilás com adesivo de estrela", "Garrafa de metal com tampa branca.", "Acessórios", "Cantina — balcão", 4, False, "open", "Mateus Oliveira"),
            ("found", "Estojo vermelho", "Estojo de tecido com lápis e canetas.", "Material de estudo", "Bloco C — corredor", 5, False, "open", "Julia Ribeiro"),
            ("lost", "Fone com fio branco", "Fone branco guardado em uma caixinha transparente.", "Eletrônicos", "Auditório — fileira do meio", 6, True, "open", "Gabriel Ferreira"),
            ("found", "Chave com chaveiro de estrela", "Uma chave prateada com chaveiro pequeno azul.", "Chaves", "Recepção principal", 7, False, "open", "Isabela Costa"),
            ("lost", "Livro de Anatomia", "Livro de capa azul com marca-texto entre as páginas.", "Material de estudo", "Laboratório de saúde", 8, False, "open", "João Pedro Lima"),
            ("found", "Guarda-chuva preto", "Guarda-chuva dobrável deixado perto da porta.", "Acessórios", "Bloco A — entrada", 9, False, "open", "Larissa Almeida"),
            ("lost", "Carteira estudantil", "Cartão estudantil dentro de um porta-cartões transparente.", "Documentos", "Pátio central", 10, True, "open", "Enzo Carvalho"),
            ("found", "Carregador de notebook", "Fonte preta encontrada em uma tomada da sala.", "Eletrônicos", "Bloco D — sala 202", 11, False, "open", "Sofia Mendes"),
        ]
        _insert_demo_examples(db, additional_examples)
        db.execute("INSERT OR IGNORE INTO app_meta(key,value) VALUES('demo_seeded_v2','1')")

    contact_file = APP_DIR.parent / "data" / "local-demo-contacts.json"
    contact_source = contact_file.read_bytes() if contact_file.exists() else b""
    contact_signature = hashlib.sha256(contact_source).hexdigest()
    saved_signature = db.execute(
        "SELECT value FROM app_meta WHERE key = 'demo_contact_file_sha256'"
    ).fetchone()
    if not saved_signature or saved_signature["value"] != contact_signature:
        try:
            contact_entries = json.loads(contact_source.decode("utf-8")).get("items", []) if contact_source else []
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            contact_entries = []
        if not isinstance(contact_entries, list):
            contact_entries = []
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        active_demo_titles = []
        for contact in contact_entries:
            if not isinstance(contact, dict):
                continue
            title = contact.get("title", "")
            kind = contact.get("kind", "")
            category = contact.get("category", "")
            location = contact.get("location", "")
            name = contact.get("name", "")
            phone = re.sub(r"\D", "", str(contact.get("phone", "")))
            try:
                days_ago = max(0, int(contact.get("daysAgo", 0)))
            except (TypeError, ValueError):
                days_ago = 0
            if not all(isinstance(value, str) and value.strip() for value in (title, name, location)):
                continue
            if kind not in KINDS or category not in CATEGORIES or len(phone) not in {10, 11}:
                continue
            row = db.execute("SELECT id FROM listings WHERE is_demo=1 AND title=? LIMIT 1", (title,)).fetchone()
            description = "Cenário de demonstração: o item é fictício. O WhatsApp abre uma conversa com o contato real indicado."
            active_demo_titles.append(title)
            if row:
                db.execute("UPDATE listings SET description=?, contact_name=?, contact_email='', contact_phone=?, status='open' WHERE id=?", (description, name, phone, row["id"]))
            else:
                db.execute(
                    "INSERT INTO listings(kind,title,description,category,location,event_date,contact_name,contact_email,contact_phone,urgent,status,management_hash,created_at,updated_at,is_demo) "
                    "VALUES(?,?,?,?,?,?,?,?,?,0,'open',?,?,?,1)",
                    (kind, title, description, category, location, (date.today() - timedelta(days=days_ago)).isoformat(), name, "", phone, hashlib.sha256(secrets.token_bytes(32)).hexdigest(), now, now),
                )
        if active_demo_titles:
            placeholders = ",".join("?" for _ in active_demo_titles)
            db.execute(
                f"UPDATE listings SET status='resolved', contact_email='', contact_phone='' WHERE is_demo=1 AND title NOT IN ({placeholders})",
                active_demo_titles,
            )
        else:
            db.execute("UPDATE listings SET status='resolved', contact_email='', contact_phone='' WHERE is_demo=1")
        db.execute(
            "INSERT OR REPLACE INTO app_meta(key,value) VALUES('demo_contact_file_sha256',?)",
            (contact_signature,),
        )

    if not db.execute("SELECT 1 FROM app_meta WHERE key = 'deleted_latest_christian_listing_v1'").fetchone():
        # Keep the legacy marker so existing databases can run the corrective
        # migration below. Never infer which user post to delete from recency.
        db.execute("INSERT OR IGNORE INTO app_meta(key,value) VALUES('deleted_latest_christian_listing_v1','1')")

    # Correct the previous cleanup: it removed the newest Christian Lopes post
    # (the black backpack) instead of the older "Fone de Ouvido" post.
    # Restore the backpack from the remaining post's publisher/contact details,
    # then remove only the specifically named headphone post.
    if (
        db.execute("SELECT 1 FROM app_meta WHERE key = 'deleted_latest_christian_listing_v1'").fetchone()
        and not db.execute("SELECT 1 FROM app_meta WHERE key = 'corrected_christian_listing_cleanup_v2'").fetchone()
    ):
        old_headphones = db.execute(
            "SELECT * FROM listings WHERE is_demo=0 AND contact_name='Christian Lopes' AND title='Fone de Ouvido' "
            "ORDER BY created_at, id LIMIT 1"
        ).fetchone()
        backpack = db.execute(
            "SELECT id FROM listings WHERE is_demo=0 AND contact_name='Christian Lopes' AND title='Mochila preta' LIMIT 1"
        ).fetchone()
        if old_headphones and not backpack:
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            db.execute(
                "INSERT INTO listings(kind,title,description,category,location,event_date,contact_name,contact_email,contact_phone,urgent,status,management_hash,created_at,updated_at,is_demo) "
                "VALUES('lost','Mochila preta','Mochila preta publicada por Christian Lopes.','Acessórios','Local não informado',?,?,?,?,?,'open',?,?,?,0)",
                (date.today().isoformat(), old_headphones["contact_name"], old_headphones["contact_email"], old_headphones["contact_phone"], old_headphones["urgent"], hashlib.sha256(secrets.token_bytes(32)).hexdigest(), now, now),
            )
        db.execute(
            "DELETE FROM listings WHERE is_demo=0 AND contact_name='Christian Lopes' AND title='Fone de Ouvido'"
        )
        db.execute("INSERT OR IGNORE INTO app_meta(key,value) VALUES('corrected_christian_listing_cleanup_v2','1')")


def _insert_demo_examples(db, examples):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for kind, title, description, category, location, days_ago, urgent, status, publisher in examples:
        if db.execute("SELECT 1 FROM listings WHERE is_demo=1 AND title=? LIMIT 1", (title,)).fetchone():
            continue
        inaccessible_token_hash = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        db.execute(
            "INSERT INTO listings(kind,title,description,category,location,event_date,contact_name,contact_email,contact_phone,urgent,status,management_hash,created_at,updated_at,is_demo) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
            (kind, title, description, category, location, (date.today() - timedelta(days=days_ago)).isoformat(), publisher, "", "", int(urgent), status, inaccessible_token_hash, now, now),
        )


def record_to_dict(row):
    return {
        "id": row["id"], "kind": row["kind"], "title": row["title"],
        "description": row["description"], "category": row["category"],
        "location": row["location"], "eventDate": row["event_date"],
        "contactName": row["contact_name"], "contactEmail": row["contact_email"],
        "contactPhone": row["contact_phone"], "urgent": bool(row["urgent"]),
        "status": row["status"], "createdAt": row["created_at"],
        "updatedAt": row["updated_at"], "demo": bool(row["is_demo"]),
        "photoEditable": bool(row["is_demo"]) or (
            row["contact_name"] == "Christian Lopes" and row["title"] == "Mochila preta"
        ),
        "photoUrl": f"/api/v1/items/{row['id']}/photo" if row["photo_data"] else "",
    }


def _match_terms(value):
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )
    return [word for word in _WORD_PATTERN.findall(folded) if len(word) > 1 and word not in _SEARCH_STOPWORDS]


def _fold_search_text(value):
    return "".join(
        char for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )


def _local_match_details(original, candidate):
    title_terms = set(_match_terms(original["title"]))
    candidate_terms = set(_match_terms(candidate["title"]))
    description_terms = set(_match_terms(original["description"]))
    other_description = set(_match_terms(candidate["description"]))
    item_terms = title_terms | description_terms
    other_terms = candidate_terms | other_description
    overlap = len(item_terms & other_terms) / max(1, len(item_terms | other_terms))
    title_overlap = len(title_terms & candidate_terms) / max(1, len(title_terms | candidate_terms))
    category = _fold_search_text(original["category"]) == _fold_search_text(candidate["category"])
    location_terms = set(_match_terms(original["location"]))
    other_location_terms = set(_match_terms(candidate["location"]))
    location = len(location_terms & other_location_terms) / max(1, len(location_terms | other_location_terms))
    days_apart = abs((date.fromisoformat(original["event_date"]) - date.fromisoformat(candidate["event_date"])).days)
    date_score = max(0, 1 - days_apart / 31)
    score = round(100 * (0.42 * overlap + 0.25 * title_overlap + 0.15 * category + 0.12 * location + 0.06 * date_score))
    reasons = []
    if category:
        reasons.append(f"Mesma categoria: {original['category']}")
    shared_terms = sorted((title_terms | description_terms) & (candidate_terms | other_description))
    if shared_terms:
        reasons.append("Palavras em comum: " + ", ".join(shared_terms[:3]))
    if location_terms & other_location_terms:
        if _fold_search_text(original["location"]) == _fold_search_text(candidate["location"]):
            reasons.append(f"Mesmo local: {original['location']}")
        else:
            reasons.append("Local com termos em comum")
    if days_apart <= 7:
        reasons.append("Mesma data do relato" if days_apart == 0 else f"Datas com diferença de {days_apart} dias")
    return score, reasons


def _allow_match_request(client_address):
    now = datetime.now(timezone.utc).timestamp()
    with _match_rate_lock:
        recent = [stamp for stamp in _match_requests.get(client_address, []) if now - stamp < 60]
        if len(recent) >= 8:
            _match_requests[client_address] = recent
            return False
        recent.append(now)
        _match_requests[client_address] = recent
        if len(_match_requests) > 4096:
            _match_requests.clear()
        return True


def _rank_matches_with_gemini(api_key, original, candidates):
    rules = (
        "Compare um anúncio perdido/encontrado com anúncios candidatos do tipo oposto. "
        "Ordene pela chance de serem o mesmo objeto, considerando título, categoria, local e data. "
        "Não invente IDs e não afirme que o objeto foi identificado com certeza. Retorne somente JSON "
        "com matchIds, uma lista ordenada de no máximo 3 IDs presentes nos candidatos."
    )
    prompt = json.dumps({"anuncio": original, "candidatos": candidates}, ensure_ascii=False)
    body = {
        "systemInstruction": {"parts": [{"text": rules}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 500,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "matchIds": {"type": "ARRAY", "items": {"type": "INTEGER"}},
                },
                "required": ["matchIds"],
            },
        },
    }
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent".format(quote(GEMINI_MODEL, safe="-_."))
    request = Request(endpoint, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers={
        "Content-Type": "application/json", "x-goog-api-key": api_key,
    }, method="POST")
    try:
        with urlopen(request, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        # Do not include provider errors or request contents in the response/log.
        raise RuntimeError("O serviço de IA não respondeu. Tente novamente em instantes.") from error
    try:
        generated = result["candidates"][0]["content"]["parts"][0]["text"]
        answer = json.loads(generated)
        match_ids = answer.get("matchIds", [])
        if not isinstance(match_ids, list):
            raise ValueError
        allowed = {candidate["id"] for candidate in candidates}
        return [item_id for item_id in match_ids if isinstance(item_id, int) and not isinstance(item_id, bool) and item_id in allowed][:3]
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError("A IA retornou uma resposta inválida.") from error


class PortalHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        super().end_headers()

    def log_message(self, fmt, *args):
        # Keep submitted descriptions and contact details out of console logs.
        super().log_message(fmt, *args)

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ValidationError("A requisição precisa informar o tamanho do conteúdo.")
        try:
            length = int(raw_length)
        except ValueError:
            raise ValidationError("Tamanho de conteúdo inválido.") from None
        if length < 0:
            raise ValidationError("Tamanho de conteúdo inválido.")
        if length > MAX_BODY_BYTES:
            self.send_json(413, {"error": {"message": "A requisição excede o limite de 1 MB."}})
            return None
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValidationError("O corpo da requisição precisa ser um JSON válido.") from None

    def do_GET(self):
        parsed = urlsplit(self.path)
        photo_parts = parsed.path.strip("/").split("/")
        if len(photo_parts) == 5 and photo_parts[:3] == ["api", "v1", "items"] and photo_parts[4] == "photo" and photo_parts[3].isdigit():
            with db_session() as db:
                row = db.execute("SELECT photo_data FROM listings WHERE id = ?", (int(photo_parts[3]),)).fetchone()
            if not row or not row["photo_data"]:
                return self.send_json(404, {"error": {"message": "Foto não encontrada."}})
            mime, encoded = row["photo_data"].split(",", 1)
            content_type = mime.removeprefix("data:").removesuffix(";base64")
            body = base64.b64decode(encoded)
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return self.wfile.write(body)
        if parsed.path == "/api/v1/health":
            return self.send_json(200, {"status": "ok"})
        if parsed.path == "/api/v1/items":
            params = parse_qs(parsed.query)
            status = params.get("status", ["open"])[0]
            kind = params.get("kind", [""])[0]
            category = params.get("category", [""])[0]
            query = params.get("q", [""])[0].strip()[:100]
            if status not in {"open", "resolved", "all"}:
                return self.send_json(400, {"error": {"message": "Filtro de status inválido."}})
            if kind and kind not in KINDS:
                return self.send_json(400, {"error": {"message": "Filtro de tipo inválido."}})
            if category and category not in CATEGORIES:
                return self.send_json(400, {"error": {"message": "Filtro de categoria inválido."}})
            clauses, values = [], []
            if status != "all":
                clauses.append("status = ?")
                values.append("open" if status == "open" else "resolved")
            if kind:
                clauses.append("kind = ?")
                values.append(kind)
            if category:
                clauses.append("category = ?")
                values.append(category)
            if query:
                clauses.append("(title LIKE ? OR description LIKE ? OR location LIKE ? OR category LIKE ?)")
                pattern = f"%{query}%"
                values.extend([pattern] * 4)
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            with db_session() as db:
                rows = db.execute(
                    f"SELECT * FROM listings{where} ORDER BY (status = 'open') DESC, urgent DESC, created_at DESC LIMIT 200",
                    values,
                ).fetchall()
                totals = db.execute(
                    "SELECT COUNT(*) AS total, SUM(CASE WHEN kind='lost' AND status='open' THEN 1 ELSE 0 END) AS lost, "
                    "SUM(CASE WHEN kind='found' AND status='open' THEN 1 ELSE 0 END) AS found, "
                    "SUM(CASE WHEN status='resolved' THEN 1 ELSE 0 END) AS resolved FROM listings"
                ).fetchone()
            stats = {key: int(totals[key] or 0) for key in ("total", "lost", "found", "resolved")}
            return self.send_json(200, {"items": [record_to_dict(row) for row in rows], "stats": stats})
        if parsed.path == "/openapi.yaml":
            contract = APP_DIR.parent / "specs" / "001-achados-e-perdidos" / "contracts" / "openapi.yaml"
            if contract.exists():
                body = contract.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/yaml; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                return self.wfile.write(body)
            return self.send_json(404, {"error": {"message": "Contrato OpenAPI não encontrado."}})
        if parsed.path.startswith("/api/"):
            return self.send_json(404, {"error": {"message": "Rota da API não encontrada."}})
        return super().do_GET()

    def do_POST(self):
        path = urlsplit(self.path).path
        match_parts = path.strip("/").split("/")
        if len(match_parts) == 5 and match_parts[:3] == ["api", "v1", "items"] and match_parts[3].isdigit() and match_parts[4] == "photo":
            # Demo images, plus the restored Christian backpack card, are editable locally only.
            if self.client_address[0] not in {"127.0.0.1", "::1"}:
                return self.send_json(403, {"error": {"message": "A edição de fotos demonstrativas só pode ser feita localmente."}})
            try:
                raw = self.read_json()
                if raw is None:
                    return
                if not isinstance(raw, dict):
                    raise ValidationError("Envie a foto em formato JSON.")
                photo = validate_photo(raw.get("photo"))
                if not photo:
                    raise ValidationError("Escolha uma foto antes de enviar.")
            except ValidationError as error:
                return self.send_json(422, {"error": {"message": str(error)}})
            with db_session() as db:
                row = db.execute("SELECT is_demo, contact_name, title FROM listings WHERE id = ?", (int(match_parts[3]),)).fetchone()
                if not row:
                    return self.send_json(404, {"error": {"message": "Anúncio não encontrado."}})
                photo_editable = bool(row["is_demo"]) or (
                    row["contact_name"] == "Christian Lopes" and row["title"] == "Mochila preta"
                )
                if not photo_editable:
                    return self.send_json(403, {"error": {"message": "A edição de foto está disponível somente localmente nos cartões autorizados."}})
                db.execute("UPDATE listings SET photo_data = ?, updated_at = ? WHERE id = ?", (photo, datetime.now(timezone.utc).isoformat(timespec="seconds"), int(match_parts[3])))
            return self.send_json(200, {"photoUrl": f"/api/v1/items/{match_parts[3]}/photo"})
        if len(match_parts) == 5 and match_parts[:3] == ["api", "v1", "items"] and match_parts[3].isdigit() and match_parts[4] == "matches":
            return self.handle_matches(int(match_parts[3]))
        if path != "/api/v1/items":
            return self.send_json(404, {"error": {"message": "Rota da API não encontrada."}})
        try:
            raw = self.read_json()
            if raw is None:
                return
            item = validate_listing(raw)
        except ValidationError as error:
            return self.send_json(422, {"error": {"message": str(error)}})
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        management_token = secrets.token_urlsafe(24)
        token_hash = hashlib.sha256(management_token.encode()).hexdigest()
        with db_session() as db:
            cursor = db.execute(
                "INSERT INTO listings(kind,title,description,category,location,event_date,contact_name,contact_email,contact_phone,urgent,management_hash,created_at,updated_at,photo_data) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (item["kind"], item["title"], item["description"], item["category"], item["location"],
                 item["eventDate"], item["contactName"], item["contactEmail"], item["contactPhone"],
                 int(item["urgent"]), token_hash, now, now, item["photo"]),
            )
            row = db.execute("SELECT * FROM listings WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self.send_json(201, {"item": record_to_dict(row), "managementToken": management_token})

    def handle_matches(self, item_id):
        if not _allow_match_request(self.client_address[0]):
            return self.send_json(429, {"error": {"message": "Muitas análises em pouco tempo. Aguarde um minuto e tente novamente."}})
        with db_session() as db:
            original = db.execute("SELECT * FROM listings WHERE id = ? AND status = 'open'", (item_id,)).fetchone()
            if not original:
                return self.send_json(404, {"error": {"message": "Anúncio aberto não encontrado."}})
            opposite_kind = "found" if original["kind"] == "lost" else "lost"
            rows = db.execute(
                "SELECT * FROM listings WHERE status='open' AND kind=? AND id<>? ORDER BY created_at DESC LIMIT 200",
                (opposite_kind, item_id),
            ).fetchall()
            ranked = sorted(
                ((_local_match_details(original, row)[0], row) for row in rows),
                key=lambda pair: (-pair[0], pair[1]["created_at"]),
            )
            ranked = [(score, row) for score, row in ranked if score >= 8][:20]
            original_for_ai = {
                "id": original["id"], "kind": original["kind"], "title": original["title"],
                "category": original["category"], "location": original["location"],
                "eventDate": original["event_date"],
            }
            candidates = [
                {"id": row["id"], "kind": row["kind"], "title": row["title"],
                 "category": row["category"], "location": row["location"], "eventDate": row["event_date"]}
                for _, row in ranked
            ]
            rows_by_id = {row["id"]: row for _, row in ranked}
            scores_by_id = {row["id"]: score for score, row in ranked}
            reasons_by_id = {row["id"]: _local_match_details(original, row)[1] for _, row in ranked}

        method = "similaridade"
        ranked_ids = [candidate["id"] for candidate in candidates[:3]]
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if api_key and candidates:
            try:
                ai_ids = _rank_matches_with_gemini(api_key, original_for_ai, candidates)
                if ai_ids:
                    ranked_ids = ai_ids
                    method = "gemini"
            except RuntimeError:
                # The local matcher remains available if the external service is down or misconfigured.
                pass
        matches = []
        for candidate_id in ranked_ids[:3]:
            row = rows_by_id.get(candidate_id)
            if row:
                matches.append({
                    "id": row["id"], "kind": row["kind"], "title": row["title"],
                    "category": row["category"], "location": row["location"],
                    "eventDate": row["event_date"], "demo": bool(row["is_demo"]),
                    "score": scores_by_id[candidate_id], "reasons": reasons_by_id[candidate_id],
                })
        return self.send_json(200, {"matches": matches, "method": method})

    def do_PATCH(self):
        item_id = self._item_id()
        if item_id is None:
            return self.send_json(404, {"error": {"message": "Anúncio não encontrado."}})
        try:
            payload = self.read_json()
            if payload is None:
                return
        except ValidationError as error:
            return self.send_json(400, {"error": {"message": str(error)}})
        if not isinstance(payload, dict) or payload.get("status") not in {"recovered", "returned"}:
            return self.send_json(422, {"error": {"message": "Informe um status de resolução válido."}})
        token = payload.get("managementToken", "")
        token_hash = hashlib.sha256(token.encode()).hexdigest() if isinstance(token, str) else ""
        with db_session() as db:
            row = db.execute("SELECT * FROM listings WHERE id = ?", (item_id,)).fetchone()
            if not row:
                return self.send_json(404, {"error": {"message": "Anúncio não encontrado."}})
            expected = "recovered" if row["kind"] == "lost" else "returned"
            if payload["status"] != expected:
                return self.send_json(422, {"error": {"message": "Esse status não corresponde ao tipo do anúncio."}})
            if not secrets.compare_digest(row["management_hash"], token_hash):
                return self.send_json(403, {"error": {"message": "Só quem publicou o anúncio pode alterar o status."}})
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            db.execute("UPDATE listings SET status='resolved', updated_at=? WHERE id=?", (now, item_id))
            updated = db.execute("SELECT * FROM listings WHERE id = ?", (item_id,)).fetchone()
        return self.send_json(200, {"item": record_to_dict(updated)})

    def do_DELETE(self):
        item_id = self._item_id()
        if item_id is None:
            return self.send_json(404, {"error": {"message": "Anúncio não encontrado."}})
        try:
            payload = self.read_json()
            if payload is None:
                return
        except ValidationError as error:
            return self.send_json(400, {"error": {"message": str(error)}})
        token = payload.get("managementToken", "") if isinstance(payload, dict) else ""
        token_hash = hashlib.sha256(token.encode()).hexdigest() if isinstance(token, str) else ""
        with db_session() as db:
            row = db.execute("SELECT management_hash FROM listings WHERE id = ?", (item_id,)).fetchone()
            if not row:
                return self.send_json(404, {"error": {"message": "Anúncio não encontrado."}})
            if not secrets.compare_digest(row["management_hash"], token_hash):
                return self.send_json(403, {"error": {"message": "Só quem publicou o anúncio pode removê-lo."}})
            db.execute("DELETE FROM listings WHERE id = ?", (item_id,))
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _item_id(self):
        parts = urlsplit(self.path).path.strip("/").split("/")
        if len(parts) == 4 and parts[:3] == ["api", "v1", "items"] and parts[3].isdigit():
            return int(parts[3])
        return None


def main():
    parser = argparse.ArgumentParser(description="Servidor local do CESMAC Achados & Perdidos")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = parser.parse_args()
    with ThreadingHTTPServer((args.host, args.port), PortalHandler) as server:
        display_host = "127.0.0.1" if args.host in {"0.0.0.0", "::"} else args.host
        base_url = "http://{}:{}".format(display_host, args.port)
        print("CESMAC Achados & Perdidos disponível em {}".format(base_url))
        print("Contrato OpenAPI em {}/openapi.yaml".format(base_url))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado.")


if __name__ == "__main__":
    main()


