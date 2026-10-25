from __future__ import annotations

import json
from datetime import date
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_stats_by_identity_returns_json_even_for_new_user():
    response = client.get("/app/stats/test_identity_123?days=30")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    assert "weight_entries" in data
    assert "training_volume" in data
    assert "diet_compliance_pct" in data
    assert "kpi" in data
    assert "xp" in data
    assert "strength_progression" in data
    assert "shooting_stats" in data
    assert "assessment_history" in data
    assert "goals" in data


def test_unmatched_api_routes_return_404_json_not_html():
    response = client.get("/app/unknown_api_subroute")
    assert response.status_code == 404
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    assert "error" in data


def test_seed_data_is_served_and_has_no_double_commas():
    response = client.get("/fitai_seed_data.js")
    assert response.status_code == 200
    content = response.text
    assert "Dragon Flag" in content
    # Ensure no empty array slots
    import re
    assert len(re.findall(r',\s*,', content)) == 0


def test_today_hub_structure_and_consistency():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    # 4 filary Today Hub obecne w HTML
    assert "todayWorkoutName" in html
    assert "todayBasketballStats" in html
    assert "todayHubKcalBar" in html
    assert "quickCheckinStatus" in html
    # Skrypty spójności i odświeżania
    assert "updateDayConsistencyScore" in html
    assert "refreshTodayHubDiet" in html
    assert "refreshTodayHubBasketball" in html
    assert "openTodayShotTrackerModal" in html


def test_sport_profile_frontend_and_backend():
    # 1. Sprawdź obecność pól w index.html
    page_resp = client.get("/")
    assert page_resp.status_code == 200
    html = page_resp.text
    assert "pBasketballPosition" in html
    assert "pTrainingExperience" in html
    assert "pHealthLimitations" in html
    assert "pEquipment" in html
    assert "pBasketballPosition" in html
    assert "saveProfileData" in html
    assert "_loadProfileIntoForm" in html

    # 2. Zarejestruj użytkownika i zaktualizuj profil sportowy przez API
    import uuid
    email = f"sport-user-{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123",
            "nickname": f"sport_{uuid.uuid4().hex[:8]}",
            "name": "Jordan Test",
            "age": 24,
            "height": 198,
            "weight": 95,
            "target_weight": 98,
            "goal": "Budowa masy mięśniowej",
            "frequency": "5-6",
            "diet": "zbilansowana",
        },
    )
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Zapisz profil sportowy (PUT /app/profile)
    put_resp = client.put(
        "/app/profile",
        json={
            "basketball_position": "SG",
            "training_experience": "advanced",
            "equipment": "hybrid",
            "health_limitations": "Lekkie przeciążenie lewego kolana",
        },
        headers=headers,
    )
    assert put_resp.status_code == 200
    put_data = put_resp.json()
    assert put_data["status"] == "ok"
    assert put_data["profile"]["basketball_position"] == "SG"
    assert put_data["profile"]["training_experience"] == "advanced"
    assert put_data["profile"]["equipment"] == "hybrid"
    assert put_data["profile"]["health_limitations"] == "Lekkie przeciążenie lewego kolana"

    # 4. Pobierz profil (GET /app/profile) i zweryfikuj trwałość
    get_resp = client.get("/app/profile", headers=headers)
    assert get_resp.status_code == 200
    profile = get_resp.json()
    assert profile["basketball_position"] == "SG"
    assert profile["training_experience"] == "advanced"
    assert profile["equipment"] == "hybrid"
    assert profile["health_limitations"] == "Lekkie przeciążenie lewego kolana"


