"""
llm_service.py — Integrasi Gemini untuk SmartRecipe
===================================================
LLM dipakai sebagai lapisan bahasa:
1. Mengekstrak filter pencarian dari pertanyaan natural user.
2. Menyusun narasi dari hasil RDF/SPARQL yang sudah terstruktur.

Sumber kebenaran rekomendasi tetap berasal dari Fuseki/SPARQL.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests

from sparql_queries import CATEGORY_LIST, CONDITION_MAP


def _load_env_file() -> None:
    """Load .env lokal tanpa dependency tambahan."""
    env_paths = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]

    for env_path in env_paths:
        if not env_path.exists():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


_load_env_file()

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class LLMConfigurationError(RuntimeError):
    """Raised saat konfigurasi Gemini belum tersedia."""


class LLMServiceError(RuntimeError):
    """Raised saat request Gemini gagal atau respons tidak valid."""


def _api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise LLMConfigurationError(
            "GEMINI_API_KEY belum diset. Set environment variable ini sebelum menjalankan Flask."
        )
    return key


def _extract_text(response_json: dict[str, Any]) -> str:
    candidates = response_json.get("candidates", [])
    if not candidates:
        raise LLMServiceError("Gemini tidak mengembalikan kandidat jawaban.")

    parts = candidates[0].get("content", {}).get("parts", [])
    text_chunks = [part.get("text", "") for part in parts if part.get("text")]
    text = "".join(text_chunks).strip()
    if not text:
        raise LLMServiceError("Gemini mengembalikan respons kosong.")
    return text


def _json_response(system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    url = GEMINI_ENDPOINT.format(model=model)

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": schema,
        },
    }

    try:
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": _api_key(),
            },
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        return json.loads(_extract_text(response.json()))
    except LLMConfigurationError:
        raise
    except requests.HTTPError as exc:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except Exception:
            detail = response.text[:300]
        raise LLMServiceError(f"Request Gemini gagal: {detail or exc}") from exc
    except json.JSONDecodeError as exc:
        raise LLMServiceError("Respons Gemini bukan JSON valid.") from exc
    except requests.RequestException as exc:
        raise LLMServiceError(f"Gagal menghubungi Gemini API: {exc}") from exc


def extract_recipe_filters(user_message: str) -> dict[str, Any]:
    """Ubah pertanyaan user menjadi filter yang aman untuk search_recipes()."""
    condition_values = ["none", *CONDITION_MAP.keys()]
    category_values = ["none", *CATEGORY_LIST]

    schema = {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "Kata kunci nama resep. Kosongkan jika user hanya menyebut kategori.",
            },
            "condition": {
                "type": "string",
                "enum": condition_values,
                "description": "Kondisi kesehatan yang cocok dengan daftar enum, atau none jika tidak disebutkan.",
            },
            "category": {
                "type": "string",
                "enum": category_values,
                "description": "Kategori bahan utama yang cocok dengan daftar enum, atau none jika tidak disebutkan.",
            },
            "interpreted_question": {
                "type": "string",
                "description": "Ringkasan singkat maksud pertanyaan user dalam bahasa Indonesia.",
            },
        },
        "required": ["keyword", "condition", "category", "interpreted_question"],
    }

    system_prompt = (
        "Kamu adalah parser pencarian untuk aplikasi resep sehat berbasis ontology. "
        "Tugasmu hanya mengekstrak filter dari pertanyaan user. "
        "Gunakan nilai none jika condition atau category tidak disebutkan. "
        "Jangan memberi rekomendasi resep dan jangan menambah kategori/kondisi di luar enum."
    )
    user_prompt = (
        f"Kategori valid: {', '.join(CATEGORY_LIST)}\n"
        f"Kondisi valid: {', '.join(CONDITION_MAP.keys())}\n"
        f"Pertanyaan user: {user_message}"
    )

    parsed = _json_response(system_prompt, user_prompt, schema)
    condition = parsed.get("condition", "")
    category = parsed.get("category", "")
    return {
        "keyword": parsed.get("keyword", "").strip(),
        "condition": "" if condition == "none" else condition,
        "category": "" if category == "none" else category,
        "interpreted_question": parsed.get("interpreted_question", "").strip(),
    }


def generate_recipe_narrative(
    user_message: str,
    filters: dict[str, Any],
    recipes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Buat narasi berdasarkan hasil query, tanpa mengarang data baru."""
    compact_recipes = [
        {
            "namaMenu": recipe.get("namaMenu", ""),
            "kategori": recipe.get("kategori", ""),
            "loves": recipe.get("loves", "0"),
        }
        for recipe in recipes[:8]
    ]

    schema = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Narasi singkat 2-4 kalimat dalam bahasa Indonesia.",
            },
            "notes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Catatan singkat. Maksimal 3 item.",
            },
        },
        "required": ["summary", "notes"],
    }

    system_prompt = (
        "Kamu adalah asisten SmartRecipe. Jelaskan hasil pencarian resep secara natural, "
        "tetapi hanya berdasarkan data JSON yang diberikan. Jangan mengarang nama resep, "
        "bahan, manfaat medis, atau klaim kesehatan baru. Tegaskan bahwa hasil berasal "
        "dari filter ontology/SPARQL dan bukan pengganti saran tenaga kesehatan."
    )
    user_prompt = json.dumps(
        {
            "pertanyaan_user": user_message,
            "filter_dipakai": filters,
            "jumlah_hasil": len(recipes),
            "contoh_hasil_teratas": compact_recipes,
        },
        ensure_ascii=False,
    )

    narrative = _json_response(system_prompt, user_prompt, schema)
    notes = narrative.get("notes", [])
    if not isinstance(notes, list):
        notes = []
    return {
        "summary": narrative.get("summary", "").strip(),
        "notes": [str(note).strip() for note in notes[:3] if str(note).strip()],
    }
