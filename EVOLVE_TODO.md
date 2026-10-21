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

### Profil użytkownika
- [~] Ekran Profil **istnieje** — pokazuje edycję danych, kalkulator makro (BMR, TDEE), cele kaloryczne
- [ ] Weryfikacja czy dane profilu zapisują się w bazie (nie tylko lokalnie)
- [ ] Brak pola: doświadczenie treningowe
- [ ] Brak pola: dostępny sprzęt
- [ ] Brak pola: miejsca treningów
- [ ] Brak pola: ograniczenia zdrowotne / kontuzje
- [ ] Brak pola: pozycja sportowa w koszykówce
- [ ] Brak pola: dostępność w tygodniu (harmonogram)

### Ocena początkowa (Assessment)
- [ ] **Brak ekranu oceny początkowej** — nie ma modułu Assessment w nawigacji
- [ ] Brak testów: skuteczność rzutu, testy szybkości, wyskok, siła, kondycja
- [ ] Brak punktu wyjścia do późniejszego porównywania postępów

### Plan treningowy
- [~] Ekran Trening pokazuje tygodniowy harmonogram i listę ćwiczeń
- [ ] Weryfikacja czy plan jest powiązany z profilem i celami użytkownika (czy to statyczny mock?)
- [ ] Brak mechanizmu "plan kroczący na 1–2 tygodnie"
- [ ] Brak rozróżnienia: plan pierwotny vs rzeczywista realizacja
- [ ] Brak adaptacji planu do sytuacji (zmęczenie, pominięty trening, brak sprzętu)

### Realizacja treningu (Training Execution)
- [~] Ekran Trening pokazuje ćwiczenia (Przysiad, Wykroki, Martwy ciąg, Wyciskanie)
- [ ] Weryfikacja czy można **rozpocząć sesję treningową**
- [ ] Weryfikacja czy można **zapisać serię** (serie, powtórzenia, ciężar)
- [ ] Weryfikacja czy można **zakończyć trening**
- [ ] Weryfikacja czy **wyniki zapisują się do bazy** (nie tylko lokalnie)
- [ ] Brak RPE (skala odczuwanego wysiłku) przy zapisie serii
- [ ] Brak możliwości pominięcia / modyfikacji ćwiczenia w trakcie sesji
- [ ] Brak porównania z poprzednimi sesjami przy ćwiczeniu

### Historia
- [ ] Weryfikacja czy historia poprawnie odtwarza wykonane treningi
- [ ] Weryfikacja czy historia nie pokazuje planowanych wyników jako rzeczywistych

---

## 🟡 MODUŁY — Stan vs zamysł

### Dashboard / Mój dzień (§5.1)
- [~] **Istnieje** — pokazuje: pozdrowienie, spójność (0%), wagę, cel, plan, postęp dnia (kcal/białko), listę zadań "Co teraz?"
- [~] **Nawigacja boczna działa** — kliknięcie każdej pozycji przełącza widok (Home, Mój dzień, Trening, Koszykówka, Dieta, Recovery, Postępy, Profil, Kontakt, Kuchnia AI)
- [~] **Przycisk "Rozpocznij trening" istnieje i reaguje na klik** — wymaga weryfikacji co robi po kliknięciu
- [ ] Dashboard oparty na mock/embedded danych — nie na danych użytkownika z bazy
- [ ] Brak: status realizacji dziennego planu (wykonane / nie wykonane) oparty na rzeczywistych danych
- [ ] Brak: gotowość do treningu wyliczona z danych (sen, zmęczenie, poprzedni trening)
- [ ] Brak: ostatnie aktywności (prawdziwe, z historii)
- [ ] "Spójność 0%" — wskaźnik nie korzysta z rzeczywistych danych

### Trening siłowy (§5.5)
- [~] **Istnieje** — lista ćwiczeń, tygodniowy plan, atlas ćwiczeń
- [ ] Weryfikacja pełnego flow: start → seria → zakończenie → historia
- [ ] Brak bezpiecznej progresji obciążeń
- [ ] Brak porównania z poprzednią sesją przy każdym ćwiczeniu

### Koszykówka / Sport (§5.6)
- [~] **Istnieje** — wybór dyscypliny, baza drilli, statystyki
- [ ] Koszykówka jest jedną z 8 dyscyplin — nie jest traktowana priorytetowo
- [ ] Brak modułu rzutu (rejestrowanie prób, trafień, skuteczności z pozycji)
- [ ] Brak modułu prowadzenia piłki / ataku
- [ ] Brak modułu gry w kontakcie
- [ ] Brak ćwiczeń specyficznych dla koszykówki (szybkość, wyskok, zmiana kierunku)
- [ ] Brak powiązania drilli koszykarskich z planem treningowym

### Odżywianie / Dieta (§5.10)
- [~] **Istnieje** — jadłospisy, biblioteka posiłków, lista zakupów, Kuchnia AI
- [ ] Weryfikacja czy dane dietetyczne zapisują się do bazy
- [ ] Weryfikacja czy makro jest powiązane z profilem użytkownika
- [ ] Brak prostych wskazówek posiłkowych przed/po treningu
- [ ] Kuchnia AI istnieje — wymaga weryfikacji działania z backendem

### Recovery / Regeneracja (§5.9)
- [~] **Istnieje** — centrum regeneracji, sen, gotowość, trendy, Decision Engine
- [ ] Weryfikacja czy dane regeneracji zapisują się (sen, zmęczenie, samopoczucie)
- [ ] Weryfikacja czy Decision Engine korzysta z prawdziwych danych
- [ ] Brak oceny gotowości do treningu powiązanej z dashboardem

### Postępy (§5.8)
- [~] **Istnieje** — system XP (poziom 1), waga, wolumen treningowy, diet compliance, streak
- [ ] **Wykresy nie działają** (błąd JSON z API) — krytyczny problem
- [ ] XP/poziom nie jest powiązane z celami z zamysłu
- [ ] Brak: historia siły (postęp w ciężarach na ćwiczeniach)
- [ ] Brak: skuteczność rzutu w czasie
- [ ] Brak: wyskok / szybkość — testy i postęp

### Profil / Assessment (§5.2)
- [~] **Profil istnieje** — edycja danych, kalkulator makro, cele kaloryczne
- [ ] **Assessment nie istnieje** — brak oceny początkowej jako osobnego modułu
- [ ] Brak testów wyjściowych do późniejszego śledzenia postępów

### Settings (§5.13)
- [ ] **Brak osobnego ekranu Ustawień** w nawigacji
- [ ] Ustawienia (jeśli są) schowane w profilu — wymaga weryfikacji

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
