# EVOLVE — External Verification Queue

This file is the source of truth for checks that cannot be reliably completed from repository/code inspection alone.

## How to use this file

- Add an item whenever implementation is complete enough that real browser/device verification is required.
- Do not mark an item PASS from static code review.
- Recommended verifier:
  - Antygravity — browser/UI/UX and real user-flow verification.
  - Copilot VS Code — fast local execution/diagnostics.
  - Kilo Code — longer local implementation/debug/test tasks.
- When the user is available to run checks, generate copy-paste prompts from this file.
- After verification, update the item with result, date, and any discovered issue.
- Do not remove completed checks; keep them as verification history.

## Status values

- PENDING — must still be externally verified.
- BLOCKED — cannot currently be verified because required environment/access is unavailable.
- PASS — externally verified successfully.
- FAIL — external verification found a problem; fix it before closing the item.

## Stage 0–1 — Core / Mój dzień / Training execution

### EV-001 — Native Mój dzień visual + UX verification
- Status: PENDING
- Verifier: Antygravity
- Type: browser UI + real user flow
- Scope:
  1. Start the application in the normal production-like local environment.
  2. Enter the main application shell and open Mój dzień.
  3. Verify the native Mój dzień view renders without legacy/landing-page flash.
  4. Verify navigation into Mój dzień reliably loads fresh data.
  5. Refresh directly on the relevant app route/hash and verify the correct view remains available.
  6. Test both states: day with a planned workout and day without a workout.
  7. In the no-workout state, verify the CTA is visibly disabled/non-actionable and cannot navigate to a training session.
  8. In the workout state, verify the training CTA opens the intended training-session UI.
  9. Check desktop and narrow/mobile viewport for clipping, overflow, broken hierarchy, or unusable controls.
- Evidence required: screenshots or concise PASS/FAIL notes for each scenario.
- Do not change code unless explicitly asked; this is verification first.

### EV-002 — Training execution end-to-end browser verification
- Status: PENDING
- Verifier: Antygravity
- Type: browser UI + real user flow
- Scope:
  1. Open today's training.
  2. Start a session.
  3. Log multiple sets for at least one exercise.
  4. Include one incomplete set and verify it is not treated as completed execution.
  5. Complete the session.
  6. Verify the UI reflects the completed state.
  7. Re-submit completion and verify it does not duplicate downstream results.
  8. Verify session/history views show the expected completed data.
  9. If possible, open two tabs and attempt the same completion/set action to exercise concurrency/idempotency behavior from the UI.
- Evidence required: PASS/FAIL plus any visible errors/network errors.

## Stage 2 — Progress / Training History

### EV-003 — Progress dashboard visual + UX verification
- Status: PENDING
- Verifier: Antygravity
- Type: browser UI + data presentation
- Scope:
  1. Open the main EVOLVE shell and select Postępy.
  2. Verify there is exactly one visible native Progress panel; no duplicate/legacy Progress panel is visible.
  3. Verify summary cards: Sesje, Serie, Wolumen, Śr. wykonania.
  4. Verify Trends, Records, Exercises, Regularność and Historia sesji sections.
  5. Verify populated, empty and error/loading states.
  6. Navigate away and back; verify fresh data loads and no stale response overwrites newer data.
  7. Refresh the app and reopen Postępy.
  8. Verify desktop and narrow/mobile layouts: no clipping, horizontal overflow or unusable controls.
- Evidence required: PASS/FAIL notes and screenshots for populated/empty states where possible.

### EV-004 — Progress data semantics with real user data
- Status: PENDING
- Verifier: Antygravity
- Type: browser data correctness
- Scope:
  1. Use an account with at least one completed session.
  2. Confirm only completed sessions contribute to Progress.
  3. Confirm incomplete sets do not inflate sets or volume.
  4. Confirm active/cancelled sessions do not appear.
  5. Confirm visible summary values match the completed execution data.
  6. If a safe second account is available, confirm cross-user isolation.
- Evidence required: PASS/FAIL and exact test scenario/data.

### EV-005 — Progress exercise drill-down
- Status: PENDING
- Verifier: Antygravity
- Type: browser UI + data correctness
- Scope:
  1. Open Postępy → Ćwiczenia.
  2. Select an exercise with completed history.
  3. Verify drill-down shows exercise name, session count, record weight and total volume.
  4. Verify per-session history shows date, sets, best weight, best reps at best weight, volume and RPE when available.
  5. Verify empty exercise state behaves safely.
  6. Verify active/cancelled sessions are excluded.
  7. If possible, verify another user's exercise key cannot expose the first user's data.
  8. Verify narrow/mobile layout.
- Evidence required: PASS/FAIL, screenshot and test data.

