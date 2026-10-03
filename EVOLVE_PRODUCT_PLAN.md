# EVOLVE — Product Plan

**Status:** Active  
**Baseline:** EVOLVE-g / Training-coach  
**Default branch:** main  
**Product phase:** EVOLVE v0 → first genuinely useful personal performance coach

---

## 1. Product Direction

EVOLVE is a personal performance application focused first on **basketball development + strength training**.

The current EVOLVE-g application is the starting product. We are **evolving the existing product**, not performing a blind rewrite and not treating the old roadmap as a rigid migration plan.

The goal is to progressively turn the current application into a system that:

1. understands the user's goals and constraints,
2. creates a practical personalized plan,
3. tells the user what to do today,
4. records what actually happened,
5. analyzes the response,
6. adapts future planning using evidence,
7. shows meaningful progress.

AI is **not required for the core product**. Deterministic data, rules, history, planning and safety come first. AI/AI Manager integration is a later layer.

---

## 2. Core Loop

The primary EVOLVE loop is:

**PROFILE → GOALS → CONSTRAINTS → PLAN → TODAY → EXECUTE → LOG → RESULT → ANALYZE → ADAPT → NEW PLAN**

Every major feature should strengthen this loop.

A feature that does not materially improve the loop should be considered secondary.

---

## 3. Product Principles

### 3.1 Existing product first
Preserve useful existing functionality and visual language where it works. Improve, expand, simplify or remove individual parts based on evidence.

### 3.2 No premature rewrite
Do not rewrite the whole frontend/backend merely for architectural cleanliness. Refactor when the current structure blocks correctness, maintainability or feature delivery.

### 3.3 Deterministic core
Important calculations and decisions must be explainable and reproducible without an LLM.

### 3.4 Real personalization
A stored user field is not enough. Important inputs must actually affect application behavior and be tested.

**STORED → READ → USED → CHANGES BEHAVIOR → TESTED**

### 3.5 Planned vs actual
The system must distinguish what was planned from what actually happened.

### 3.6 Safety before optimization
Safety constraints take priority over performance optimization.

### 3.7 Evidence before adaptation
One isolated result should not cause large automatic changes. Adaptation should be based on sufficient evidence and remain explainable.

### 3.8 Progressive complexity
Build the smallest useful version of each subsystem, then expand it only when the core loop benefits.

---

## 4. Target Product Areas

### TODAY
Make TODAY the central action-oriented screen.

It should answer:
- What should I do?
- Why am I doing it?
- When?
- Where?
- How long?
- What equipment is needed?
- What is the primary action?

It should connect training, basketball, recovery and nutrition without becoming a giant dashboard.

### PLAN
Turn planning into a genuinely personalized plan based on:
- goals,
- training level,
- history,
- availability,
- equipment,
- locations,
- basketball commitments,
- recovery/readiness,
- desired frequency.

Start deterministic. Do not depend on AI.

### TRAINING
Support the complete flow:

**PLAN → START → EXECUTE → LOG → COMPLETE → RESULT**

Training data should support, where applicable:
- exercises,
- sets,
- reps,
- load,
- RPE,
- duration,
- notes,
- planned vs actual values.

### ADAPTATION
Use repeated real-world responses to improve future plans.

Examples:
- appropriate progression after repeated successful sessions,
- volume/load reduction after sustained excessive difficulty,
- schedule changes when constraints repeatedly prevent completion.

No silent major future-plan rewrites.

### EXERCISE LIBRARY
Create structured exercise knowledge with:
- stable ID,
- name,
- category,
- movement pattern,
- target muscles,
- level,
- equipment,
- location,
- instructions,
- common mistakes,
- alternatives,
- regressions,
- progressions.

### BASKETBALL
Basketball becomes the first dedicated sport pillar.

Target areas:
- basketball profile,
- initial assessment,
- shooting,
- free throws,
- three-point shooting,
- ball handling,
- sprinting,
- vertical/jump,
- agility,
- conditioning,
- later defensive/performance metrics.

Basketball training should coexist with and influence strength training rather than being an isolated module.

### RECOVERY
Track useful signals such as:
- fatigue,
- soreness,
- energy,
- stress,
- later sleep/readiness.

Recovery data must influence planning rather than only produce a decorative score.

### NUTRITION
Keep the useful current functionality while evolving toward:

**PROFILE → TARGETS → MEALS → ACTUAL INTAKE → HISTORY**

