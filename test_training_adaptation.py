from app.training.adaptation import ADAPTATION_ALGORITHM, adapt_exercise


def _planned(weight=100, reps=5, sets=3):
    return {
        "exercise_key": "squat-1",
        "exercise_name": "Squat",
        "sets": sets,
        "reps": reps,
        "weight_kg": weight,
    }


def test_progress_is_bounded_and_deterministic():
    planned = _planned()
    evaluation = {"decision": "progress", "reason_codes": ["TARGET_COMPLETED"]}
    result = adapt_exercise(planned, evaluation)
    assert result["proposed"]["weight_kg"] == 102.5
    assert result["proposed"]["sets"] == 3
    assert result["algorithm"] == ADAPTATION_ALGORITHM
    assert planned["weight_kg"] == 100


def test_reduce_is_bounded_and_deterministic():
    result = adapt_exercise(_planned(weight=100), {"decision": "reduce", "reason_codes": ["LOW_SET_COMPLETION"]})
    assert result["proposed"]["weight_kg"] == 97.5


def test_maintain_does_not_change_load():
    result = adapt_exercise(_planned(weight=100), {"decision": "maintain", "reason_codes": ["HIGH_RPE"]})
    assert result["action"] == "unchanged"
    assert result["proposed"] == result["current"]


def test_insufficient_data_never_progresses():
    result = adapt_exercise(_planned(weight=100), {"decision": "insufficient_data", "reason_codes": ["NO_COMPLETED_SETS"]})
    assert result["action"] == "unchanged"
    assert result["proposed"] == result["current"]


def test_bodyweight_progress_adds_one_rep_without_changing_sets():
    result = adapt_exercise(_planned(weight=0, reps=8), {"decision": "progress", "reason_codes": ["TARGET_COMPLETED"]})
    assert result["proposed"]["reps"] == 9
    assert result["proposed"]["sets"] == 3


def test_small_load_progression_still_moves_forward():
    result = adapt_exercise(_planned(weight=10), {"decision": "progress", "reason_codes": ["TARGET_COMPLETED"]})
    assert result["proposed"]["weight_kg"] == 12.5


def test_small_load_reduction_still_moves_down():
    result = adapt_exercise(_planned(weight=10), {"decision": "reduce", "reason_codes": ["LOW_SET_COMPLETION"]})
    assert result["proposed"]["weight_kg"] == 7.5

def test_progression_never_exceeds_five_percent_even_at_large_load():
    result = adapt_exercise(_planned(weight=1000), {'decision': 'progress', 'reason_codes': ['TARGET_COMPLETED']})
    assert result['proposed']['weight_kg'] == 1025
    assert result['proposed']['weight_kg'] <= 1050

def test_reduce_never_exceeds_five_percent_even_at_large_load():
    result = adapt_exercise(_planned(weight=1000), {'decision': 'reduce', 'reason_codes': ['LOW_SET_COMPLETION']})
    assert result['proposed']['weight_kg'] == 975
    assert result['proposed']['weight_kg'] >= 950

def test_unknown_decision_is_fail_safe_and_does_not_change_plan():
    result = adapt_exercise(_planned(weight=100), {'decision': 'unexpected', 'reason_codes': ['MALFORMED']})
    assert result['action'] == 'unchanged'
    assert result['proposed'] == result['current']