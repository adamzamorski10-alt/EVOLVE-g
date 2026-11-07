#!/usr/bin/env bash
# ==============================================================================
# EVOLVE — Skrypt tworzenia kopii zapasowej PostgreSQL (pg_dump)
# Użycie: ./scripts/backup_db.sh [katalog_docelowy]
# ==============================================================================
set -euo pipefail

DEST_DIR="${1:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${DEST_DIR}/evolve_backup_${TIMESTAMP}.sql.gz"
SHA_FILE="${BACKUP_FILE}.sha256"

mkdir -p "${DEST_DIR}"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "BŁĄD: Zmienna środowiskowa DATABASE_URL nie jest ustawiona." >&2
  exit 1
fi

if [[ "${DATABASE_URL}" == sqlite* ]]; then
  echo "UWAGA: Wykryto SQLite. Kopiowanie pliku bazy SQLite..."
  SQLITE_PATH="${DATABASE_URL#sqlite:///}"
  if [ -f "${SQLITE_PATH}" ]; then
    gzip -c "${SQLITE_PATH}" > "${BACKUP_FILE}"
  else
    echo "BŁĄD: Plik bazy SQLite nie istnieje: ${SQLITE_PATH}" >&2
    exit 1
  fi
else
  # Obsługa PostgreSQL URL (w tym postgresql+psycopg://)
  CLEAN_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"
  
  if ! command -v pg_dump >/dev/null 2>&1; then
    echo "BŁĄD: Narzędzie pg_dump nie jest zainstalowane w systemie." >&2
    exit 1
  fi

  echo "Tworzenie kopii zapasowej PostgreSQL z DATABASE_URL..."
  pg_dump --no-owner --no-privileges --clean --if-exists "${CLEAN_URL}" | gzip > "${BACKUP_FILE}"
fi

# Obliczenie sumy kontrolnej SHA-256
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "${BACKUP_FILE}" > "${SHA_FILE}"
elif command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "${BACKUP_FILE}" > "${SHA_FILE}"
fi

FILE_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "✅ Kopia zapasowa utworzona pomyślnie:"
echo "   Plik: ${BACKUP_FILE} (${FILE_SIZE})"
if [ -f "${SHA_FILE}" ]; then
  echo "   Suma SHA256: $(cat "${SHA_FILE}")"
fi
