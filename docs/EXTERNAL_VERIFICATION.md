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
  1. Open the training dashboard / Postępy training area.
  2. Verify progress summary cards render correctly: Sesje, Serie, Wolumen, Śr. wykonania.
  3. Verify existing adaptive preview and session history still render and remain usable.
  4. Verify loading, empty-data, and populated-data states.
  5. Verify values are legible and layout remains usable on narrow/mobile viewport.
  6. Verify no duplicate requests or visibly stale data after navigating away and back.
- Evidence required: screenshots for populated and empty states if available, plus PASS/FAIL notes.

### EV-004 — Progress data semantics with real user data
- Status: PENDING
- Verifier: Antygravity
- Type: browser data correctness
- Scope:
  1. Use a user/account with at least one completed training session.
  2. Confirm progress includes completed sets only.
  3. Confirm incomplete sets do not inflate set count or volume.
  4. Confirm active/cancelled sessions do not appear as completed progress.
  5. Confirm a second user/account cannot see another user's progress, if a safe test account/environment is available.
  6. Confirm exercise summaries and recent sessions are internally consistent with visible training history.
- Evidence required: PASS/FAIL and the test data/scenario used.

## Future checks to add as implementation progresses

### EV-005 — Progress exercise drill-down
- Status: PENDING
- Verifier: Antygravity
- Add detailed steps when exercise-level progress UI is implemented.

### EV-006 — Trends / records / consistency
- Status: PENDING
- Verifier: Antygravity
- Add detailed steps when these features are implemented.

### EV-007 — Main-shell Progress navigation
- Status: PENDING
- Verifier: Antygravity
- Add detailed steps when Progress becomes a first-class shell section.

### EV-008 — Local automated regression gate
- Status: PENDING
- Verifier: Copilot VS Code or Kilo Code
- Type: local command execution
- Scope:
  - run the project's expected test suite,
  - run migration checks,
  - report exact failing tests without weakening/deleting them,
  - distinguish pre-existing failures from regressions introduced by the current branch.
- Exact commands must be generated from the repository's current tooling when the user is available; do not invent commands in advance.

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
| EV-005 | Future | Exercise progress drill-down | PENDING |
| EV-006 | Future | Trends/records/consistency | PENDING |
| EV-007 | Future | Main-shell Progress | PENDING |
| EV-008 | 0–2+ | Local automated regression | PENDING |
