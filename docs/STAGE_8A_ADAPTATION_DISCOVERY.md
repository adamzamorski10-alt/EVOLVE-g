# Stage 8A — Training Adaptation Loop Discovery

## Scope
Discovery of the existing deterministic training execution, measurement, progress, progression and adaptive-plan infrastructure before implementing Stage 8.

## Current flow
PLAN → TRAIN → MEASURE → ANALYZE/PROGRESS → ADAPTIVE PLAN → EFFECTIVE PLAN

| Area | Current state | Evidence |
|---|---|---|
| Planned workout | Present | app/plan/deterministic.py generates weekly plans with per-exercise sets/reps/weight |
| Effective plan | Present | app/training/routes.py::_effective_plan() resolves base/adaptive plan and applies transient recovery constraint |
| Session snapshot | Present | POST /app/training/sessions/start stores an immutable planned snapshot |
| Set execution | Present | POST /app/training/sessions/{id}/sets validates exercise ownership against snapshot |
| Completion | Present | POST /app/training/sessions/{id}/complete atomically completes session and creates ExerciseResultDB records |
| Execution provenance | Present | ExerciseResultDB.source_session_id/source_exercise_key link results to the exact session snapshot |
| Progress aggregates | Present | history, consistency, exercise progress, trends and records endpoints |
| Recovery constraint | Present | effective plan applies bounded 25%/50% transient volume reduction |
| Adaptive plan persistence | Present | AdaptivePlanRevisionDB is resolved by _effective_plan() |
| Evaluation boundary | Missing/fragmented | no current dedicated pure Result → Evaluation layer |
| Result → next-plan adaptation | Not yet closed | existing persistence/resolution can support it, but the deterministic evaluation contract should be established first |

## Key architectural finding
The system has enough raw execution data to close the next loop, but evaluation should become a pure, deterministic domain layer instead of embedding decision rules directly inside HTTP routes.

Stage 8B therefore introduces:
completed execution → deterministic evaluation → structured decision

without mutating a plan.

## Safety constraints for Stage 8
1. Evaluation is read-only.
2. Only authenticated/owned training sessions can be evaluated.
3. Only completed sets from the session snapshot are used.
4. Missing data produces insufficient_data, never an optimistic progression.
5. High effort and incomplete execution must not trigger progression.
6. Evaluation does not directly persist or apply an adaptive plan.
7. Stage 8C will consume this contract to generate bounded adaptations.
8. Recovery remains a separate transient safety constraint and is not overwritten by training evaluation.

## Stage 8B contract
Per exercise:
- progress — planned execution achieved and effort is acceptable.
- maintain — enough execution exists, but effort/reps do not justify progression.
- reduce — meaningful under-completion indicates the target was too demanding.
- insufficient_data — no reliable completed-set evidence.

Current conservative thresholds:
- low completion: < 80% of planned sets
- high average RPE: > 8
- below-target average reps: < planned reps

Precedence:
insufficient_data → reduce → maintain → progress

The evaluation response is diagnostic and carries reason codes plus measured values. It does not modify the stored plan.