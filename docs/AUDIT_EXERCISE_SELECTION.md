# AUDIT EXERCISE SELECTION — EVOLVE (dobór ćwiczeń i budowa planu siłowego + baza ćwiczeń)

**Status:** tylko odczyt (zero zmian w kodzie aplikacji i w bazie ćwiczeń).
**Gałąź:** `audit/exercise-selection` (utworzona z `main`, working tree czysty przed začciem).
**Zakres:** kod generatora planu w `app/` oraz baza ćwiczeń `_exercise_pool()` w `app/legacy_routes.py`. Raport nie opisuje niczego, czego nie zweryfikowano w kodzie lub w uruchomieniu generatora (12 person, symulacja w `audit_tmp_plans.py`).

---

## CZĘŚĆ A — Generator planu (kod)

### A1. Pliki i funkcje odpowiedzialne za poszczególne obszary

| Obszar | Plik | Funkcja / fragment |
|--------|------|--------------------|
| Wybór splitu (liczba dni, full body / upper-lower / PPL) | `app/plan/deterministic.py` | `build_deterministic_plan()` — `target_days` z `assessment.sessions_per_week` lub `user.frequency`, clamp 1–6 (linia ~150); dni rozpisywane Pon–Sob, Niedziela stały dzień spoczynku (`_DAY_SCHEDULE` linia 25); partie przypisywane cyklicznie z listy `preferred` (linia 430-439). Nie ma szablonów FB/UL/PPL — każdy dzień to jedna partia z listy użytkownika. |
| Dobór ćwiczeń | `app/plan/deterministic.py` + `app/legacy_routes.py` | `_exercise_pool()` (linia 852) — słownik 62 ćwiczeń w 9 grupach; `_exercise_allowed()` (linia 93) — filtrowanie sprzętowe i `avoid_exercises`; wybór `available[:exercise_limit]` (linia 461) po sortowaniu po priorytecie postępu (`_progress_priority`, linia 382) i kolejności w puli. |
| Serie / powtórzenia / RIR / przerwy | `app/plan/deterministic.py` | Wzięte na sztywno z puli (`ex["sets"]`, `ex["reps"]`, np. `"4"`, `"6-8"`). Brak pola RIR, brak przerw między seriami, brak dopasowania zakresów do celu. |
| Progresja i deload | `app/training/adaptation.py` (`adapt_exercise`), `app/training/evaluation.py` (`evaluate_exercise`/`evaluate_session`), `app/decision_engine.py` (`build_decision`), `app/training/routes.py` (`_build_adaptive_plan`, `/adaptive/apply`) | Progresja działa po zakończeniu sesji: ocena (completion <80% → reduce; RPE >8 → maintain; reps poniżej celu → maintain; else progress) + adaptacja (+2.5% obciążenia, limit 5%, rzut 2,5 kg, min +2,5 kg; jeśli weight=0 → +1 powtórzenie; reduce → −2,5% lub −1 rep). Deload: **brak** logiki tygodnia odciążającego; tylko transientne obniżenie objętości z contraintes odzyskiwania (`_apply_recovery_constraint`, reduce_volume_25/50). |
| Dopasowanie do poziomu | `app/plan/deterministic.py` linia 397-399 | `training_level == "początkujący"` → `exercise_limit = 3` (reszta 4); `recovery_score <= 4` → max 2 ćwiczeń; `<= 6` → max 3. Poziom pochodzi wyłącznie z `assessment.training_level` (pole `user.training_experience` nie jest czytane przez generator). Nie ma filtrowania ćwiczeń po poziomie trudności (pula nie ma takiego pola). |
| Dopasowanie do sprzętu | `app/plan/deterministic.py` linia 342-353 + `app/legacy_routes.py` `_exercise_required_equipment` / `_exercise_allowed` | Sprzęt z `user.get_list("available_equipment_json")` lub preset `user.equipment` (gym_full/gym_free/dumbbells/bodyweight/court/hybrid). Filtrowanie wnioskowane z nazwy ćwiczenia (sztanga/hantle/kettlebell/maszyny/wyciąg/poręcze/ławka). **Błąd:** pusta lista sprzętu (`bodyweight`) spełnia `if not equipment` → wszystkie ćwiczenia dozwolone (patrz TOP 10). |
| Dopasowanie do kontuzji | `app/plan/deterministic.py` linia 356-360 | `health_limitations` / `injuries` skanowane tylko pod kątem słów kluczowych: `"kolan"` → dodaj do avoid `"przysiad ze sztangą"`; `"bark"` → dodaj do avoid `"wyciskanie żołnierskie"`. Brak reguły dla pleców/kręgosłupa, barka poza żołnierskim, stawów itp. |
| Dopasowanie do celu | `app/plan/deterministic.py` linia 534 | `goal` trafia wyłącznie do pola `weekly_goal` w wyjściu. **Nie wpływa na dobór ćwiczeń, serie, powtórzenia, RIR ani przerwy.** Masa, siła i redukcja dostają identyczne zakresy z puli. |

