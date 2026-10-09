# Stage 20 — Core Loop Integration Audit

Status: discovery complete; implementation and acceptance gates are not yet complete.

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
