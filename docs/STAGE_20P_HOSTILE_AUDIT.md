# Stage 20P — Hostile Audit of Training Transaction Safety

Date: 2026-10-10
Status: static/code-level review complete; backend-specific concurrency verification remains open.

## Scope reviewed

- `app/training/routes.py`: session start, set logging, and session completion.
- `app/models.py`: active-session partial unique index metadata.
- `alembic/versions/evolve21active_session_unique.py` and `evolve25_user_key_constraint_cleanup.py`.
- Existing hostile tests in `test_training_execution.py` and `test_training_set_validation.py`.
- Current Stage 0–5 regression, SQLite/PostgreSQL migration-integrity CI, and PostgreSQL route-level transaction-test results.

## Findings

### P20-1 — Session start has layered guards

- The start route claims a write/row lock on the authenticated user's row before rechecking today's active session.
- A partial unique index enforces at most one active session per `(user_id, session_date)` on supported SQLite/PostgreSQL backends.
- A failed lock claim fails closed; a uniqueness/commit conflict rolls back and attempts to resume the user's existing active session.
- Existing barrier-based test `test_start_session_serializes_concurrent_requests_to_at_most_one_active_session` checks concurrent start requests in the current SQLite test configuration.

Assessment: no new confirmed defect in the reviewed path. This is code review plus SQLite-backed test evidence, not proof of production behavior.

### P20-2 — Set writes revalidate session state at mutation time

- The set endpoint checks ownership and status early, then performs a conditional update scoped by session ID, user ID, and `status = 'active'` before mutating set results.
- The duplicate-set `IntegrityError` path rolls back and reacquires the same active-session claim before retrying.
- Existing deterministic test `test_set_write_rechecks_session_status_after_initial_read` verifies that a session completed between the initial read and write claim rejects the set with 409 and does not persist the set.

Assessment: no new confirmed defect in the reviewed path. Real concurrent behavior still needs backend-specific integration/browser verification.

### P20-3 — Completion and canonical result materialization

- Completion conditionally transitions only an owned active session to completed.
- The status transition and `ExerciseResultDB` materialization share a transaction; an empty-session validation failure rolls back the transition.
- Aggregation filters sets by both session ID and user ID, and existing provenance uniqueness/idempotency logic avoids duplicate session-derived results.
- Existing hostile test `test_completion_materializes_only_sets_owned_by_session_user` checks that foreign-owned set data linked to a session is not materialized into the owner's history.

Assessment: no new confirmed defect in the reviewed path.

### P20-4 — Database migration integrity

- Current-head CI passed the Stage 0–5 regression (CI run #730; 315 passed, 7 warnings).
- SQLite clean-database migration integrity passed, including `alembic current --check-heads`, `alembic check`, and the active-session partial unique index assertion.
- PostgreSQL 16 clean-database migration integrity passed the Alembic checks and verified the partial unique index definition. The latest PostgreSQL job also passed route-level transaction tests for concurrent session starts, set-write rejection after completion, and user-scoped completion materialization (CI run #730).
- Legacy regression remains an informational failure and is not counted as a passing gate.

Evidence:
- Earlier push CI: https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/38083454264
- Earlier PR CI: https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/38083457254
- Latest corrected CI including PostgreSQL route-level transaction tests: https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/38084825190

## Open risks / blockers

1. PostgreSQL CI route-level tests now pass for concurrent start serialization, set-vs-completion status recheck, and user-scoped completion materialization. This is controlled CI evidence, not proof of the deployed environment or a real browser flow.
2. The deployed Render database backend and deployed Alembic head/index are still unknown because the deployment environment has not been inspected.
3. EV-022 browser verification remains PENDING: real UI parallel starts, set write racing completion, refresh/resume consistency, cross-user isolation, observed HTTP statuses, and environment/backend evidence.
4. Legacy regression is still informationally red; preserve that distinction in reports.

## Decision

The static hostile review found no new confirmed defect in the three transaction paths reviewed. Stage 20 is **not ready to close or merge** until EV-022 is completed and the deployed backend is identified. Prefer adding PostgreSQL route-level concurrency coverage if PostgreSQL is the deployed backend or is a supported production backend.

## Stage 20R — Current-head re-review — 2026-10-10

Status: static re-review complete; external verification remains pending.

### Current code re-reviewed

- Re-read the current branch versions of `app/training/routes.py`, `app/models.py`, and `test_training_execution.py`.
- Session start performs a same-value update on the authenticated user's row before rechecking the active session; the partial unique index remains a second guard for supported SQLite/PostgreSQL backends.
- Set writes recheck `status = 'active'` with a user-scoped conditional update immediately before mutation; the duplicate-key recovery path reacquires the same guard after rollback.
- Completion conditionally transitions an owned active session and materializes canonical exercise results in the same transaction. Set aggregation is filtered by both session and authenticated user.
- The current PostgreSQL CI job exercises route-level concurrent-start, set-after-completion rejection, and user-scoped materialization tests.

### Current CI checkpoint

- Latest checked PR workflow #734: https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/38085139296
- Current Stage 0–5 regression: PASS.
- SQLite clean-database Alembic integrity: PASS.
- PostgreSQL 16 migration integrity plus route-level transaction tests: PASS.
- Legacy regression: informational FAIL; not counted as a passing required gate.

### Assessment and remaining blockers

- This re-review found no new confirmed defect in the inspected transaction paths. It is not a claim that all application behavior is defect-free.
- Browser-level two-tab races, refresh/resume/history consistency, and cross-user direct-ID behavior have not been independently observed in a real browser; EV-022 remains PENDING.
- The actual deployed database backend, deployed Alembic head, and deployed `uq_training_active_user_day` definition remain unverified.
- Keep PR #50 as Draft and do not merge until deployment evidence and EV-022 are recorded, then run the final required CI gates on the resulting head.
