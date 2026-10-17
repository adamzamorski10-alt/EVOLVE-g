# EVOLVE — Pre-Stage 6 Full-System Audit

## Purpose

This audit is a release gate for Stages 0–5. Stage 6 must not begin until the current system is verified as a coherent, executable, user-scoped product.

## Required gates

1. Source/compile integrity
2. Full automated regression
3. Alembic clean-database upgrade + single-head check
4. API route registration and ownership
5. Native shell/domain exposure
6. End-to-end integration across Profile → Assessment → Goals → Plan → Mój dzień → Training → Progress → Nutrition → Adaptation
7. Browser/device verification
8. Independent second-user isolation
9. Final security review
10. Release smoke test

## Findings discovered by the first executable audit

### Fixed

- Duplicate app/training/routes.py implementation was removed. The retained implementation contains the hardened atomic completion flow.
- Malformed nutrition shell injection in app/__init__.py was repaired.
- Alembic was added to runtime requirements.
- Alembic model imports were isolated from application eager DB bootstrap.
- Missing revision 7a6d4c3e9b12 was restored as an explicitly documented no-op bridge because its original file is absent while 9d8e7f6a5b43 references it.
- The independent 72efb594294f migration branch is now reconciled with the Stage 5 chain through evolve20migration_merge.

### Not yet proven

- Full pytest suite has not yet completed successfully.
- Clean alembic upgrade head has not yet completed successfully after the graph repair.
- Browser/device verification is pending.
- Second-user isolation is pending.
- Production-like runtime smoke test is pending.

## Rule

No PASS is inferred from static inspection. Every gate needs executable evidence.