def test_live_workout_runner_frontend_and_lifecycle():
    # 1. Weryfikacja obecności Workout Runnera w index.html
    page_resp = client.get("/")
    assert page_resp.status_code == 200
    html = page_resp.text
    assert "evolveStartTraining" in html
    assert "openLiveWorkoutModal" in html
    assert "todayStartWorkoutBtn" in html
    assert "runnerRestBanner" in html
    assert "btnFinishWorkout" in html
    assert "completeSessionBox" in html

    # 2. Rejestracja użytkownika i przypisanie planu treningowego na dziś
    import uuid
    from datetime import date
    from sqlmodel import Session, select
    from app.database import engine
    from app.models import UserDB

    email = f"runner-{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123",
            "nickname": f"runner_{uuid.uuid4().hex[:8]}",
            "name": "Runner Test",
            "age": 26,
            "height": 182,
            "weight": 83,
            "target_weight": 80,
            "goal": "Siła i dynamika",
            "frequency": "3-4",
            "diet": "zbilansowana",
        },
    )
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    today_label = {0: "Pon", 1: "Wt", 2: "Śr", 3: "Czw", 4: "Pt", 5: "Sob", 6: "Niedz"}[date.today().weekday()]
    plan = {
        "days": [{
            "day": today_label,
            "workout": {
                "title": "Trening A",
                "exercises": [
                    {
                        "id": "bench-press-1",
                        "name": "Wyciskanie sztangi",
                        "sets": 3,
                        "reps": 8,
                        "weight_kg": 85.0,
                        "rpe": 7,
                    }
                ],
            },
        }]
    }

    with Session(engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == email)).first()
        assert user is not None
        user.weekly_plan_json = json.dumps(plan, ensure_ascii=False)
        session.add(user)
        session.commit()

    # 3. Rozpoczęcie sesji (POST /app/training/sessions/start)
    start_resp = client.post("/app/training/sessions/start", headers=headers)
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert start_data["status"] in ("started", "resumed")
    session_id = start_data["session"]["id"]

    # 4. Zalogowanie serii (POST /app/training/sessions/{session_id}/sets)
    set_resp = client.post(
        f"/app/training/sessions/{session_id}/sets",
        json={
            "exercise_key": "bench-press-1",
            "set_number": 1,
            "actual_reps": 8,
            "actual_weight_kg": 85.0,
            "actual_rpe": 7,
            "completed": True,
            "note": "Płynna seria",
        },
        headers=headers,
    )
    assert set_resp.status_code == 200
    set_data = set_resp.json()
    assert set_data["set"]["completed"] is True
    assert set_data["set"]["actual_weight_kg"] == 85.0

    # 5. Zakończenie treningu (POST /app/training/sessions/{session_id}/complete)
    complete_resp = client.post(
        f"/app/training/sessions/{session_id}/complete",
        json={"final_rpe": 8, "notes": "Ukończono w teście Live Workout Runner"},
        headers=headers,
    )
    assert complete_resp.status_code == 200
    comp_data = complete_resp.json()
    assert comp_data["session"]["status"] == "completed"
    assert comp_data["session"]["final_rpe"] == 8


