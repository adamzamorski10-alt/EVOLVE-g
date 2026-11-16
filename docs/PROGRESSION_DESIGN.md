# PROGRESSION_DESIGN.md

Projekt systemu progresji i adaptacji treningu siłowego dla EVOLVE.
Dokument opisuje projekt bez kodu implementacyjnego. Jest wzorcem dla kolejnych PR-ów.

## 1. Cel

System ma realnie przybliżać użytkownika do celu (siła, hipertrofia, sprawność) poprzez:
- wyznaczanie ciężaru startowego (kalibracja),
- podwójną progresję (ciężar + powtórzenia),
- autoregulację objętości tygodniowej na mięsień,
- deloady planowe i reaktywne,
- bezpieczne 경계 przypadki (przerwy, zmiana ćwiczenia, ból, nierealistyczne dane).

Wszystkie reguły są deterministyczne i objaśnialne; użytkownik zawsze widzi uzasadnienie rekomendacji w jednym zdaniu.

## 2. Stan obecny (audyt kodu)

### 2.1 Tabela funkcji

| funkcja | plik | wejście | wyjście | ograniczenia |
|---|---|---|---|---|
| `adapt_exercise(planned, evaluation)` | `app/training/adaptation.py` | plan ćwiczenia (sets, reps, weight_kg) + ewaluacja (decision) | propozycja kolejnego planu (next reps/weight, action, reason_codes) | czysta funkcja, brak zapisów do DB, brak mutacji planu, brak dostępu do użytkownika |
| `evaluate_exercise(planned, completed_sets)` | `app/training/evaluation.py` | plan ćwiczenia + lista zakończonych serii (TrainingSetResultDB) | decyzja per ćwiczenie (progress/maintain/reduce/insufficient_data) + statystyki | brak znajomości kontekstu użytkownika, brak historii poza sesją, brak 1RM |
| `evaluate_session(planned_items, completed_by_exercise)` | `app/training/evaluation.py` | lista ćwiczeń planu + wyniki grupowane po kluczu | ogólna decyzja sesji + podsumowanie | decyduje po najgorszym ćwiczeniu (reduce wygrywa), brak autoregulacji objętości |
| `build_decision(...)` | `app/decision_engine.py` | stany celów, recovery, nutrition, training, constraints | jedna decyzja pętli rdzenia (train_as_planned/reduce/recover/progress/maintain/insufficient_data) | read-only, nie mutuje planu, nie zna weight_kg ani RPE serii |
| `decision_for_user(user, db, target_date)` | `app/decision_service.py` | użytkownik + sesja DB | decyzja dla użytkownika na dzień | importuje `app.training.evaluation` (istnieje na gałęzi), bazuje na ostatniej zakończonej sesji |
| `decision_today(...)` | `app/decision_routes.py` | uwierzytelniony użytkownik + DB | JSON decyzji na dziś | endpoint GET `/app/decision/today`, read-only |
| `_build_adaptive_plan(user_id, session)` | `app/training/routes.py:1472` | użytkownik + sesja DB | propozycja planu adaptacyjnego + źródłowe sesje + podsumowanie | bazuje na ostatnich 6 zakończonych sesjach i migawkę planu, nie zna 1RM |
| `_progression_decision(planned, completed_sets)` | `app/training/routes.py:1231` | plan ćwiczenia + serie | decyzja ewaluacji (owijka evaluate_exercise) | deleguje do evaluation.py |
| `_next_plan_exercise(planned, decision)` | `app/training/routes.py:1292` | plan + decyzja | propozycja kolejnego ćwiczenia (owijka adapt_exercise) | deleguje do adaptation.py |
| `apply_adaptive_plan(user, db)` | `app/training/routes.py:1648` | użytkownik + DB | zapis AdaptivePlanRevisionDB (wersja planu) | POST `/app/training/adaptive/apply`, audit trail, brak wagi startowej/1RM |
| `TrainingSetResultDB` | `app/models.py:426` | session_id, user_id, exercise_key, exercise_name, set_number, planned_weight_kg, actual_weight_kg, actual_rpe, completed | wiersz wyniku jednej serii | ćwiczenie po kluczu tekstowym (exercise_key), nie po id ćwiczenia z bazy |
| `ExerciseResultDB` | `app/models.py:444` | user_id, exercise_name, session_date, sets, reps, weight_kg, rpe, source_session_id | historia wyników ćwiczeń | indeks po nazwie, nie po id ćwiczenia; source_session_id opcjonalny |
| `AdaptivePlanRevisionDB` | `app/models.py:532` | user_id, previous_plan_json, applied_plan_json, decision_summary_json, version | audit trail wersji planu adaptacyjnego | brak powiązania z ćwiczeniem ani 1RM |
| `TrainingSessionDB` | `app/models.py:397` | user_id, session_date, planned_snapshot_json, final_rpe, status | sesja treningowa z migawką planu | final_rpe na poziomie sesji, nie per seria |
| wyświetlanie planu w sesji | `index.html:10653` | dane ćwiczenia (sets, reps, weight_kg, rpe) | tekst celu: "series × reps · weight kg · RPE rpe" | tylko odczyt, weight_kg i rpe opcjonalne |
| input serii w sesji | `index.html:1873,1878,1903` | old.actual_weight_kg, ex.weight_kg, ghost.average_weight_kg; input RPE | POST `/app/training/sessions/{id}/sets` (actual_reps, actual_weight_kg, actual_rpe) | użytkownik może edytować ciężar i RPE każdej serii |
| checkin RPE sesji | `index.html:21030,21228` | _activeDay.rpe | payload.rpe / training_rpe | RPE na poziomie całej sesji, nie per seria |

