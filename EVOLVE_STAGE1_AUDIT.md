# EVOLVE — Stage 1 Product Audit

**Audit status:** In progress — first repository pass  
**Audited baseline:** current `main`  
**Product baseline:** EVOLVE-g / Training-coach  
**Audit principle:** current repository code is the source of truth; older documentation is historical evidence only.

> Note: GitHub code-search results can lag behind `main`. Where search results conflicted with direct file reads, the current `main` file was treated as authoritative.

---

## 1. Executive Assessment

The current application is **substantially more capable than the old FitAI README suggests**, but it is also a hybrid of several generations.

There are three major layers:

1. **Current modular backend**
   - FastAPI
   - SQLModel
   - SQLite
   - JWT authentication
   - modular auth / fitness / AI / plan / notifications / health / meta packages
   - Alembic migrations
   - structured exercise and drill results
   - daily logs and extended recovery-like fields

2. **Current product frontend**
   - very large monolithic `index.html`
   - approximately 2 MB
   - single-page application behavior
   - Tailwind CDN + custom CSS
   - Chart.js
   - plan / day / sport / progress / profile functionality
   - PWA/service-worker support

3. **Legacy / compatibility layer**
   - `app/legacy_routes.py`
   - `fitai_api.py`
   - `fitai_dashboard.html`
   - `fitai_discord_bot.py`
   - old generated HTML scripts
   - old FitAI documentation
   - Stripe/Netlify artifacts
   - historical migration/audit documents

The correct strategy is therefore **not a rewrite**. We should progressively establish one active EVOLVE product path while safely isolating and later retiring obsolete paths.

---

# 2. Current Architecture Map

## Backend

### Active application entry point

`main.py` imports:

```python
from app import app
```

The FastAPI application is assembled in `app/__init__.py`.

Currently included routers:

- auth
- health
- fitness
- AI
- meta
- notifications
- plan
- legacy

The SPA fallback serves root `index.html`.

### Active backend domains

| Domain | Current state | EVOLVE decision |
|---|---|---|
| Auth | Active JWT/native auth | KEEP + harden |
| Profile | Active in UserDB + fitness routes | MODIFY |
| Daily logging | Active and fairly rich | MODIFY |
| Plan | Active but legacy-coupled | MODIFY |
| Training | Active inside fitness routes | MODIFY |
| Exercise results | Active | KEEP + strengthen |
| Basketball/drills | Active inside fitness domain | MODIFY + deepen |
| Recovery/check-in | Fields exist in daily logs | MODIFY into real domain behavior |
| Nutrition | Active but mixed with plan/day logging | MODIFY |
| Progress/weekly analysis | Active | MODIFY around “What changed?” |
| Notifications/Discord | Active | DEFER |
| AI | Active | DEFER from core product |
| Billing/Stripe | Historical/current artifacts | DEFER |
| Legacy routes | Still mounted | ISOLATE / later retire |

---

# 3. Data Model Findings

## UserDB

`UserDB` currently contains a large amount of information:

- personal profile,
- goals,
- training frequency,
- diet,
- allergies,
- food preferences,
- equipment,
- avoided exercises,
- sport focus,
- sport specialization,
- sport training days,
- authentication,
- subscription/role,
- XP,
- streak,
- injuries,
- Discord/reminder state,
- serialized weekly plan.

This is useful as a baseline but is already becoming a **large aggregate with many unrelated responsibilities**.

### EVOLVE decision

**MODIFY, not rewrite.**

For the first EVOLVE version we should keep the current schema where practical, but new functionality should avoid making `UserDB` an even larger catch-all.

Longer term, domain data should be separated where the product actually needs it.

---

## JSON fields

Several important fields are stored as serialized JSON:

- sports
- training focus
- improvement areas
- food preferences
- equipment
- avoided exercises
- reminders
- weekly plan
- substitution history
- sport training days

This is acceptable for the current product but creates limitations for:

- querying,
- indexing,
- history,
- relational integrity,
- adaptation,
- analytics.

### EVOLVE decision

**KEEP for existing data.**

Do not perform a mass normalization migration now.

For new high-value historical/transactional data, prefer dedicated tables when justified.

---

# 4. Core Loop Audit

## PROFILE

### Existing
The system already stores substantial profile data.

### Missing / weak
Not all stored inputs have clear evidence of changing downstream behavior.

### Decision
**MODIFY**

