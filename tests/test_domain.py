"""Unit tests for the listing rules."""

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

from domain import ValidationError, validate_listing  # noqa: E402


def valid_listing(**overrides):
    listing = {
        "kind": "lost",
        "title": "Chaveiro azul",
        "description": "Chaveiro encontrado perto da biblioteca.",
        "category": "Chaves",
        "location": "Biblioteca",
        "eventDate": date.today().isoformat(),
        "contactName": "Pessoa Fictícia",
        "contactEmail": "contato@example.invalid",
        "contactPhone": "",
        "urgent": False,
        "photo": "",
    }
    listing.update(overrides)
    return listing


class ListingValidationTests(unittest.TestCase):
    def test_accepts_lost_and_found_and_normalizes_date(self):
        for kind in ("lost", "found"):
            with self.subTest(kind=kind):
                result = validate_listing(valid_listing(kind=kind))
                self.assertEqual(result["kind"], kind)
                self.assertEqual(result["eventDate"], date.today().isoformat())

    def test_requires_supported_kind_category_and_contact(self):
        invalid_cases = (
            {"kind": "unknown"},
            {"category": "Categoria desconhecida"},
            {"contactEmail": "", "contactPhone": ""},
            {"title": "   "},
            {"description": "   "},
            {"location": "   "},
            {"contactName": "   "},
        )
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides), self.assertRaises(ValidationError):
                validate_listing(valid_listing(**overrides))

    def test_rejects_future_date(self):
        future = (date.today() + timedelta(days=1)).isoformat()
        with self.assertRaises(ValidationError):
            validate_listing(valid_listing(eventDate=future))

    def test_accepts_phone_at_30_characters_and_rejects_31(self):
        accepted = validate_listing(valid_listing(contactEmail="", contactPhone="1" * 30))
        self.assertEqual(len(accepted["contactPhone"]), 30)
        with self.assertRaises(ValidationError):
            validate_listing(valid_listing(contactEmail="", contactPhone="1" * 31))

    def test_enforces_text_field_limits(self):
        invalid_cases = (
            {"title": "x" * 101},
            {"description": "x" * 1501},
            {"category": "x" * 41},
            {"location": "x" * 121},
            {"contactName": "x" * 81},
            {"contactEmail": "a" * 255},
            {"contactPhone": "1" * 31},
        )
        for overrides in invalid_cases:
            with self.subTest(overrides=list(overrides)):
                with self.assertRaises(ValidationError):
                    validate_listing(valid_listing(**overrides))

    def test_rejects_invalid_email(self):
        with self.assertRaises(ValidationError):
            validate_listing(valid_listing(contactEmail="email-invalido"))

    def test_validates_photo_format_and_size(self):
        result = validate_listing(valid_listing(photo="data:image/png;base64,aGVsbG8="))
        self.assertTrue(result["photo"].startswith("data:image/png;base64,"))
        with self.assertRaises(ValidationError):
            validate_listing(valid_listing(photo="data:image/svg+xml;base64,PHN2Zz4="))
        with self.assertRaises(ValidationError):
            validate_listing(valid_listing(photo="x" * 700_001))

    def test_urgent_must_be_boolean(self):
        with self.assertRaises(ValidationError):
            validate_listing(valid_listing(urgent="yes"))


if __name__ == "__main__":
    unittest.main()