### A2. Charakter algorytmu

Generator planu (`build_deterministic_plan`) jest **deterministyczny i regułowy**. Przy tych samych danych wejściowych zawsze zwraca ten sam plan (zweryfikowane — dwa wywołania dla każdej z 12 person dały identyczny wynik, patrz sekcja C).

**AI nie jest wywoływane przy generowaniu planu siłowego.** Groq (llama-3.1-8b-instant) i Gemini (gemini-2.5-flash) aparecen tylko w:
- `_generate_how_to_ai` w `app/legacy_routes.py` (linia 1072) — generuje brakujący opis techniki ćwiczenia, tylko gdy użytkownik ma plan PRO i `get_how_to()` zwróciło `""`. Wynik to darmowy tekst, **nie walidowany względem bazy ćwiczeń** — AI może wymyślić opis dla ćwiczenia spoza bazy (ale nie doda go do planu, bo plan i tak ćwiczy tylko z puli).
- `regenerate_plan_with_ai` w `app/legacy_routes.py` (linia 2029) — LLM przydziela ćwiczenia do dni (JSON); ćwiczenia są mapowane po nazwie do oryginalnych obiektów z planu, więc ćwiczenie spoza bazy nie trafi do planu.
- `ask_ai` — czat/analiza logów/przepisy, nie dotyczy budowy planu siłowego.

Wniosek: plan sam w себе nie może "wymyślić ćwiczenia spoza bazy"; ćwiczenia w planie zawsze pochodzą z `_exercise_pool()`.

### A3. Dane o użytkowniku: zbierane w onboardingu vs. wykorzystywane przez generator

Zbierane (`AppOnboardingRequest`, `app/schemas.py` linia 223): name, age, height, weight, target_weight, gender, goal, frequency, sports, training_focus, improvement_areas, diet, allergies, preferred_foods, avoid_foods, available_equipment, avoid_exercises, meals_per_day, notes. Później dopisywane: sport_focus, sport_specialization, basketball_position, training_experience, equipment, health_limitations, injuries, training_locations, training_availability.

Wykorzystywane przez `build_deterministic_plan`: `goal` (tylko etykieta w output), `frequency` (liczba dni), `training_focus` + `improvement_areas` (partie dni), `available_equipment` / `equipment` (sprzęt), `avoid_exercises` + `health_limitations`/`injuries` (tylko słowa kluczowe "kolan"/"bark").

**Ignorowane:** wiek, wzrost, waga, target_weight, płeć, dieta, alergie, posiłki/dzień, notatki, dyscyplina sportowa, `training_experience` (poziom pochodzi z assessment), stan zdrowia poza dwoma słowami kluczowymi, dostępność czasowa poza dniami (`availability_hours_per_week` z assessment tylko obniża `exercise_limit` gdy `hours/days < 0.75`).

### A4. Wykorzystanie danych z wykonanych treningów (ciężary, powtórzenia, RIR) — logika progresji

Po zakończeniu sesji zapisuje się `TrainingSetResultDB` (`actual_weight_kg`, `actual_reps`, `actual_rpe`).

