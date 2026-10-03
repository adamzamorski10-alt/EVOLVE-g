# EVOLVE — Pre-Stage 6 Full System Audit

Date: 2026-10-03

## Goal

Reach a high-confidence release candidate for Stages 0–5 before implementing Stage 6. External AI/browser testing is the final independent confirmation, not the primary debugging mechanism.

## Verification layers

1. **Repository/static** — route registration, ownership guards, UI contracts, migration graph, duplicate routes.
2. **Automated runtime** — compileall, full pytest, clean Alembic upgrade and head check.
3. **Security** — authenticated principal → canonical user → owned resource → action; second-user IDOR tests.
4. **Browser/E2E** — real login and native UI flows.
5. **Independent second account** — no cross-user data leakage or mutation.
6. **Release gate** — only after all required evidence exists.

## Defects discovered in this audit

### D1 — Alembic import/bootstrap coupling
Application import eagerly created/mutated DB tables, which made a clean migration verification unsafe.

**Fix:** normal runtime keeps eager bootstrap for compatibility; Alembic sets `EVOLVE_ALEMBIC_CONTEXT=1` before model import so migrations do not trigger application DB bootstrap.

### D2 — Missing explicit Alembic dependency
Alembic was used by the repository but was not explicitly declared.

**Fix:** added Alembic to requirements.

### D3 — CI did not run the full regression
The previous workflow ran only a partial modular list and had no clean-database migration gate.

**Fix:** CI now runs compileall + full pytest + Alembic heads/upgrade/current --check-heads.

### D4 — Native Nutrition shell syntax defect
The generated HTML injection contained a malformed Python string.

**Fix:** nutrition shell is now a dedicated triple-quoted integration block.

### D5 — Duplicate Training route implementation
The training router contained a duplicated implementation block, which could register duplicate HTTP routes.

**Fix:** removed the duplicated tail and added an executable duplicate-route audit test.

### D6 — Broken historical migration graph
`9d8e7f6a5b43` referenced a missing historical revision and a fatigue migration was an orphan head.

**Fix:** repaired the documented chain:
`c8b1f3d9a77d → 9d8e7f6a5b43 → a1b2c3d4e5f6 → 72efb594294f`
while preserving the separate EVOLVE feature branch from `9d8e7f6a5b43`, which is joined by the existing `evolve20migration_merge` migration.

No undocumented schema operation was invented.

## Current automated gate

**Not PASS yet.**

The repository changes are on branch `audit/pre-stage-6-full-system` and PR #43. GitHub Actions evidence must be observed before declaring the automated gate green.

## External gate

EV-001 through EV-019 remain PENDING until a real browser/device/runtime run is executed. In particular EV-018 and EV-019 are mandatory before Stage 6.

## Stage 6 rule

Do not implement Recovery until:
- automated CI gate is green,
- migration graph is verified on a clean DB,
- second-user isolation is externally verified,
- full Stage 0–5 integration flow is externally verified,
- all discovered defects are dispositioned.
