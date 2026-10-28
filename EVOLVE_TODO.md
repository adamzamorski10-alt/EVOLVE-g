# EVOLVE — Lista zadań i śledzenie postępów

**Ostatni audyt:** 2026-10-28 (Etap E — loadProgressStats + podpięcie wykresów siły, rzutów, assessmentu i celów)
**Wdrożona koncepcja:** 7 Filarów Performance OS (ZAMYSŁ_EVOLVE §6.2)  
**Aplikacja:** https://evolve-d2h0.onrender.com/app#my-day  
**Repozytorium:** https://github.com/adamzamorski10-alt/EVOLVE-g  

Legenda statusów:
- `[ ]` — do zrobienia
- `[~]` — częściowo / wymaga weryfikacji
- `[x]` — zrobione i zweryfikowane
- `[!]` — zablokowane / krytyczny błąd

---

## 🔴 KRYTYCZNE — Błędy blokujące lub psujące działanie

> **Stan po audycie 2026-10-25:** błędy inicjalizacji danych i tras API są naprawione.
> Pozostało zastąpienie Tailwind CDN zbudowanym CSS oraz ponowna weryfikacja
> produkcyjna w przeglądarce.

- [x] **Backend API nie odpowiada poprawnie** — Naprawiono: `API_BASE` w `index.html` skierowany na właściwy backend na tym samym originie (zamiast starego wygasłego URL).
- [x] **loadInitialData naprawione** — Usunięto błąd składni (pusty slot przez podwójny przecinek) w `fitai_seed_data.js`, dodano defensywne sprawdzanie obiektów w `_deduplicateByName` i `_preScanInline` oraz absolutną ścieżkę `/fitai_seed_data.js`.
- [x] **Wykresy nie działają (`initCharts` error)** — Naprawiono: backend obsługuje teraz endpoint `GET /app/stats/{identity_id}`, a catch-all SPA w `app/__init__.py` nie serwuje już HTML dla tras API; frontend sprawdza poprawność Content-Type i przekazuje Bearer token.
- [ ] **Tailwind CDN w produkcji** — ostrzeżenie w konsoli; docelowo do zastąpienia zbudowanym CSS.
- [x] **Uwierzytelnianie i deep linki** — dashboard respektuje JWT, odrzuca nieaktualne tokeny i nie renderuje chronionych danych po odpowiedzi `401`.
- [x] **19 wpisów ćwiczeń usuniętych (`validateVideos`)** — Zweryfikowano: jest to zamierzony filtr wideo atlasu (prunuje wpisy bez adresu wideo do odtwarzacza instruktażowego), a nie błąd bazy ćwiczeń.
- [x] **Obsługa `HEAD /app`** — routing SPA obsługuje teraz żądania `HEAD`, wymagane przez monitoring, proxy i narzędzia weryfikujące dostępność aplikacji.

---

## 🟠 GŁÓWNY CYKL — Profil → Ocena → Plan → Realizacja → Historia → Analiza (Etap B zamysłu)

### Profil użytkownika (§5.2, §5.3)
- [x] Ekran Profil — edycja danych, kalkulator makro (BMR, TDEE) i cele kaloryczne
- [x] Profil planistyczny — sprzęt, harmonogram, pozycja koszykarska, ograniczenia zdrowotne i doświadczenie
- [x] Serializacja, `GET/PUT /app/profile`, migracja `evolve26sportprofile` i testy workflow

### Ocena początkowa (Initial Assessment / Baseline) (§5.2)
- [x] **Moduł „Ocena początkowa”** — dedykowana zakładka, wersjonowanie i audit trail
- [ ] Formularz testów bazowych:
  - **Skuteczność rzutu**: próby i trafienia (rzuty osobiste, rzuty z dystansu z 5 pozycji)
  - **Wyskok dosiężny (Vertical Jump)**: wynik w cm (z miejsca i z nabiegu)
  - **Szybkość i zmiana kierunku**: test wahadłowy / lane agility
  - **Siła bazowa**: test wyciskania / przysiadu / podciągania
- [x] Zapis wyników oceny początkowej w bazie jako punkt odniesienia do późniejszej analizy postępów