Target:

`PROFILE → GOALS → CONSTRAINTS → PLAN`

Every important field should eventually satisfy:

**STORED → READ → USED → CHANGES BEHAVIOR → TESTED**

---

## GOALS

### Existing
Current `goal`, `training_focus`, `improvement_areas` exist.

### Weakness
Goals are partly represented as profile fields rather than as an explicit planning input model.

### Decision
**MODIFY**

Do not create a complex goal-management system yet.

First make existing goals materially influence planning.

---

## PLAN

### Existing
There is already:

- weekly plan generation,
- saved plans,
- plan retrieval,
- plan swapping,
- exercise progression enrichment,
- day-level plan data.

### Major architectural weakness

`app/plan/routes.py` imports:

```python
_build_weekly_plan
_enrich_exercises_with_progression
_is_profile_ready_for_plan
```

from:

```
app.legacy_routes
```

This means the supposedly newer plan module still depends on the legacy layer.

### Decision

**MODIFY — high priority**

The first planning improvement should extract the planning logic from `legacy_routes.py` into a proper service without changing behavior unnecessarily.

This is a targeted refactor, not a rewrite.

---

## TODAY / DAY EXECUTION

The current application already has a relatively advanced daily logging system.

Current backend supports:

- meals,
- workouts,
- custom meals,
- exercise entries,
- toggling day items,
- swapping items,
- water,
- sleep,
- sleep quality,
- energy,
- stress,
- fatigue,
- mood,
- RPE,
- notes,
- weight.

This is a strong starting point for the EVOLVE core loop.

### Decision

**KEEP the underlying capability, MODIFY the product experience.**

The main goal is to turn the existing functionality into a clear:

**WHAT DO I DO TODAY → START → LOG → COMPLETE → RESULT**

experience.

---

# 5. Training Execution Audit

Current backend has dedicated `ExerciseResultDB` data and progression-related calculations.

Existing information includes:

- exercise,
- session date,
- sets,
- reps,
- weight,
- RPE,
- progression suggestions.

This is much closer to the required EVOLVE model than a simple free-text workout logger.

### Decision

**KEEP + MODIFY**

Priority improvements:

1. clearly separate planned vs actual;
2. make execution state explicit;
3. make session completion explicit;
4. calculate session result from actual data;
5. preserve historical records;
6. use actual results as evidence for later adaptation.

This is likely the first major product vertical slice.

---

# 6. Basketball Audit

The current backend already contains a sport drill catalog.

Basketball examples include:

- three-point shooting,
- free throws,
- mid-range,
- layups,
- catch-and-shoot,
- ball handling,
- passing,
- defense.

There is also drill-result persistence and progression logic.

### Current weakness

Basketball functionality is still embedded largely inside the broader fitness domain.

There is also a catalog containing multiple sports.

### EVOLVE decision

**KEEP + MODIFY**

Basketball should become the first dedicated sport pillar.

Do not build multiple sports now.

---

# 7. Recovery Audit

The current daily-log model already contains:

- sleep hours,
- sleep quality,
- energy,
- stress,
- fatigue,
- mood,
- RPE.

This is valuable raw data.

### Current weakness

These values are primarily collected/logged. The product direction requires them to **change planning behavior**.

### Decision

**MODIFY**

First goal:

`RECOVERY INPUT → READINESS/CONSTRAINT → PLAN BEHAVIOR`

No advanced recovery prediction is needed yet.

---

# 8. Nutrition Audit

Current system has:

- calorie target,
- protein target,
- daily macros,
- meals,
- meal alternatives,
- diet preference,
- allergies,
- preferred foods,
- avoided foods.

### Current weakness

Nutrition is strongly coupled to the weekly plan and legacy FitAI architecture.

The current system is therefore more of a **diet-plan generator/logger** than a clean nutrition-response subsystem.

### Decision

**KEEP + MODIFY**

MVP direction:

**TARGETS → MEALS → ACTUAL INTAKE → HISTORY → RESPONSE**

AI Kitchen remains deferred.

---

# 9. Progress Audit

Current backend already has weekly analysis combining:

- exercise results,
- drill results,
- daily logs,
- completion,
- volume,
- RPE,
- water,
- sleep,
- mood,
- weight.

This is useful raw material.

### EVOLVE decision

**KEEP + MODIFY**

The first progress experience should prioritize:

