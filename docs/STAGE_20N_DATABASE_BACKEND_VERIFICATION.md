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
- CI run #690 caught the outdated expected-head assertion after migration integrity passed; the assertion was corrected. Latest test commit: `5f6ff6e966b3076cbcac297d21c53d92ff204179`; push run #693 is queued at last check.