def test_assessment_and_rolling_plan_tied_to_profile():
    """Weryfikuje Etap D: Assessment początkowy i generowanie planu kroczącego powiązanego z profilem."""
    import uuid
    email = f"plan-user-{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123",
            "nickname": f"plan_{uuid.uuid4().hex[:8]}",
            "name": "Alex Evolve",
            "age": 25,
            "height": 188,
            "weight": 82,
            "target_weight": 85,
            "goal": "Budowa siły i wyskoku",
            "frequency": "4",
            "diet": "zbilansowana",
        },
    )
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Zapisz profil ze sprzętem i pozycją
    prof_resp = client.put(
        "/app/profile",
        json={
            "basketball_position": "SG",
            "training_experience": "intermediate",
            "equipment": "dumbbells",
            "health_limitations": "Lekkie przeciążenie lewego kolana",
        },
        headers=headers,
    )
    assert prof_resp.status_code == 200

    # 2. Przed assessmentem plan readiness wskazuje brak assessmentu
    ready_resp = client.get("/app/plan/readiness", headers=headers)
    assert ready_resp.status_code == 200
    readiness = ready_resp.json()
    assert readiness["profile_ready"] is True
    assert readiness["assessment_ready"] is False
    assert readiness["ready"] is False

    # 3. Zapisz assessment
    assm_resp = client.post(
        "/app/assessment",
        json={
            "training_level": "intermediate",
            "training_experience_years": 3,
            "sessions_per_week": 4,
            "availability_hours_per_week": 6.0,
            "recovery_score": 8,
            "basketball_level": "6",
            "shooting_pct": 55.0,
            "free_throw_pct": 78.0,
            "sprint_30m_seconds": 4.15,
            "vertical_jump_cm": 68.0,
            "notes": "Cel: poprawa skuteczności z wyskoku",
            "metrics": {},
        },
        headers=headers,
    )
    assert assm_resp.status_code == 200
    assm_data = assm_resp.json()
    assert assm_data["status"] == "created"
    assert assm_data["assessment"]["version"] == 1

    # 4. Sprawdź readiness po assessmencie
    ready_resp2 = client.get("/app/plan/readiness", headers=headers)
    assert ready_resp2.status_code == 200
    readiness2 = ready_resp2.json()
    assert readiness2["ready"] is True
    assert readiness2["assessment_ready"] is True

    # 5. Wygeneruj plan powiązany z profilem i assessmentem
    gen_resp = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=headers,
    )
    assert gen_resp.status_code == 200
    plan_data = gen_resp.json()
    assert plan_data["status"] == "ok"
    plan = plan_data["plan"]
    assert "rolling_plan" in plan
    assert "planned_days" in plan["rolling_plan"]
    assert len(plan["rolling_plan"]["planned_days"]) >= 7
    assert plan["rolling_plan"]["plan_version"] == "rolling-v1"

    # Sprawdź provenance powiązania
    provenance = plan["_evolve_core"]
    assert provenance["profile_inputs"]["basketball_position"] == "SG"
    assert provenance["profile_inputs"]["equipment"] == "dumbbells"
    assert provenance["profile_inputs"]["health_limitations"] == "Lekkie przeciążenie lewego kolana"
    assert provenance["assessment_version"] == 1

    # 6. Modyfikacja profilu sportowego powoduje natychmiastowe wykrycie przedawnienia (profile_stale)
    prof_update = client.put(
        "/app/profile",
        json={"equipment": "gym_full"},
        headers=headers,
    )
    assert prof_update.status_code == 200

    ready_resp3 = client.get("/app/plan/readiness", headers=headers)
    assert ready_resp3.status_code == 200
    readiness3 = ready_resp3.json()
    assert readiness3["profile_stale"] is True
    assert readiness3["plan_stale"] is True