1. `evaluate_exercise` (`app/training/evaluation.py`): completion < 80% planowanych serii → `reduce`; średnie RPE > 8 → `maintain`; średnie powtórzenia poniżej celu → `maintain`; w pozostałych przypadkach → `progress`.
2. `build_decision` (`app/decision_engine.py`) łączy to z celami, odzyskiwaniem i oceną celów do decyzji: `progress_training` / `maintain_training` / `reduce_training` / `recover` / `insufficient_data`.
3. `adapt_exercise` (`app/training/adaptation.py`): przy `progress` i `weight_kg > 0` → nowe obciążenie = min(current × 1.025, current × 1.05), zaokrąglone do 2,5 kg, jeśli bez zmiany → +2,5 kg; przy `weight_kg == 0` → `reps + 1`. Przy `reduce` → −2,5% lub −1 powtórzenie.
4. `_build_adaptive_plan` (`app/training/routes.py`) tworzy nową wersję planu dla danego dnia (`AdaptivePlanRevisionDB`) z nowymi `sets`/`reps`/`weight_kg`; **bazowy `weekly_plan_json` nie jest mutowany**.

Istotne ograniczenie: ćwiczenia z planu deterministycznego mają `reps` w zakresie (np. `"6-8"`) i **brak pola `weight_kg`**. Przy normalizacji (`_normalize_plan_item`, `app/training/routes.py` linia 105) `reps` parsowane jako ostatnia liczba z zakresu, `weight_kg = 0` — więc progresja dla nowych ćwiczeń idzie wyłącznie w powtórzeniach. Nie ma prognozy 1RM, nie ma autoregulacji objętościowej, nie ma zaplanowanego deloadu.

---

## CZĘŚĆ B — Baza ćwiczeń (dane)

Źródło: `_exercise_pool()` w `app/legacy_routes.py` (linie 852-1062). Opisy techniki: `app/exercise_descriptions.py` (`EXERCISE_HOW_TO`, `get_how_to`).

### Liczby i struktura
- **62 ćwiczeń razem** w 9 grupach: klatka 8, nogi 8, plecy 8, barki 7, biceps 6, triceps 6, brzuch 7, full body 6, cardio 6.
- Pola na wpis: wyłącznie `name`, `sets`, `reps`, `notes`, `how_to`.
- **Brak pól:** główna/pomocnicza grupa mięśniowa, wzorzec ruchu, wymagany sprzęt, poziom trudności, typ (złożone/izolowane), przeciwwskazania, wskazówki (cues), typowe błędy, wariant łatwiejszy/trudniejszy.
- Wszystkie 62 wpisy mają wszystkie 5 pola wypełnione (brak pustych wartości).

### Duplikaty i prawie-duplikaty
- **Dokładny duplikat (1):** "Martwy ciąg konwencjonalny" występuje w `plecy` (4×4-6) i w `full body` (4×5-6) — różne serie/powtórzenia.
- **Prawie-duplikaty (4 pary, taka nazwa bazowa, inna grupa):**
  - Pompki na poręczach (`klatka`) vs Pompki na poręczach (triceps dips) (`triceps`).
  - Przysiad ze sztangą (back squat) (`nogi`) vs Przysiad ze sztangą (`full body`).
  - Podciąganie nachwytem (szerokim chwytem) (`plecy`) vs Podciąganie nachwytem (`full body`).
  - Martwy ciąg konwencjonalny (patrz wyżej).

### Opisy techniki
- `get_how_to()` zwraca non-empty dla **62/62** ćwiczeń z puli (39 dopasowanie dokładne klucza, 23 przez fallback substring).
- **39 rozbieżności** tekstu między opisem w słowniku `exercise_descriptions.py` a polem `how_to` w puli dla tego samego ćwiczenia (klucz dokładny) — dwa rozbieżne źródła opisu.
- **Brak osobnych pól:** wskazówki (cues), typowe błędy, wariant łatwiejszy/trudniejszy — nie istnieją ani w puli, ani w słowniku opisu.
- `get_how_to` używa fallbacku substring (np. "side plank z rotacją" → opis "plank"), co może dopasować nieodpowiedni opis.
- **Wyświetlanie w interfejsie:** dane `how_to` i `alternatives` są zapisywane w JSON planu (`weekly_plan_json`), ale wbudowane widoki serwerowe **nie renderują `how_to`**: zakładka Plan (`app/plan/routes.py`, `plan_ui`, render pokazuje tylko nazwę, serie, powtórzenia, ciężar) oraz Trening/Mój dzień (`training_today_ui`, `session-ui`) pokazują tylko cel serii. Użytkownik nie widzi opisu techniki w zakładce Trening ani Plan w serwerowym UI.

