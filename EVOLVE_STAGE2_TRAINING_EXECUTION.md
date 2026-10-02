# EVOLVE Stage 2 — Training Execution Vertical Slice

## Objective

Turn the existing weekly plan into a real, resumable training execution flow without rewriting the current frontend or legacy plan generator.

Target loop:

**PLAN → START → EXECUTE → LOG → COMPLETE → RESULT**

## Current baseline

The existing implementation already provides:
- `GET /app/day/today` — materializes planned workouts into the daily log.
- `POST /app/day/item/toggle` — marks a workout item complete and currently creates a single `ExerciseResultDB` row.
- `POST /app/exercise-result` — records an aggregate exercise result.
- `GET /app/exercise-history` and `GET /app/progression-summary` — consume historical exercise results.

The limitation is that execution is currently represented by a checkbox plus one aggregate result. It cannot reliably represent a started session, partial progress, individual sets, pause/resume, planned-vs-actual comparison, or a final session result.

## Stage 2 design

### 1. Training session

Introduce a dedicated `training_sessions` table with:
- authenticated `user_id`
- session date
- status: `active | completed | abandoned`
- start/completion timestamps
- immutable planned-workout snapshot JSON
- final session RPE
- optional notes
- created/updated timestamps

The plan snapshot is copied when the session starts so later plan changes cannot silently rewrite an in-progress or historical session.

### 2. Actual set results

Introduce a dedicated `training_set_results` table linked to the session with:
- exercise key/index
- exercise name snapshot
- set number
- planned reps/load
- actual reps/load
- actual RPE
- completion state
- optional note
- timestamp

Ownership is always resolved through the authenticated principal and canonical user; client-supplied user IDs are never trusted.

### 3. API contract

Minimum endpoints:
- `POST /app/training/sessions/start`
- `GET /app/training/sessions/{session_id}`
- `POST /app/training/sessions/{session_id}/sets`
- `POST /app/training/sessions/{session_id}/complete`

Rules:
- starting a session without a usable planned workout returns a clear 404/422 rather than manufacturing a plan;
- an active session for the same user/date is resumed rather than duplicated;
- every session/set lookup is scoped to the authenticated user;
- set numbers are validated and duplicate set writes are idempotent where practical;
- completion is rejected for an empty session;
- completed sessions are immutable except for explicitly supported result metadata;
- future session dates are rejected;
- the existing `ExerciseResultDB` remains the compatibility/progression aggregate and is populated from actual completed session data, not from checkbox clicks.

### 4. Legacy interaction

Do not remove the existing `/app/day/*` endpoints yet.

During Stage 2:
- existing Today/day tracking remains compatible;
- the new training session is the authoritative execution record;
- automatic `ExerciseResultDB` creation from `day/item/toggle` must be prevented for executions that use the new session flow, avoiding duplicate history;
- legacy behavior remains available until the new UI path is verified.

### 5. Testing gate

Focused tests must cover:
1. authenticated user can start a session from their own plan;
2. another user's session cannot be read or mutated by ID;
3. planned snapshot survives later plan changes;
4. sets persist with planned and actual values;
5. resume returns the same active session;
6. empty completion is rejected;
7. completed session produces progression-compatible exercise results exactly once;
8. future-date and invalid-set inputs are rejected;
9. legacy day logging does not create duplicate results when the new execution flow is used.

Stage gate requires focused tests plus relevant existing training/plan regression tests before frontend migration.

## Explicit non-goals

- no frontend framework rewrite;
- no AI/autoregulation implementation;
- no complete legacy deletion;
- no mass database normalization;
- no multiple-sport execution redesign;
- no advanced analytics dashboard.

## Checkpoint

**DONE:** Stage 1 product direction, first-pass audit, current-tree database-artifact cleanup, ignore rules.

**CURRENT:** Stage 2 execution contract and persistence boundary defined from the real existing code.

**NEXT:** Implement the backend vertical slice, add focused tests, then connect the existing Today/Training UI to the new contract.
