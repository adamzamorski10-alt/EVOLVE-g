# Próbki planów treningowych - generator v2 (szablony sesji oparte na wzorcach ruchu)

Generowane realnym kodem z `PLAN_GENERATOR=v2` (`app.plan.deterministic.build_deterministic_plan` -> `build_split_plan`).
Serie są liczbami całkowitymi (pierwsze ćwiczenie złożone sesji dostaje górną wartość zakresu, pozostałe dolną).
estimated_minutes = suma serii x 2,5 min + 5 min.

## persona 1 (początkujący, 3 dni, masa, pełna siłownia)
- Split: `full_body_3` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 3/3 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa czworogłowe: 6 serii, cel 7-10 (brakuje 1).

- Balans pchanie/ciągnięcie: Pchanie = 12 serii, Ciągnięcie = 12 serii (stosunek ciągnięcie/pchanie = 1.00)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wyciskanie sztangi leżąc | 3 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Środa | full_body_b | Hip thrust z hantlem | 3 | 10-15 | hinge | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | full_body_a | Leg press | 3 | 10-12 | squat | - |
|  |  | Hip thrust ze sztanga | 3 | 8-12 | hinge | - |
|  |  | Wyciskanie hantli na skosie dodatnim | 3 | 8-10 | horizontal_push | - |
|  |  | Wioslowanie hantlami na lawce skosnej | 3 | 10-12 | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Pallof press na wyciagu | 3 | 10-12 | core | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)

| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Przysiad goblet z hantlem | 3 | squat | quads | żadne |
| Poniedziałek | Rumuński martwy ciąg z hantlami | 3 | hinge | hamstrings | żadne |
| Poniedziałek | Wyciskanie sztangi leżąc | 3 | horizontal_push | chest | PCHANIE |
| Poniedziałek | Wiosłowanie na maszynie siedząc (cable row) | 3 | horizontal_pull | back | CIĄGNIĘCIE |
| Poniedziałek | Unoszenie hantli bokiem | 3 | isolation | side_delts | żadne |
| Poniedziałek | Crunch na maszynie z linką | 3 | core | abs | żadne |
| Środa | Hip thrust z hantlem | 3 | hinge | glutes | żadne |
| Środa | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | front_delts | PCHANIE |
| Środa | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | vertical_pull | lats | CIĄGNIĘCIE |
| Środa | Rozpiętki na bramie (kabel dolny) | 3 | isolation | chest | PCHANIE |
| Środa | Uginania na wyciągu | 3 | isolation | biceps | CIĄGNIĘCIE |
| Środa | Uginanie nóg leżąc | 3 | isolation | hamstrings | żadne |
| Piątek | Leg press | 3 | squat | quads | żadne |
| Piątek | Hip thrust ze sztanga | 3 | hinge | glutes | żadne |
| Piątek | Wyciskanie hantli na skosie dodatnim | 3 | horizontal_push | chest | PCHANIE |
| Piątek | Wioslowanie hantlami na lawce skosnej | 3 | horizontal_pull | back | CIĄGNIĘCIE |
| Piątek | Unoszenie hantli bokiem | 3 | isolation | side_delts | żadne |
| Piątek | Pallof press na wyciagu | 3 | core | abs | żadne |
| **SUMA** | | | | | **Pchanie: 12, Ciągnięcie: 12 (ratio: 1.00)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 3 | 9 |
| plecy | 3 | 9 |
| barki | 3 | 9 |
| biceps | 1 | 3 |
| triceps | 0 | 0 |
| nogi | 3 | 18 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 9 | 7-10 |
| plecy (back) | 9 | 8-11 |
| barki (side_delts) | 6 | 6-8 |
| biceps | 3 | 4-7 |
| triceps | 0 | 4-7 |
| czworogłowe (quads) | 6 | 7-10 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 6 | 6-8 |
| łydki (calves) | 0 | 4-7 |

## persona 2 (2 dni, hantle + ławka)
- Split: `full_body_2` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: hantle, ławka
- Dni treningowe: 2/2 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa klatka: 6 serii, cel 7-10 (brakuje 1). Grupa plecy: 6 serii, cel 8-11 (brakuje 2). Grupa barki boczne: 3 serii, cel 6-8 (brakuje 3). Grupa czworogłowe: 3 serii, cel 7-10 (brakuje 4). Grupa dwugłowe: 3 serii, cel 6-8 (brakuje 3).

