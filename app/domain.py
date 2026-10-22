"""Validation and small domain rules for the CESMAC lost-and-found portal."""

from __future__ import annotations

import re
from datetime import date


CATEGORIES = {
    "Acessórios", "Documentos", "Eletrônicos", "Material de estudo",
    "Roupas e acessórios", "Chaves", "Outros",
}
KINDS = {"lost", "found"}
STATUSES = {"open", "recovered", "returned"}
MAX_TEXT = 1500
MAX_PHOTO_DATA = 700_000


class ValidationError(ValueError):
    pass


def validate_photo(value: object) -> str:
    """Validate the compact data URL used by listing photo uploads."""
    if not isinstance(value, str) or len(value) > MAX_PHOTO_DATA:
        raise ValidationError("A foto precisa ter no máximo 700 KB após a compactação.")
    if value and not re.fullmatch(r"data:image/(?:jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}", value):
        raise ValidationError("Envie uma foto JPG, PNG ou WebP válida.")
    return value


def clean_text(value: object, field: str, maximum: int, *, required: bool = True) -> str:
    if not isinstance(value, str):
        if required:
            raise ValidationError(f"Informe {field}.")
        return ""
    result = re.sub(r"\s+", " ", value).strip()
    if required and not result:
        raise ValidationError(f"Informe {field}.")
    if len(result) > maximum:
        raise ValidationError(f"{field.capitalize()} deve ter no máximo {maximum} caracteres.")
    return result


def validate_listing(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValidationError("Envie os dados do anúncio em formato JSON.")
    kind = data.get("kind")
    if kind not in KINDS:
        raise ValidationError("Escolha se o item foi perdido ou encontrado.")

    category = clean_text(data.get("category"), "uma categoria", 40)
    if category not in CATEGORIES:
        raise ValidationError("Escolha uma categoria válida.")

    event_date = data.get("eventDate")
    try:
        parsed_date = date.fromisoformat(event_date)
        if parsed_date > date.today():
            raise ValueError
    except (TypeError, ValueError):
        raise ValidationError("Informe uma data válida, que não seja futura.") from None

    email = clean_text(data.get("contactEmail"), "um e-mail ou telefone", 254, required=False)
    phone = clean_text(data.get("contactPhone"), "um e-mail ou telefone", 30, required=False)
    if not email and not phone:
        raise ValidationError("Informe pelo menos um e-mail ou telefone para contato.")
    if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValidationError("Informe um endereço de e-mail válido.")

    urgent = data.get("urgent", False)
    if not isinstance(urgent, bool):
        raise ValidationError("O campo de urgência deve ser verdadeiro ou falso.")

    photo = validate_photo(data.get("photo", ""))

    return {
        "kind": kind,
        "title": clean_text(data.get("title"), "o nome do item", 100),
        "description": clean_text(data.get("description"), "uma descrição", MAX_TEXT),
        "category": category,
        "location": clean_text(data.get("location"), "o local", 120),
        "eventDate": parsed_date.isoformat(),
        "contactName": clean_text(data.get("contactName"), "seu nome", 80),
        "contactEmail": email,
        "contactPhone": phone,
        "urgent": urgent,
        "photo": photo,
    }

