"""Regresja generatora planu — persona 2 (hantle+ławka) i 7 (masa własna).

Uruchamia realny kod generatora (build_deterministic_plan) i weryfikuje,
ze filtrowanie sprzedzatu respektuje deklarowany sprzedz uzytkownika.
"""
from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, ".")

import pytest

from app.plan.deterministic import build_deterministic_plan


def _first_int(value):
    m = re.search(r"\d+", str(value or ""))
    return int(m.group()) if m else None


class _MockUser:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self._lists = kw.get("_lists", {})
        self._dicts = kw.get("_dicts", {})

    def get_list(self, field):
        if field in self._lists:
            return self._lists[field]
        attr = getattr(self, field, None)
        if attr is None:
            return []
        if isinstance(attr, list):
            return attr
        try:
            return json.loads(attr)
        except Exception:
            return []

    def get_dict(self, field):
        if field in self._dicts:
            return self._dicts[field]
        attr = getattr(self, field, None)
        if attr is None:
            return {}
        if isinstance(attr, dict):
            return attr
        try:
            return json.loads(attr)
        except Exception:
            return {}


def _make_user(
    goal,
    frequency,
    equipment_preset,
    training_focus=None,
    improvement_areas=None,
    available_equipment=None,
    health_limitations="",
    injuries="",
    diet="zrownowazona",
    calories_target=2500,
    meals_per_day=4,
    availability_days=None,
    session_duration=60,
):
    lists = {
        "training_focus_json": training_focus or [],
        "improvement_areas_json": improvement_areas or [],
        "available_equipment_json": (
            available_equipment if available_equipment is not None else []
        ),
        "avoid_exercises_json": [],
        "preferred_foods_json": [],
        "avoid_foods_json": [],
        "training_locations_json": [],
        "sport_training_days_json": [],
    }
    dicts = {
        "training_availability_json": {
            "days": availability_days or [],
            "windows": {},
            "session_duration_minutes": session_duration,
        }
        if availability_days is not None
        else {},
        "sport_training_schedule_json": {},
    }
    return _MockUser(
        goal=goal,
        frequency=frequency,
        diet=diet,
        calories_target=calories_target,
        meals_per_day=meals_per_day,
        equipment=equipment_preset,
        health_limitations=health_limitations,
        injuries=injuries,
        sport_focus="",
        sport_specialization="",
        basketball_position=None,
        _lists=lists,
        _dicts=dicts,
    )


def _make_assessment(level, sessions_per_week, hours_per_week=None, recovery=None):
    class _A:
        pass

    a = _A()
    a.training_level = level
    a.sessions_per_week = sessions_per_week
    a.availability_hours_per_week = hours_per_week
    a.recovery_score = recovery
    return a


_PERSONA_2 = (
    _make_user(
        "ogolna sprawnosc",
        "2 razy w tygodniu",
        "dumbbells",
        available_equipment=["hantle", "lawka"],
    ),
    _make_assessment("poczatkujacy", 2, 3.0, 7),
)

_PERSONA_7 = (
    _make_user(
        "ogolna sprawnosc",
        "3 razy w tygodniu",
        "bodyweight",
        available_equipment=[],
    ),
    _make_assessment("sredniozaawansowany", 3, 4.0, 7),
)


def _plan_names(plan):
    names = []
    for day in plan.get("days", []):
        for ex in (day.get("workout") or {}).get("exercises", []):
            names.append(ex.get("name"))
    return names


def test_persona_2_dumbbells_bench_no_barbell_or_pullup():
    user, assessment = _PERSONA_2
    plan = build_deterministic_plan(user, assessment, [])
    names = _plan_names(plan)
    joined = " | ".join(names)
    assert "Martwy ciag konwencjonalny" not in joined, joined
    assert "Martwy ciag" not in joined, joined
    assert "Podciaganie" not in joined, joined
    assert "Podciagniecie" not in joined, joined


def test_persona_7_bodyweight_only_equipment():
    user, assessment = _PERSONA_7
    plan = build_deterministic_plan(user, assessment, [])
    names = _plan_names(plan)
    # exercise_limit dla durchschnitt poziomu i recovery 7 -> 4 cwiczen
    # Każde wybrane cwiczenie powinno wymagac wyłącznie bodyweight.
    for name in names:
        lowered = str(name or "").lower()
        assert "sztang" not in lowered, name
        assert "hantl" not in lowered, name
        assert "lawk" not in lowered, name
        assert "drazek" not in lowered or "podciaganie" in lowered, name


def test_deterministic_stability_persona_2_and_7():
    for user, assessment in (_PERSONA_2, _PERSONA_7):
        p1 = build_deterministic_plan(user, assessment, [])
        p2 = build_deterministic_plan(user, assessment, [])
        assert json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True)