### 2.2 Odpowiedzi na pytania

**(a) Czy plan v2 przekazuje weight_kg i czy sesja pozwala zapisać ciężar, powtórzenia i RPE dla każdej serii?**
Tak, częściowo. Plan v2 (generator_v2.py) przekazuje dla każdego ćwiczenia `sets`, `reps` i `weight_kg` (w widoku sesji index.html:10653 pokazuje `weight_kg` jeśli obecne). Sesja treningowa pozwala zapisać dla każdej serii: `actual_reps`, `actual_weight_kg`, `actual_rpe` (index.html:1903, model TrainingSetResultDB: `actual_weight_kg`, `actual_rpe`, `actual_reps`). Brak: nie ma trwałego powiązania ćwiczenia z `id` z `app/exercises/data.py` — używany jest `exercise_key`/`exercise_name` tekstowo.

**(b) Co dokładnie dzieje się po zakończeniu sesji?**
1. Użytkownik kończy sesję; `TrainingSessionDB` otrzymuje `status = completed`, `completed_at`, opcjonalnie `final_rpe`.
2. Dla każdej serii zapisywany jest `TrainingSetResultDB` (`actual_weight_kg`, `actual_reps`, `actual_rpe`, `exercise_key`, `exercise_name`).
3. `decision_service._latest_training_signal` pobiera ostatnią zakończoną sesję, grupuje serie po `exercise_key` i wywołuje `evaluate_session`.
4. Wynik (overall_decision: progress/maintain/reduce/insufficient_data) trafia do `build_decision`, który podejmuje decyzję pętli rdzenia.
5. `_build_adaptive_plan` (routes.py:1472) buduje propozycję kolejnego planu na bazie ostatnich 6 sesji i migawki planu, stosując `adapt_exercise` per ćwiczenie.
6. Użytkownik może zastosować adaptację przez `apply_adaptive_plan`, co zapisuje `AdaptivePlanRevisionDB` (nowa wersja planu, audit trail).

**(c) Czy wyniki zapisane pod starą nazwą ćwiczenia (np. przed zmianą name_pl lub scaleniem) łączą się z id ćwiczenia?**
Nie. `TrainingSetResultDB.exercise_key` i `ExerciseResultDB.exercise_name` to pola tekstowe oparte na nazwie, a nie na niezmiennym `id` ćwiczenia z `app/exercises/data.py`. Zmiana `name_pl` lub scalenie ćwiczeń rozrywa ciągłość historii — system nie wie, że stare i nowe nazwy dotyczą tego samego ćwiczenia. Brak mapowania nazwa → id ćwiczenia w tabelach wyników.