### Spójność nazw i tagów
- Nie istnieje słownik tagów ani standaryzacja nazw poza pulą.
- Rozbieżność opisów pool vs `exercise_descriptions.py` (39 ćwiczeń).
- Fallback substring w `get_how_to` może zwrócić opis innego ćwiczenia niż nazwa z puli sugeruje.

### Pokrycie według sprzętu
Brak pola sprzętu w bazie — sprzęt wnioskowany z nazwy (`_exercise_required_equipment`), co jest nieszczelne: "Martwy ciąg konwencjonalny" nie zawiera słowa "sztanga", "Podciąganie nachwytem" nie zawiera "poręcz" — przechodzą przez filtr sprzętowego mimo braku sprzętu (zweryfikowane w symulacji persona 2, hantle+ławka, plan obsahuje martwy ciąg i podciąganie). Przy `bodyweight` (pusta lista) **wszystkie ćwiczenia są dozwolone** (`if not equipment → return True`) — użytkownik "tylko masa własna" dostaje sztangę, ławkę, drążek (zweryfikowane, persona 7). Nie da się ocenić pokrycia "pełna siłownia / hantle / masa własna" per grupa, bo baza nie declaró wymaganego sprzętu.

### Ćwiczenia podejrzane merytorycznie
- Martwy ciąg konwencjonalny, rumuński martwy ciąg, przysiad ze sztangą, wiosłowanie sztangą — przepisywane **początkującym bez ostrzeżenia** i bez pola poziomu trudności (brak różnicowania ćwiczeń według poziomu).
- Przy zadeklarowanym bólu dolnego odcinka pleców / kontuzji kręgosłupa generator nie wyklucza martwego ciągu, wiosłowania ani przysiadów (reguła obsługuje tylko "kolan" i "bark") — persona 9 otrzymuje martwy ciąg, RMD, wiosłowanie, przysiad (ryzyko bez ostrzeżenia).
- Przy kontuzji barku wykluczane jest tylko "wyciskanie żołnierskie"; wyciskanie sztangi leżąc i pompki na poręczach (obciążające bark) pozostają; brak ćwiczeń stabilizujących bark (face pull nie trafia do 3-dniowego splitu, bo nie ma dnia barków).

---

## CZĘŚĆ C — Symulacja plany (12 person)

Plany wygenerowane przez wywołanie prawdziwego kodu `build_deterministic_plan` (skrypt `audit_tmp_plans.py`, nie pisane ręcznie). Każdy plan wygenerowany dwa razy — wyniki identyczne (stabilność OK we wszystkich 12).

Kryteria oceny: split vs dni/poziom, częstotliwość grup (~2x/tyd dla masy/siły), objętość séries/tydzień/grupa (norma ~10-20 hipertrofia, mniej dla początkujących), kolejność złożone przed izolowanymi, zakresy powtórzeń i RIR zgodne z celem, przerwy, balans push/pull i przód/tył, brak redundancji, respekt sprzętu i kontuzji, czas sesji, stabilność.