### Plan treningowy i adaptacja (§5.4)
- [x] Ekran Trening pokazuje tygodniowy harmonogram i listę ćwiczeń
- [x] Plan uwzględnia sprzęt, ograniczenia zdrowotne, dni treningowe i pozycję koszykarską
- [x] Mechanizm planu kroczącego na 7–14 dni z readiness/provenance i `profile_stale`
- [x] Bezpieczna progresja obciążeń (sugestia ciężaru i ghost weights na bazie poprzedniej sesji i RPE)
- [x] Możliwość adaptacji planu (zmęczenie po meczu koszykarskim, brak czasu -> wersja skrócona / recovery override w decision engine)

### Realizacja treningu w aplikacji (Workout Execution) (§5.5)
- [x] Istnieje zewnętrzna podstrona `/app/training/session-ui` (jako fallback)
- [x] **Integracja rejestratora treningu bezpośrednio w aplikacji głównej (Tech Noir UI)** — modal Live Workout Runner
- [x] Start treningu jednym kliknięciem z Dashboardu („Rozpocznij trening”)
- [x] Rejestrowanie serii: ciężar (kg), powtórzenia (reps), RPE (skala wysiłku 1–10)
- [x] Zegar przerw między seriami (Rest Timer)
- [x] Zakończenie treningu i natychmiastowy zapis do bazy PostgreSQL oraz aktualizacja historii

### Historia treningów i aktywności (§5.7)
- [x] Widok historii wykonanych treningów z rozbiciem na serie, obciążenia i RPE (karta `postepyTrainingHistoryWrap` z lazy-loadem pojedynczych serii)
- [x] Rozróżnienie w historii: planowane założenia vs rzeczywiste wykonanie (liczba serii, % ukończenia, RPE)
- [ ] Kalendarz zrealizowanych aktywności (siłownia + koszykówka)

---

## 🟡 MODUŁY — Stan vs zamysł

### Dashboard / TODAY 2.0 (§5.1)
- [x] **Karta Trening na dziś**: dynamiczny start treningu bez konieczności szukania w menu, dynamiczny podgląd zaplanowanych ćwiczeń i statusów (Zaplanowany / W trakcie / Wykonany).
- [x] **Karta Koszykówka na dziś**: zintegrowany cel rzutowy (50 rzutów), podgląd bilansu oddanych i trafionych rzutów z danego dnia oraz przycisk Szybkiego Shot Trackera (modal Tech Noir).
- [x] **Karta Dieta na dziś**: podsumowanie kcal i makroskładników (białko, węglowodany, tłuszcze) z paskami postępu live, synchronizacją zaznaczania posiłków w Mój Dzień i backendem `/app/day/today`.
- [x] **Karta Recovery na dziś**: pełny poranny check-in (5 sygnałów: sen, jakość, energia, zmęczenie, nastrój) zapisywany bezpośrednio do `/app/checkin` z automatycznym przeliczaniem Readiness Score.
- [x] **Rzeczywisty wskaźnik spójności dnia (Consistency %)**: wyliczany reaktywnie w `updateDayConsistencyScore()` z 4 filarów (dieta, trening siłowy, check-in regeneracji, sesje rzutowe).


### Koszykówka i Rozwój Umiejętności (§5.6)
- [x] **Katalog drilli istnieje** (wspólny atlas dla wielu sportów z wyróżnieniem koszykówki)
- [x] **Wydzielenie Koszykówki jako priorytetowego modułu sportowego**:
  - [x] **Moduł Rzutu**: szybki rejestrator prób i trafień (osobiste, 3-point, pull-up jump shot, spot-up, mid-range) z wyliczaniem % celności na żywo
  - [x] **Moduł Prowadzenia piłki & Finiszu**: drille kontroli piłki, wejścia pod kosz i wykończenia akcji w kontakcie (Finishing & Kontakt)
  - [x] **Przygotowanie motoryczne pod koszykówkę**: wyskok (max vertical, penultimate step), pierwszy krok, zmiana kierunku (lane agility), prewencja urazów kolana/kostki (drop-landings)
  - [x] **Zapis sesji rzutowej do historii**: bezpośredni zapis do `/app/drill-result` i integracja z historią wyników drilli `/app/drill-history`

