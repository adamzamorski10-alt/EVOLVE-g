# Stage 20 — Core Loop Integration Audit

Status: continued hostile integration audit on the isolated Stage 20 branch. No merge to main. External browser verification remains open. Legacy regression remains informational and non-blocking.

## Objective

Verify the complete non-AI EVOLVE loop using one consistent, user-scoped source of truth:

Profile and initial assessment → deterministic plan → safe training execution → canonical completed-training history → progress evidence → planning continuity/adaptation → goals and TODAY decision.

Stage 20 is an integration audit, not a feature expansion. Preserve deterministic behavior, read-only decision/evidence layers, execution safety, and `insufficient_data` when evidence is inadequate.

## Confirmed architecture from current source

- `app/plan/deterministic.py` generates a weekly plan from profile, assessment, and optional canonical progress evidence.
- `app/training/routes.py` owns execution endpoints and resolves the base/effective adaptive plan.
- `app/training/history.py` reads completed `TrainingSessionDB` records and associates sets using both `session_id` and `user_id`.
- `app/training/progress.py` compares recent completed observations and emits explicit insufficient-data state when fewer than two observations exist.
- `app/plan/progress_evidence.py` translates canonical progress evidence into a read-only planning input.
- `app/plan/rolling.py` expands a weekly template into a date-scoped horizon and does not decide whether a session may start.
- `app/goals/training_state.py` joins goal definitions with supplied training snapshots without reading or mutating the database.
- `/app/today` aggregates decision, evidence, workout readiness, and safety state; tests assert that it is read-only and can block session start.
- Existing tests cover plan provenance staleness after availability changes, user-scoped history, deterministic planning evidence, missing goal evidence, and TODAY safety behavior.

## Stage 20A — hostile integration checks

1. **Execution → history**
   - Only completed canonical sessions count as completed history.
   - Active, incomplete, duplicate, or foreign-user set records cannot inflate another user's history or progress.
   - History data-quality flags must match the evidence actually available, not merely the presence of any set row.

2. **History → progress**
   - Progress uses completed sets with finite, meaningful values.
   - Missing, malformed, non-finite, or contradictory observations must not become a positive/negative progress conclusion.
   - Insufficient evidence must remain explicitly insufficient.

3. **Progress → planning**
   - Progress is continuity evidence only; it cannot inject decisions, recovery overrides, permissions, or direct plan mutations.
   - Identical inputs produce identical plan decisions.
   - Changed source evidence or scheduling constraints must correctly invalidate stale provenance.

4. **Training → goals**
   - Goal progress uses completed, user-scoped evidence only.
   - Missing or malformed evidence cannot fabricate a current value, trend, or on-track result.
   - Goal state building remains read-only and deterministic.

5. **TODAY / effective plan → execution**
   - Decision and recovery safety overrides must agree with the effective-plan/session-start contract.
   - A read-only summary cannot independently authorize execution.
   - Stale plans and unavailable sessions must not bypass execution gates.

6. **Rolling plan consistency**
   - Dated sessions, rest days, completed history, effective adaptive plan, and scheduling diagnostics must remain semantically consistent.
   - A rolling horizon is a projection, not a second source of truth.

## Stage 20A — findings and fixes in progress

Verified from code and covered by targeted regression tests:

- **History quality flag:** history previously marked `sufficient_data` when any set row existed, including all-incomplete sets. It now requires at least one completed set.
- **Malformed Goal evidence:** the pure goal-state builder previously called `float()` on supplied values without validating the item, value, or date. It now skips malformed records, non-finite values, invalid dates, and boolean-as-number inputs; if nothing usable remains, it reports insufficient training evidence.
- **Progress set counts:** progress evidence previously counted all completed rows in an observation even when some rows had malformed/non-finite values. It now ignores malformed history/exercise/set containers and counts only valid completed set observations.
- **Metric-specific Goal snapshots:** cumulative Goal snapshots previously could reuse an old metric value on a later session with no fresh value for that metric. Snapshot generation now requires metric-specific evidence in the current session (e.g. an RPE for an average-RPE snapshot, or actual weight for a best-weight snapshot) and rejects non-finite/invalid numeric values.

Remaining Stage 20A verification:

- `/app/plan/rolling` takes diagnostics from the effective plan's `_planner` metadata. Confirm with an integration test that applying a valid adaptive revision preserves scheduling diagnostics.
- Continue checking the full execution → history → progress → goals → TODAY path for cross-user isolation, incomplete-session leakage, stale-plan safety, and agreement between read-only decisions and execution gates.

