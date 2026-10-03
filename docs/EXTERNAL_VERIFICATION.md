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


## EV-010 — Stage 3E Goals UX
**Status:** PENDING  
**Owner:** Antygravity  
**Scope:**
- native Cele navigation in shared shell
- active/completed/archive states
- create/edit goal flow
- metric and target fields
- progress cards and detail view
- complete/archive actions
- empty and error states
- refresh/repeated navigation and stale-response behavior
- mobile/responsive layout
- authenticated user sees only owned goals
**Evidence required:** screenshots, test data, navigation/reload behavior, responsive check, discrepancies. Do not mark PASS from static review alone.


## EV-011 — Stage 3F Goal ↔ Progress Integration
**Status:** PENDING  
**Owner:** Antygravity / local test runner  
**Scope:**
- Goal Progress values match existing Training Progress for the same completed execution window
- Records/Trends/Exercise Progress semantics remain consistent
- cumulative metrics do not regress to last-session-only values
- active/cancelled sessions and incomplete sets never contribute
- exercise-specific goals only use the selected exercise
- cross-user isolation
- no duplicated or conflicting visible values in Goals vs Progress
- target, remaining, percentage, trend and on-track states remain deterministic
**Evidence required:** exact test commands and exit codes, API/browser evidence, representative real data, discrepancies. Do not mark PASS from static inspection alone.


## EV-012 — Stage 4A-4C Training UX
**Status:** PENDING  
**Scope:** end-to-end training start/resume/execution UI; plan snapshot; responsive set cards; actual reps/weight/RPE/notes; edit/re-save/idempotency; refresh/resume; duplicate clicks; cross-user isolation; completed-session lock; mobile layout; error/loading states.
**Evidence required:** browser/device walkthrough, screenshots or equivalent evidence, reload/resume test, repeated-save test, malformed input/error handling, and exact automated test results. Do not mark PASS from static inspection alone.


## EV-013 — Stage 4D-4F Rest, Flow, Completion and Final Audit
- Status: PENDING
- Scope: rest timer/skip, next exercise focus, partial execution, completion summary, Progress/History consistency, refresh/resume, repeated actions, mobile layout, security/ownership, focused tests, full regression and migration integrity.
- Evidence required: exact commands and exit codes plus browser/device evidence. Do not mark PASS from static inspection alone.


## EV-014 — Stage 5A Nutrition Foundation
- Status: PENDING
- Owner: Antygravity / local test runner
- Scope:
  - authenticated nutrition entry creation
  - structured calories/protein/carbs/fat/fiber/water persistence
  - today aggregation and target/remaining calculations
  - date-range history and 31-day bound
  - malformed/negative payload rejection
  - cross-user entry isolation and delete protection
  - repeated delete behavior
  - migration chain integrity (`evolve17goalmetrics -> evolve18nutrition`)
  - native shell/API integration once Dieta UX is introduced
- Evidence required: exact automated commands and exit codes, API/browser evidence where applicable, migration check output and discrepancies.
- Do not mark PASS from static inspection alone.



## EV-015 — Stage 5B Nutrition Adherence
- Status: PENDING
- Owner: local test runner / Antygravity
- Scope:
  - 1–28 day adherence window validation
  - only days with actual structured intake count toward adherence
  - deterministic calorie 90–110% rule
  - deterministic protein >=90% rule
  - daily ratios and rolling averages match stored entries
  - cross-user isolation
  - no silent classification of missing days as failures
  - native Dieta presentation once UX is introduced
- Evidence required: exact test commands and exit codes plus representative API/browser evidence.
- Do not mark PASS from static inspection alone.



## EV-016 — Stage 5C–5D Nutrition Response + Native Dieta
- Status: PENDING
- Scope:
  - response requires >=3 logged days
  - deterministic under/near/over target signals
  - protein signal
  - response never mutates profile targets
  - native Dieta shell and main navigation
  - today's totals and entries
  - authenticated add/delete
  - refresh/stale-response behavior
  - mobile layout and interaction
  - cross-user isolation
- Evidence required: focused tests with exit codes plus browser/mobile evidence.
- Do not mark PASS from static inspection alone.