Target MVP data:
- calories,
- protein,
- carbohydrates,
- fats,
- fiber,
- water,
- meals.

Preferences/allergies/constraints must influence relevant results.

### PROGRESS
Prioritize:

**WHAT CHANGED?**

before charts and dashboards.

Progress should consume actual historical data and explain meaningful changes.

### PROFILE
Organize important user information around:
- Personal,
- Goals,
- Training,
- Basketball,
- Availability,
- Equipment,
- Locations.

Important fields must have downstream behavioral impact.

### ONBOARDING + ASSESSMENT
Target flow:

**Registration → Personal → Goals → Schedule → Location → Equipment → Level → Basketball Assessment → First Plan**

The initial assessment should provide useful baseline data rather than being a cosmetic questionnaire.

### HISTORY
Build a unified factual history of relevant events and outcomes.

History is foundational for:
- progress,
- adaptation,
- pattern discovery,
- future AI.

Where appropriate, historical records should be append-only and include timestamp, source/provenance, schema version and relevant context.

---

## 5. UX Direction

Do not perform a visual revolution.

Keep the current product's useful visual language while improving:
- hierarchy,
- information density,
- action clarity,
- navigation,
- empty/loading/error states,
- consistency,
- mobile usability,
- completion flows.

Remove clutter and screens that do not contribute enough value.

---

## 6. Development Stages

### Stage 1 — Product Audit
**Goal:** understand the real current product before changing behavior.

Audit every important:
- screen,
- route,
- user flow,
- backend domain,
- data model,
- current feature,
- legacy artifact.

For each feature classify:

**KEEP / MODIFY / ADD / REMOVE / DEFER**

Also identify:
- duplicated behavior,
- dead code,
- misleading UI,
- broken flows,
- missing data links,
- security issues,
- personalization gaps,
- test gaps.

**Gate:** current product is mapped well enough to implement Stage 2 without guessing.

---

### Stage 2 — Core Loop
Build the strongest end-to-end loop:

**Profile → Goals → Plan → Today → Training → Log → Result**

Do not expand into every domain simultaneously.

**Gate:** a user can complete a realistic training day from plan creation through logging and result.

---

### Stage 3 — Personalization
Integrate:
- availability,
- equipment,
- locations,
- training level,
- basketball profile,
- recovery constraints.

**Gate:** changing meaningful user constraints changes relevant planning behavior.

---

### Stage 4 — Adaptation
Introduce deterministic evidence-based adaptation.

**Gate:** adaptation is explainable, bounded, tested and never silently destructive.

---

### Stage 5 — Progress
Build useful historical analysis and the **WHAT CHANGED?** experience.

**Gate:** progress is based on real stored events/results and remains correct across realistic histories.

---

### Stage 6 — Basketball
Deepen basketball-specific assessment, training and performance tracking.

**Gate:** basketball is a real integrated pillar rather than a collection of isolated screens.

---

### Stage 7 — Nutrition
Harden nutrition targets, logging, history and response to preferences/constraints.

**Gate:** nutrition data is consistent, useful and integrated with the wider performance picture.

---

### Stage 8 — Hardening
Final broad pass over:
- authentication/authorization,
- ownership boundaries,
- validation,
- migrations,
- data integrity,
- error handling,
- tests,
- regression,
- performance,
- UX consistency,
- security,
- mobile behavior.

**Gate:** release-quality first useful EVOLVE version.

---

## 7. Explicitly Deferred

Do not let these distract from the first useful product unless a concrete dependency appears:

- AI Coach,
- AI Manager,
- autonomous agents,
- BYOK AI,
- advanced AI Kitchen,
- Discord integration,
- Stripe/subscriptions,
- multiple sports,
- wearables,
- social features,
- marketplace,
- advanced gamification,
- predictive AI,
- video analysis,
- food vision,
- native mobile applications.

These can return after the core product proves useful.

---

## 8. Architecture Direction

The current architecture should evolve incrementally.

Preferred long-term separation:

- authentication/identity,
- profile,
- goals,
- constraints,
- planning,
- training execution,
- basketball,
- recovery,
- nutrition,
- progress,
- history/events,
- safety,
- decision/adaptation services.

However, architectural cleanup should be driven by real product needs rather than performed as a large rewrite.

---

## 9. Safety and Data Rules

Security invariant:

**AUTHENTICATED PRINCIPAL → CANONICAL USER → OWNED RESOURCE → ACTION**

Never trust client-provided ownership identifiers.

Fitness functionality is wellness/performance oriented, not diagnosis or treatment.

Important decisions should have:
- clear inputs,
- deterministic rules where applicable,
- bounded effects,
- explainable outputs,
- tests.

---

## 10. Testing Strategy

Every meaningful stage should use focused tests during implementation.

At the end of each stage:
1. targeted tests,
2. integration checks,
3. relevant regression,
4. final stage gate.

Do not run enormous regression suites after every tiny change.

Final release requires a broader hostile/security/regression audit.

---

## 11. Definition of Done

A feature is not complete merely because its UI exists.

For important functionality, verify:

- UI exists,
- backend behavior exists,
- data is persisted correctly,
- ownership/security is correct,
- validation exists,
- edge cases are handled,
- real downstream behavior changes,
- tests cover critical paths,
- no relevant existing functionality regresses.

---

## 12. Current Project Checkpoint

**DONE**
- EVOLVE-g accepted as the starting product.
- Existing Training-coach functionality accepted as the baseline.
- Product direction and priorities accepted.
- AI-first development explicitly deferred.
- Staged development strategy accepted.

**CURRENT**
- Stage 1: Product Audit / Discovery.

**NEXT**
- Map the actual current repository screen-by-screen and flow-by-flow.
- Produce a concrete KEEP / MODIFY / ADD / REMOVE / DEFER matrix.
- Identify the smallest high-value Stage 2 implementation slice.
- Implement Stage 2 incrementally with verification gates.

---

## 13. Working Rule for Future Development

Before implementing a major feature:

1. Inspect the current implementation.
2. Identify the smallest coherent change.
3. Implement it.
4. Test it.
5. Verify real behavior.
6. Update this plan/checkpoint if the product direction changes.

This document is the current product source of truth, but it is intentionally **living** and may be updated when evidence from the real application justifies a change.

---

**Current target:** make EVOLVE genuinely useful first; make it sophisticated later.
---

## 14. Core Loop Implementation Checkpoint — 2026-10-02

### DONE
- **0. Fundamenty techniczne:** core user/profile data remains authenticated/user-scoped; planning writes now keep UserDB datetime fields typed correctly; assessment has a real migration and blocking CI coverage.
- **1. Profil użytkownika:** profile editing now supports planning-critical constraints: sport, training focus, improvement areas, equipment, avoided exercises, sport specialization and training days, with validation.
- **2. Assessment:** added a versioned, append-only baseline assessment domain with ownership isolation and a usable UI.
- **3. Planowanie treningu:** added planning readiness, a dedicated planning UI, and deterministic plan provenance (schema_version, planning algorithm, profile inputs and assessment version).
- **4. Realizacja treningu:** existing end-to-end execution remains connected to the effective plan: START → LOG SET → COMPLETE → RESULT, including user scoping and validation.

### CURRENT
The first four core-loop layers are implemented as a connected product path:
PROFILE → ASSESSMENT → PLAN → TODAY → TRAINING EXECUTION.

### NEXT
- **Core Loop hardening:** connect assessment/profile constraints more deeply to plan selection (availability, equipment and basketball specialization) without breaking the existing deterministic generator.
- Then continue with **History + Progress → rolling 1–2 week planning → basketball development → recovery → nutrition**.


## Stage 5A — Nutrition Foundation Checkpoint — 2026-10-03

### DONE
- Added canonical structured `NutritionEntryDB` for actual food/water intake.
- Added Alembic migration `evolve18nutrition` after `evolve17goalmetrics`.
- Added authenticated user-scoped nutrition endpoints:
  - `POST /app/nutrition/entries`
  - `GET /app/nutrition/entries`
  - `GET /app/nutrition/today`
  - `DELETE /app/nutrition/entries/{entry_id}`
- Added deterministic daily aggregation for calories, protein, carbohydrates, fat, fiber and water.
- Added calorie/protein target exposure from the existing user profile calculation.
- Added bounded date-range validation and ownership checks.
- Kept legacy `DailyLogDB` meal JSON intact for compatibility; it is not the new canonical analytics source.

### CURRENT
Stage 5A establishes a real structured source for **ACTUAL INTAKE**. No adaptation is performed yet.

