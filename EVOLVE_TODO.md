# EVOLVE — Lista zadań i śledzenie postępów

**Ostatni audyt:** 2026-10-21 (audyt przeglądarkowy zweryfikowany)  
**Deploy:** commit `f0ecfdd` (Merge PR #50 — stage-20-core-loop-integration-audit)  
**Aplikacja:** https://evolve-d2h0.onrender.com/app#my-day  
**Repozytorium:** https://github.com/adamzamorski10-alt/EVOLVE-g  
**Nagranie audytu:** [evolve_audit_detail.webp](file:///C:/Users/adamz/.gemini/antigravity-ide/brain/b542ab08-eee4-4262-bae0-9e43c8ef3863/evolve_audit_detail_1792568912491.webp)  

Legenda statusów:
- `[ ]` — do zrobienia
- `[~]` — częściowo / wymaga weryfikacji
- `[x]` — zrobione i zweryfikowane
- `[!]` — zablokowane / krytyczny błąd

---

## 🔴 KRYTYCZNE — Błędy blokujące lub psujące działanie

> **Potwierdzone błędy konsoli z audytu 2026-10-21:**
> 1. `Tailwind CDN warning` — CDN użyty w produkcji zamiast zbudowanego CSS
> 2. `loadInitialData fetch error: Cannot read properties of undefined (reading 'name')` — aplikacja odpada na embedded fallback data
> 3. `initCharts error: SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON` — API endpoint zwraca HTML (404/500) zamiast JSON

- [x] **Backend API nie odpowiada poprawnie** — Naprawiono: `API_BASE` w `index.html` skierowany na właściwy backend na tym samym originie (zamiast starego wygasłego URL).
- [x] **loadInitialData naprawione** — Usunięto błąd składni (pusty slot przez podwójny przecinek) w `fitai_seed_data.js`, dodano defensywne sprawdzanie obiektów w `_deduplicateByName` i `_preScanInline` oraz absolutną ścieżkę `/fitai_seed_data.js`.
- [x] **Wykresy nie działają (`initCharts` error)** — Naprawiono: backend obsługuje teraz endpoint `GET /app/stats/{identity_id}`, a catch-all SPA w `app/__init__.py` nie serwuje już HTML dla tras API; frontend sprawdza poprawność Content-Type i przekazuje Bearer token.
- [ ] **Tailwind CDN w produkcji** — ostrzeżenie w konsoli; docelowo do zastąpienia zbudowanym CSS.
- [ ] **Uwierzytelnianie** — aplikacja domyślnie pokazuje "Witaj, Użytkowniku!" (mock user). Wymaga weryfikacji flow logowania end-to-end.
- [x] **19 wpisów ćwiczeń usuniętych (`validateVideos`)** — Zweryfikowano: jest to zamierzony filtr wideo atlasu (prunuje wpisy bez adresu wideo do odtwarzacza instruktażowego), a nie błąd bazy ćwiczeń.

---

## 🟠 GŁÓWNY CYKL — Profil → Ocena → Plan → Realizacja → Historia → Analiza (Etap B zamysłu)

### Profil użytkownika (§5.2, §5.3)
- [~] Ekran Profil **istnieje** — pokazuje edycję danych, kalkulator makro (BMR, TDEE), cele kaloryczne
- [ ] Dodać pole: **Dostępny sprzęt** (Pełna siłownia, Hantle/Kettle, Drążek, Piłka do koszykówki, Dostęp do kosza)
- [ ] Dodać pole: **Dostępność w tygodniu / Harmonogram** (dni na siłownię, dni na koszykówkę, czas trwania sesji)
- [ ] Dodać pole: **Pozycja sportowa w koszykówce** (PG - Rozgrywający, SG - Rzucający, SF - Niski skrzydłowy, PF - Silny skrzydłowy, C - Środkowy)
- [ ] Dodać pole: **Ograniczenia zdrowotne / kontuzje** (kolana, stawy skokowe, bark, plecy)
- [ ] Dodać pole: **Doświadczenie treningowe** (początkujący, średniozaawansowany, zaawansowany)
- [ ] Weryfikacja zapisu i odczytu rozszerzonego profilu z bazy PostgreSQL

### Ocena początkowa (Initial Assessment / Baseline) (§5.2)
- [ ] **Dodać moduł „Ocena początkowa” do nawigacji bocznej** (brak w obecnym UI)
- [ ] Formularz testów bazowych:
  - **Skuteczność rzutu**: próby i trafienia (rzuty osobiste, rzuty z dystansu z 5 pozycji)
  - **Wyskok dosiężny (Vertical Jump)**: wynik w cm (z miejsca i z nabiegu)
  - **Szybkość i zmiana kierunku**: test wahadłowy / lane agility
  - **Siła bazowa**: test wyciskania / przysiadu / podciągania
- [ ] Zapis wyników oceny początkowej w bazie jako punkt odniesienia do późniejszej analizy postępów

### Plan treningowy i adaptacja (§5.4)
- [~] Ekran Trening pokazuje tygodniowy harmonogram i listę ćwiczeń
- [ ] Dynamiczne powiązanie planu z wybranym sprzętem i dniami z Profilu
- [ ] Mechanizm "plan kroczący na 1–2 tygodnie"
- [ ] Bezpieczna progresja obciążeń (sugestia ciężaru na bazie poprzedniej sesji i RPE)
- [ ] Możliwość adaptacji planu (zmęczenie po meczu koszykarskim, brak czasu -> wersja skrócona)

### Realizacja treningu w aplikacji (Workout Execution) (§5.5)
- [~] Istnieje zewnętrzna podstrona `/app/training/session-ui`
- [ ] **Integracja rejestratora treningu bezpośrednio w aplikacji głównej (Tech Noir UI)** zamiast surowej podstrony HTML
- [ ] Start treningu jednym kliknięciem z Dashboardu („Rozpocznij trening”)
- [ ] Rejestrowanie serii: ciężar (kg), powtórzenia (reps), RPE (skala wysiłku 1–10)
- [ ] Zegar przerw między seriami (Rest Timer)
- [ ] Możliwość zamiany lub pominięcia ćwiczenia w trakcie sesji (brak sprzętu/ból)
- [ ] Zakończenie treningu i natychmiastowy zapis do bazy PostgreSQL oraz aktualizacja historii

### Historia treningów i aktywności (§5.7)
- [ ] Widok historii wykonanych treningów z rozbiciem na serie, obciążenia i RPE
- [ ] Rozróżnienie w historii: planowane założenia vs rzeczywiste wykonanie
- [ ] Kalendarz zrealizowanych aktywności (siłownia + koszykówka)

---

## 🟡 MODUŁY — Stan vs zamysł

### Dashboard / TODAY 2.0 (§5.1)
- [~] **Istnieje** — pokazuje: nagłówek dnia, spójność, wagę, plan, postęp kcal/białko, checklistę zadań
- [ ] **Karta Trening na dziś**: dynamiczny start treningu bez konieczności szukania w menu
- [ ] **Karta Koszykówka na dziś**: zastąpienie tekstu *"Brak osobnej sesji na dziś. Domena zostanie podłączona"* rzeczywistym zadaniem koszykarskim (np. 100 rzutów / ball handling)
- [ ] **Karta Dieta na dziś**: zastąpienie tekstu *"Dane w przygotowaniu"* podsumowaniem zaplanowanych posiłków i makro
- [ ] **Karta Recovery na dziś**: zastąpienie tekstu *"Brak check-inu"* formularzem szybkiego zapisu snu (godziny) i samopoczucia (1-5) wraz z wyliczoną gotowością (Readiness Score)
- [ ] Rzeczywisty wskaźnik spójności dnia (Consistency %) wyliczany z wykonanych zadań

### Koszykówka i Rozwój Umiejętności (§5.6)
- [~] **Katalog drilli istnieje** (wspólny atlas dla wielu sportów)
- [ ] **Wydzielenie Koszykówki jako priorytetowego modułu sportowego**:
  - **Moduł Rzutu**: rejestrator prób i trafień (osobiste, 3-point, pull-up jump shot, spot-up) z wyliczaniem % celności
  - **Moduł Prowadzenia piłki & Finiszu**: drille kontroli piłki, wejścia pod kosz i wykończenia akcji w kontakcie
  - **Przygotowanie motoryczne pod koszykówkę**: wyskok, pierwszy krok, zmiana kierunku, prewencja urazów kolana/kostki
  - **Zapis sesji rzutowej do historii**

### Odżywianie / Dieta (§5.10)
- [~] **Istnieje** — biblioteka posiłków, jadłospis, Kuchnia AI
- [ ] Wskazówki posiłkowe okołotreningowe:
  - Rekomendacja posiłku przedtreningowego (węglowodany złożone, lekkostrawne białko)
  - Rekomendacja posiłku potreningowego (odbudowa glikogenu, regeneracja mięśniowa)
- [ ] Zapis i synchronizacja dziennika posiłków z bazą danych użytkownika

### Recovery & Gotowość do treningu (§5.9)
- [~] **Istnieje** — ekran Recovery
- [ ] Formularz porannego check-inu: sen (h), jakość snu (1-5), bolesność mięśni (DOMS), poziom stresu
- [ ] Algorytm wyliczania gotowości do treningu (Readiness Score 0-100%)
- [ ] Połączenie wyniku gotowości z rekomendacją treningową na dany dzień (np. przy dużym zmęczeniu sugestia lżejszej sesji)

### Postępy i Cele (§5.8)
- [x] Naprawiono błąd JSON (`initCharts`) — wykresy renderują się stabilnie
- [ ] Wykres historii siły w głównych ćwiczeniach (1RM estymowane z serii i powtórzeń)
- [ ] Wykres skuteczności rzutu w koszykówce w czasie (%)
- [ ] Wykres postępu wyskoku dosiężnego (cm)
- [ ] Moduł mierzalnych celów z paskiem postępu (np. waga docelowa, wyskok +5 cm, rzuty wolne 80%)

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
- [ ] **Sprawdzić** `render.yaml` — CORS origins nie zawiera `evolve-d2h0.onrender.com`
- [ ] Naprawić API endpoints które zwracają HTML zamiast JSON

---

## 📋 KOLEJNOŚĆ PRAC (według etapów zamysłu)

### Etap A — Audyt i fundamenty (aktualny)
- [~] Audyt wizualny aplikacji — **wykonany 2026-10-21**
- [ ] Potwierdzenie konfiguracji bazy danych na Render (PostgreSQL / SQLite?)
- [ ] Sprawdzenie czy backend API działa (endpointy zwracają JSON)
- [ ] Sprawdzenie logowania/rejestracji — czy działa end-to-end

### Etap B — Domknięcie głównego cyklu
- [ ] Naprawienie błędów JS blokujących inicjalizację
- [ ] Naprawienie API endpoints (JSON zamiast HTML)
- [ ] Weryfikacja i naprawa zapisu danych do bazy
- [ ] Pełny flow treningu: start → seria → zakończenie → historia
- [ ] Powiązanie dashboardu z rzeczywistymi danymi użytkownika

### Etap C — TODAY 2.0
- [ ] Dashboard pokazuje dzisiejszy zaplanowany trening
- [ ] Przycisk "Rozpocznij trening" na dashboardzie
- [ ] Status wykonania planu dnia (rzeczywisty)
- [ ] Gotowość do treningu na podstawie danych

### Etap D — Profil i planowanie
- [ ] Uzupełnienie profilu (sprzęt, harmonogram, ograniczenia, doświadczenie)
- [ ] Ocena początkowa (Assessment) jako osobny moduł
- [ ] Plan kroczący powiązany z profilem

### Etap E — Postępy
- [ ] Naprawienie wykresów (API JSON)
- [ ] Historia siły, skuteczności rzutu, testów
- [ ] Cele z mierzalnym postępem

### Etap F — Odżywianie i regeneracja
- [ ] Weryfikacja zapisu danych dietetycznych
- [ ] Weryfikacja Decision Engine
- [ ] Wskazówki posiłkowe powiązane z treningiem

---

*Plik aktualizowany po każdej zmianie. Format: `[x]` = zrobione, `[~]` = częściowe, `[!]` = zablokowane, `[ ]` = do zrobienia.*
