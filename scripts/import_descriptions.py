"""Import exercise descriptions from descriptions.json into the exercise database.

Reads a list of description objects (keys: id, summary, setup, execution (list of steps),
cues (list), common_mistakes (list), easier_variant, harder_variant, breathing),
validates each entry, and writes the imported descriptions with
description_status="needs_review" to an output JSON file.

An entry whose description_status is already "reviewed" is never overwritten.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.exercises.data import list_exercises

# Dozwolone znaki: ASCII 32-126 plus polskie litery i stopień (taki sam zbiór co w teście
# app/plan routes no-foreign-chars).
_ALLOWED_EXTRA = {
    176, 260, 261, 262, 263, 280, 281, 321, 322, 323, 324, 243, 346, 347, 377, 378, 379, 380,
}

_TEXT_FIELDS = ["summary", "setup", "easier_variant", "harder_variant", "breathing"]
_LIST_FIELDS = ["execution", "cues", "common_mistakes"]
_REQUIRED_FIELDS = [
    "id", "summary", "setup", "execution", "cues", "common_mistakes",
    "easier_variant", "harder_variant", "breathing",
]


def _has_pl_or_en_only(text: str) -> bool:
    for ch in text:
        code = ord(ch)
        if 32 <= code <= 126:
            continue
        if code in _ALLOWED_EXTRA:
            continue
        return False
    return True


def _nonempty(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, tuple)):
        return len(value) > 0
    return bool(value)


def load_descriptions(path: str) -> list:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("descriptions.json must contain a list of objects")
    return data


def validate_entry(entry: dict, available_ids: set) -> list:
    """Zwraca listę komunikatów o błędach walidacji dla jednego wpisu (pusta = poprawny)."""
    errors: list[str] = []
    eid = entry.get("id")
    if not eid or eid not in available_ids:
        errors.append(f"id {eid!r}: nie istnieje w bazie ćwiczeń")
        return errors

    if entry.get("description_status") == "reviewed":
        errors.append(f"{eid}: description_status to reviewed - nie nadpisuję")
        return errors

    for field in _REQUIRED_FIELDS:
        if field not in entry or not _nonempty(entry[field]):
            errors.append(f"{eid}: pole {field!r} jest puste")

    if "execution" in entry and isinstance(entry["execution"], list):
        steps = entry["execution"]
        if len(steps) < 3 or len(steps) > 8:
            errors.append(f"{eid}: execution ma {len(steps)} kroków (wymagane 3-8)")
        for i, step in enumerate(steps):
            if not isinstance(step, str) or not step.strip():
                errors.append(f"{eid}: execution[{i}] jest pusty")

    for fld, mn, mx in (("cues", 2, 4), ("common_mistakes", 2, 4)):
        if fld in entry and isinstance(entry[fld], list):
            n = len(entry[fld])
            if n < mn or n > mx:
                errors.append(f"{eid}: {fld} ma {n} elementów (wymagane {mn}-{mx})")

    for field in _TEXT_FIELDS:
        if field in entry and isinstance(entry[field], str):
            if not _has_pl_or_en_only(entry[field]):
                errors.append(f"{eid}: pole {field!r} zawiera niedozwolone znaki")

    for fld in _LIST_FIELDS:
        if fld in entry and isinstance(entry[fld], list):
            for i, item in enumerate(entry[fld]):
                if isinstance(item, str) and not _has_pl_or_en_only(item):
                    errors.append(f"{eid}: {fld}[{i}] zawiera niedozwolone znaki")

    return errors


def import_descriptions(descriptions_path=None, descriptions=None, available_ids=None,
                        output_path=None):
    """Importuj opisy. Zwraca (imported, errors)."""
    if descriptions is None:
        descriptions = load_descriptions(descriptions_path)
    if available_ids is None:
        available_ids = {ex.id for ex in list_exercises()}

    imported: list[dict] = []
    errors: list[str] = []
    skipped_reviewed: list[str] = []

    for entry in descriptions:
        errs = validate_entry(entry, available_ids)
        if errs:
            # rozdziel błędy walidacji od pominiętych reviewed
            for e in errs:
                if "nie nadpisuję" in e:
                    skipped_reviewed.append(entry.get("id", "?"))
                else:
                    errors.append(e)
            continue
        eid = entry["id"]
        imported.append({
            "id": eid,
            "description": {
                "summary": entry["summary"],
                "setup": entry["setup"],
                "execution": entry["execution"],
                "cues": entry["cues"],
                "common_mistakes": entry["common_mistakes"],
                "easier_variant": entry["easier_variant"],
                "harder_variant": entry["harder_variant"],
                "breathing": entry["breathing"],
            },
            "description_status": "needs_review",
        })

    if output_path:
        Path(output_path).write_text(
            json.dumps(imported, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return imported, errors, skipped_reviewed


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    descriptions_path = argv[0] if len(argv) > 0 else "descriptions.json"
    output_path = argv[1] if len(argv) > 1 else "descriptions.imported.json"
    descriptions = load_descriptions(descriptions_path)
    imported, errors, skipped = import_descriptions(
        descriptions=descriptions, output_path=output_path
    )
    print(f"Zaimportowano: {len(imported)}, pominięte (reviewed): {len(skipped)}, błędy: {len(errors)}")
    for e in errors:
        print("  -", e)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