- Balans pchanie/ciągnięcie: Pchanie = 9 serii, Ciągnięcie = 9 serii (stosunek ciągnięcie/pchanie = 1.00)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wyciskanie hantli na skosie dodatnim | 3 | 8-10 | horizontal_push | - |
|  |  | Wioslowanie hantlami na lawce skosnej | 3 | 10-12 | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Plank przedni | 3 | 45-60 s | core | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Czwartek | full_body_b | Hip thrust z hantlem | 3 | 10-15 | hinge | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Wiosłowanie hantlem jednostronnie | 3 | 8-12/strona | horizontal_pull | - |
|  |  | Rozpiętki hantlami na podłodze | 3 | 10-15 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)

| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Przysiad goblet z hantlem | 3 | squat | quads | żadne |
| Poniedziałek | Rumuński martwy ciąg z hantlami | 3 | hinge | hamstrings | żadne |
| Poniedziałek | Wyciskanie hantli na skosie dodatnim | 3 | horizontal_push | chest | PCHANIE |
| Poniedziałek | Wioslowanie hantlami na lawce skosnej | 3 | horizontal_pull | back | CIĄGNIĘCIE |
| Poniedziałek | Unoszenie hantli bokiem | 3 | isolation | side_delts | żadne |
| Poniedziałek | Plank przedni | 3 | core | abs | żadne |
| Czwartek | Hip thrust z hantlem | 3 | hinge | glutes | żadne |
| Czwartek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | front_delts | PCHANIE |
| Czwartek | Wiosłowanie hantlem jednostronnie | 3 | horizontal_pull | back | CIĄGNIĘCIE |
| Czwartek | Rozpiętki hantlami na podłodze | 3 | isolation | chest | PCHANIE |
| Czwartek | Uginania młotkowe | 3 | isolation | biceps | CIĄGNIĘCIE |
| Czwartek | Wspięcia na palce stojąc | 2 | isolation | calves | żadne |
| **SUMA** | | | | | **Pchanie: 9, Ciągnięcie: 9 (ratio: 1.00)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 6 |
| plecy | 2 | 6 |
| barki | 2 | 6 |
| biceps | 1 | 3 |
| triceps | 0 | 0 |
| nogi | 2 | 11 |
| brzuch | 1 | 3 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 6 | 7-10 |
| plecy (back) | 6 | 8-11 |
| barki (side_delts) | 3 | 6-8 |
| biceps | 3 | 4-7 |
| triceps | 0 | 4-7 |
| czworogłowe (quads) | 3 | 7-10 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 3 | 6-8 |
| łydki (calves) | 2 | 4-7 |

## persona 3 (średniozaawansowany, 4 dni, masa, pełna siłownia)
- Split: `upper_lower_4` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 4/4 | Niewypełnione: 0
- Diagnostyka: -

- Balans pchanie/ciągnięcie: Pchanie = 20 serii, Ciągnięcie = 26 serii (stosunek ciągnięcie/pchanie = 1.30)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 70 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Wtorek | lower_a | Przysiad ze sztangą | 4 | 6-8 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wykroki bułgarskie (na ławce) | 3 | 8/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Czwartek | upper_b | Wyciskanie sztangi na lawce skosnej | 4 | 6-8 | horizontal_push | - |
|  |  | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
|  |  | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
|  |  | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | Odwrotne rozpiętki na maszynie (rear delt fly) | 3 | 12-15 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
|  |  | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 75 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | lower_b | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
|  |  | Leg press | 4 | 10-12 | squat | - |
|  |  | Wejscia na lawke z hantlami | 3 | 10/strona | lunge | - |
|  |  | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Pallof press na wyciagu | 3 | 10-12 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)

| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Wyciskanie sztangi leżąc | 4 | horizontal_push | chest | PCHANIE |
| Poniedziałek | Wiosłowanie na maszynie siedząc (cable row) | 3 | horizontal_pull | back | CIĄGNIĘCIE |
| Poniedziałek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | front_delts | PCHANIE |
| Poniedziałek | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | vertical_pull | lats | CIĄGNIĘCIE |
| Poniedziałek | Unoszenie hantli bokiem | 4 | isolation | side_delts | żadne |
| Poniedziałek | Face pull na wyciągu (z liną) | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Poniedziałek | Uginania na wyciągu | 3 | isolation | biceps | CIĄGNIĘCIE |
| Poniedziałek | Prostowanie ramion na wyciągu | 3 | isolation | triceps | PCHANIE |
| Wtorek | Przysiad ze sztangą | 4 | squat | quads | żadne |
| Wtorek | Rumuński martwy ciąg z hantlami | 3 | hinge | hamstrings | żadne |
| Wtorek | Wykroki bułgarskie (na ławce) | 3 | lunge | quads | żadne |
| Wtorek | Uginanie nóg leżąc | 3 | isolation | hamstrings | żadne |
| Wtorek | Wspięcia na palce stojąc | 3 | isolation | calves | żadne |
| Wtorek | Crunch na maszynie z linką | 3 | core | abs | żadne |
| Czwartek | Wyciskanie sztangi na lawce skosnej | 4 | horizontal_push | chest | PCHANIE |
| Czwartek | Podciąganie nachwytem | 4 | vertical_pull | lats | CIĄGNIĘCIE |
| Czwartek | Wiosłowanie sztangą w opadzie tułowia | 4 | horizontal_pull | back | CIĄGNIĘCIE |
| Czwartek | Rozpiętki na bramie (kabel dolny) | 3 | isolation | chest | PCHANIE |
| Czwartek | Unoszenie hantli bokiem | 4 | isolation | side_delts | żadne |
| Czwartek | Odwrotne rozpiętki na maszynie (rear delt fly) | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Czwartek | Uginania młotkowe | 3 | isolation | biceps | CIĄGNIĘCIE |
| Czwartek | French press ze sztangą stojąc | 3 | isolation | triceps | PCHANIE |
| Piątek | Rumuński martwy ciąg ze sztangą | 3 | hinge | hamstrings | żadne |
| Piątek | Leg press | 4 | squat | quads | żadne |
| Piątek | Wejscia na lawke z hantlami | 3 | lunge | glutes | żadne |
| Piątek | Wyprosty nóg na maszynie | 3 | isolation | quads | żadne |
| Piątek | Wspięcia na palce stojąc | 3 | isolation | calves | żadne |
| Piątek | Pallof press na wyciagu | 3 | core | abs | żadne |
| **SUMA** | | | | | **Pchanie: 20, Ciągnięcie: 26 (ratio: 1.30)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 11 |
| plecy | 2 | 14 |
| barki | 2 | 17 |
| biceps | 2 | 6 |
| triceps | 2 | 6 |
| nogi | 2 | 32 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 11 | 10-14 |
| plecy (back) | 14 | 12-16 |
| barki (side_delts) | 8 | 8-12 |
| biceps | 6 | 6-10 |
| triceps | 6 | 6-10 |
| czworogłowe (quads) | 14 | 10-14 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 9 | 8-12 |
| łydki (calves) | 6 | 6-10 |

## persona 7 pure bodyweight (3 dni, bez sprzętu)
- Split: `full_body_3` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: masa własna
- Dni treningowe: 3/3 | Niewypełnione: 0
- Diagnostyka: Brak ćwiczeń ciągnących bez drążka, stołu lub gum. Dodaj sprzęt w profilu, aby plan zawierał wiosłowanie i podciąganie. Uwaga: niektóre grupy poniżej celu objętości.

- Balans pchanie/ciągnięcie: Pchanie = 9 serii, Ciągnięcie = 15 serii (stosunek ciągnięcie/pchanie = 1.67)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad z masą własną | 3 | 10-15 | squat | - |
|  |  | Mostek biodrowy | 3 | 12-15 | hinge | - |
|  |  | Pompki klasyczne | 3 | 8-15 | horizontal_push | - |
|  |  | Superman | 3 | 10-15 | isolation | - |
|  |  | Prone Y-T-W raises | 3 | 10-15 | isolation | - |
|  |  | Plank przedni | 3 | 45-60 s | core | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Środa | full_body_b | Dobry poranek bez obciążenia | 3 | 10-15 | hinge | - |
|  |  | Pompki diamentowe na kolanach | 3 | 8-12 | horizontal_push | - |
|  |  | Cobra w lezu przodem | 3 | 10-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 32 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | full_body_a | Pompki wąskie | 3 | 8-12 | horizontal_push | - |
|  |  | Wall sit | 3 | 30-45 s | squat | - |
|  |  | Reverse snow angel | 3 | 10-15 | isolation | - |
|  |  | Dead bug | 3 | 10/strona | core | - |
| | | **Szacowany czas sesji: 35 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)

| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Przysiad z masą własną | 3 | squat | quads | żadne |
| Poniedziałek | Mostek biodrowy | 3 | hinge | glutes | żadne |
| Poniedziałek | Pompki klasyczne | 3 | horizontal_push | chest | PCHANIE |
| Poniedziałek | Superman | 3 | isolation | lower_back | CIĄGNIĘCIE |
| Poniedziałek | Prone Y-T-W raises | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Poniedziałek | Plank przedni | 3 | core | abs | żadne |
| Środa | Dobry poranek bez obciążenia | 3 | hinge | lower_back | CIĄGNIĘCIE |
| Środa | Pompki diamentowe na kolanach | 3 | horizontal_push | triceps | PCHANIE |
| Środa | Cobra w lezu przodem | 3 | isolation | lower_back | CIĄGNIĘCIE |
| Środa | Wspięcia na palce stojąc | 2 | isolation | calves | żadne |
| Piątek | Pompki wąskie | 3 | horizontal_push | triceps | PCHANIE |
| Piątek | Wall sit | 3 | squat | quads | żadne |
| Piątek | Reverse snow angel | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Piątek | Dead bug | 3 | core | abs | żadne |
| **SUMA** | | | | | **Pchanie: 9, Ciągnięcie: 15 (ratio: 1.67)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 1 | 3 |
| plecy | 2 | 9 |
| barki | 2 | 6 |
| biceps | 0 | 0 |
| triceps | 2 | 6 |
| nogi | 3 | 11 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 3 | 7-10 |
| plecy (back) | 9 | 8-11 |
| barki (side_delts) | 0 | 6-8 |
| biceps | 0 | 4-7 |
| triceps | 6 | 4-7 |
| czworogłowe (quads) | 6 | 7-10 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 0 | 6-8 |
| łydki (calves) | 2 | 4-7 |

## persona 7 ze sprzętem (3 dni, gumy + drążek)
- Split: `full_body_3` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: masa własna, gumy oporowe, drążek
- Dni treningowe: 3/3 | Niewypełnione: 0
- Diagnostyka: Uwaga: niektóre grupy poniżej celu objętości.

- Balans pchanie/ciągnięcie: Pchanie = 9 serii, Ciągnięcie = 21 serii (stosunek ciągnięcie/pchanie = 2.33)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad z masą własną | 3 | 10-15 | squat | - |
|  |  | Mostek biodrowy | 3 | 12-15 | hinge | - |
|  |  | Pompki klasyczne | 3 | 8-15 | horizontal_push | - |
|  |  | Wioslowanie z guma oporowa | 3 | 12-15 | horizontal_pull | - |
|  |  | Rozciaganie gumy przed klatka | 3 | 15-20 | isolation | - |
|  |  | Plank przedni | 3 | 45-60 s | core | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Środa | full_body_b | Dobry poranek bez obciążenia | 3 | 10-15 | hinge | - |
|  |  | Pompki diamentowe na kolanach | 3 | 8-12 | horizontal_push | - |
|  |  | Podciaganie negatywne na drazku | 3 | 5-8 | vertical_pull | - |
|  |  | Uginania bicepsa z guma oporowa | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | full_body_a | Pompki wąskie | 3 | 8-12 | horizontal_push | - |
|  |  | Podciaganie na drazku z guma | 3 | 6-10 | vertical_pull | - |
|  |  | Wall sit | 3 | 30-45 s | squat | - |
|  |  | Prone Y-T-W raises | 3 | 10-15 | isolation | - |
|  |  | Dead bug | 3 | 10/strona | core | - |
| | | **Szacowany czas sesji: 42 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)

| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Przysiad z masą własną | 3 | squat | quads | żadne |
| Poniedziałek | Mostek biodrowy | 3 | hinge | glutes | żadne |
| Poniedziałek | Pompki klasyczne | 3 | horizontal_push | chest | PCHANIE |
| Poniedziałek | Wioslowanie z guma oporowa | 3 | horizontal_pull | back | CIĄGNIĘCIE |
| Poniedziałek | Rozciaganie gumy przed klatka | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Poniedziałek | Plank przedni | 3 | core | abs | żadne |
| Środa | Dobry poranek bez obciążenia | 3 | hinge | lower_back | CIĄGNIĘCIE |
| Środa | Pompki diamentowe na kolanach | 3 | horizontal_push | triceps | PCHANIE |
| Środa | Podciaganie negatywne na drazku | 3 | vertical_pull | lats | CIĄGNIĘCIE |
| Środa | Uginania bicepsa z guma oporowa | 3 | isolation | biceps | CIĄGNIĘCIE |
| Środa | Wspięcia na palce stojąc | 2 | isolation | calves | żadne |
| Piątek | Pompki wąskie | 3 | horizontal_push | triceps | PCHANIE |
| Piątek | Podciaganie na drazku z guma | 3 | vertical_pull | lats | CIĄGNIĘCIE |
| Piątek | Wall sit | 3 | squat | quads | żadne |
| Piątek | Prone Y-T-W raises | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Piątek | Dead bug | 3 | core | abs | żadne |
| **SUMA** | | | | | **Pchanie: 9, Ciągnięcie: 21 (ratio: 2.33)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 1 | 3 |
| plecy | 3 | 12 |
| barki | 2 | 6 |
| biceps | 1 | 3 |
| triceps | 2 | 6 |
| nogi | 3 | 11 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 3 | 7-10 |
| plecy (back) | 12 | 8-11 |
| barki (side_delts) | 0 | 6-8 |
| biceps | 3 | 4-7 |
| triceps | 6 | 4-7 |
| czworogłowe (quads) | 6 | 7-10 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 0 | 6-8 |
| łydki (calves) | 2 | 4-7 |

## intermediate gym 5d (5 dni, siłownia)
- Split: `upper_lower_push_pull_legs_5` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 5/5 | Niewypełnione: 0
- Diagnostyka: -

- Balans pchanie/ciągnięcie: Pchanie = 26 serii, Ciągnięcie = 29 serii (stosunek ciągnięcie/pchanie = 1.12)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 70 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Wtorek | lower_a | Przysiad ze sztangą | 4 | 6-8 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wykroki bułgarskie (na ławce) | 3 | 8/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Środa | push | Wyciskanie sztangi na lawce skosnej | 4 | 6-8 | horizontal_push | - |
|  |  | Wyciskanie na maszynie siedzac | 3 | 10-12 | vertical_push | - |
|  |  | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
|  |  | Triceps kick-back hantlem | 3 | 12-15/strona | isolation | - |
| | | **Szacowany czas sesji: 55 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | pull | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
|  |  | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
|  |  | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
|  |  | Uginania ze sztangą stojąc | 3 | 8-10 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Sobota | legs | Leg press | 4 | 10-12 | squat | - |
|  |  | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
|  |  | Wykroki w marszu z hantlami | 3 | 10/strona | lunge | - |
|  |  | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Pallof press na wyciagu | 3 | 10-12 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)

| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Wyciskanie sztangi leżąc | 4 | horizontal_push | chest | PCHANIE |
| Poniedziałek | Wiosłowanie na maszynie siedząc (cable row) | 3 | horizontal_pull | back | CIĄGNIĘCIE |
| Poniedziałek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | front_delts | PCHANIE |
| Poniedziałek | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | vertical_pull | lats | CIĄGNIĘCIE |
| Poniedziałek | Unoszenie hantli bokiem | 4 | isolation | side_delts | żadne |
| Poniedziałek | Face pull na wyciągu (z liną) | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Poniedziałek | Uginania na wyciągu | 3 | isolation | biceps | CIĄGNIĘCIE |
| Poniedziałek | Prostowanie ramion na wyciągu | 3 | isolation | triceps | PCHANIE |
| Wtorek | Przysiad ze sztangą | 4 | squat | quads | żadne |
| Wtorek | Rumuński martwy ciąg z hantlami | 3 | hinge | hamstrings | żadne |
| Wtorek | Wykroki bułgarskie (na ławce) | 3 | lunge | quads | żadne |
| Wtorek | Uginanie nóg leżąc | 3 | isolation | hamstrings | żadne |
| Wtorek | Wspięcia na palce stojąc | 3 | isolation | calves | żadne |
| Wtorek | Crunch na maszynie z linką | 3 | core | abs | żadne |
| Środa | Wyciskanie sztangi na lawce skosnej | 4 | horizontal_push | chest | PCHANIE |
| Środa | Wyciskanie na maszynie siedzac | 3 | vertical_push | front_delts | PCHANIE |
| Środa | Rozpiętki na bramie (kabel dolny) | 3 | isolation | chest | PCHANIE |
| Środa | Unoszenie hantli bokiem | 4 | isolation | side_delts | żadne |
| Środa | French press ze sztangą stojąc | 3 | isolation | triceps | PCHANIE |
| Środa | Triceps kick-back hantlem | 3 | isolation | triceps | PCHANIE |
| Piątek | Wiosłowanie sztangą w opadzie tułowia | 4 | horizontal_pull | back | CIĄGNIĘCIE |
| Piątek | Podciąganie nachwytem | 4 | vertical_pull | lats | CIĄGNIĘCIE |
| Piątek | Face pull na wyciągu (z liną) | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Piątek | Uginania ze sztangą stojąc | 3 | isolation | biceps | CIĄGNIĘCIE |
| Piątek | Uginania młotkowe | 3 | isolation | biceps | CIĄGNIĘCIE |
| Sobota | Leg press | 4 | squat | quads | żadne |
| Sobota | Rumuński martwy ciąg ze sztangą | 3 | hinge | hamstrings | żadne |
| Sobota | Wykroki w marszu z hantlami | 3 | lunge | quads | żadne |
| Sobota | Wyprosty nóg na maszynie | 3 | isolation | quads | żadne |
| Sobota | Wspięcia na palce stojąc | 3 | isolation | calves | żadne |
| Sobota | Pallof press na wyciagu | 3 | core | abs | żadne |
| **SUMA** | | | | | **Pchanie: 26, Ciągnięcie: 29 (ratio: 1.12)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 11 |
| plecy | 2 | 14 |
| barki | 3 | 20 |
| biceps | 2 | 9 |
| triceps | 2 | 9 |
| nogi | 2 | 32 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 11 | 10-14 |
| plecy (back) | 14 | 12-16 |
| barki (side_delts) | 8 | 8-12 |
| biceps | 9 | 6-10 |
| triceps | 9 | 6-10 |
| czworogłowe (quads) | 17 | 10-14 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 9 | 8-12 |
| łydki (calves) | 6 | 6-10 |

