# EVOLVE — Strength Training System Direction

**Document status:** Active product and engineering direction  
**Last updated:** 2026-11-22  
**Scope:** Strength-training plan creation and its supporting user data, exercise selection, load prescription, progression and validation.  
**Repository:** adamzamorski10-alt/EVOLVE-g

> This document defines the intended product behavior and development direction. It is not proof that the current implementation already satisfies these requirements. Verify every implementation claim against current code and tests.

## 1. Purpose and product outcome

EVOLVE should create strength-training plans that behave like the work of a careful, experienced personal trainer: individualized, explainable, practical, progressive and appropriately conservative.

The objective is not to generate impressive-looking workouts or maximize exercise count. The objective is to prescribe the smallest effective, sustainable training dose that fits the user's goals, training experience, actual capabilities, available equipment, schedule and recovery.

The system must:
1. Understand the user's real training context rather than infer ability from body measurements.
2. Select exercises the user can perform with their actual equipment and skill.
3. Prescribe realistic sets, reps, effort and starting loads.
4. Distribute work sensibly across the week and muscle groups.
5. Progress from recorded performance rather than arbitrary assumptions.
6. Explain important decisions and expose uncertainty.
7. Fail safely when required information is missing or inconsistent.

The strength-training system should remain useful without an LLM. Core constraints, calculations, selection and progression must be deterministic, testable and explainable. AI may later assist with explanations or coaching, but must not bypass hard safety and feasibility rules.

## 2. Current project scope and boundaries

### In scope now
- Strength-training profile inputs.
- Initial strength/training calibration.
- Equipment and load-capability modeling.
- Exercise catalog quality and selection.
- Weekly split, session structure, volume and time budgeting.
- Sets, reps, effort and starting-load prescription.
- Training execution data feeding progression.
- Plan validation, explanations and tests.

### Explicitly deferred
- Designing or implementing the dedicated basketball module.
- Automatically coordinating strength plans with basketball sessions.
- A broad rewrite of unrelated EVOLVE domains.
- LLM-driven autonomous training decisions.

The architecture may avoid blocking future sports integration, but basketball must not expand the current strength MVP scope. Until that integration exists, strength planning must not silently assume basketball sessions or claim to optimize around them.

## 3. User context for initial real-world validation

The following is the current example profile supplied for validating generated plans. Treat it as a test fixture, not as universal defaults.

| Attribute | Current value |
|---|---|
| Age | 16 |
| Sex | Male |
| Height | 179 cm |
| Current body mass | 69 kg |
| Desired body mass | 75 kg |
| Main physique goal | Build muscle |
| Strength-training experience | Beginner / limited structured experience (approximately six months of occasional home training) |
| Available training days | Tuesday, Friday, Sunday |
| Available session duration | Up to 60 minutes |
| Training location | Home |
| Declared equipment | Dumbbells, bench, resistance bands, mat, jump rope |
| Default set effort preference | Medium |
| Muscle priorities (user ratings) | Chest 9/10; lats/back 1/10; shoulders 6/10; biceps 9/10; triceps 5/10; core 8/10; quadriceps/hamstrings 6/10; glutes 3/10; calves/tendons 7/10 |

Important interpretation:
- The user is a beginner in structured resistance training. General athletic or basketball experience must not automatically imply intermediate/advanced lifting skill.
- Priority ratings express preference, not permission to neglect foundational balance, movement patterns, joint function or less-prioritized muscle groups.
- The listed equipment does **not** establish the maximum dumbbell load, available increments, whether dumbbells are adjustable, or the exact resistance-band strengths. Those values remain unknown until explicitly collected.
- A cable machine and barbell have not been declared. Do not prescribe cable or barbell exercises unless the user later confirms access.
- The desired body mass is a long-term preference, not a deadline or an instruction to force weight gain at an unsafe rate.
- Because this example user is 16, recommendations must be age-appropriate and conservative. Avoid maximal-lift testing, aggressive loading, routine forced repetitions or training to technical failure. Emphasize technique, gradual progression, recovery and qualified supervision when learning demanding movements.

## 4. Required user model: collect real capabilities

The plan generator must not infer starting strength from age, sex, height, body mass, target weight or a generic experience label.

### 4.1 Training experience
- Resistance-training experience level: beginner, intermediate or advanced.
- Approximate duration and consistency of structured strength training.
- Familiarity/confidence with individual movement patterns or exercises.
- Optional exercise-specific technique status: not tried, learning, familiar, confidently performed.
- General sport experience must be stored separately from strength-training experience.