**(d) Jak adaptacja traktuje ćwiczenie bez historii?**
`evaluate_exercise` zwraca `insufficient_data` gdy `completed_count == 0` (brak zakończonych serii) lub `planned_sets == 0`. `evaluate_session` przy wszystkich ćwiczeniach z `insufficient_data` daje ogólną decyzję `insufficient_data` i reason_code `INSUFFICIENT_SESSION_DATA`. `build_progress_evidence` wymaga co najmniej 2 obserwacji; przy mniejszej liczbie zwraca `status: insufficient_data`. Adaptacja nie wykonuje prognozy wagi dla nowego ćwiczenia — wymaga kalibracji (pierwsza sesja).

## 3. Model danych (projekt)

Zapisywane per użytkownik i per ćwiczenie (po niezmiennym `id` z `app/exercises/data.py`):

### 3.1 Tabela `exercise_progression` (nowa)

| pole | typ | opis |
|---|---|---|
| `user_id` | FK | użytkownik |
| `exercise_id` | FK (app/exercises/data.py id) | niezmienny identyfikator ćwiczenia |
| `estimated_1rm_kg` | float | ostatni szacowany 1RM (wzór Epley z poprawką RIR) |
| `working_weight_kg` | float | aktualny ciężar roboczy dla docelowych powtórzeń i RIR |
| `target_reps_min` / `target_reps_max` | int | zakres powtórzeń z bazy ćwiczeń |
| `target_rir` | int | docelowy RIR (1-3) |
| `reps_at_current_weight` | int | najlepsze powtórzenia przy aktualnym ciężarze |
| `sessions_without_progress` | int | licznik sesji bez progresu (dla deloadu reaktywnego) |
| `last_session_date` | date | data ostatniej sesji z tym ćwiczeniem |
| `deload_count` | int | liczba wykonanych deloadów |
| `last_deload_date` | date | data ostatniego deloadu |
| `calibrated` | bool | czy wykonana kalibracja startowa |

Zapisywane per sesję i per serię (rozszerzenie istniejącego):

### 3.2 Rozszerzenie `TrainingSetResultDB`

Dodatkowo (opcjonalnie, nie ruszając istniejących kolumn):
- `exercise_id` (FK) — powiązanie z niezmiennym id ćwiczenia (migracja wypełnia dla nowych wyników, stare zostają z kluczem tekstowym).
- `est_1rm_kg` — szacowany 1RM z tej serii (Epley z RIR), ułatwiający śledzenie.

### 3.3 Tabela `deload_history` (nowa)

| pole | typ | opis |
|---|---|---|
| `user_id` | FK | użytkownik |
| `start_date` | date | początek deloadu |
| `end_date` | date | koniec deloadu |
| `type` | text | `planned` lub `reactive` |
| `trigger` | text | powód (np. "2 ćwiczenia bez progresu × 2 sesje + RPE ≥ 8") |

## 4. Wyznaczanie ciężaru startowego

### 4.1 Brak historii — pierwsza sesja kalibracyjna

Użytkownik wykonuje pierwszą sesję z danym ćwiczeniem jako kalibracyjną. Podaje:
- ciężar, który uniósł (`weight_kg`),
- liczbę powtórzeń (`reps`),
- RPE lub RIR (jeśli brak, domyślne RIR = 2 z ostrzeżeniem).

Szacowany 1RM (wzór Epley z poprawką na RIR):

```
est1RM = weight * (1 + (reps + RIR) / 30)
```

Gdzie RIR = 11 - RPE (jeśli podano RPE), w przeciwnym razie podany RIR.

### 4.2 Ciężar roboczy dla docelowych powtórzeń i RIR

```
working_weight = est1RM / (1 + (target_reps + target_RIR) / 30)
```

`target_reps` i `target_RIR` pochodzą z bazy ćwiczeń (zakres powtórzeń) i ustawień użytkownika (docelowy RIR 1-3).

### 4.3 Zaokrąglenia do kroków sprzętu