These changes are on the isolated Stage 20 branch and remain subject to the final CI gate.

## Required acceptance gate

- Targeted tests cover the five integration boundaries above and all newly fixed edge cases.
- Full current EVOLVE regression passes.
- Alembic clean-database integrity passes.
- Legacy regression remains informational and must be reported transparently.
- No changes are merged into `main` without separate review.
- No AI Coach/AI Manager integration is introduced in Stage 20.

## Stage 20B — adaptive rolling-diagnostics integration test

Added `test_rolling_plan_preserves_schedule_diagnostics_after_adaptation` in `test_training_next_effective_plan.py`.

The test seeds canonical planner diagnostics into a base plan, completes a session, applies the adaptive revision, and verifies both the persisted adaptive plan and `/app/plan/rolling` retain the exact diagnostics. It also asserts the rolling endpoint identifies the applied plan as adaptive, guarding against the UI silently losing the weekly-target explanation when adaptation is active.

### Verified CI checkpoint

- Commit: `47d713e02ede2085b584198810ced63510f44e94`
- Workflow run #621: [GitHub Actions](https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/37966480624)
- Current EVOLVE regression: **304 passed, 7 warnings**
- Alembic clean-database integrity: **PASS**
- Legacy regression: **FAIL, informational / non-blocking**, as configured in the workflow
- Overall workflow: **SUCCESS**

This closes the specific adaptive rolling-diagnostics preservation check. The broader Stage 20 audit remains open until remaining integration boundaries and the final current-SHA gate are reviewed.

## Stage 20C — TODAY decision validation

The TODAY semantic mapper previously treated an unknown decision value as the default train-as-planned state. The execution endpoint independently enforced its safety gate, but the presentation contract could still become misleading if fed malformed or mismatched decision data.

The mapper now accepts only canonical Decision Engine values. Unknown strings, nulls, booleans, and other malformed values map to `insufficient_data`, block the TODAY start action, mark data quality insufficient, and emit `INVALID_DECISION_FAIL_CLOSED`. Hostile unit coverage verifies this even when the training payload otherwise reports that a workout can start. This does not replace the independent execution gate.

