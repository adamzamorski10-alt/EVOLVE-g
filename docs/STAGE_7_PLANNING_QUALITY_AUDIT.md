# Stage 7 — Planning Quality Audit and Closure

## Scope
Stage 7 audited the deterministic planner across profile, assessment, recovery, nutrition, sport, performance, equipment, avoidance and time/frequency inputs.

## Audit matrix

| Input | Stored | Validated | Consumed | Changes plan | Tested | Priority |
|---|---|---|---|---|---|---|
| Goal | yes | yes | yes | yes | existing | P1 |
| Frequency / sessions per week | yes | yes | yes | yes | yes | PASS |
| Training focus | yes | yes | yes | yes | yes | PASS |
| Improvement areas | yes | yes | yes | yes | yes | PASS |
| Equipment | yes | yes | yes | yes | yes | PASS |
| Avoid exercises | yes | yes | yes | yes | yes | PASS |
| Sport focus | yes | yes | yes | yes | yes | PASS |
| Sport specialization | yes | yes | yes | yes | yes | PASS |
| Sport training days | yes | yes | yes | yes | yes | PASS |
| Training level | yes | yes | yes | yes | partial effect | P2 |
| Recovery score | yes | yes | yes | yes | yes | PASS |
| Basketball level | yes | yes | no | no | no | P2 |
| Shooting % | yes | yes | yes | yes | yes | PASS |
| Free throw % | yes | yes | yes | yes | yes | PASS |
| Sprint 30 m | yes | yes | yes | yes | yes | PASS |
| Vertical jump | yes | yes | yes | yes | yes | PASS |
| Availability hours | yes | yes | yes | yes | partial effect | P1 |
| Preferred foods | yes | yes | yes | yes | existing/extended | PASS |
| Avoid foods | yes | yes | yes | yes | extended | PASS |
| Allergies | yes | yes | previously not consumed safely | now filtered | new | P0 fixed |
| Meals per day | yes | yes | previously ignored | now changes meal slots | new | P1 fixed |
| Injuries | yes | yes | not safely mappable | not changed | — | P0/P1 deferred to dedicated safety design |
| Recovery response | yes | yes | through effective plan layer | yes | Stage 6 gate | PASS |

## Findings closed in Stage 7D

### P0 — Food constraint fallback
The planner could filter all catalog meals and then fall back to the original catalog, potentially reintroducing a forbidden food. This was unsafe for explicit food restrictions.

**Fix:** filtering is now performed before preference selection and forbidden items are never reintroduced. If no catalog item can be proven safe, the planner emits an explicit blocked placeholder instead of guessing.

### P1 — meals_per_day was ignored
The planner always emitted five meal slots regardless of the user's configured meal count.

**Fix:** canonical deterministic mapping:
- 3 → breakfast, lunch, dinner
- 4 → breakfast, snack 1, lunch, dinner
- 5+ → all five canonical slots

### P1 — restrictive exercise fallback
When equipment/avoidance constraints removed all exercises, the planner could inject a generic Push-up fallback that itself could violate an explicit avoidance rule.

**Fix:** no unsafe fallback. The planner returns an empty workout rather than silently bypassing explicit restrictions.

### P1 — availability hours
The existing planner uses availability to bound exercise count. It does not yet estimate exact session duration. This remains a bounded limitation and is deferred until the training adaptation loop can use actual duration/performance evidence.

## Intentionally deferred

- Basketball level is currently stored but not independently used. Adding another heuristic without a validated exercise/drill mapping would add complexity without enough quality benefit.
- Injuries require a dedicated safety model. Free-text injury strings must not be converted into simplistic body-part keyword exclusions because that could create false reassurance. Until that model exists, injury-aware planning must not claim medical personalization.
- Exact workout-duration optimization is deferred to the training execution/adaptation stage.

## Stage 7 outcome

The planner now has explicit deterministic behavior for the high-value MVP inputs and does not silently violate explicit food, meal-count, equipment or exercise-avoidance constraints.

Next stage: **Stage 8 — Training Adaptation Loop**:
PLAN → TRAIN → MEASURE → EVALUATE → ADAPT → NEW PLAN.