Experience level is a useful prior for exercise complexity and initial programming, not a substitute for performance evidence.

### 4.2 Actual equipment and load limits
Represent equipment as structured capabilities, not only broad labels such as home or gym.

For dumbbells, collect where applicable:
- fixed or adjustable;
- maximum load **per dumbbell**;
- minimum load and available increments;
- whether a pair is available;
- whether load can be changed during a session.

For bands, collect type/strength or a user-friendly resistance category if exact force is unknown. Record bench adjustability (flat/incline) and other relevant attachments only when confirmed.

Every exercise should declare required equipment and any load requirements. Equipment compatibility is a hard constraint, not a ranking preference.

### 4.3 Initial strength and exercise calibration
Use a safe, submaximal familiarization/calibration process, preferably during normal early sessions:
- record exercise variant and setup;
- record load with an unambiguous unit convention;
- record completed repetitions and sets;
- record perceived effort or repetitions in reserve (RIR), when the user can estimate it reliably;
- record technique confidence or coach/user technique status;
- record whether the set was pain-free and completed with controlled technique, where appropriate.

Do not require one-repetition maximum testing. Do not ask a novice/minor to test maximal strength. If reliable performance evidence is absent, use a conservative, clearly provisional starting prescription and let the first sessions calibrate it.

### 4.4 Health and constraints
Capture relevant injuries, pain, medical restrictions, movement limitations and exercises the user must avoid. Missing health information must not be interpreted as proof that no restrictions exist. Do not diagnose; advise professional assessment for persistent pain or medical concerns.

## 5. Exercise catalog requirements

Each exercise record should provide enough structured information for safe selection and validation:
- stable unique ID and canonical name;
- movement pattern and exercise category;
- primary and secondary muscles;
- required equipment and location compatibility;
- difficulty/skill level and prerequisites;
- setup and execution instructions;
- common technique errors and safety notes;
- available regressions, progressions and substitutions;
- unilateral/bilateral status;
- loading model and supported load type;
- relevant range-of-motion or mobility demands;
- contraindication/limitation tags where evidence-based and appropriate.

Exercise selection rules:
1. Hard-filter unavailable equipment and known user restrictions before ranking exercises.
2. Prefer familiar, teachable movements for beginners.
3. Use exercise complexity only when it adds meaningful value.
4. Avoid selecting an exercise if the catalog lacks enough metadata to validate its requirements.
5. Provide a feasible alternative when an exercise is unavailable or unsuitable.
6. Ensure the displayed exercise instructions and prescribed equipment match the selected catalog entry.

A plan must never contain a cable face pull for a home user who has only declared dumbbells, bench, bands, mat and jump rope. A band-based alternative may be selected only if it exists in the catalog and is actually compatible with the user's bands and setup.

## 6. Plan-generation requirements

### 6.1 Goals and priorities
Translate the user's main goal and muscle priorities into a balanced program. Higher-priority muscles may receive relatively more attention, but the generator must retain adequate work for foundational movement patterns and all major muscle groups.

Do not interpret a 1/10 back priority as a reason to omit back training. Do not let a high chest priority create excessive pressing volume or an avoidable push/pull imbalance.

### 6.2 Weekly structure
Generate a split that fits:
- selected training days;
- session time limits;
- available equipment and locations;
- experience and tolerable training dose;
- recovery between sessions;
- the user's stated preferences.

For the current validation profile, the available strength sessions are Tuesday, Friday and Sunday, each up to 60 minutes. A possible three-day structure may use different emphases (for example, upper, lower, upper/full-body balance), but the split must be chosen from actual constraints and total weekly coverage rather than hardcoded to this example.

Repeating a movement can be useful for skill development. Repetition is not automatically wrong; unjustified duplication and poor weekly distribution are.

### 6.3 Volume and balance
- Count direct and indirect muscle involvement consistently.
- Distinguish hard working sets from warm-up sets.
- Avoid double-counting secondary involvement as equivalent to direct work.
- Keep initial volume conservative for beginners and increase only when supported by recovery and performance.
- Check weekly balance across push, pull, knee-dominant, hip-dominant, unilateral, trunk and other relevant patterns.
- Do not use a single universal weekly-set target for every user.
- Validate that the total session fits the user's time limit, including realistic rest periods and transitions.

### 6.4 Sets, reps and effort
Prescriptions should reflect the exercise, goal, experience, equipment and safe technique. Use manageable rep ranges and a clear effort target. For beginners, prioritize controlled repetitions and leaving repetitions in reserve rather than routinely training to failure.