Verification: [CI run #624](https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/37972087577) passed the current regression (**305 passed, 7 warnings**) and Alembic integrity. The legacy regression remains a non-blocking informational failure. Commits: `2cc14cf873e3cfd40e648c58d178ced1c93c7820` and `5a27fb8694e8bd42cf32f34b3b654194e94f6ad4`.

## Stage 20D — TODAY and execution-gate consistency

The integration audit found that TODAY treated the canonical `insufficient_data` decision as a hard safety block, while the independent execution gate permits it. The execution contract explicitly distinguishes missing evidence for optimization from a contraindication to training. This caused the read-only summary to disagree with the actual session-start endpoint.

TODAY now preserves the `insufficient_data` state and insufficient data-quality marker, but permits starting an available planned workout when the canonical execution gate allows it. It does not imply that adaptation or progression is justified. Invalid or malformed decision values remain fail-closed: TODAY blocks start and reports `INVALID_DECISION_FAIL_CLOSED`.

Added:
- A semantic unit test that distinguishes canonical insufficient evidence from an invalid decision.
- An end-to-end integration test that supplies the same canonical `insufficient_data` decision to TODAY and the execution route, then verifies that both permit the planned session consistently.

This change aligns presentation with the existing execution policy rather than silently changing the safety policy itself. The Stage 20 final gate must still verify the latest branch SHA; Stage 20 remains open until that gate and the remaining audit review are complete.

## Stage 20E — stale-plan execution boundary

Added an integration regression that gives the current weekly plan provenance pointing to a no-longer-current assessment. It verifies that the training-today endpoint exposes `plan_stale=true` and `can_start=false`, the session-start endpoint rejects the stale plan with HTTP 409, and no active session is created. This complements the existing plan-readiness stale-state tests by exercising the actual execution boundary.

The test is included in the next current-SHA CI gate. Stage 20 remains open until the gate passes and the remaining integration review is complete.

## Stage 20 implementation acceptance checkpoint (historical; hostile audit continued afterward)

**Status at that checkpoint: implementation gate passed on `stage-20-core-loop-integration-audit`; this did not close the later hostile audit or external browser verification.**

Final verified commit before this documentation checkpoint: `c83f1b4fda4f8dadf3e0a40cfe97d007568bf979`.

- CI run #631: [GitHub Actions](https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/37972958939)
- Current EVOLVE regression: **307 passed, 7 warnings**
- Alembic clean-database integrity: **PASS**
- Legacy regression: **FAIL, informational / non-blocking**
- The Stage 20D consistency test confirms TODAY and the independent execution endpoint agree for canonical `insufficient_data`.
- The Stage 20E test confirms stale plans remain blocked at the execution boundary and do not create an active session.
- Earlier gates cover malformed TODAY decisions, adaptive rolling diagnostics, completed-history quality, malformed progress evidence, and metric-specific Goal snapshots.
- No Stage 20 changes have been merged into `main`; the branch remains isolated pending a separate integration review.
- No AI Coach/AI Manager integration was introduced.

The Stage 20 acceptance gate is complete on this branch. The informational legacy regression failure remains visible and is not represented as passing.


## Stage 20F — recovery signal parsing hardening

The recovery signal normalizer now handles malformed numeric input defensively. Conversion failures (TypeError, ValueError, and OverflowError), non-finite values (NaN and infinities), and values outside the signal's accepted range are ignored rather than raising or contributing to recovery scoring.

Added `test_recovery_ignores_malformed_and_non_finite_signals`, which mixes one valid sleep-quality signal with malformed sleep hours and non-finite energy, stress, and fatigue values. It verifies that only the valid signal contributes, and that the resulting evidence remains `insufficient_data` with no recovery constraint.

Verification on current code/test SHA `9da1c4614558908c64671cea2d225b07e292d567`:
- CI run #634: [GitHub Actions](https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/37974775621) — overall **SUCCESS**.
- Current EVOLVE regression: **PASS**.
- Alembic clean-database integrity: **PASS**.
- Legacy regression: **FAIL, informational / non-blocking**.

This closes the targeted malformed/non-finite recovery-signal check. It does not replace the pending external browser verification documented in `docs/EXTERNAL_VERIFICATION.md`, nor does it authorize merging Stage 20 into `main`.


## Stage 20G — Decision Engine execution-gate hostile input hardening

The execution permission helper now fails closed when the decision payload is not a dictionary, the `decision` field is absent, or the value is not a string in the canonical decision set. This avoids exceptions from unhashable malformed values and prevents a missing/null decision from being silently converted into `insufficient_data`.

A canonical explicit `insufficient_data` decision remains execution-eligible when other execution checks pass; this represents lack of optimization evidence, not a safety contraindication. The canonical `recover` decision remains blocked.

Added hostile tests for missing/null/boolean/dict/list/unknown decisions and coverage for every canonical decision state. The prior expectation that an empty dictionary was allowed was updated to match the fail-closed contract.

Verification on code/test SHA `807395601f8b4a7e7465f72a6b792447dacc40f1`:
- CI run #638: [GitHub Actions](https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/37977890035) — overall **SUCCESS**.
- Current EVOLVE regression: **310 passed, 7 warnings**.
- Alembic clean-database integrity: **PASS**.
- Legacy regression: **FAIL, informational / non-blocking**.

This closes the targeted malformed execution-decision input check. It does not mark external browser verification complete and does not authorize merging Stage 20 into `main`.


## Stage 20H — resumed-session set ownership hardening

The hostile review found two resume paths that loaded set rows using the active session ID without also filtering by the authenticated user's ID: the normal resume path and the database-conflict recovery path. Although session IDs are unique in normal operation, this was inconsistent with the repository's explicit user-scoped data-access contract and could expose an incorrectly associated foreign-user row if the database contained inconsistent ownership data.

Both queries now require `TrainingSetResultDB.user_id == user.id`.

Added `test_resuming_session_serializes_only_sets_owned_by_session_user`, which deliberately seeds a foreign-user set against an owned session and verifies that the resume response serializes only the owner's set.

Verification for test commit `495710ccf5d2d3740c03f99b628e12482f75ba98`:
- CI run #641: [GitHub Actions](https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/37979372184)
- Current EVOLVE regression: **311 passed, 7 warnings**
- Alembic clean-database integrity: **PASS**
- Legacy regression: **FAIL, informational / non-blocking**
- The full regression and migration jobs passed; the workflow's informational legacy job remains non-blocking.

Stage 20 remains isolated and is not merged into `main`. External browser verification is still pending; CI does not substitute for that check.


## Stage 20I — safe resume and close when recovery blocks execution

The active-session recovery path exposed a UX/safety gap: the start endpoint rejected every resume when the current Decision Engine result was `recover`, so the user could not reopen the active session UI to close it, even though set logging was correctly blocked and the completion endpoint is intentionally allowed to persist already-completed work.

The resume path now checks for an existing active session before rejecting a new session start. If an active session exists, it returns that owned session with `execution_blocked` and `execution_block_reason` metadata when the current decision disallows exercise. The session UI displays a recovery warning, disables set editing/logging controls, and keeps the completion action available for previously completed sets. If there is no active session, a recovery-blocked user still cannot start a new one. The set-logging API remains independently guarded by the canonical decision gate.

Regression coverage:
- An active session can be resumed in close-only mode when recovery changes to `recover`.
- Attempting to log another set remains blocked with `TRAINING_EXECUTION_BLOCKED`.
- A session with previously completed work can be safely completed and materialize its result despite a newly active recovery block.
- The UI disables editing controls when the resumed session reports `execution_blocked`.

CI for test commit `33a0d3697c2107966ef664b595b70118e649fa6b`:
- [GitHub Actions run #646](https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/37983041303): overall **SUCCESS**
- Current EVOLVE regression: **311 passed, 7 warnings**
- Alembic clean-database integrity: **PASS**
- Legacy regression: **FAIL, informational / non-blocking**

The preceding implementation-only commit's run #645 failed because the then-current test still asserted the old 409-on-resume behavior; the test was updated to the intended safe-close-only contract and run #646 passed. Stage 20 remains unmerged. External browser verification remains open, particularly confirming that the disabled controls and safe completion UX behave correctly in a real browser.



## Stage 20J — atomic set-write gate against session completion

A review of the session lifecycle found a potential interleaving: set logging checked the ORM session status early, while completion independently changed the database status to `completed`. A set request could therefore pass the early check and attempt to persist after completion had already claimed the session. This was a code-level race hypothesis; it was not represented as a previously reproduced production failure.

The set endpoint now performs a conditional database update scoped to session ID, authenticated user ID, and `status == "active"` before mutating the set result. The write claim and set mutation share the same transaction. On databases with row-level locking, the conditional update holds the row lock through commit; on SQLite it participates in the database's write-lock semantics. If completion wins first, the conditional update affects no row and set logging returns HTTP 409. The integrity-conflict retry path reacquires the same gate after rollback, so it cannot bypass session closure.

Added `test_set_write_rechecks_session_status_after_initial_read`, a deterministic interleaving test that marks the session completed after the endpoint's initial status check and before the conditional claim, then verifies the set write is rejected and no set row is persisted.

Verification status at documentation time:
- Code commit: `261b98e1773eee519591f01654b457e26012fd42`
- Test commit: `5b64ec1b0a4b78876c5e788eabd91157f7ad17a9`
- The GitHub connector did not return workflow runs for the test commit through its PR-only workflow lookup. A successful CI result has **not** been confirmed here; test execution and workflow status remain pending verification.
- This change does not close external browser verification and does not authorize merging Stage 20 into `main`.

## Stage 20K — serialize concurrent session starts

A further code review identified a possible check-then-insert race in `/sessions/start`: two requests could both observe no active session for the user/date and then insert separate active sessions. This is a code-level concurrency risk, not a confirmed production incident.

The start route now updates the authenticated user's `updated_at` row before querying for an active session. The write lock is held in the same transaction as the active-session recheck and any new-session insert. On databases with row-level locks, competing starts for the same user serialize on the user row; after the first request commits, the next request re-reads the active session and resumes it instead of creating another. SQLite uses its database write-lock semantics for the same write claim.

This is intentionally a narrow application-level serialization change and does not add a migration or alter historical data. If the database rejects the write claim (for example, due to concurrent SQLite write-lock contention), the route rolls back and returns HTTP 409 rather than continuing without the claim or leaking a database exception. A focused regression test simulates this lock-claim failure and verifies that no active session is created. This test validates the fail-closed path, not true parallel-request serialization; a dedicated parallel-request integration test remains desirable before treating the race as fully closed. Verify the full current regression and clean-database migration jobs for the exact final commit.

Stage 20 remains unmerged. External browser verification remains open.