## EV-017 — Stage 5E Nutrition Adaptation
- Status: PENDING
- Scope:
  - minimum 7 nutrition evidence days
  - minimum 2 completed training sessions in evidence window
  - deterministic preview
  - maximum ±100 kcal per application
  - absolute 1200–5000 kcal bounds
  - protein target remains unchanged
  - GET preview is non-mutating
  - explicit apply action only
  - optimistic concurrency conflict handling
  - adaptation audit persistence
  - native Dieta adaptation UX
  - cross-user isolation
  - repeated apply behavior
  - migration integrity `evolve18nutrition -> evolve19nutrition_adaptations`
- Evidence required: exact focused/full test commands and exit codes, migration execution, browser/mobile evidence, concurrency evidence.
- Do not mark PASS from static inspection alone.



### EV-018 — Full Stage 0–5 second-user isolation / release E2E

- Status: PENDING
- Owner: Antygravity + local test runner
- Purpose: independent verification that a second account can use the complete current EVOLVE without seeing, modifying or inheriting User A data.
- Setup:
  1. Create User A and User B independently.
  2. Give User A distinctive profile, assessment, goals, training execution, progress and nutrition/adaptation data.
  3. Give User B different data.
- Required checks:
  - login/logout/session switching
  - Profile ownership and update isolation
  - Assessment history/latest isolation
  - Plan readiness/generation isolation
  - Mój dzień and active-session isolation
  - Training session/set/completion/history isolation
  - Progress/trends/records/consistency/exercise drill-down isolation
  - Goal CRUD/progress/metrics isolation
  - Nutrition entries/today/adherence/response/adaptation isolation
  - cross-user direct-ID requests return 403/404 and never mutate the other account
  - repeated actions do not duplicate downstream records
  - refresh/new tab does not leak the previous account's UI state
  - logout clears the usable authenticated session
- Evidence required: exact test data, screenshots/network evidence where useful, PASS/FAIL for every module, and exact commands/exit codes for API/runtime checks.
- Do not mark PASS from static inspection alone.


### EV-019 — Stage 0–5 full integration / release gate

- Status: PENDING
- Owner: Antygravity + local test runner
- Purpose: verify the complete deterministic product loop on a clean runtime before Stage 6.
- Required flow:
  1. Register/login
  2. Complete Profile
  3. Complete Assessment
  4. Generate/readiness-check a plan
  5. Open Mój dzień and confirm the plan is represented there
  6. Start training
  7. Log, edit and re-save sets
  8. Complete training
  9. Confirm the result appears exactly once in Progress/History/Records
  10. Create a Goal tied to a supported metric
  11. Confirm Goal Progress reflects the completed training
  12. Add Nutrition entries
  13. Confirm Today → Adherence → Response
  14. Build sufficient evidence and confirm bounded Adaptation preview
  15. Apply adaptation once and confirm audit + updated target
  16. Repeat/refresh all relevant screens and verify deterministic state
- Negative checks:
  - malformed IDs and payloads
  - missing/invalid auth
  - cross-user direct-ID access
  - repeated clicks/submissions
  - incomplete/cancelled sessions excluded from analytics
  - preview endpoints are non-mutating
  - concurrent updates do not overwrite newer state
- Evidence required:
  - clean runtime/migration output
  - exact automated test command + exit code
  - browser screenshots or equivalent evidence for each native domain
  - final list of discovered defects and their disposition
- Gate rule: EV-019 remains PENDING until the complete flow has been executed externally. Static inspection and repository tests alone are insufficient.


## EV-018 — Stage 0–5 second-user isolation
- Status: PENDING
- Verifier: Antygravity + local runner
- Type: real runtime security verification
- Scope: create independent User A and User B; create profile/assessment/plan/training/results/goals/nutrition data for A; attempt direct-ID reads, edits, deletes and mutations from B; verify every cross-user action is rejected or returns not-found without leaking data.
- Evidence required: exact account scenarios, endpoints/screens tested, PASS/FAIL and any leakage found.

## EV-019 — Stage 0–5 full integration release gate
- Status: PENDING
- Verifier: Antygravity + local runner
- Type: full browser/runtime E2E
- Scope: Register/login → Profile → Assessment → Plan → Mój dzień → Training → Results → Progress → Goals → Nutrition → Adherence → Response → Adaptation. Verify refresh/resume, repeated actions, incomplete/cancelled exclusion, deterministic summaries and no duplicate downstream results.
- Evidence required: screenshots or equivalent browser evidence, exact automated test command/exit code, migration output, discovered defects and disposition.
- Gate rule: EV-019 remains PENDING until the complete flow is executed externally.