| # | Persona | Werdykt | Uzasadnienie |
|---|---------|---------|--------------|
| 1 | początkujący, 3 dni, masa, siłownia | WARN | Split 3×1 partia, każda grupa 1×/tydzień — poniżej zalecanej ~2× przy masie. Objętość 11 séries/grupa OK dla początkującego. Złożone przed izolowanymi OK. Brak RIR, przerw, dopasowania zakresów do celu (masa = te same rep ranges co siła). Stabilny. |
| 2 | początkujący, 2 dni, ogólna sprawność, dom + hantle | WARN | Częstotliwość 1×/tydzień/grupa. **Naruszenie sprzętu:** przy dostępnych tylko hantlach i ławce plan obsahuje martwy ciąg ze sztangą i podciąganie (filtrowanie nazwowe nie wykrywa sprzętu). Brak RIR/przerw. |
| 3 | średniozaawansowany, 4 dni, masa | WARN | Klatka/plecy/nogi 1×/tydzień (zalecane ~2× przy masie). Objętość 11 séries OK. Brak RIR, przerw, deloadu, różnicy między celem masa/siła/redukcja. Stabilny. |
| 4 | średniozaawansowany, 3 dni, siła | WARN | Plan identyczny jak dla masy (brak niskich range'ów typowych dla siły, brak progresji obciążenia w samym planie). Częstotliwość 1×/tydzień/grupa. Brak RIR/przerw. |
| 5 | zaawansowany, 5 dni, masa | WARN | Klatka 2×/tydzień, pozostałe grupy 1×/tydzień — niezbalansowana częstotliwość. 6 dni aktywnych, tylko 1 dzień spoczynku, **brak deloadu**. Objętości OK. Stabilny. |
| 6 | redukcja, 4 dni | WARN | Plan **identyczny jak dla masy** — cel redukcji nie zmienia objętości, range'ów ani nie dodaje cardio. Objętość 11 séries na grupę przy deficycie może być wysoka. |
| 7 | tylko masa własna | FAIL | Preset `bodyweight` = pusta lista sprzętu → `_exercise_allowed` przepuszcza **wszystkie** ćwiczenia (`if not equipment → return True`, `app/plan/deterministic.py:97`). Użytkownik receives sztangę, ławkę, drążek — nie do wykonania w domu. Krytyczne naruszenie sprzętu. |
| 8 | kontuzja barku | WARN | Wykluczone tylko "wyciskanie żołnierskie". Wyciskanie sztangi leżąc i pompki na poręczach (obciążają bark) pozostają. Brak dnia barków (split 3× klatka/plecy/nogi), brak ćwiczeń stabilizujących (face pull). |
| 9 | ból dolnego odcinka pleców | FAIL | Brak reguły dla pleców/kręgosłupa (obsługiwane tylko "kolan"/"bark"). Plan obsahuje martwy ciąg, RMD, wiosłowanie sztangą, przysiad ze sztangą — obciążenie kręgosłupa przy zadeklarowanym bólu LBP bez ostrzeżenia. |
| 10 | kobieta, początkująca, priorytet pośladki/nogi | WARN | Fokus "pośladki" mapowany na "nogi" — wszystkie 3 dni to nogi, ten sam zbiór 3 ćwiczeń każdego dnia (brak rotacji, brak odpoczynku partii, górne partie pominięte). Objętość nóg 33 séries/tydzień, brak ćwiczeń aktywujących pośladki specyficznie. |
| 11 | 6 dni w tygodniu | WARN | Klatka 2×/tydzień, plecy/nogi/brzuch/barki 1×/tydzień — niezbalansowane. Tylko 1 dzień spoczynku, brak deloadu. Częstotliwość nieodpowiednia dla masy przy tej konstrukcji splitu. |
| 12 | 1 dzień w tygodniu | WARN | Tylko klatka w tygodniu (11 séries), pozostałe grupy 0 — inherentne ograniczenie 1 dnia, ale dla "ogólna sprawność" słabe pokrycie ciała. Brak RIR/przerw/deloadu (nieistotny przy 1 dniu). Stabilny. |

**Stabilność:** 12/12 person — dwa wywołania dla tych samych danych dają identyczny plan (generator deterministyczny).

---

## CZĘŚĆ D — Raport końcowy

### D1. Werdykt (jeden akapit)

Plany EVOLVE są technicznie poprawne jako struktura (podział na partie, kolejność ćwiczeń złożonych przed izolowanymi, rozsądna objętość dla początkujących, deterministyczna i powtarzalna generacja, bezpieczna obsługa braku pasujących ćwiczeń), ale są **generyczne i niewystarczająco spersonalizowane**: cel treningowy (masa/siła/redukcja) nie zmienia programu, brak RIR i przerw między seriami, brak deloadu, brak progresji w samym planie (progresja tylko po zakończonej sesji przez `adapt_exercise`), a najpoważniej — system **nie respektuje wiarygodnie sprzętu ani kontuzji**: preset "masa własna" przepisuje sztangę i ławkę, a ból dolnego odcinka pleców nie wyklucza martwego ciągu ani przysiadów. Plany działają najlepiej dla zdrowych początkujących i średnio zaawansowanych trenujących na pełnej siłowni, którzy potrzebują prostego, sztywnego szablonu. Nie nadają się dla osób z kontuzjami (szczególnie pleców i barku), trenujących w domu lub wyłącznie własnym ciałem, ani dla użytkowników oczekujących prognozy postępu i planowanej okresowej regeneracji.

### D2. Tabela person z werdyktami

(patrz sekcja C powyżej — tabela 12 wierszy: 0 × PASS, 10 × WARN, 2 × FAIL)

### D3. TOP 10 problemów (wg wpływu na użytkownika)

| # | Problem | Dowód (plik:linia / przykład) | Proponowana poprawka | Trudność |
|---|---------|-------------------------------|----------------------|----------|
| 1 | Preset sprzętu "bodyweight" przepuszcza wszystkie ćwiczenia (brak ograniczenia do masy własnej) | `app/plan/deterministic.py:97` (`if not equipment → return True`); persona 7 erhält sztangę/ławkę/drążek | Pusta lista sprzętu powinna oznaczać wyłącznie ćwiczenia własnego ciała; walidować wymagany sprzęt per ćwiczenie zamiast wnioskować z nazwy | Mała |
| 2 | Brak reguły kontuzji pleców/kręgosłupa — martwy ciąg, wiosłowanie, przysiad przy bólu LBP | `app/plan/deterministic.py:356-360` (obsługiwane tylko "kolan"/"bark"); persona 9 FAIL | Dodać wykluczenia dla "plecy"/"kręgosłup"/"lędźwie" (martwy ciąg, RMD, wiosłowanie, przysiad ze sztangą) z ostrzeżeniem | Mała |
| 3 | Cel treningowy ignorowany — masa, siła, redukcja dostają identyczne serie/powtórzenia | `app/plan/deterministic.py:534` (goal tylko w `weekly_goal`); persony 1, 4, 6 identyczne range'y | Dołączyć wybór zakresów powtórzeń i serii do celu (np. siła: 3-5 reps, redukcja: więcej serii/wyższe reps) | Średnia |
| 4 | Brak RIR i przerw między seriami w planie | Pula ćwiczeń ma tylko `sets`/`reps`/`notes`/`how_to` (brak pól RIR/rest) | Dodać pola RIR i przerwy do puli oraz uwzględniać je w wyjściu planu | Średnia |
| 5 | Brak deloadu / periodizacji tygodniowej | Brak logiki tygodni odciążających w `build_deterministic_plan` i adaptacji | Dodać co 4-8 tydzień obniżenie objętości ~40-50% lub luźniejszy split | Średnia/duża |
| 6 | Częstotliwość grup mięśniowych 1×/tydzień przy 3-4 dniach i celu masy/siły (zalecane ~2×) | Symulacja persony 1, 3, 4 (vol per group 1×/tydzień) | Rozdzielić partie tak, by główne grupy występowały 2×/tydzień (np. upper-lower lub PPL) | Średnia |
| 7 | Filtrowanie sprzętowe nieszczelne — "martwy ciąg" nie zawiera "sztanga", "podciąganie" nie zawiera "poręcz" | `app/legacy_routes.py:976-990` (`_exercise_required_equipment`); persona 2 (hantle+ławka) reçoit martwy ciąg | Uzupełnić wykrywanie sprzętu (np. martwy ciąg → sztanga, podciąganie → poręcz/drążek) lub dodać pole sprzętu do puli | Mała/średnia |
| 8 | Brak różnicowania ćwiczeń według poziomu trudności (początkujący i zaawansowany dostają te same ćwiczenia) | Pula nie ma pola poziomu; `exercise_limit` różni się tylko liczbą ćwiczeń (3 vs 4) | Oznaczyć ćwiczenia poziomem i oferować początkującym bezpieczniejsze warianty | Średnia |
| 9 | Plan deterministyczny bez rotacji — te same ćwiczenia co tydzień, brak progresji w samym planie | `build_deterministic_plan` zawsze zwraca ten sam zestaw; progresja tylko przez `adapt_exercise` po sesji | Wprowadzić rotację ćwiczeń w puli i progresję objętości/obciążenia w samym generatorze planu | Średnia |
| 10 | Opis techniki (`how_to`) nie jest wyświetlany użytkownikowi w zakładce Trening ani Plan | `app/plan/routes.py` `plan_ui` i `app/training/routes.py` `training_today_ui`/`session-ui` renderują tylko nazwę/serię/powtórzenia/ciężar | Renderować `how_to` w karcie ćwiczenia w Plan i Trening | Mała |

### D4. Statystyka bazy ćwiczeń

- Razem: **62** ćwiczeń (9 grup: klatka 8, nogi 8, plecy 8, barki 7, biceps 6, triceps 6, brzuch 7, full body 6, cardio 6).
- Z opisem techniki (`how_to` non-empty przez `get_how_to`): **62/62**.
- Bez opisu techniki: **0/62**.
- Brak osobnych pól (wskazówki/cues, typowe błędy, wariant łatwiejszy/trudniejszy, grupa mięśniowa, wzorzec ruchu, sprzęt, poziom, typ, przeciwwskazania): **62/62 niekompletne** pod kątem metadanych.
- Duplikaty dokładne: **1** ("Martwy ciąg konwencjonalny" w plecy + full body).
- Prawie-duplikaty (ta nazwa, inna grupa): **4 pary** (pompki na poręczach, przysiad ze sztangą, podciąganie nachwytem, martwy ciąg konwencjonalny).
- Rozbieżność opisów pool vs `exercise_descriptions.py` dla tych samych ćwiczeń: **39 ćwiczeń**.
- Testy `test_exercise_descriptions.py`: **38 passed** — testują tylko funkcję `get_how_to` (znane/nieznane ćwiczenie, wielkość liter, fallback substring, wszystkie wartości non-empty, klucze lowercase, podstawowe ćwiczenia mają opisy). Nie testują pokrycia puli ćwiczeń, spójności opisów ani metadanych.

### D5. Co działa dobrze (żeby tego nie zepsuć)

- Generowanie deterministyczne i powtarzalne — ten sam input daje ten sam plan (zweryfikowane dla 12 person).
- Bezpieczne podejście do braku danych: plan nie jest mutowany w locie; adaptacja zapisywana jako nowa wersja (`AdaptivePlanRevisionDB`) z pełnym audytem; gdy żadne ćwiczenie nie przechodzi filtrów, `available = []` — nigdy nie pomija ograniczeń sprzętowych/kontuzji cichutko.
- Ocena wykonanej sesji z jasnymi, spiegowalnymi regułami (`evaluate_exercise`: completion <80%, RPE >8, reps poniżej celu).
- Niedziela jako stały dzień spoczynku; diagnostyka harmonogramu (`unmet_training_days`, `schedule_diagnostics`) nie maskuje niespełnionego celu tygodniowego.
- Progress evidence używane tylko do priorytetyzacji ćwiczeń (`_progress_priority`), nigdy do podejmowania decyzji bezpiecznościowych — zgodne z deklaracją "mutates_plan: False".

### D6. Czego nie udało się sprawdzić i dlaczego

- Frontend SPA (netlify/, index.html, React) — nie wiem, czy renderuje `how_to` w zakładce Plan/Trening; zweryfikowałem tylko serwerowe widoki HTML w `app/plan/routes.py` i `app/training/routes.py`, które nie wyświetlają opisu techniki.
- Wywołania AI w produkcji (Groq/Gemini) — brak skonfigurowanych kluczy API w środowisku, nie wywoływano sieciowych endpointów AI; oceniono tylko kod ścieżek AI.
- Pełny cykl adaptacji po zakończonych sesjach w bazie z historią treningów — brak bazy z ukończonymi sesjami, nie uruchamiano serwera API; logikę oceniono statycznie w kodzie (`evaluation.py`, `adaptation.py`, `_build_adaptive_plan`).
- Rzeczywisty czas sesji vs deklarowany — nie mierzono (plan nie zawiera szacowanego czasu; 3-4 ćwiczenia ~45-60 min szacowane orientacyjnie).
- Różnice SQLite vs PostgreSQL w produkcji (testy używają `ci_test.db`).

---

**Metodologia:** analiza statyczna kodu (`app/plan/deterministic.py`, `app/legacy_routes.py`, `app/training/*`, `app/decision_engine.py`, `app/exercise_descriptions.py`, `app/schemas.py`, `app/models.py`), uruchomienie rzeczywistego generatora `build_deterministic_plan` dla 12 person (skrypt `audit_tmp_plans.py`, plik tymczasowy, nie commitowany), uruchomienie `test_exercise_descriptions.py` (38 passed). Brak żadnych zmian w kodzie ani w bazie ćwiczeń.