| sprzęt | krok |
|---|---|
| sztanga | 2,5 kg |
| hantle | 1-2 kg (zależnie od zakresu) |
| maszyny | 2,5-5 kg |
| wyciąg | 2,5 kg |
| masa własna | progresja przez powtórzenia i warianty (brak kroku ciężaru) |

Ciężar roboczy jest zaokrąglany w dół do najbliższego dostępnego kroku sprzętu, aby uniknąć przeciążenia przy starcie.

## 5. Podwójna progresja

Zakres powtórzeń pochodzi z bazy ćwiczeń (`target_reps_min`–`target_reps_max`). Docelowy RIR = 1-3 (zalecane 2).

### 5.1 Reguły decyzyjne po sesji

Dla każdego ćwiczenia, na podstawie wszystkich serii robocze z tej sesji:

1. **Wszystkie serie robocze osiągnęły górę zakresu powtórzeń przy RIR ≥ 1** → podnieś ciężar o jeden krok sprzętu i wróć do dolnej granicy zakresu powtórzeń.
2. **W zakresie powtórzeń, ale poniżej góry** → ten sam ciężar, następna sesja cel = +1 powtórzenie (do osiągnięcia górnej granicy).
3. **Poniżej dolnej granicy zakresu dwa razy z rzędu** → zmniejsz ciężar o 5-10 procent (maksymalnie jeden krok w dół).

### 5.2 Limit skoku

Nigdy więcej niż jeden krok sprzętu lub 5 procent na sesję (to, co mniejsze). Dla ćwiczeń z małymi ciężarami (mięśnie małe) krok 1 kg lub 2,5 kg zamiast procentu.

### 5.3 Masa własna

Gdy ćwiczenie nie używa zewnętrznego ciężaru, progresja odbywa się przez:
- zwiększenie liczby powtórzeń w zakresie,
- przejście na trudniejszy wariant (np. przysiad klasyczny → przysiad bułgarski),
- dodanie serii w granicach celu objętości.

## 6. Autoregulacja objętości tygodniowej na mięsień

Cel objętościowy pochodzi z `VOLUME_TARGETS_INTERMEDIATE` (generator_v2.py) i mnożnika dla początkujących (0.7):

| mięsień | cel intermediate (min-max) | cel początkujący (min-max) |
|---|---|---|
| klatka | 10-14 | 7-10 |
| plecy | 12-16 | 8-11 |
| barki boczne | 8-12 | 6-8 |
| biceps | 6-10 | 4-7 |
| triceps | 6-10 | 4-7 |
| czworogłowe | 10-14 | 7-10 |
| dwugłowe | 8-12 | 6-8 |
| łyżki | 6-10 | 4-7 |

### 6.1 Reguły dodawania / odejmowania jednej serii

Na koniec każdego tygodnia, per mięsień, ocenia się:
- średni RPE ćwiczeń danego mięśnia,
- realizację planu (procent serii wykonanych),
- zgłoszone bóle (użytkownik zaznacza ból w aplikacji),
- ocenę regeneracji (checkin: energia, sen, stres, nastrój).

Decyzja:
- **Dodaj jedną serię** jeśli: średni RPE ≤ 6, plan wykonany w ≥ 90%, brak bólu, regeneracja dobra, i obecna objętość < górnej granicy celu.
- **Odejmij jedną serię** jeśli: średni RPE ≥ 8.5, plan wykonany w < 80%, lub ból / regeneracja zła, i obecna objętość > dolnej granicy celu.
- **Bez zmian** w pozostałych przypadkach.

Objętość nigdy nie wychodzi poza zakres celu (min-max) dla danego poziomu. Limity czasu sesji (np. max 75 min) ograniczają liczbę ćwiczeń/serii — jeśli dodanie serii przekracza limit, pomijaj dodanie.

## 7. Deload

### 7.1 Deload planowy

Co 5-6 tygodni treningu danego ćwiczenia (lub planu ogólnie) następuje deload planowy.

### 7.2 Deload reaktywny

