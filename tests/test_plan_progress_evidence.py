from app.plan.progress_evidence import build_planning_progress_evidence


def test_insufficient_progress_is_fail_safe():
    result = build_planning_progress_evidence({
        "status": "insufficient_data",
        "sufficient_data": False,
        "exercise_key": "bench",
        "reason_codes": ["INSUFFICIENT_PROGRESS_HISTORY"],
    })

    assert result["recommended_action"] == "none"
    assert result["sufficient_data"] is False
    assert result["mutates_plan"] is False


def test_positive_progress_becomes_planning_evidence_not_a_mutation():
    result = build_planning_progress_evidence({
        "status": "sufficient",
        "sufficient_data": True,
        "exercise_key": "bench",
        "material_change": True,
        "reason_codes": ["MATERIAL_CHANGE"],
        "changes": {
            "average_weight_kg_delta": 2.5,
            "average_reps_delta": 0,
            "volume_kg_delta": 20,
        },
        "latest": {"session_id": "new"},
        "previous": {"session_id": "old"},
    })

    assert result["recommended_action"] == "progress"
    assert result["exercise_key"] == "bench"
    assert result["source"] == "canonical_progress"
    assert result["mutates_plan"] is False


def test_negative_progress_is_bounded_to_reduce_evidence():
    result = build_planning_progress_evidence({
        "status": "sufficient",
        "sufficient_data": True,
        "exercise_key": "bench",
        "material_change": True,
        "reason_codes": ["MATERIAL_CHANGE"],
        "changes": {
            "average_weight_kg_delta": -2.5,
            "average_reps_delta": -1,
            "volume_kg_delta": -20,
        },
    })

    assert result["recommended_action"] == "reduce"
    assert result["mutates_plan"] is False


def test_missing_metrics_are_not_invented():
    result = build_planning_progress_evidence({
        "status": "sufficient",
        "sufficient_data": True,
        "exercise_key": "bench",
        "material_change": True,
        "reason_codes": ["MATERIAL_CHANGE"],
        "changes": {
            "average_weight_kg_delta": None,
            "average_reps_delta": None,
            "volume_kg_delta": None,
            "average_rpe_delta": None,
        },
    })

    assert result["recommended_action"] == "maintain"
    assert result["changes"] == {}


def test_non_finite_changes_are_ignored():
    result = build_planning_progress_evidence({
        "status": "sufficient",
        "sufficient_data": True,
        "exercise_key": "bench",
        "material_change": True,
        "reason_codes": ["MATERIAL_CHANGE"],
        "changes": {
            "average_weight_kg_delta": float("nan"),
            "average_reps_delta": float("inf"),
            "volume_kg_delta": 2.5,
        },
    })

    assert result["recommended_action"] == "progress"
    assert result["changes"] == {"volume_kg_delta": 2.5}


def test_invalid_input_is_fail_safe():
    result = build_planning_progress_evidence(None)

    assert result["status"] == "insufficient_data"
    assert result["recommended_action"] == "none"
    assert result["mutates_plan"] is False