### EV-006 — Trends / records / consistency / session history
- Status: PENDING
- Verifier: Antygravity
- Type: browser UI + data correctness
- Scope:
  1. Verify Trends shows deterministic weight, volume and RPE states.
  2. Verify Records shows best weight, best reps at the corresponding weight and best session volume.
  3. Verify Regularność shows training days, sessions/week, current streak and longest streak.
  4. Verify Historia sesji lists completed sessions only.
  5. Open a history item and verify session drill-down contains only that owned completed session and its sets.
  6. Verify active/cancelled sessions are absent.
  7. Verify values are consistent with the same completed execution data shown elsewhere.
  8. Verify empty-state behavior and mobile layout.
- Evidence required: PASS/FAIL with screenshots/data notes.

### EV-007 — Main-shell Progress navigation
- Status: PENDING
- Verifier: Antygravity
- Type: browser navigation + shell integration
- Scope:
  1. Open the normal /app shell.
  2. Verify Postępy is a first-class navigation item.
  3. Select Postępy and verify the native panel opens without navigating to a standalone legacy dashboard.
  4. Navigate between Mój dzień, Trening and Postępy repeatedly.
  5. Verify each transition loads the correct data and no stale Progress request overwrites another view.
  6. Refresh/reopen the app and verify shell integrity.
- Evidence required: PASS/FAIL plus screenshot or concise navigation notes.

### EV-008 — Local automated regression gate
- Status: PENDING
- Verifier: Copilot VS Code or Kilo Code
- Type: local execution + regression
- Scope:
  1. Inspect current repository tooling before choosing commands.
  2. Run the focused training/progress test files.
  3. Run the complete pytest suite.
  4. Run Alembic migration/revision consistency checks using the repository's configured tooling.
  5. If any test fails, classify it as pre-existing vs introduced by Stage 2; do not weaken/delete tests.
  6. Report exact commands, exit codes, failing tests and environment/runtime errors.
  7. Do not mark PASS if the command did not actually execute or if failures remain unexplained.
- Suggested starting commands, subject to repository inspection:
  - python -m pytest -q
  - python -m alembic current
  - python -m alembic heads
- Evidence required: command transcript/summary with exit codes and exact failures.

## Stage 2 gate
Stage 2 is considered **fully verified** only when:
- static code review passes,
- focused tests pass,
- full regression passes,
- required migration checks pass,
- EV-003 through EV-007 pass external browser verification,
- EV-008 passes local execution verification,
- any discovered issue is fixed and the affected checks are rerun.

Pending external checks must not be represented as PASS.

## Verification protocol

For every future implementation stage:
1. Static verification — performed by the primary development process.
2. Automated tests — performed where the environment permits.
3. External browser/device verification — add an Antygravity item when UI or real user behavior matters.
4. Local command/runtime verification — add a Copilot or Kilo item when execution on the user's machine is required.
5. Only after required checks pass should the stage be considered fully verified.

## Current queue summary

| ID | Stage | Verification | Status |
|---|---|---|---|
| EV-001 | 0–1 | Mój dzień UI/UX | PENDING |
| EV-002 | 0–1 | Training execution E2E | PENDING |
| EV-003 | 2 | Progress dashboard UI/UX | PENDING |
| EV-004 | 2 | Progress data semantics | PENDING |
| EV-005 | 2 | Progress exercise drill-down | PENDING |
| EV-006 | 2 | Trends/records/consistency/history | PENDING |
| EV-007 | 2 | Main-shell Progress navigation | PENDING |
| EV-008 | 2+ | Local automated regression | PENDING |


## Deferred verification note — 2026-10-03

The user is currently unable to run external verification prompts. Do not block implementation on this. EV-001 through EV-008 remain **PENDING** and must be executed later when the user has access to Antygravity/Copilot/Kilo. Generate the copy-paste prompts from the scopes above at that time. Do not mark these checks PASS based on static review alone.

Implementation may continue to subsequent stages while these checks remain pending, provided each new stage records its own required external verification items here.


## EV-009 — Stage 3 Goals API + Metrics + Progress
**Status:** PENDING  
**Owner:** Antygravity / local test runner  
**Scope:**
- authenticated Goal CRUD through /app/goals
- create/edit/archive lifecycle
- validation of goal type, dates, metric and target
- second-user IDOR isolation
- /app/goals/metrics supported metric catalog
- completed training data drives Goal Progress
- active/cancelled sessions and incomplete sets must not contribute
- exercise-specific goals honor metadata.exercise_key
- progress %, remaining, trend, deadline and on-track semantics
- empty/no-metric goal behavior
- malformed IDs/payloads and repeated update/delete behavior
- responsive UI/API behavior once Goals UX is added in Stage 3E
**Evidence required:** exact commands, exit codes, API/browser screenshots where applicable, test data, discrepancies. Do not mark PASS from static inspection alone.
