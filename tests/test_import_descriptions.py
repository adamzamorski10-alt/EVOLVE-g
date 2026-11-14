"""Testy skryptu scripts/import_descriptions.py na przykładzie dwóch ćwiczeń."""

from types import SimpleNamespace

import pytest

import scripts.import_descriptions as im


VALID_ID = "barbell_bench_press"
INVALID_ID = "bird_dog"  # istnieje w bazie, ale użyjemy go z błędnym opisem


def _available_ids():
    return {VALID_ID, INVALID_ID}


def _valid_entry(exercise_id):
    return {
        "id": exercise_id,
        "summary": "Krótki opis ćwiczenia testowego.",
        "setup": "Przygotuj sprzęt i pozycję wyjściową.",
        "execution": [
            "Chwyć sprzęt i ustabilizuj tułów.",
            "Wykonaj ruch kontrolowanie w pełnym zakresie.",
            "Wróć do pozycji wyjściowej napinając mięsień.",
        ],
        "cues": ["Trzymaj plecy proste", "Wyczerp wydech w wysiłku"],
        "common_mistakes": ["Zaokrąglenie pleców", "Zbyt szybki tempo"],
        "easier_variant": "pushups_knee",
        "harder_variant": "pushups_feet_elevated",
        "breathing": "Wdech przy opadaniu, wydech przy wysiłku.",
    }


def test_import_valid_entry_sets_needs_review(monkeypatch):
    entry = _valid_entry(VALID_ID)
    imported, errors, skipped = im.import_descriptions(
        descriptions=[entry], available_ids=_available_ids()
    )
    assert errors == []
    assert skipped == []
    assert len(imported) == 1
    assert imported[0]["id"] == VALID_ID
    assert imported[0]["description_status"] == "needs_review"
    assert imported[0]["description"]["summary"] == entry["summary"]
    assert len(imported[0]["description"]["execution"]) == 3


def test_import_invalid_entry_rejected(monkeypatch):
    entry = _valid_entry(INVALID_ID)
    entry["execution"] = ["krok 1", "krok 2"]  # za mało kroków (wymagane 3-8)
    imported, errors, skipped = im.import_descriptions(
        descriptions=[entry], available_ids=_available_ids()
    )
    assert imported == []
    assert skipped == []
    assert len(errors) == 1
    assert "execution ma 2 kroków" in errors[0]


def test_import_unknown_id_rejected():
    entry = _valid_entry("nie_istnieje")
    imported, errors, skipped = im.import_descriptions(
        descriptions=[entry], available_ids=_available_ids()
    )
    assert imported == []
    assert skipped == []
    assert any("nie istnieje w bazie ćwiczeń" in e for e in errors)


def test_import_reviewed_not_overwritten():
    entry = _valid_entry(VALID_ID)
    entry["description_status"] = "reviewed"
    imported, errors, skipped = im.import_descriptions(
        descriptions=[entry], available_ids=_available_ids()
    )
    assert imported == []
    assert errors == []
    assert skipped == [VALID_ID]


def test_validate_unknown_id():
    errors = im.validate_entry({"id": "brak"}, _available_ids())
    assert any("nie istnieje w bazie ćwiczeń" in e for e in errors)
