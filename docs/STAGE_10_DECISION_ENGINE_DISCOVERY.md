# Stage 10 — Decision Engine Foundation Discovery

**Status:** 10A DISCOVERY COMPLETE  
**Branch:** `stage-10-decision-engine-foundation`

## Objective

Create a deterministic, read-only decision layer that can later answer:

> Given current goals, completed training evidence, recovery/readiness, nutrition evidence and recent progress, what should EVOLVE recommend doing next, and why?

This stage does **not** introduce AI, automatic goal rewriting, or a new adaptation algorithm.

## Existing decision-capable domains

### Goals
Canonical source: `app/goals/service.py` + Stage 9 `app/goals/training_state.py`.

Already available:
- goal lifecycle/status
- metric definitions and direction
- baseline/target/current
- progress percentage and remaining
- trend
- on-track state
- evidence count
- supporting session IDs
- deterministic reason codes

Stage 9 explicitly provides a read-only cross-domain Goal ↔ Training state.

### Training evaluation
Canonical source: `app/training/evaluation.py`.

Already available:
- exercise/session decision: progress / maintain / reduce / insufficient_data
- completion percentage
- actual reps/load/RPE
- deterministic precedence
- explainable reason codes
- explicit no-mutation contract

The Decision Engine must consume this output, not duplicate its rules.

### Training adaptation
Canonical source: `app/training/adaptation.py`.

Already available:
- bounded `deterministic-v2` load/repetition adaptation
- explicit algorithm/provenance
- pure policy

The Decision Engine must **not** become a second adaptation engine. It may recommend/use existing adaptation outcomes, but Stage 8 remains the canonical implementation of exercise-level progression.

### Recovery
Current recovery subsystem already provides deterministic readiness/constraint semantics:
- readiness scoring from available recovery signals
- insufficient-data state
- ready / caution / recovery states
- bounded transient training constraints
- no mutation of stored training/adaptive plans

Recovery is a safety constraint and must have higher priority than performance optimization.

### Nutrition
Current nutrition loop provides:
- profile-derived targets
- actual structured intake
- adherence
- deterministic response
- bounded adaptation eligibility/audit

Nutrition evidence should remain a supporting signal. It must not silently mutate targets from the Decision Engine.

### TODAY / planning
TODAY exposes the action-oriented daily training context and should eventually consume a Decision Engine recommendation. The engine should not reconstruct or mutate TODAY state.

## Canonical Decision Engine boundary

### Inputs

The first implementation should accept already-materialized, authenticated data:

- goal training states
- recent completed training/session outcomes
- recovery state
- nutrition response/adherence state
- current effective plan context
- optional `as_of` date/time for deterministic testing

The pure engine must not access the database, authentication context, or external services.

### Output

Canonical output should contain:

- `decision`
- `priority`
- `action`
- `reason_codes`
- `supporting_goal_ids`
- `supporting_session_ids`
- `constraints`
- `confidence` or data-sufficiency indicator
- `algorithm_version`
- explicit `mutates_plan: false`

Initial decision vocabulary should be deliberately small:

- `train_as_planned`
- `reduce_training`
- `recover`
- `progress_training`
- `maintain_training`
- `insufficient_data`

The engine should return one primary recommendation plus structured evidence rather than a large collection of competing recommendations.

## Decision precedence

Safety and data quality must dominate optimization:

1. **Insufficient critical data** → insufficient_data
2. **Recovery/safety constraint** → recover or reduce_training
3. **Explicit schedule/constraint conflict** → reduce_training / reschedule recommendation
4. **Strong goal + training evidence for progression** → progress_training
5. **Evidence supports continuation without progression** → maintain_training
6. **No material change required** → train_as_planned

This precedence is a contract for Stage 10B and should be tested explicitly.

## Important separation

- Goal Training State = factual state/read model.
- Training Evaluation = evaluates completed execution.
- Training Adaptation = bounded exercise-level next-plan policy.
- Recovery = safety/readiness constraint.
- Nutrition Response = nutrition evidence/adherence.
- Decision Engine = chooses the **highest-priority next action** from these signals.

No domain should be reimplemented inside the Decision Engine.

## Safety invariants

1. Authenticated ownership is enforced before data reaches the pure engine.
2. Pure engine performs no DB reads/writes.
3. Decision Engine never mutates goals, plans, adaptive revisions, nutrition targets or recovery records.
4. Recovery constraints override performance progression.
5. Missing evidence never becomes implicit positive evidence.
6. Every non-trivial decision has deterministic reason codes.
7. Decisions are reproducible from the same inputs.
8. Algorithm version is explicit.
9. No LLM is required.
10. Automatic execution of decisions is out of scope for the initial Decision Engine.

## Stage 10 sequence

- **10A — Discovery + canonical contract:** DONE
- **10B — Pure deterministic Decision Engine:** NEXT
- **10C — Read-only API / integration boundary**
- **10D — Goal/Training/Recovery/Nutrition evidence integration**
- **10E — Security + hostile regression**
- **10F — Final stage gate**

## Non-goals

- AI/LLM decisions
- automatic plan mutation
- automatic goal completion
- new exercise adaptation algorithm
- nutrition target mutation
- recovery score redesign
- UI redesign
- predictive injury/medical logic

## Gate

10A passes when the implementation boundary is explicit, inputs are already authenticated/materialized, decision precedence is deterministic, and existing domain rules are reused rather than duplicated.
