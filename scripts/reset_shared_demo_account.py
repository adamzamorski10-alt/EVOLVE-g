#!/usr/bin/env python3
"""
scripts/reset_shared_demo_account.py — Narzędzie administracyjne do czyszczenia/resetowania współdzielonego konta #01

OPIS:
Konto #01 (oraz ewentualne konta demo utworzone w poprzednich wersjach) mogło być
przez pewien czas publicznie dostępne z powodu automatycznego logowania.
Dane zgromadzone na tym koncie należy traktować jako NIEZAUFANE.

To narzędzie pozwala:
1. Sprawdzić (w trybie --dry-run jako domyślnym), ile rekordów w każdej tabeli
   jest powiązanych ze wskazanym kontem (--email lub --user-number).
2. Wyzerować profil biometryczny oraz historię treningów/odżywiania (--reset-data).
3. Opcjonalnie usunąć całe konto i wszystkie powiązane rekordy kaskadowo (--cascade-delete).
4. Ustawić nowe, silne hasło dla właściciela konta (--password <nowe_hasło>).

BEZPIECZEŃSTWO:
- Domyślnie działa w trybie bezpiecznym [DRY-RUN] (żadne dane nie są zmieniane).
- Wymaga podania flagi --execute, aby faktycznie zapisać zmiany w bazie.
"""
import argparse
import os
import pathlib
import sys
from typing import Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import create_engine, text
from sqlmodel import Session, select


RELATED_TABLES = [
    "daily_logs",
    "nutrition_entries",
    "nutrition_adaptations",
    "training_sessions",
    "training_set_results",
    "exercise_results",
    "goals",
    "adaptive_plan_revisions",
    "drill_results",
    "sport_attempts",
    "assessments",
    "refresh_tokens",
    "user_number_sequence",
]


def count_related_records(session: Session, user_id: str) -> dict[str, int]:
    counts = {}
    for table in RELATED_TABLES:
        try:
            res = session.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE user_id = :uid"),
                {"uid": user_id},
            ).scalar()
            counts[table] = int(res or 0)
        except Exception:
            counts[table] = 0
    return counts


def main():
    parser = argparse.ArgumentParser(
        description="Resetowanie danych lub usuwanie współdzielonego konta EVOLVE."
    )
    parser.add_argument("--database-url", default=None, help="URL bazy danych (domyślnie z DATABASE_URL)")
    parser.add_argument("--email", default=None, help="Email użytkownika do resetu")
    parser.add_argument("--user-number", type=int, default=None, help="Numer konta użytkownika (np. 1)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Tylko inspekcja (domyślnie włączone)")
    parser.add_argument("--execute", action="store_true", help="Faktyczne wykonanie operacji zapisu")
    parser.add_argument("--reset-data", action="store_true", help="Zeruje dane treningowe i profil biometryczny")
    parser.add_argument("--cascade-delete", action="store_true", help="Usuwa konto oraz powiązane rekordy kaskadowo")
    parser.add_argument("--password", default=None, help="Nowe hasło do konta")

    args = parser.parse_args()

    # Określenie trybu pracy
    is_dry_run = not args.execute

    if not args.email and args.user_number is None:
        print("BŁĄD: Musisz podać --email lub --user-number.", file=sys.stderr)
        sys.exit(1)

    db_url = args.database_url or os.getenv("DATABASE_URL")
    if not db_url:
        print("BŁĄD: Brak DATABASE_URL w argumencie lub środowisku.", file=sys.stderr)
        sys.exit(1)

    # Importy po ew. ustawieniu DATABASE_URL
    os.environ["DATABASE_URL"] = db_url
    from app.models import UserDB
    from app.auth.security import hash_password

    engine = create_engine(db_url)

    with Session(engine) as session:
        # Znajdź użytkownika
        query = select(UserDB)
        if args.email:
            query = query.where(UserDB.email == args.email.strip().lower())
        if args.user_number is not None:
            query = query.where(UserDB.user_number == args.user_number)

        user = session.exec(query).first()
        if not user:
            ident = args.email or f"#{args.user_number}"
            print(f"Użytkownik {ident} nie został odnaleziony w bazie danych.")
            sys.exit(0)

        user_id = str(user.id)
        mode_str = "[DRY-RUN]" if is_dry_run else "[EXECUTE]"
        print(f"\n{mode_str} Znaleziono użytkownika: id={user.id}, email={user.email}, user_number={user.user_number}, name={user.name}")

        counts = count_related_records(session, user_id)
        print("\nPowiązane rekordy w bazie:")
        total_records = 0
        for table, count in counts.items():
            print(f"  - {table}: {count}")
            total_records += count
        print(f"Łącznie powiązanych rekordów: {total_records}\n")

        if is_dry_run:
            print("[DRY-RUN] Żadne dane nie zostały zmodyfikowane. Aby wykonać zmiany, dodaj flagę --execute.")
            return

        # Tryb wykonawczy
        if args.cascade_delete:
            print(f"[EXECUTE] Usuwanie kaskadowe użytkownika {user.email} (id={user.id})...")
            for table in RELATED_TABLES:
                session.execute(
                    text(f"DELETE FROM {table} WHERE user_id = :uid"),
                    {"uid": user_id},
                )
            session.delete(user)
            session.commit()
            print(f"[EXECUTE] Użytkownik {user.email} oraz wszystkie powiązane rekordy zostały usunięte.")
            return

        if args.reset_data:
            print(f"[EXECUTE] Zerowanie danych profilu i historii dla {user.email}...")
            # Usuń wpisy historii
            for table in [
                "daily_logs",
                "nutrition_entries",
                "nutrition_adaptations",
                "training_sessions",
                "training_set_results",
                "exercise_results",
                "goals",
                "adaptive_plan_revisions",
                "drill_results",
                "sport_attempts",
                "assessments",
                "refresh_tokens",
            ]:
                session.execute(
                    text(f"DELETE FROM {table} WHERE user_id = :uid"),
                    {"uid": user_id},
                )

            # Wyzeruj dane profilu użytkownika
            nullable_fields = [
                "age", "height", "weight", "start_weight", "target_weight",
                "goal", "frequency", "diet", "weekly_plan_json",
                "sport_focus", "sport_specialization",
                "health_limitations", "basketball_position",
                "training_experience", "equipment",
            ]
            for f in nullable_fields:
                if hasattr(user, f):
                    setattr(user, f, None)

            user.allergies = ""
            user.notes = ""
            user.injuries = ""
            user.calories_target = 0
            user.protein_target = 0
            user.sport_training_days_json = "[]"
            user.training_availability_json = "{}"
            user.training_locations_json = "[]"
            user.sport_training_schedule_json = "{}"
            user.basketball_profile_json = "{}"
            user.name = "Użytkownik"

        if args.password:
            print(f"[EXECUTE] Ustawianie nowego hasła dla {user.email}...")
            user.hashed_password = hash_password(args.password)

        session.add(user)
        session.commit()
        print(f"[EXECUTE] Zmiany zostały pomyślnie zapisane dla użytkownika {user.email}.")


if __name__ == "__main__":
    main()
