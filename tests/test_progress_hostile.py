from app.training.progress import build_progress_evidence

def _history(weight_a, reps_a, weight_b, reps_b):
    return [
        {"session_id": "new", "session_date": "2026-10-05", "exercises": [{"exercise_key": "squat", "exercise_name": "Squat", "sets": [{"actual_weight_kg": weight_a, "actual_reps": reps_a, "actual_rpe": 7, "completed": True}]}]},
        {"session_id": "old", "session_date": "2026-10-01", "exercises": [{"exercise_key": "squat", "exercise_name": "Squat", "sets": [{"actual_weight_kg": weight_b, "actual_reps": reps_b, "actual_rpe": 8, "completed": True}]}]},
    ]

def test_progress_ignores_non_finite_numeric_values():
    result = build_progress_evidence(_history(float("nan"), 5, 100, 5), exercise_key="squat")
    assert result["status"] == "insufficient_data"

def test_progress_volume_pairs_metrics_per_set_instead_of_cross_set_zip():
    history = [
        {"session_id": "new", "session_date": "2026-10-05", "exercises": [{"exercise_key": "squat", "sets": [{"actual_weight_kg": 100, "actual_reps": 5, "actual_rpe": 7, "completed": True}, {"actual_weight_kg": None, "actual_reps": 6, "actual_rpe": 7, "completed": True}]}]},
        {"session_id": "old", "session_date": "2026-10-01", "exercises": [{"exercise_key": "squat", "sets": [{"actual_weight_kg": 100, "actual_reps": 5, "actual_rpe": 8, "completed": True}]}]},
    ]
    result = build_progress_evidence(history, exercise_key="squat")
    assert result["latest"]["volume_kg"] == 500.0

def test_progress_never_uses_uncompleted_sets_as_evidence():
    history = [
        {"session_id": "new", "session_date": "2026-10-05", "exercises": [{"exercise_key": "squat", "sets": [{"actual_weight_kg": 500, "actual_reps": 20, "actual_rpe": 1, "completed": False}]}]},
        {"session_id": "old", "session_date": "2026-10-01", "exercises": [{"exercise_key": "squat", "sets": [{"actual_weight_kg": 100, "actual_reps": 5, "actual_rpe": 8, "completed": True}]}]},
    ]
    result = build_progress_evidence(history, exercise_key="squat")
    assert result["status"] == "insufficient_data"

def test_unknown_exercise_is_fail_safe():
    result = build_progress_evidence(_history(105, 5, 100, 5), exercise_key="does-not-exist")
    assert result["status"] == "insufficient_data"
    assert result["observations"] == []