If RIR/RPE is shown, explain it in beginner-friendly language and do not assume the user can estimate it precisely on day one.

### 6.5 Load prescription and units
- Define whether dumbbell load is **per hand/per dumbbell** or combined total. Use one explicit convention consistently in UI, API, history, progression and exports.
- Distinguish dumbbells, barbell total load, machine stack and band resistance.
- Never prescribe a load above confirmed available equipment capacity.
- Never invent a precise load when evidence is insufficient.
- Do not use bodyweight-only formulas as the primary source of exercise-specific starting loads.
- If no reliable baseline exists, provide a conservative provisional load or a load-selection instruction (for example, choose a weight that permits the prescribed repetitions with controlled form and several repetitions in reserve), then record the actual result.
- Respect available weight increments and avoid suggesting impossible increments.

## 7. Progression and adaptation

Progression must be evidence-led, gradual and explainable.

Use repeated completed-session evidence where possible:
- completed reps and sets;
- actual load;
- RIR/RPE and confidence in that estimate;
- technique status;
- pain or limitation flags;
- completion rate and recent consistency.

A single unusually good or bad session should not trigger a large automatic change. Missing or unreliable evidence should lead to maintaining the plan or using a conservative calibration step, not pretending certainty.

The system should:
- explain why a load/repetition/set changed;
- preserve planned versus actual values;
- avoid progression when technique, pain or safety flags make it inappropriate;
- avoid sudden large jumps;
- support deload/reduction or substitution when repeated evidence indicates the current prescription is not tolerable;
- keep a traceable decision record where the existing architecture supports it.

Do not reintroduce reverted Stage 9E functionality or commits merely because this document describes desired behavior. First inspect why the rollback occurred, what was lost, and whether the underlying behavior can be safely reimplemented in a smaller verified change.

## 8. Safety and age-appropriate behavior

For minors and novice lifters:
- prioritize qualified instruction for learning unfamiliar or technically demanding lifts;
- use submaximal training and controlled technique;
- do not prescribe maximal testing, forced reps or routine failure training;
- progress gradually and avoid arbitrary load jumps;
- stop or modify an exercise if pain or concerning symptoms occur;
- do not let physique priorities override balanced development, recovery or safety;
- do not make medical, injury-treatment or growth claims.

Safety constraints must be enforced in code and tests, not merely shown as a disclaimer.

## 9. Explainability and user experience

For every generated session, the user should be able to understand:
- why each exercise was selected;
- which muscles/movement patterns it trains;
- what equipment is required;
- how to set up and perform it;
- how many sets/repetitions to complete;
- how to select/use the load;
- what effort level to aim for;
- how long to rest;
- what to do if the equipment or exercise is unavailable.

Clearly label provisional loads and explain when the system needs calibration. Do not display false precision.

## 10. Validation and quality gates

A plan is not acceptable merely because it is syntactically valid or passes a basic schema test.

Build deterministic tests for at least these scenarios:
1. Beginner, home equipment only: no cable/machine/barbell exercise appears unless explicitly available.
2. Dumbbell maximum and increments: no impossible load is prescribed.
3. Unknown strength baseline: no falsely precise or bodyweight-guessed load is treated as verified.
4. Load convention: per-hand versus total load is consistent across generation, UI, logging and progression.
5. Beginner skill: advanced/complex movements are excluded or replaced unless familiarity/prerequisites are satisfied.
6. High chest/biceps priorities: priorities influence allocation without eliminating back, legs or essential patterns.
7. Low back priority: pulling work remains adequate for a balanced program.
8. Three sessions/week and 60-minute limit: all sessions fit realistic time budgets.
9. Missing experience/equipment data: safe explicit fallback or clarification; no silent intermediate/gym_full assumption.
10. Age-appropriate profile: no maximal-strength test or unsafe default intensity.
11. Pain/restriction flags: affected exercises are blocked or appropriately substituted.
12. Insufficient history: progression does not make unsupported jumps.
13. Repeat generation with identical inputs: deterministic output where intended.
14. Exercise catalog gaps: invalid/incomplete entries cannot bypass equipment and skill validation.

Tests should assert the quality constraints and behavior, not brittle exact exercise names unless the exact selection is itself the contract.

## 11. Development strategy and sequencing

Work in small, reviewable stages. Do not combine discovery, implementation, broad regression and hostile audit into one task.