Uruchamia się gdy spełnione są wszystkie:
- co najmniej dwa ćwiczenia bez progresu w dwóch kolejnych sesjach,
- wzrost średniego RPE (≥ 8) w tych sesjach,
- lub zgłoszona zła regeneracja przez dwa checkiny z rzędu.

### 7.3 Parametry deloadu

- serie: minus 40 procent (zaokrąglone w dół, minimum 1 seria na ćwiczenie),
- ciężar: minus 10 procent (lub ten sam ciężar, mniej powtórzeń, dla ćwiczeń z masą własną),
- czas trwania: jeden tydzień.

### 7.4 Powrót

Po deloadzie wraca się do poprzedniego ciężaru roboczego i kontynuuje progresję od dolnej granicy zakresu powtórzeń. Licznik `sessions_without_progress` się resetuje.

## 8. Bezpieczeństwo i przypadki brzegowe

| sytuacja | reguła |
|---|---|
| przerwa dłuższa niż 14 dni | zmniejsz ciężar roboczy o 10-15 procent przy powrocie, पहली sesja po przerwie jest lekka (RIR wyższy) |
| zmiana ćwiczenia | przenieś est1RM wyłącznie w tej samej rodzinie ćwiczeń (np. przysiad z hantlami → przysiad klasyczny); między rodzinami zacznij od kalibracji |
| brak RPE | domyślne RIR = 2, wyświetl ostrzeżenie "Brak oceny wysiłku — założono RIR 2" |
| użytkownik zgłasza ból | zdejmij ćwiczenie z planu na następną sesję i zaproponuj zamiennik (ten sam wzorzec ruchu, inny sprzęt lub wariant) |
| nierealistyczne dane | skok est1RM o więcej niż 15 procent między sesjami: odrzuć wynik, poproś użytkownika o potwierdzenie lub korektę |
| brak historii | pierwsza sesja kalibracyjna, nie stosuj progresji |

## 9. Interfejs użytkownika

### 9.1 Co użytkownik widzi w sesji

Dla każdego ćwiczenia w planie dzisiejszym:
- **Ostatnio:** ciężar × powtórzenia (z ostatniej sesji tego ćwiczenia),
- **Dzisiaj:** rekomendacja (ciężar × powtórzenia, RIR) z uzasadnieniem w jednym zdaniu (np. "Osiągnąłeś górę zakresu 10-12 przy RIR 2 — podnoszę ciężar o 2,5 kg i wracam do 10 powtórzeń"),
- stan kalibracji (jeśli पहली sesja: komunikat "To twoja pierwsza sesja z tym ćwiczeniem — podaj ciężar, powtórzenia i RPE").

### 9.2 Wprowadzanie serii

Dla każdej serii użytkownik wprowadza:
- liczbę wykonanych powtórzeń,
- rzeczywisty ciężar (kg),
- RPE (1-10) lub RIR.

Wartości domyślne: ciężar z planu, RPE pusty (domyślnie RIR 2 z ostrzeżeniem).

### 9.3 Kalibracja

Pierwsza sesja z nowym ćwiczeniem otwiera formularz kalibracyjny: ciężar, powtórzenia, RPE/RIR. System oblicza est1RM i ciężar roboczy, wyświetla je użytkownikowi przed pierwszą serią roboczą.

## 10. Plan testów

### 10.1 Testy jednostkowe

- wyznaczanie ciężaru startowego (Epley z poprawką RIR) dla zestawu wag/powtórzeń/RIR,
- zaokrąglenia do kroków sprzętu (sztanga 2,5 kg, hantle 1-2 kg, maszyny 2,5-5 kg, wyciąg 2,5 kg),
- reguły podwójnej progresji (podnieś ciężar / ten sam ciężar +1 powtórzenie / zmniejsz o 5-10%),
- limit skoku (max jeden krok lub 5% na sesję),
- autoregulacja objętości (dodaj/odejmij jedną serię w granicach VOLUME_TARGETS_INTERMEDIATE i mnożnika 0.7 dla początkujących),
- deload planowy (co 5-6 tygodni) i reaktywny (2 ćwiczenia bez progresu × 2 sesje + RPE ≥ 8),
- przypadki brzegowe (przerwa >14 dni, zmiana ćwiczenia w tej samej rodzinie, brak RPE, ból, skok est1RM >15%).