### WHAT CHANGED?

Examples:

- training volume,
- exercise performance,
- basketball accuracy,
- consistency,
- bodyweight trend,
- recovery trend.

Charts remain supporting evidence, not the main product.

---

# 10. Authentication / Ownership

The current active routes generally use:

`Depends(get_current_user)`

and resolve the canonical user from the JWT subject.

This is the correct direction.

### Important rule for future work

Never introduce a new endpoint that trusts a client-provided `user_id` or `identity_id` for ownership.

Required invariant:

**AUTHENTICATED PRINCIPAL → CANONICAL USER → OWNED RESOURCE → ACTION**

This should remain a permanent EVOLVE security rule.

---

# 11. Repository Hygiene Findings

Several obsolete or potentially dangerous artifacts remain in the public repository.

Examples:

- `fitai.db`
- `fitai.db-shm`
- `fitai.db-wal`
- database backups
- legacy API files
- old dashboard
- generated HTML
- old FitAI documentation
- Stripe/Netlify artifacts

The current `.gitignore` does **not** ignore `*.db`, `*.db-shm`, or `*.db-wal`.

### Security finding

Because this repository is public, committed database artifacts must be treated as a **high-priority security/data-exposure concern**.

Before removing anything, we must inspect what is actually contained in the committed database and determine whether it contains real user data or only development/test data.

### Decision

**AUDIT IMMEDIATELY; REMOVE FROM REPOSITORY IF SAFE**

This is separate from product feature work and should not be ignored.

---

# 12. Frontend Audit

The current primary frontend is:

`index.html`

It is approximately **2 MB** and contains:

- HTML,
- CSS,
- application JavaScript,
- UI state,
- API integration,
- multiple product sections,
- modals,
- plan UI,
- exercise/drill UI,
- charts,
- PWA-related behavior.

The repository also contains:

- `app/index.html`
- `app/index_new.html`
- `fitai_dashboard.html`
- `generate_html.py`
- `generate_complete_dashboard.py`
- additional HTML-generation artifacts.

### Decision

**DO NOT REWRITE THE FRONTEND NOW.**

Instead:

1. establish which frontend is actually active;
2. treat `index.html` as the current product surface;
3. improve flows incrementally;
4. extract code only when a concrete product change requires it.

---

# 13. Legacy Layer

The legacy layer is still operationally important because current plan generation depends on it.

Therefore:

### REMOVE NOW?

**NO.**

### Keep permanently?

**NO.**

### Correct strategy

**ISOLATE → MIGRATE BEHAVIOR → VERIFY → RETIRE**

This prevents accidental regressions while progressively removing architectural debt.

---

# 14. Feature Decision Matrix

| Feature | Decision | Priority |
|---|---|---:|
| Existing auth | KEEP + HARDEN | High |
| Profile | MODIFY | High |
| Goals | MODIFY | High |
| Availability | ADD/CONNECT | High |
| Equipment | CONNECT TO PLAN | High |
| Locations | ADD/CONNECT | Medium |
| Weekly plan | MODIFY | High |
| Today/day execution | MODIFY | **Critical** |
| Exercise logging | KEEP + MODIFY | **Critical** |
| Planned vs actual | ADD/STRENGTHEN | **Critical** |
| Training result | ADD/STRENGTHEN | **Critical** |
| Deterministic adaptation | ADD | High |
| Basketball | MODIFY + DEEPEN | High |
| Recovery | MODIFY | High |
| Progress | MODIFY | High |
| Nutrition | MODIFY | Medium |
| History/events | ADD INCREMENTALLY | High |
| AI Coach | DEFER | Later |
| AI Manager | DEFER | Later |
| AI Kitchen | DEFER | Later |
| Discord | DEFER | Later |
| Stripe/subscriptions | DEFER | Later |
| Multiple sports | DEFER | Later |
| Wearables | DEFER | Later |
| Social/marketplace | DEFER | Later |
| Advanced gamification | DEFER | Later |

---

# 15. Recommended Implementation Order After Audit

## Stage 1A — Repository/Security Baseline

Before product feature work:

1. inspect committed database files;
2. determine whether any real/private data is present;
3. fix repository ignore rules;
4. remove sensitive artifacts if appropriate;
5. verify the active runtime path;
6. establish a clean baseline commit.

**Gate:** repository does not unnecessarily expose private database artifacts.

---