### Odżywianie / Dieta (§5.10)
- [~] **Istnieje** — biblioteka posiłków, jadłospis, Kuchnia AI
- [ ] Wskazówki posiłkowe okołotreningowe:
  - Rekomendacja posiłku przedtreningowego (węglowodany złożone, lekkostrawne białko)
  - Rekomendacja posiłku potreningowego (odbudowa glikogenu, regeneracja mięśniowa)
- [ ] Zapis i synchronizacja dziennika posiłków z bazą danych użytkownika

### Recovery & Gotowość do treningu (§5.9)
- [x] **Dedykowany ekran Recovery (Filar 5)** — zintegrowany z API `/app/recovery/today` oraz `/app/recovery/history`
- [x] Formularz porannego check-inu: sen (h), jakość snu (1–10), energia, zmęczenie, bolesność mięśni (DOMS), poziom stresu, waga
- [x] Algorytm wyliczania gotowości do treningu (Readiness Score 0–100%, pierścień SVG, rozbicie sygnałów)
- [x] Połączenie wyniku gotowości z rekomendacją treningową na dany dzień (Decision Engine z ograniczeniami `reduce_volume_25`, `reduce_volume_50` i blokadą sesji przy stanie regeneracji)

### Postępy i Cele (§5.8)
- [x] Naprawiono błąd JSON (`initCharts`) — wykresy renderują się stabilnie
- [x] **Estymowane 1RM** — `_etapE_loadStrength` pobiera `/app/progress/evidence/{key}` dla 8 kluczowych ćwiczeń i wyświetla estymowane 1RM (formuła Epley) w sekcji Postępy
- [x] **Skuteczność rzutowa** — `_etapE_loadShooting` pobiera `/app/drill-history` i pokazuje sumaryczne próby/trafienia/% oraz historię 10 ostatnich sesji
- [x] **Historia assessmentów** — `_etapE_loadAssessment` pobiera `/app/assessment/history` i wyświetla metryki bazowe (wyskok, sprint, rzuty wolne, siła)
- [x] **Mierzalne cele** — `_etapE_loadGoals` pobiera `/app/goals` i renderuje paski postępu (baseline → current → target)
- [ ] Wykres postępu wyskoku dosiężnego w czasie (wymaga kolejnych assessmentów)
- [ ] Ghost Weights — podgląd poprzedniego ciężaru podczas logowania serii

### Uwierzytelnianie & Ustawienia (§5.13)
- [ ] **Widoczny przycisk logowania / rejestracji w nawigacji głównej**:
  - Modal logowania i rejestracji bez konieczności przechodzenia przez ukryte ekrany
  - Automatyczne powiązanie tokenu JWT i sesji użytkownika
- [ ] **Ekran Ustawienia (Settings)**:
  - Zmiana hasła i danych konta
  - Eksport danych treningowych i żywieniowych (JSON / CSV)
  - Ustawienia prywatności i powiadomień

---

## 🔵 UX / WYGLĄD (§6)

- [~] Styl Tech Noir z ciemnym tłem i neonowym akcentem — **istnieje**
- [~] Nawigacja boczna — **istnieje i działa**
- [ ] Błąd czcionki Syne (`SyntaxError`) — może powodować fallback do domyślnej czcionki
- [ ] Brak czcionki Plus Jakarta Sans (wymaga weryfikacji)
- [ ] Tailwind CDN warning — produkcja powinna używać zbudowanego CSS, nie CDN
- [ ] Responsywność na mobile — wymaga weryfikacji
- [ ] Brak spójnego systemu komponentów (przyciski, karty, formularze)

---

## 🟢 NIEZAWODNOŚĆ / BACKEND (§9, §11)