## intermediate gym 6d (6 dni, siłownia)
- Split: `push_pull_legs_x2_6` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 6/6 | Niewypełnione: 0
- Diagnostyka: -

- Balans pchanie/ciągnięcie: Pchanie = 32 serii, Ciągnięcie = 32 serii (stosunek ciągnięcie/pchanie = 1.00)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | push | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
|  |  | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 55 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Wtorek | pull | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 42 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Środa | legs | Leg press | 4 | 10-12 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wykroki w marszu z hantlami | 3 | 10/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Czwartek | push | Wyciskanie sztangi na lawce skosnej | 4 | 6-8 | horizontal_push | - |
|  |  | Wyciskanie na maszynie siedzac | 3 | 10-12 | vertical_push | - |
|  |  | Rozpiętki na maszynie (pec deck) | 3 | 12-15 | isolation | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | Francuskie wyciskanie hantli oburącz zza głowy | 3 | 10-12 | isolation | - |
|  |  | Triceps kick-back hantlem | 3 | 12-15/strona | isolation | - |
| | | **Szacowany czas sesji: 55 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | pull | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
|  |  | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
|  |  | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
|  |  | Uginania ze sztangą stojąc | 3 | 8-10 | isolation | - |
|  |  | Uginania hantlami naprzemiennie | 3 | 10/strona | isolation | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Sobota | legs | Front squat | 4 | 6-8 | squat | - |
|  |  | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
|  |  | Wejscia na lawke z hantlami | 3 | 10/strona | lunge | - |
|  |  | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Pallof press na wyciagu | 3 | 10-12 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)

| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Wyciskanie sztangi leżąc | 4 | horizontal_push | chest | PCHANIE |
| Poniedziałek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | front_delts | PCHANIE |
| Poniedziałek | Rozpiętki na bramie (kabel dolny) | 3 | isolation | chest | PCHANIE |
| Poniedziałek | Unoszenie hantli bokiem | 4 | isolation | side_delts | żadne |
| Poniedziałek | Prostowanie ramion na wyciągu | 3 | isolation | triceps | PCHANIE |
| Poniedziałek | French press ze sztangą stojąc | 3 | isolation | triceps | PCHANIE |
| Wtorek | Wiosłowanie na maszynie siedząc (cable row) | 3 | horizontal_pull | back | CIĄGNIĘCIE |
| Wtorek | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | vertical_pull | lats | CIĄGNIĘCIE |
| Wtorek | Face pull na wyciągu (z liną) | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Wtorek | Uginania na wyciągu | 3 | isolation | biceps | CIĄGNIĘCIE |
| Wtorek | Uginania młotkowe | 3 | isolation | biceps | CIĄGNIĘCIE |
| Środa | Leg press | 4 | squat | quads | żadne |
| Środa | Rumuński martwy ciąg z hantlami | 3 | hinge | hamstrings | żadne |
| Środa | Wykroki w marszu z hantlami | 3 | lunge | quads | żadne |
| Środa | Uginanie nóg leżąc | 3 | isolation | hamstrings | żadne |
| Środa | Wspięcia na palce stojąc | 3 | isolation | calves | żadne |
| Środa | Crunch na maszynie z linką | 3 | core | abs | żadne |
| Czwartek | Wyciskanie sztangi na lawce skosnej | 4 | horizontal_push | chest | PCHANIE |
| Czwartek | Wyciskanie na maszynie siedzac | 3 | vertical_push | front_delts | PCHANIE |
| Czwartek | Rozpiętki na maszynie (pec deck) | 3 | isolation | chest | PCHANIE |
| Czwartek | Unoszenie hantli bokiem | 4 | isolation | side_delts | żadne |
| Czwartek | Francuskie wyciskanie hantli oburącz zza głowy | 3 | isolation | triceps | PCHANIE |
| Czwartek | Triceps kick-back hantlem | 3 | isolation | triceps | PCHANIE |
| Piątek | Wiosłowanie sztangą w opadzie tułowia | 4 | horizontal_pull | back | CIĄGNIĘCIE |
| Piątek | Podciąganie nachwytem | 4 | vertical_pull | lats | CIĄGNIĘCIE |
| Piątek | Face pull na wyciągu (z liną) | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Piątek | Uginania ze sztangą stojąc | 3 | isolation | biceps | CIĄGNIĘCIE |
| Piątek | Uginania hantlami naprzemiennie | 3 | isolation | biceps | CIĄGNIĘCIE |
| Sobota | Front squat | 4 | squat | quads | żadne |
| Sobota | Rumuński martwy ciąg ze sztangą | 3 | hinge | hamstrings | żadne |
| Sobota | Wejscia na lawke z hantlami | 3 | lunge | glutes | żadne |
| Sobota | Wyprosty nóg na maszynie | 3 | isolation | quads | żadne |
| Sobota | Wspięcia na palce stojąc | 3 | isolation | calves | żadne |
| Sobota | Pallof press na wyciagu | 3 | core | abs | żadne |
| **SUMA** | | | | | **Pchanie: 32, Ciągnięcie: 32 (ratio: 1.00)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 14 |
| plecy | 2 | 14 |
| barki | 4 | 20 |
| biceps | 2 | 12 |
| triceps | 2 | 12 |
| nogi | 2 | 32 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 14 | 10-14 |
| plecy (back) | 14 | 12-16 |
| barki (side_delts) | 8 | 8-12 |
| biceps | 12 | 6-10 |
| triceps | 12 | 6-10 |
| czworogłowe (quads) | 14 | 10-14 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 9 | 8-12 |
| łydki (calves) | 6 | 6-10 |

## intermediate gym 1d (1 dzień, siłownia)
- Split: `full_body_1` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 1/1 | Niewypełnione: 0
- Diagnostyka: Uwaga: niektóre grupy poniżej celu objętości.

- Balans pchanie/ciągnięcie: Pchanie = 7 serii, Ciągnięcie = 8 serii (stosunek ciągnięcie/pchanie = 1.14)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_1_ext | Przysiad ze sztangą | 4 | 6-8 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 4 | 10-12 | horizontal_pull | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 4 | 10-12 | vertical_pull | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 68 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)

| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Przysiad ze sztangą | 4 | squat | quads | żadne |
| Poniedziałek | Rumuński martwy ciąg z hantlami | 3 | hinge | hamstrings | żadne |
| Poniedziałek | Wyciskanie sztangi leżąc | 4 | horizontal_push | chest | PCHANIE |
| Poniedziałek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | front_delts | PCHANIE |
| Poniedziałek | Wiosłowanie na maszynie siedząc (cable row) | 4 | horizontal_pull | back | CIĄGNIĘCIE |
| Poniedziałek | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 4 | vertical_pull | lats | CIĄGNIĘCIE |
| Poniedziałek | Crunch na maszynie z linką | 3 | core | abs | żadne |
| **SUMA** | | | | | **Pchanie: 7, Ciągnięcie: 8 (ratio: 1.14)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 1 | 4 |
| plecy | 1 | 8 |
| barki | 1 | 3 |
| biceps | 0 | 0 |
| triceps | 0 | 0 |
| nogi | 1 | 7 |
| brzuch | 1 | 3 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 4 | 10-14 |
| plecy (back) | 8 | 12-16 |
| barki (side_delts) | 0 | 8-12 |
| biceps | 0 | 6-10 |
| triceps | 0 | 6-10 |
| czworogłowe (quads) | 4 | 10-14 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 3 | 8-12 |
| łydki (calves) | 0 | 6-10 |