### NEXT
- Nutrition target semantics and adherence windows.
- Connect actual intake with training/load and recovery signals.
- Build bounded deterministic nutrition response/adaptation rules.
- Native Dieta UX should consume the structured API rather than legacy JSON.


## Stage 5B — Nutrition Adherence Checkpoint — 2026-10-03

### DONE
- Added deterministic `GET /app/nutrition/adherence?days=1..28`.
- Aggregates only days with actual structured intake.
- Reports calorie adherence using a bounded 90–110% target window.
- Reports protein adherence at >=90% of target.
- Exposes daily ratios and rolling averages.
- Missing intake days are not silently classified as failures.

### CURRENT
Nutrition now has the first analytical layer:
**PROFILE TARGETS → ACTUAL INTAKE → ADHERENCE**.

### NEXT
- Add response/adaptation rules using sufficient evidence.
- Keep adaptation bounded and explainable.
- Integrate training/recovery context before changing nutrition targets.


## Stage 5C–5D — Nutrition Response + Native Dieta UX — 2026-10-03

### DONE
- Added deterministic `GET /app/nutrition/response?days=3..28`.
- Requires at least 3 logged days before producing a response signal.
- Distinguishes under-target, near-target and over-target calorie patterns.
- Separately reports protein signal.
- Explicitly returns `adaptation_allowed=false`; this stage never mutates nutrition targets.
- Added native Dieta shell to the main application.
- Dieta shows today's calories/protein, entries and deterministic response.
- Added authenticated create/delete interaction and stale-request protection.
- Added native navigation loading for the Dieta tab.
- Added API/UI regression contracts.

### CURRENT
Nutrition loop is now:
`PROFILE TARGETS → ACTUAL INTAKE → ADHERENCE → RESPONSE → DIETA UX`.

### NEXT
Stage 5E will connect nutrition evidence with training/recovery context and define bounded adaptation eligibility. Target changes remain disabled until that evidence gate is implemented and tested.


## Stage 5E — Nutrition Adaptation Checkpoint — 2026-10-03

### DONE
- Added a separate `NutritionAdaptationDB` audit trail.
- Added Alembic `evolve19nutrition_adaptations`.
- Added deterministic adaptation preview requiring:
  - at least 7 logged nutrition days,
  - at least 2 completed training sessions in the same 14–28 day evidence window.
- Adaptation is bounded to a maximum ±100 kcal per application and a safe absolute range of 1200–5000 kcal.
- Protein target is not automatically changed by this stage.
- Added optimistic concurrency protection: the target is updated only if its stored base value still matches the preview base.
- Added explicit user-triggered apply endpoint.
- Added native Dieta presentation and explicit “Zastosuj zmianę” action.
- Added audit record for every applied adaptation.

### SAFETY INVARIANTS
- No adaptation from a single day.
- No adaptation without training context.
- No silent mutation from a GET/preview.
- No unbounded calorie jump.
- No automatic protein-target mutation.
- Concurrent target changes produce a conflict instead of overwriting newer data.

### CURRENT
Stage 5 nutrition loop is complete:
`PROFILE → TARGETS → ACTUAL INTAKE → ADHERENCE → RESPONSE → EVIDENCE → BOUNDED ADAPTATION → AUDIT → DIETA UX`.

### NEXT
Stage 6 — Recovery Response.


## Stage 6A — Recovery Response Foundation — 2026-10-03

### DONE
- Added authenticated `/app/recovery/today` and bounded `/app/recovery/history` endpoints using the existing structured daily check-in signals.
- Added deterministic readiness scoring from sleep, sleep quality, energy, stress, fatigue and mood when available.
- Requires at least two recovery signals before applying a training constraint.
- Uses three explainable states: ready, caution and recovery.
- Recovery constraints are bounded to no reduction, ~25% volume reduction or ~50% volume reduction.
- The effective training plan now consumes today's recovery state transiently; the stored base/adaptive plan is never mutated by the recovery response.
- Added focused readiness and non-mutation regression tests and registered the recovery router in the Stage 0–5 audit contract.

### CURRENT
Recovery has its first deterministic product link:
`CHECK-IN → READINESS → BOUNDED TRAINING CONSTRAINT → TODAY/TRAINING`.

### NEXT
- Add native Recovery UX to the shared shell.
- Verify recovery constraint behavior through the full Today → Training browser flow.
- Add history/trend presentation and safety/edge-case tests before expanding the model.