def test_progress_hub_strength_shooting_goals_and_tests():
    """Weryfikuje Etap E: Postępy — siła, skuteczność rzutowa, testy motoryczne i mierzalne cele."""
    # 1. Sprawdź obecność kontenerów w HTML
    index_resp = client.get("/")
    assert index_resp.status_code == 200
    html = index_resp.text
    assert "postepyGoalsWrap" in html
    assert "postepyStrengthWrap" in html
    assert "postepyShootingWrap" in html
    assert "postepyAssessmentWrap" in html

    # 2. Utwórz użytkownika
    import uuid
    email = f"progress-user-{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123",
            "nickname": f"prog_{uuid.uuid4().hex[:8]}",
            "name": "Jordan Progress",
            "age": 23,
            "height": 195,
            "weight": 88,
            "target_weight": 92,
            "goal": "Siła i wyskok",
            "frequency": "4",
            "diet": "zbilansowana",
        },
    )
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    today_label = {0: "Pon", 1: "Wt", 2: "Śr", 3: "Czw", 4: "Pt", 5: "Sob", 6: "Niedz"}[date.today().weekday()]
    plan = {
        "days": [{
            "day": today_label,
            "workout": {
                "title": "Trening A",
                "exercises": [
                    {
                        "id": "bench-press-1",
                        "name": "Wyciskanie leżąc",
                        "sets": 3,
                        "reps": 6,
                        "weight_kg": 90.0,
                    }
                ],
            },
        }]
    }

    from sqlmodel import Session, select
    from app.database import engine
    from app.models import UserDB
    with Session(engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == email)).first()
        assert user is not None
        user.weekly_plan_json = json.dumps(plan, ensure_ascii=False)
        session.add(user)
        session.commit()

    # 3. Zaloguj trening siłowy (Bench Press 90kg x 6)
    start_resp = client.post("/app/training/sessions/start", headers=headers)
    assert start_resp.status_code == 200
    sess_id = start_resp.json()["session"]["id"]

    set_resp = client.post(
        f"/app/training/sessions/{sess_id}/sets",
        json={
            "exercise_key": "bench-press-1",
            "set_number": 1,
            "actual_reps": 6,
            "actual_weight_kg": 90.0,
            "actual_rpe": 8,
            "completed": True,
        },
        headers=headers,
    )
    assert set_resp.status_code == 200

    comp_resp = client.post(f"/app/training/sessions/{sess_id}/complete", json={"final_rpe": 8}, headers=headers)
    assert comp_resp.status_code == 200

    # 4. Zaloguj sesję rzutową (50 prób, 38 trafień = 76%)
    drill_resp = client.post(
        "/app/drill-result",
        json={
            "drill_name": "Rzuty za 3 punkty",
            "attempts": 50,
            "made": 38,
            "rpe": 7,
            "notes": "Dobra powtarzalność",
        },
        headers=headers,
    )
    assert drill_resp.status_code == 200

    # 5. Zapisz assessment
    assm_resp = client.post(
        "/app/assessment",
        json={
            "training_level": "intermediate",
            "vertical_jump_cm": 72.0,
            "sprint_30m_seconds": 4.10,
            "shooting_pct": 76.0,
            "free_throw_pct": 82.0,
            "recovery_score": 8,
            "notes": "Test bazowy motoryki",
            "metrics": {},
        },
        headers=headers,
    )
    assert assm_resp.status_code == 200

    # 6. Dodaj mierzalny cel (Wyciskanie leżąc 100 kg, baseline 80 kg -> przy 90 kg postęp to 50%)
    goal_resp = client.post(
        "/app/goals",
        json={
            "goal_type": "strength",
            "title": "Wyciskanie leżąc 100kg",
            "metric_key": "best_weight_kg",
            "baseline_value": 80.0,
            "target_value": 100.0,
            "priority": 90,
        },
        headers=headers,
    )
    assert goal_resp.status_code == 200

    # 7. Pobierz statystyki (/app/stats) i sprawdź agregacje
    stats_resp = client.get("/app/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()

    # Siła
    assert len(stats["strength_progression"]) >= 1
    bench = next(s for s in stats["strength_progression"] if "bench" in s["exercise_key"].lower())
    assert bench["best_weight_kg"] == 90.0
    assert bench["best_reps"] == 6
    assert bench["estimated_1rm"] >= 105.0

    # Rzuty
    shooting = stats["shooting_stats"]
    assert shooting["total_attempts"] == 50
    assert shooting["total_made"] == 38
    assert shooting["accuracy_pct"] == 76.0
    assert len(shooting["history"]) >= 1

    # Assessment
    assert len(stats["assessment_history"]) >= 1
    last_assm = stats["assessment_history"][-1]
    assert last_assm["vertical_jump_cm"] == 72.0
    assert last_assm["sprint_30m_seconds"] == 4.10

    # Cele z postępem
    assert len(stats["goals"]) >= 1
    goal = next(g for g in stats["goals"] if "Wyciskanie" in g["title"])
    assert goal["baseline_value"] == 80.0
    assert goal["target_value"] == 100.0
    assert goal["current_value"] == 90.0
    assert goal["progress_pct"] == 50.0


