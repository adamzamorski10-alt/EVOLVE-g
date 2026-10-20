# Stage 20N — Database Backend Verification

Status: repository-side work in progress; deployed backend verification is blocked pending environment access.

## Findings

- `render.yaml` does not declare `DATABASE_URL`; `app/config.py` defaults to SQLite. This does not prove the deployed service's actual backend because hosting dashboard variables may override defaults.
- CI explicitly uses SQLite.
- Migration `0d74b80a4276_evolve21_sync_models_with_migrations.py` drops `uq_training_active_user_day`; the previous migration chain did not recreate it at the latest schema head.
- Added `alembic/versions/evolve21active_session_unique.py` to recreate the partial unique index on `training_sessions(user_id, session_date)` for rows with `status = 'active'`. It supports SQLite/PostgreSQL and fails closed on other dialects.
- The initial CI run caught an Alembic multiple-head error because the new migration was initially attached directly to `0d74b80a4276`. It was corrected to follow the current schema tip, `evolve24_sport_training_schedule`.
- `.github/workflows/tests.yml` now asserts the expected partial unique index exists after the clean migration upgrade.

## Evidence and remaining gates

- Corrected migration commit: `175db6cade26044bbc807cd6d418dd335de45cda`.
- CI PR run #688: https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/38080808206 (in progress at last check).
- CI push run #687: https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/38080805306 (queued at last check).
- Actual deployed database backend, deployed Alembic head/index, and concurrent-start / set-write-vs-completion checks on that backend remain unverified. Do not expose credentials or run destructive race tests against real user data.
- EV-022 real-browser verification remains pending.
- Keep PR #50 draft and do not merge until current-head CI passes and deployment-specific evidence is recorded.


## Follow-up CI corrections

- The migration was chained after `evolve24_sport_training_schedule`; the initial attachment to `0d74b80a4276` produced two heads and was rejected by CI.
- `TrainingSessionDB` now declares the same partial unique index in SQLModel metadata so `alembic check` can compare the migrated database with the model definitions without reporting the index as an unexpected removal.
- Updated the migration-head regression assertion to expect `evolve21active_session_unique` as the single current head.
- CI run #690 caught the outdated expected-head assertion after migration integrity passed; the assertion was corrected. Final Stage 20N repository CI head: `155c6eb56d22bdf065dfa40e8a2a263687ad707b`. Push workflow #693 (https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/38080939768) and PR workflow #694 (https://github.com/adamzamorski10-alt/EVOLVE-g/actions/runs/38080942789) both completed successfully: 315 passed, 7 warnings; Alembic clean-database integrity and the new partial-index assertion passed. The legacy regression remains an informational failure and is not counted as passing.


## PostgreSQL CI follow-up (2026-10-10)

- The PostgreSQL 16 job now successfully upgrades the clean database to the latest head and confirms the partial active-session index exists.
- `alembic check` exposed a pre-existing schema drift: PostgreSQL retained the implicit unique constraint `users_user_key_key`, while current SQLModel metadata models this invariant through the unique index `ix_users_user_key`. Added migration `evolve25userkey` to remove only that redundant PostgreSQL constraint when present; the unique index remains the uniqueness enforcement.
- The migration-chain test now expects `evolve25userkey` as the single head.
- The CI run for commit `6bea808f` passed the current Stage 0–5 regression and clean SQLite migration integrity, but PostgreSQL `alembic check` failed on the schema drift described above. The new migration and updated head assertion are awaiting CI verification.
- This proves only CI behavior against PostgreSQL 16 and SQLite. It does not identify the actual deployed Render database backend or verify production schema.
- EV-022 browser verification remains pending.

- A follow-up PostgreSQL run caught that the first revision identifier exceeded Alembic's 32-character version column. Renamed the revision to the short identifier `evolve25userkey`; the rerun is required before the PostgreSQL gate can be considered green.


## Latest PostgreSQL assertion correction (2026-10-10)

- CI run #38082938837 confirmed the PostgreSQL migration chain and `alembic check` completed, but the final partial-index assertion failed because its mixed-case expected fragments were compared against a lowercased database definition. The failure was in the test assertion; the returned index definition was `CREATE UNIQUE INDEX ... WHERE ((status)::text = 'active'::text)`.
- Updated the assertion to normalize the returned definition to uppercase and whitespace-normalized text, then verify the filtered predicate contains `WHERE`, `STATUS`, and `'ACTIVE'`.
- Fix commit: `04872302b66507169e9a49c5b06b955b54094966`. Push run #38083403310 and PR run #38083406643 are currently running; PostgreSQL gate is not yet considered PASS.
- Legacy regression continues to fail as an informational job and is not represented as passing.
- Production backend verification and EV-022 browser verification remain pending.