### 10.2 Symulacja 12 tygodni (wirtualny użytkownik)

Deterministyczny model odpowiedzi użytkownika:
- siła rośnie w czasie dla ćwiczeń złożonych (est1RM rośnie o ustalony procent co tydzień),
- zmęczenie narasta (RPE rośnie stopniowo),
- losowe słabsze tygodnie z ustalonym ziarnem (co trzeci tydzień niższe powtórzenia/wyższe RPE).

Asercje:
1. Ciężary rosną w czasie dla ćwiczeń złożonych (średni ciężar w tygodniu 12 > tygodniu 1).
2. Skoki ciężaru nie przekraczają limitu (jeden krok lub 5% na sesję).
3. Deload uruchamia się w poprawnym momencie (planowy w tygodniu 5 lub 6; reaktywny przy spełnieniu warunków).
4. Objętość pozostaje w granicach celu (VOLUME_TARGETS_INTERMEDIATE lub 0.7× dla początkujących).
5. Po deloadzie wraca progresja (ciężar w tygodniu po deloadzie >= ciężar przed deloadem po 2 sesjach).

Symulacja jest deterministyczna (ustalone ziarno losowości), więc wyniki są powtarzalne.

## 11. Podział na PR-y

| PR | zakres | trudność |
|---|---|---|
| PR-1 | Model danych: nowa tabela `exercise_progression` i `deload_history`, rozszerzenie `TrainingSetResultDB` o `exercise_id` + migracja wypełniająca id dla nowych wyników | średnia (migracje, kompatybilność wsteczna) |
| PR-2 | Wyznaczanie ciężaru startowego: kalibracja, Epley z poprawką RIR, zaokrąglenia do kroków sprzętu, interfejs kalibracji w sesji | średnia |
| PR-3 | Podwójna progresja: reguły decyzyjne, limit skoku, progresja masy własnej | średnia |
| PR-4 | Autoregulacja objętości tygodniowej na mięsień z granicami VOLUME_TARGETS_INTERMEDIATE i limitem czasu sesji | wysoka (wymaga danych o mięśniach ćwiczeń) |
| PR-5 | Deload planowy i reaktywny, parametry, powrót, licznik sesji bez progresu | średnia |
| PR-6 | Bezpieczeństwo i przypadki brzegowe (przerwa >14d, zmiana ćwiczenia, brak RPE, ból, skok est1RM >15%) | niska |
| PR-7 | Interfejs: ostatnio/dzisiaj z uzasadnieniem, wprowadzanie serii, kalibracja | średnia (frontend index.html + endpointy) |
| PR-8 | Testy jednostkowe + symulacja 12 tygodni z asercjami | średnia |

Kolejność: PR-1 → PR-2 → PR-3 → PR-4 → PR-5 → PR-6 → PR-7 → PR-8.

## 12. Ryzyka dla istniejących danych

- **Migracje:** dodanie kolumny `exercise_id` do `TrainingSetResultDB` wymaga migracji; stare wiersze mają tylko `exercise_key`/`exercise_name` tekstowo — nie da się ich w pełni powiązać z id ćwiczenia jeśli nazwa uległa zmianie. Nowe wyniki muszą zapisywać oba pola.
- **Kompatybilność z aktualnymi sesjami:** istniejące sesje w bazie mają migawki planu bez `weight_kg` per ćwiczenie (lub z opcjonalnym); system progresji musi obsługiwać brak `weight_kg` (upadek do kalibracji).
- **Zmiana name_pl / scalanie ćwiczeń:** bez mapowania nazwa → id ćwiczenia historia jest fragmentarna; zalecane jest wprowadzenie tabeli aliasów ćwiczeń (stara nazwa → nowe id) przed uruchomieniem progresji na danych historycznych.
- **Brak katalogu `app/training/` na niektórych gałęziach:** importy `app.training.evaluation` mogą być uszkodzone poza główną linią desarrollo; trzeba zweryfikować przed wdrożeniem.
