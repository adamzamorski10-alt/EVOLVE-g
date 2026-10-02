from pathlib import Path


INDEX = Path(__file__).with_name("index.html")


def test_training_execution_ui_is_wired_to_stage2_api():
    html = INDEX.read_text(encoding="utf-8")
    required = [
        'id="evolveStartTrainingBtn"',
        'window.evolveStartTraining',
        '/app/training/sessions/start',
        '/app/training/sessions/' + "' + encodeURIComponent(session.id) + '" + '/sets',
        '/app/training/sessions/' + "' + encodeURIComponent(session.id) + '" + '/complete',
        'data-save-ex',
        '✓ Zakończ trening',
    ]
    for marker in required:
        assert marker in html, f"Missing training UI integration marker: {marker}"


def test_training_execution_ui_keeps_existing_today_container():
    html = INDEX.read_text(encoding="utf-8")
    assert 'id="activeDayExerciseList"' in html
    assert 'loadTodayData' in html
    assert 'renderWorkoutsList' in html
