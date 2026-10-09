"""
FitAI Schemas — Pydantic request/response models for FastAPI
"""

import re  # kept for potential future validators
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.config import JWT_EXPIRE_MINUTES


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    # Dane profilu — opcjonalne, można uzupełnić później
    name: Optional[str] = "Użytkownik"
    age: Optional[int] = 25
    height: Optional[float] = 170.0
    weight: Optional[float] = 70.0
    target_weight: Optional[float] = 70.0
    gender: str = "mężczyzna"
    goal: str = "Utrzymanie wagi"
    frequency: str = "3-4 razy w tygodniu"
    diet: str = "Brak preferencji"

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Hasło musi mieć co najmniej 8 znaków")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Nieprawidłowy adres email")
        return value


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshAccessRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = JWT_EXPIRE_MINUTES * 60   # sekundy
    user_id: str
    user_number: Optional[int] = None
    display_name: str = "Użytkownik"
    name: str
    role: str
    plan: str
    refresh_token: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @classmethod
    def validate_new(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Hasło musi mieć co najmniej 8 znaków")
        return v


# ─── Profile / User Schemas ───────────────────────────────────────────────────

class UserProfile(BaseModel):
    name: str
    age: int
    height: float
    weight: float
    target_weight: float
    gender: str = "mężczyzna"
    goal: str
    frequency: str
    training_focus: list[str] = []
    improvement_areas: list[str] = []
    sports: list[str] = []
    diet: str
    allergies: str = ""
    preferred_foods: list[str] = []
    avoid_foods: list[str] = []
    available_equipment: list[str] = []
    avoid_exercises: list[str] = []
    substitutes_history: dict = {}
    meals_per_day: int = 4
    notes: str = ""


class ProfileUpdateRequest(BaseModel):
    """Edycja profilu użytkownika — tylko zmienne pola."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    age: Optional[int] = Field(default=None, ge=13, le=100)
    height: Optional[float] = Field(default=None, gt=100, le=250)
    weight: Optional[float] = Field(default=None, gt=25, le=400)
    target_weight: Optional[float] = Field(default=None, gt=25, le=400)
    gender: Optional[str] = Field(default=None, max_length=40)
    goal: Optional[str] = Field(default=None, max_length=120)
    frequency: Optional[str] = Field(default=None, max_length=80)
    diet: Optional[str] = Field(default=None, max_length=120)
    allergies: Optional[str] = Field(default=None, max_length=2000)
    meals_per_day: Optional[int] = Field(default=None, ge=1, le=12)
    notes: Optional[str] = Field(default=None, max_length=3000)
    sports: Optional[list[str]] = None
    training_focus: Optional[list[str]] = None
    improvement_areas: Optional[list[str]] = None
    available_equipment: Optional[list[str]] = None
    avoid_exercises: Optional[list[str]] = None
    sport_focus: Optional[str] = Field(default=None, max_length=80)
    sport_specialization: Optional[str] = Field(default=None, max_length=120)
    sport_training_days: Optional[list[str]] = None


class AssessmentRequest(BaseModel):
    """Versioned baseline assessment used as an input to planning."""
    training_level: Optional[str] = Field(default=None, max_length=40)
    training_experience_years: Optional[float] = Field(default=None, ge=0, le=80)
    sessions_per_week: Optional[int] = Field(default=None, ge=0, le=14)
    availability_hours_per_week: Optional[float] = Field(default=None, ge=0, le=168)
    recovery_score: Optional[int] = Field(default=None, ge=1, le=10)
    basketball_level: Optional[str] = Field(default=None, max_length=40)
    shooting_pct: Optional[float] = Field(default=None, ge=0, le=100)
    free_throw_pct: Optional[float] = Field(default=None, ge=0, le=100)
    sprint_30m_seconds: Optional[float] = Field(default=None, gt=0, le=30)
    vertical_jump_cm: Optional[float] = Field(default=None, ge=0, le=150)
    metrics: dict[str, Any] = {}
    notes: str = Field(default="", max_length=3000)

    @property
    def has_baseline(self) -> bool:
        return any(value is not None for value in (
            self.training_level, self.training_experience_years,
            self.sessions_per_week, self.availability_hours_per_week,
            self.recovery_score, self.basketball_level, self.shooting_pct,
            self.free_throw_pct, self.sprint_30m_seconds, self.vertical_jump_cm,
        )) or bool(self.metrics)


class NicknameChangeRequest(BaseModel):
    new_nickname: str


class AppOnboardingRequest(BaseModel):
    identity_id: str
    email: str
    name: str
    age: int
    height: float
    weight: float
    target_weight: float
    gender: str
    goal: str
    frequency: str
    sports: list[str] = []
    training_focus: list[str] = []
    improvement_areas: list[str] = []
    diet: str
    allergies: str = ""
    preferred_foods: list[str] = []
    avoid_foods: list[str] = []
    available_equipment: list[str] = []
    avoid_exercises: list[str] = []
    meals_per_day: int = 4
    notes: str = ""


# ─── Daily Log / Check-in Schemas ─────────────────────────────────────────────

class DailyLog(BaseModel):
    food: str = ""
    workout: str = ""
    mood: str = ""
    weight: Optional[float] = None


class WaterLogRequest(BaseModel):
    ml: int


class AppDailyCheckinRequest(BaseModel):
    # Pola tekstowe (legacy — zachowane dla kompatybilności)
    food: str = ""
    workout: str = ""
    mood: str = ""
    # Podstawowe dane liczbowe
    weight: Optional[float] = None
    water_ml: Optional[int] = Field(
        default=None, ge=0, le=10000,
        description="Spożyta woda w ml (zostanie przeliczona na litry)"
    )
    # Sen
    sleep_hours: Optional[float] = Field(
        default=None, ge=0, le=24,
        description="Czas snu w godzinach (np. 7.5)"
    )
    sleep_quality: Optional[int] = Field(
        default=None, ge=1, le=10,
        description="Jakość snu 1–10"
    )
    sleep_start: Optional[str] = Field(
        default=None,
        description="Godzina zaśnięcia HH:MM (np. 23:00)"
    )
    sleep_end: Optional[str] = Field(
        default=None,
        description="Godzina wstania HH:MM (np. 07:00)"
    )
    # Samopoczucie
    energy_level: Optional[int] = Field(
        default=None, ge=1, le=10,
        description="Poziom energii 1–10"
    )
    stress_level: Optional[int] = Field(
        default=None, ge=1, le=10,
        description="Poziom stresu 1–10"
    )
    fatigue_score: Optional[int] = Field(
        default=None, ge=1, le=10,
        description="Poziom zmęczenia 1–10"
    )
    mood_score: Optional[int] = Field(
        default=None, ge=1, le=5,
        description="Nastrój 1–5 (1=fatalny, 5=świetny)"
    )
    # Trening
    rpe: Optional[int] = Field(
        default=None, ge=1, le=10,
        description="RPE treningu 1–10"
    )
    meals_eaten: Optional[int] = Field(
        default=None, ge=0, le=20,
        description="Liczba zjedzonych posiłków"
    )
    workouts_done: Optional[int] = Field(
        default=None, ge=0, le=50,
        description="Liczba wykonanych ćwiczeń/drilli"
    )
    notes: Optional[str] = Field(
        default=None, max_length=1000,
        description="Dowolna notatka do dnia"
    )
    # Legacy — zachowane dla kompatybilności
    energy_score: Optional[int] = Field(
        default=None, ge=1, le=10
    )
    soreness: Optional[str] = None


class DayItemToggleRequest(BaseModel):
    item_id: str
    item_type: str
    checked: bool
    log_date: Optional[str] = None


class DayItemAddRequest(BaseModel):
    item_type: str
    name: str
    source: str = "custom"
    kcal: Optional[int] = None
    protein: Optional[float] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    rpe: Optional[int] = None
    meal_type: Optional[str] = None
    log_date: Optional[str] = None


class DayItemSwapRequest(BaseModel):
    item_id: str
    item_type: str
    new_name: str
    new_kcal: Optional[int] = None
    new_protein: Optional[float] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    rpe: Optional[int] = None
    log_date: Optional[str] = None


# ─── Fitness / Exercise Schemas ───────────────────────────────────────────────

class ExerciseResultRequest(BaseModel):
    """Wpis wyniku ćwiczenia z oceną RPE."""
    exercise_name: str
    sets: int
    reps: int
    weight_kg: float
    rpe: int = Field(ge=1, le=10, description="Rate of Perceived Exertion 1-10")
    notes: str = ""
    session_date: Optional[str] = None  # ISO date; jeśli brak → today


class DrillResultRequest(BaseModel):
    """Wynik sesji drilla sportowego z oceną RPE.
    
    Pola zależą od typu drilla:
    - Rzuty: success_count + total_attempts
    - Bieg/Sprint: time_seconds + distance_meters
    """
    drill_name: str
    drill_category: Optional[str] = None
    drill_sport: Optional[str] = None
    target_pct: Optional[int] = Field(default=None, ge=0, le=100)
    rpe: int = Field(ge=1, le=10, description="Rate of Perceived Exertion 1-10")
    notes: str = ""
    session_date: Optional[str] = None          # ISO date; jeśli brak → today
    # Rzuty
    success_count: int = 0
    total_attempts: int = 0
    # Bieg / Sprint
    time_seconds: Optional[float] = Field(default=None, gt=0, description="Czas w sekundach")
    distance_meters: Optional[float] = Field(default=None, gt=0, description="Dystans w metrach")
    # Ogólne
    duration_seconds: Optional[int] = Field(default=None, ge=0, description="Czas trwania [s]")
    weight_kg: Optional[float] = Field(default=None, ge=0, description="Obciążenie [kg]")


class TrainingAvailabilityRequest(BaseModel):
    """Weekly days on which the user can realistically train."""
    days: list[str] = Field(min_length=1, max_length=7)


class SportConfigRequest(BaseModel):
    """Konfiguracja modułu sportowego użytkownika."""
    sport_focus: str                            # np. "koszykówka"
    sport_specialization: str = ""             # np. "rzuty"
    sport_training_days: list[str] = []        # np. ["Środa", "Sobota"]


# ─── Plan / Reminder Schemas ──────────────────────────────────────────────────

class PlanUpdateRequest(BaseModel):
    plan: str


class WeeklyPlanSaveRequest(BaseModel):
    plan: dict


class PlanGenerateRequest(BaseModel):
    force: bool = False


class PlanSwapRequest(BaseModel):
    day_index: int
    section: str
    item_index: int
    alternative_index: int


class ReminderPrefsRequest(BaseModel):
    email_enabled: bool = True
    discord_enabled: bool = True
    discord_channel_id: Optional[str] = None


# ─── AI / Content Schemas ─────────────────────────────────────────────────────

class AIRequest(BaseModel):
    user_id: str
    extra_context: str = ""


# ─── Integration Schemas ──────────────────────────────────────────────────────

class DiscordLinkRequest(BaseModel):
    identity_id: str
    discord_user_id: str


# ─── Training Execution Schemas ───────────────────────────────────────────────

class TrainingSetResultRequest(BaseModel):
    exercise_key: str = Field(min_length=1, max_length=200)
    set_number: int = Field(ge=1, le=100)
    actual_reps: int = Field(ge=0, le=1000)
    actual_weight_kg: float = Field(default=0, ge=0, le=10000)
    actual_rpe: Optional[int] = Field(default=None, ge=1, le=10)
    completed: bool = True
    note: str = Field(default="", max_length=1000)


class TrainingCompleteRequest(BaseModel):
    final_rpe: Optional[int] = Field(default=None, ge=1, le=10)
    notes: str = Field(default="", max_length=2000)


class GoalCreateRequest(BaseModel):
    goal_type: str
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=3000)
    start_date: Optional[str] = None
    target_date: Optional[str] = None
    priority: int = Field(default=0, ge=0, le=100)
    metric_key: Optional[str] = None
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    metadata: dict[str, Any] = {}


class GoalUpdateRequest(BaseModel):
    goal_type: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=3000)
    start_date: Optional[str] = None
    target_date: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=0, le=100)
    status: Optional[str] = None
    metric_key: Optional[str] = None
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None
