"""Pakiet ćwiczeń — jednolite źródło danych dla systemu EVOLVE."""

from __future__ import annotations

from app.exercises.data import (
    CONTRAINDICATIONS,
    DESCRIPTION_STATUSES,
    EQUIPMENT,
    EXERCISE_TYPES,
    EXERCISES,
    LEVELS,
    MOVEMENT_PATTERNS,
    MUSCLE_GROUPS,
    Exercise,
    ExerciseDescription,
    get_exercise,
    list_exercises,
)

__all__ = [
    "MUSCLE_GROUPS",
    "EQUIPMENT",
    "MOVEMENT_PATTERNS",
    "LEVELS",
    "EXERCISE_TYPES",
    "CONTRAINDICATIONS",
    "DESCRIPTION_STATUSES",
    "Exercise",
    "ExerciseDescription",
    "EXERCISES",
    "get_exercise",
    "list_exercises",
]