- [ ] **Potwierdzić** czy Render deployuje automatycznie z `main`
- [ ] **Potwierdzić** czy baza danych PostgreSQL jest poprawnie skonfigurowana na Render
- [ ] **Potwierdzić** trwałość danych — czy dane przeżywają restart serwisu
- [x] **Sprawdzić** `render.yaml` — CORS origins zweryfikowane: zawiera `https://evolve-d2h0.onrender.com` oraz domeny produkcyjne.
- [x] Naprawić API endpoints które zwracają HTML zamiast JSON — routing w `app/__init__.py` zwraca 404 JSON dla nieistniejących tras API i `/app/stats/{identity_id}` obsługuje poprawnie endpointy statystyk.

---

## 📋 KOLEJNOŚĆ PRAC (według etapów zamysłu)

### Etap A — Audyt i fundamenty (aktualny)
- [~] Audyt wizualny aplikacji — **wykonany 2026-10-21**
- [ ] Potwierdzenie konfiguracji bazy danych na Render (PostgreSQL / SQLite?)
- [ ] Sprawdzenie czy backend API działa (endpointy zwracają JSON)
- [ ] Sprawdzenie logowania/rejestracji — czy działa end-to-end

### Etap B — Domknięcie głównego cyklu
- [ ] Naprawienie błędów JS blokujących inicjalizację
- [x] Naprawienie API endpoints (JSON zamiast HTML dla błędnych ścieżek i statystyk)
- [x] Weryfikacja i naprawa zapisu danych do bazy
- [x] **Pełny flow treningu: start → seria → zakończenie → historia**: zintegrowany Live Workout Runner w UI (`openLiveWorkoutModal`, stoper odpoczynku, zapis serii w czasie rzeczywistym, finalizacja z RPE i przyznaniem +100 XP) oraz pełna ścieżka API `/app/training/sessions`.
- [x] Powiązanie dashboardu z rzeczywistymi danymi użytkownika (Today Hub)

### Etap C — TODAY 2.0
- [x] Dashboard pokazuje dzisiejszy zaplanowany trening (pobierany z Decision Engine i planu)
- [x] Przycisk "Rozpocznij trening" na dashboardzie (`window.evolveStartTraining`) uruchamiający sesję live
- [x] Status wykonania planu dnia (rzeczywisty — dieta, siłownia, rzuty, check-in)
- [x] Gotowość do treningu na podstawie danych (Readiness Score)

### Etap D — Profil i planowanie
- [x] **Uzupełnienie profilu** (sprzęt, pozycja koszykarska, ograniczenia zdrowotne, doświadczenie treningowe): zintegrowane w zakładce Profil (Dane) w UI, obsłużone w API (`PUT /app/profile`, `GET /app/profile`), zmigrowana baza (`evolve26sportprofile`) i dodane automatyczne testy E2E.
- [x] **Ocena początkowa (Assessment) jako osobny moduł**: zintegrowana dedykowana zakładka `#tab-assessment` w SPA (`Performance OS -> 7. Assessment & Baza`), weryfikacja gotowości przed generowaniem planu, wersjonowanie bazy wyjściowej (v1, v2...) i pełny audit trail w API `/app/assessment`.
- [x] **Plan kroczący powiązany z profilem**: plan deterministyczny i 7–14 dniowy horyzont kroczący (`rolling_plan`) uwzględniający profil sprzętowy (`equipment`), ograniczenia zdrowotne (`health_limitations`) oraz specjalizację pozycji koszykarskiej (`basketball_position`), z automatyczną detekcją zmian profilu (`profile_stale`) w `/app/plan/readiness`.

### Etap E — Postępy ✅ DONE
- [x] `loadProgressStats` zdefiniowana i podpięta do zakładki Postępy
- [x] Siła (est. 1RM Epley), Rzuty (accuracy%), Assessment, Cele (paski postępu)
- [x] 16/16 testów backendu zaliczonych

### Etap F — Odżywianie i regeneracja
- [ ] Weryfikacja zapisu danych dietetycznych
- [ ] Weryfikacja Decision Engine
- [ ] Wskazówki posiłkowe powiązane z treningiem

---

*Plik aktualizowany po każdej zmianie. Format: `[x]` = zrobione, `[~]` = częściowe, `[!]` = zablokowane, `[ ]` = do zrobienia.*