## Stage 1B — Core Product Mapping

Next map the actual active frontend into:

- TODAY
- PLAN
- TRAINING
- PROGRESS
- SPORT
- NUTRITION
- PROFILE
- SETTINGS/INTEGRATIONS

For each screen document actual current behavior and backend endpoints.

**Gate:** no important core-loop behavior remains unknown.

---

## Stage 2 — First Vertical Slice

The first implementation target should be:

### TRAINING EXECUTION VERTICAL SLICE

```
Existing Plan
   ↓
Today's Session
   ↓
Start
   ↓
Execute
   ↓
Log sets/reps/load/RPE
   ↓
Complete
   ↓
Session Result
   ↓
Persist actual result
```

This is the smallest slice that materially transforms the existing application toward EVOLVE.

It also creates the foundation for adaptation and progress.

---

# 16. What We Should NOT Do Yet

Do not start by:

- rewriting `index.html`,
- creating a new frontend framework,
- splitting every database table,
- building AI Coach,
- building an autonomous agent,
- implementing all basketball metrics,
- implementing all nutrition features,
- removing all legacy code,
- adding multiple sports,
- building a huge dashboard,
- redesigning every screen.

The current product already contains useful capabilities. The goal is to **connect and improve them**, not discard them.

---

# 17. Current Checkpoint

### DONE

- EVOLVE product direction approved.
- Product plan committed as `EVOLVE_PRODUCT_PLAN.md`.
- Current `main` inspected directly.
- Backend architecture mapped at first-pass level.
- Core data model inspected.
- Plan/training/logging/basketball/recovery/progress capabilities identified.
- Legacy coupling identified.
- Repository database-artifact risk identified.

### CURRENT

**Stage 1 — Product Audit**

Current substage:

**1A / 1B — repository baseline + active product mapping**

### NEXT

1. Inspect committed database artifacts safely.
2. Determine the exact active frontend flow.
3. Map the current core-loop screens/endpoints.
4. Finalize the Stage 1 KEEP/MODIFY/ADD/REMOVE/DEFER matrix.
5. Commit the completed Stage 1 audit.
6. Begin the first Training Execution vertical slice.

---

## Final Stage 1 conclusion

The current application is **not a blank starting point**.

It already has much of the raw machinery required for EVOLVE:

**profile + plan + daily execution + exercise results + basketball drills + recovery inputs + nutrition + progress analysis.**

The main problem is that these capabilities are still organized around the older **FitAI dashboard architecture**, rather than one coherent **performance-coach loop**.

Therefore the central EVOLVE strategy is:

> **Connect what already exists, strengthen the core loop, remove legacy coupling gradually, and only then expand the system.**


## Stage 1 Security Closure — Database Artifacts

Status: **CURRENT TREE CLEAN / HISTORY REQUIRES SEPARATE DECISION**

The public `main` tree previously contained SQLite runtime artifacts:
- `fitai.db`
- `fitai.db-shm`
- `fitai.db-wal`
- two `fitai.db.bak_*` backups

Because the GitHub connector cannot safely inspect binary SQLite contents, these artifacts were treated as potentially sensitive rather than assumed to be test-only data. They were removed from the current `main` tree and `.gitignore` now excludes `*.db`, `*.db-shm`, and `*.db-wal`.

**Important:** deletion from the current tree does not erase historical Git objects. A later history purge may be warranted if the database ever contained real/private data, but that is intentionally kept separate from the normal Stage 1 implementation flow because it is a destructive repository-history operation.

Verification after cleanup: recursive `main` tree contains **0 SQLite database artifacts** matching the audited patterns.

## Stage 1 Updated Checkpoint

**DONE**
- Product direction documented in `EVOLVE_PRODUCT_PLAN.md`.
- First-pass architecture/product audit documented.
- Public repository database-artifact exposure closed in the current tree.
- SQLite artifacts added to ignore rules.

**CURRENT**
- Finalize the active Training/TODAY execution contract from the existing implementation.
- Identify the smallest deterministic vertical slice that turns an existing planned workout into a persisted actual training result.

**NEXT**
- Stage 2: Training Execution vertical slice: **Plan → Start → Execute → Log → Complete → Result**.
- Keep the existing UI and data model where possible; introduce only the minimum new persistence/contracts needed to make planned-vs-actual execution reliable.
- Add focused tests first, then the stage gate regression/security checks.