## beginner gym 4d (4 dni, siłownia)
- Split: `upper_lower_4` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 4/4 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa klatka: 6 serii, cel 7-10 (brakuje 1). Grupa barki boczne: 3 serii, cel 6-8 (brakuje 3).

- Balans pchanie/ciągnięcie: Pchanie = 15 serii, Ciągnięcie = 18 serii (stosunek ciągnięcie/pchanie = 1.20)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 3 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Wtorek | lower_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wejscia na lawke z hantlami | 3 | 10/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Czwartek | upper_b | Wyciskanie hantli na skosie dodatnim | 3 | 8-10 | horizontal_push | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Wioslowanie hantlami na lawce skosnej | 3 | 10-12 | horizontal_pull | - |
|  |  | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
|  |  | Triceps kick-back hantlem | 3 | 12-15/strona | isolation | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | lower_b | Hip thrust z hantlem | 3 | 10-15 | hinge | - |
|  |  | Leg press | 3 | 10-12 | squat | - |
|  |  | Wykrok w tył | 3 | 10/strona | lunge | - |
|  |  | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
|  |  | Pallof press na wyciagu | 3 | 10-12 | core | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)

| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Wyciskanie sztangi leżąc | 3 | horizontal_push | chest | PCHANIE |
| Poniedziałek | Wiosłowanie na maszynie siedząc (cable row) | 3 | horizontal_pull | back | CIĄGNIĘCIE |
| Poniedziałek | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | vertical_pull | lats | CIĄGNIĘCIE |
| Poniedziałek | Unoszenie hantli bokiem | 3 | isolation | side_delts | żadne |
| Poniedziałek | Uginania na wyciągu | 3 | isolation | biceps | CIĄGNIĘCIE |
| Poniedziałek | Prostowanie ramion na wyciągu | 3 | isolation | triceps | PCHANIE |
| Wtorek | Przysiad goblet z hantlem | 3 | squat | quads | żadne |
| Wtorek | Rumuński martwy ciąg z hantlami | 3 | hinge | hamstrings | żadne |
| Wtorek | Wejscia na lawke z hantlami | 3 | lunge | glutes | żadne |
| Wtorek | Uginanie nóg leżąc | 3 | isolation | hamstrings | żadne |
| Wtorek | Wspięcia na palce stojąc | 2 | isolation | calves | żadne |
| Wtorek | Crunch na maszynie z linką | 3 | core | abs | żadne |
| Czwartek | Wyciskanie hantli na skosie dodatnim | 3 | horizontal_push | chest | PCHANIE |
| Czwartek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | front_delts | PCHANIE |
| Czwartek | Wioslowanie hantlami na lawce skosnej | 3 | horizontal_pull | back | CIĄGNIĘCIE |
| Czwartek | Face pull na wyciągu (z liną) | 3 | isolation | rear_delts | CIĄGNIĘCIE |
| Czwartek | Uginania młotkowe | 3 | isolation | biceps | CIĄGNIĘCIE |
| Czwartek | Triceps kick-back hantlem | 3 | isolation | triceps | PCHANIE |
| Piątek | Hip thrust z hantlem | 3 | hinge | glutes | żadne |
| Piątek | Leg press | 3 | squat | quads | żadne |
| Piątek | Wykrok w tył | 3 | lunge | quads | żadne |
| Piątek | Wyprosty nóg na maszynie | 3 | isolation | quads | żadne |
| Piątek | Wspięcia na palce stojąc | 2 | isolation | calves | żadne |
| Piątek | Pallof press na wyciagu | 3 | core | abs | żadne |
| **SUMA** | | | | | **Pchanie: 15, Ciągnięcie: 18 (ratio: 1.20)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 6 |
| plecy | 2 | 9 |
| barki | 2 | 9 |
| biceps | 2 | 6 |
| triceps | 2 | 6 |
| nogi | 2 | 28 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 6 | 7-10 |
| plecy (back) | 9 | 8-11 |
| barki (side_delts) | 3 | 6-8 |
| biceps | 6 | 4-7 |
| triceps | 6 | 4-7 |
| czworogłowe (quads) | 12 | 7-10 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 6 | 6-8 |
| łydki (calves) | 4 | 4-7 |
