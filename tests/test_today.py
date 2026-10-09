from app.today import TODAY_STATES, build_today_action


def _decision(state, **overrides):
    value = {
        "decision": state,
        "priority": "normal",
        "action": "Canonical explanation.",
        "reason_codes": ["TEST_REASON"],
        "supporting_goal_ids": ["g1"],
        "supporting_session_ids": ["s1"],
        "constraints": [],
        "sufficient_data": state != "insufficient_data",
    }
    value.update(overrides)
    return value


def _training(*, has_workout=True, can_start=True):
    return {"has_workout": has_workout, "can_start": can_start}


def test_today_state_model_covers_all_semantic_states():
    assert TODAY_STATES == {
        "recover",
        "reduce_training",
        "train_as_planned",
        "progress_training",
        "maintain_training",
        "insufficient_data",
        "rest",
    }


def test_recover_state_blocks_start():
    result = build_today_action(
        decision=_decision("recover", priority="critical"),
        training=_training(),
    )
    assert result["state"] == "recover"
    assert result["primary_action"]["can_start"] is False
    assert result["safety"]["blocked"] is True


def test_reduce_training_state_preserves_effective_training_start():
    result = build_today_action(
        decision=_decision("reduce_training"),
        training=_training(),
    )
    assert result["state"] == "reduce_training"
    assert result["primary_action"]["can_start"] is True
    assert result["safety"]["blocked"] is False


def test_train_as_planned_state():
    result = build_today_action(
        decision=_decision("train_as_planned"),
        training=_training(),
    )
    assert result["state"] == "train_as_planned"
    assert result["primary_action"]["can_start"] is True


def test_progress_state():
    result = build_today_action(
        decision=_decision("progress_training"),
        training=_training(),
    )
    assert result["state"] == "progress_training"


def test_maintain_state():
    result = build_today_action(
        decision=_decision("maintain_training"),
        training=_training(),
    )
    assert result["state"] == "maintain_training"


def test_insufficient_data_state_blocks_training():
    result = build_today_action(
        decision=_decision("insufficient_data"),
        training=_training(),
    )
    assert result["state"] == "insufficient_data"
    assert result["primary_action"]["can_start"] is False
    assert result["data_quality"]["sufficient_data"] is False


def test_no_workout_maps_to_rest_after_decision_is_safe():
    result = build_today_action(
        decision=_decision("train_as_planned"),
        training=_training(has_workout=False, can_start=False),
    )
    assert result["state"] == "rest"
    assert result["primary_action"]["can_start"] is False


def test_mapping_is_deterministic_and_does_not_mutate_inputs():
    decision = _decision("progress_training")
    training = _training()
    before = (repr(decision), repr(training))
    first = build_today_action(decision=decision, training=training)
    second = build_today_action(decision=decision, training=training)
    assert first == second
    assert (repr(decision), repr(training)) == before

def test_unknown_or_malformed_decision_fails_closed():
    for invalid_value in ("unexpected_decision", None, True, {"decision": "recover"}):
        result = build_today_action(
            decision=_decision(invalid_value, sufficient_data=True),
            training=_training(has_workout=True, can_start=True),
        )
        assert result["state"] == "insufficient_data"
        assert result["primary_action"]["can_start"] is False
        assert result["workout"]["can_start"] is False
        assert result["safety"]["blocked"] is True
        assert result["data_quality"]["status"] == "insufficient"
        assert result["data_quality"]["sufficient_data"] is False
        assert result["explanation"]["reason_codes"] == ["INVALID_DECISION_FAIL_CLOSED"]