### Stage A — Focused discovery (currently in progress)
Read-only audit of the real generation path, profile/assessment data flow, equipment model, exercise catalog, load estimation, progression and existing tests.

**Exit gate:** report actual code paths, confirmed findings, missing data, preserved functionality, and prioritized gaps with file/line references. No code changes during discovery.

### Stage B — User data and hard feasibility constraints
Implement only the missing high-value profile/equipment/experience fields and enforce equipment/weight compatibility through the actual generation path.

**Exit gate:** end-to-end tests prove stored inputs are read and materially change generated output; impossible equipment/load prescriptions are blocked.

### Stage C — Exercise selection and beginner-appropriate structure
Improve exercise metadata, skill filtering, movement-pattern coverage, weekly balance, volume and session-time budgeting.

**Exit gate:** representative profiles generate balanced, feasible sessions; targeted tests cover priority and beginner edge cases.

### Stage D — Starting-load calibration and progression
Replace unsupported estimates with safe provisional prescription and performance-based calibration. Verify the complete planned → performed → logged → next-plan flow.

**Exit gate:** actual training evidence influences future loads conservatively and explainably; insufficient evidence never creates false precision.

### Stage E — Real-user validation
Generate plans for the current example profile, inspect every exercise/load/session, then test actual sessions and compare planned versus completed results.

**Exit gate:** no critical feasibility or safety defects; user can execute the plan with declared equipment; issues are traceable and corrected.

### Stage F — MVP readiness
Run the relevant focused regression first, then the appropriate final regression gate. Confirm data persistence, deterministic behavior, UI clarity and absence of regressions.

**Exit gate:** the strength-plan workflow is reliable enough for regular supervised personal use, with known limitations documented.

## 12. Engineering rules for implementation agents

- Begin each task with a recommended reasoning level: LOW for small, bounded implementation/tests; MEDIUM for complex debugging or multi-file behavior; HIGH only for architecture or final hostile/security audits.
- Prefer the smallest change that fixes a confirmed problem.
- Inspect current code before relying on old audit documents or assumptions.
- Do not rewrite the generator or unrelated systems without evidence that the current design blocks correctness.
- Preserve working functionality and existing contracts.
- Add regression tests alongside behavior changes.
- Do not silently change user data, defaults or historical records.
- Do not create branches, commits, migrations or modify files during a task explicitly marked read-only.
- Report exact files changed, tests run and results, unresolved risks, and the next smallest step.
- Do not claim a feature is complete merely because fields exist: verify **STORED → READ → USED → CHANGES BEHAVIOR → TESTED**.

## 13. Current status and known initial observations

**Current work item:** focused read-only generator audit has been requested from the coding agent. Its response has not yet been reviewed in this project document.

Initial observations from a sample plan generated for the example profile:
- The plan repeated several pressing movements across all three sessions and appeared heavily chest-dominant.
- Direct biceps work was absent despite a high biceps priority.
- The plan included cable face pulls although cable equipment was not declared.
- It included a 70 kg RDL prescription although the user's home load capacity was not known and the user reported not owning that amount of weight.
- It prescribed 22 kg dumbbells for pressing despite the user reporting a much lower familiar working load (approximately 12 kg per dumbbell, with the exact exercise/setup still to be confirmed).
- The plan's day labels contained a duplicate Friday where the third session was expected to be Sunday; verify whether this was a transcription issue or a generator/scheduling defect.
- The plan contained substantial repeated chest work and limited lower-body movement-pattern coverage.

These are observed sample-output issues, not yet proven root causes in code. The read-only audit must establish which are caused by profile defaults, data flow, catalog metadata, selection rules, load estimation, schedule mapping or user-interface rendering.

A previous repository rollback reverted Stage 9E. Do not assume the reverted implementation is correct or restore it without investigating the reason for rollback and validating the smallest safe replacement.

## 14. Definition of done

The strength-plan generator is ready for regular use only when it consistently:
- uses the user's real experience and capabilities;
- respects confirmed equipment and load limits;
- creates balanced, goal-relevant weekly plans;
- provides beginner-appropriate exercise choices and clear instructions;
- prescribes safe, realistic starting loads;
- fits available session time;
- progresses based on actual performance evidence;
- explains its decisions and uncertainty;
- passes targeted automated tests and final regression;
- has no known critical safety or feasibility defects.

**North star:** EVOLVE should not merely produce a workout. It should make a defensible training decision for this user, explain that decision, observe what happened, and improve the next decision without sacrificing safety or practicality.
