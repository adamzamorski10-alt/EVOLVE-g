# Stage 9 — Goals ↔ Training ↔ Progress Discovery

## Objective
Close the existing separation between Goals, completed Training execution, and Progress so the system can answer one deterministic question:

**Given the user's active goals and actual training history, what is the current goal state and what training evidence supports it?**

Stage 9 should not yet become a general Decision Engine. It should create a canonical, deterministic Goals ↔ Training ↔ Progress domain boundary that later stages can consume.

## Existing foundations

### Goals
- `GoalDB` is user-owned and has lifecycle states: active/completed/cancelled/archived.
- Goals support metric-driven progress.
- Supported metrics:
  - `best_weight_kg`
  - `best_reps_at_best_weight`
  - `total_volume_kg`
  - `sessions`
  - `training_days`
  - `average_rpe`
- `GET /app/goals/{goal_id}/progress` already calculates cumulative metric history from completed owned training sessions.
- Goal progress already ignores cancelled/non-completed execution and foreign-user execution.

### Training
- Completed training sessions contain immutable planned snapshots.
- Completed set results are owned by the session/user and carry actual reps, weight and RPE.
- Stage 8 provides deterministic Evaluation → Adaptation → Next Effective Plan.
- Adaptive revisions are audited and user-scoped.

### Progress
- Training progress already exposes exercise-level historical aggregates.
- Goal metric history and training progress intentionally consume completed execution evidence.

## Architectural gap
The existing pieces are individually correct, but there is no canonical cross-domain read model that joins:

**active goal → goal metric → supporting training evidence → current progress state → training trend**

without forcing clients to independently reconstruct these relationships.

## Stage 9 boundary

Stage 9 should introduce a pure/read-only deterministic domain service first.

Recommended contract:

`build_goal_training_state(user, goal, completed execution)`

Output should contain:
- goal identity/status/type/title
- metric definition
- baseline/target/current value
- progress percentage / remaining / on-track
- trend
- target/deadline information
- supporting session IDs
- latest supporting training date
- evidence count
- sufficient-data flag
- deterministic reason codes

## Rules

1. Only authenticated user's own goals and training execution may contribute.
2. Only completed sessions and completed sets count as training evidence.
3. Cancelled/incomplete sessions never contribute.
4. No plan mutation.
5. No adaptive-plan mutation.
6. No goal lifecycle mutation.
7. Missing evidence must be represented explicitly, never inferred as progress.
8. Goal metric semantics remain deterministic and reuse existing metric definitions.
9. Stage 9 must not duplicate Stage 8 evaluation/adaptation rules.
10. A later Decision Engine may consume this state, but Stage 9 itself remains read-only.

## Recommended implementation sequence

### 9A — Cross-domain discovery + canonical contract
Define the exact goal-training state schema and ownership/data-source rules.

### 9B — Pure Goal ↔ Training state builder
Extract/reuse metric snapshot logic without changing existing API semantics.

### 9C — Read-only API
Expose a user-scoped endpoint for all active goals or one goal, backed by the canonical builder.

### 9D — Progress/trend integration
Add deterministic cross-domain evidence and trend information without changing existing training progression behavior.

### 9E — Security + regression gate
Ownership, foreign execution, cancelled sessions, missing data, metric edge cases, and consistency against existing Goal Progress API.

### 9F — Final verification
Full current regression + migration integrity + hostile ownership audit.

## Explicit non-goals
- No AI.
- No automatic goal rewriting.
- No automatic goal completion.
- No new adaptive algorithm.
- No Decision Engine yet.
- No UI redesign before the domain/API contract is verified.

## Stage gate
Do not begin 9B implementation until the 9A contract is reviewed against the existing Goals and Training/Progress behavior.
