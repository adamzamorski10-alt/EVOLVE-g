# Próbki planów treningowych - generator v2 (szablony sesji oparte na wzorcach ruchu)

Generowane realnym kodem z `PLAN_GENERATOR=v2` (`app.plan.deterministic.build_deterministic_plan` -> `build_split_plan`).
Serie są liczbami całkowitymi (pierwsze ćwiczenie złożone sesji dostaje górną wartość zakresu, pozostałe dolną).
estimated_minutes = suma serii x 2,5 min + 5 min.

## persona 1 (3 dni, siłownia)
- Split: `full_body_3` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 3/3 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa czworogłowe: 6 serii, cel 7-12 (brakuje 1).

- Balans pchanie/ciągnięcie: Pchanie = 12 serii, Ciągnięcie = 12 serii (stosunek ciągnięcie/pchanie = 1.00)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
| Poniedziałek | full_body_a | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
| Poniedziałek | full_body_a | Wyciskanie sztangi leżąc | 3 | 6-8 | horizontal_push | - |
| Poniedziałek | full_body_a | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
| Poniedziałek | full_body_a | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
| Poniedziałek | full_body_a | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Środa | full_body_b | Hip thrust z hantlem | 3 | 10-15 | hinge | - |
| Środa | full_body_b | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
| Środa | full_body_b | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
| Środa | full_body_b | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
| Środa | full_body_b | Uginania na wyciągu | 3 | 12-15 | isolation | - |
| Środa | full_body_b | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | full_body_a | Leg press | 3 | 10-12 | squat | - |
| Piątek | full_body_a | Wznosy tułowia na ławce rzymskiej | 3 | 10-15 | hinge | - |
| Piątek | full_body_a | Wyciskanie hantli na skosie dodatnim | 3 | 8-10 | horizontal_push | - |
| Piątek | full_body_a | Wiosłowanie hantlami na ławce skosnej | 3 | 10-12 | horizontal_pull | - |
| Piątek | full_body_a | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
| Piątek | full_body_a | Pallof press na wyciągu | 3 | 10-12 | core | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)
| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Przysiad goblet z hantlem | 3 | squat | nogi | żadne |
| Poniedziałek | Rumuński martwy ciąg z hantlami | 3 | hinge | nogi | żadne |
| Poniedziałek | Wyciskanie sztangi leżąc | 3 | horizontal_push | klatka | PCHANIE |
| Poniedziałek | Wiosłowanie na maszynie siedząc (cable row) | 3 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Poniedziałek | Unoszenie hantli bokiem | 3 | isolation | barki | żadne |
| Poniedziałek | Crunch na maszynie z linką | 3 | core | brzuch | żadne |
| Środa | Hip thrust z hantlem | 3 | hinge | nogi | żadne |
| Środa | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | barki | PCHANIE |
| Środa | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | vertical_pull | plecy | CIĄGNIĘCIE |
| Środa | Rozpiętki na bramie (kabel dolny) | 3 | isolation | klatka | PCHANIE |
| Środa | Uginania na wyciągu | 3 | isolation | biceps | CIĄGNIĘCIE |
| Środa | Uginanie nóg leżąc | 3 | isolation | nogi | żadne |
| Piątek | Leg press | 3 | squat | nogi | żadne |
| Piątek | Wznosy tułowia na ławce rzymskiej | 3 | hinge | plecy | CIĄGNIĘCIE |
| Piątek | Wyciskanie hantli na skosie dodatnim | 3 | horizontal_push | klatka | PCHANIE |
| Piątek | Wiosłowanie hantlami na ławce skosnej | 3 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Piątek | Unoszenie hantli bokiem | 3 | isolation | barki | żadne |
| Piątek | Pallof press na wyciągu | 3 | core | brzuch | żadne |
| **SUMA** | | | | | **Pchanie: 12, Ciągnięcie: 15 (ratio: 1.25)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową
| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 3 | 9 |
| plecy | 3 | 12 |
| barki | 3 | 9 |
| biceps | 1 | 3 |
| triceps | 0 | 0 |
| nogi | 3 | 15 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)
| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 9 | 7-10 |
| plecy (back) | 12 | 8-11 |
| barki boczne (side_delts) | 6 | 6-8 |
| biceps (biceps) | 3 | 4-7 |
| triceps (triceps) | 0 | 4-7 |
| czworogłowe (quads) | 6 | 7-10 |
| dwugłowe (hamstrings) | 6 | 6-8 |
| łydki (calves) | 0 | 4-7 |

## persona 2 (2 dni, siłownia)
- Split: `full_body_2` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: hantle, ławka
- Dni treningowe: 2/2 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa klatka: 6 serii, cel 7-12 (brakuje 1). Grupa plecy: 6 serii, cel 8-13 (brakuje 2). Grupa barki boczne: 3 serii, cel 6-10 (brakuje 3). Grupa czworogłowe: 3 serii, cel 7-12 (brakuje 4). Grupa dwugłowe: 3 serii, cel 4-8 (brakuje 1).

- Balans pchanie/ciągnięcie: Pchanie = 9 serii, Ciągnięcie = 9 serii (stosunek ciągnięcie/pchanie = 1.00)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
| Poniedziałek | full_body_a | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
| Poniedziałek | full_body_a | Wyciskanie hantli na skosie dodatnim | 3 | 8-10 | horizontal_push | - |
| Poniedziałek | full_body_a | Wiosłowanie hantlami na ławce skosnej | 3 | 10-12 | horizontal_pull | - |
| Poniedziałek | full_body_a | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
| Poniedziałek | full_body_a | Plank przedni | 3 | 45-60 s | core | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Czwartek | full_body_b | Hip thrust z hantlem | 3 | 10-15 | hinge | - |
| Czwartek | full_body_b | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
| Czwartek | full_body_b | Wiosłowanie hantlem jednostronnie | 3 | 8-12/strona | horizontal_pull | - |
| Czwartek | full_body_b | Rozpiętki hantlami na podłodze | 3 | 10-15 | isolation | - |
| Czwartek | full_body_b | Uginania młotkowe | 3 | 10-12 | isolation | - |
| Czwartek | full_body_b | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)
| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Przysiad goblet z hantlem | 3 | squat | nogi | żadne |
| Poniedziałek | Rumuński martwy ciąg z hantlami | 3 | hinge | nogi | żadne |
| Poniedziałek | Wyciskanie hantli na skosie dodatnim | 3 | horizontal_push | klatka | PCHANIE |
| Poniedziałek | Wiosłowanie hantlami na ławce skosnej | 3 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Poniedziałek | Unoszenie hantli bokiem | 3 | isolation | barki | żadne |
| Poniedziałek | Plank przedni | 3 | core | brzuch | żadne |
| Czwartek | Hip thrust z hantlem | 3 | hinge | nogi | żadne |
| Czwartek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | barki | PCHANIE |
| Czwartek | Wiosłowanie hantlem jednostronnie | 3 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Czwartek | Rozpiętki hantlami na podłodze | 3 | isolation | klatka | PCHANIE |
| Czwartek | Uginania młotkowe | 3 | isolation | biceps | CIĄGNIĘCIE |
| Czwartek | Wspięcia na palce stojąc | 2 | isolation | nogi | żadne |
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
| barki boczne (side_delts) | 3 | 6-8 |
| biceps (biceps) | 3 | 4-7 |
| triceps (triceps) | 0 | 4-7 |
| czworogłowe (quads) | 3 | 7-10 |
| dwugłowe (hamstrings) | 3 | 6-8 |
| łydki (calves) | 2 | 4-7 |

## persona 3 (4 dni, siłownia)
- Split: `upper_lower_4` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 4/4 | Niewypełnione: 0
- Diagnostyka: -

- Balans pchanie/ciągnięcie: Pchanie = 20 serii, Ciągnięcie = 26 serii (stosunek ciągnięcie/pchanie = 1.30)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
| Poniedziałek | upper_a | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
| Poniedziałek | upper_a | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
| Poniedziałek | upper_a | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
| Poniedziałek | upper_a | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
| Poniedziałek | upper_a | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
| Poniedziałek | upper_a | Uginania na wyciągu | 3 | 12-15 | isolation | - |
| Poniedziałek | upper_a | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 70 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Wtorek | lower_a | Przysiad ze sztangą | 4 | 6-8 | squat | - |
| Wtorek | lower_a | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
| Wtorek | lower_a | Wykroki bułgarskie (na ławce) | 3 | 8/strona | lunge | - |
| Wtorek | lower_a | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
| Wtorek | lower_a | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
| Wtorek | lower_a | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Czwartek | upper_b | Wyciskanie sztangi na ławce skosnej | 4 | 6-8 | horizontal_push | - |
| Czwartek | upper_b | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
| Czwartek | upper_b | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
| Czwartek | upper_b | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
| Czwartek | upper_b | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
| Czwartek | upper_b | Odwrotne rozpiętki na maszynie (rear delt fly) | 3 | 12-15 | isolation | - |
| Czwartek | upper_b | Uginania młotkowe | 3 | 10-12 | isolation | - |
| Czwartek | upper_b | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 75 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | lower_b | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
| Piątek | lower_b | Leg press | 4 | 10-12 | squat | - |
| Piątek | lower_b | Wejścia na ławkę z hantlami | 3 | 10/strona | lunge | - |
| Piątek | lower_b | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
| Piątek | lower_b | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
| Piątek | lower_b | Pallof press na wyciągu | 3 | 10-12 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)
| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Wyciskanie sztangi leżąc | 4 | horizontal_push | klatka | PCHANIE |
| Poniedziałek | Wiosłowanie na maszynie siedząc (cable row) | 3 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Poniedziałek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | barki | PCHANIE |
| Poniedziałek | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | vertical_pull | plecy | CIĄGNIĘCIE |
| Poniedziałek | Unoszenie hantli bokiem | 4 | isolation | barki | żadne |
| Poniedziałek | Face pull na wyciągu (z liną) | 3 | isolation | barki | CIĄGNIĘCIE |
| Poniedziałek | Uginania na wyciągu | 3 | isolation | biceps | CIĄGNIĘCIE |
| Poniedziałek | Prostowanie ramion na wyciągu | 3 | isolation | triceps | PCHANIE |
| Wtorek | Przysiad ze sztangą | 4 | squat | nogi | żadne |
| Wtorek | Rumuński martwy ciąg z hantlami | 3 | hinge | nogi | żadne |
| Wtorek | Wykroki bułgarskie (na ławce) | 3 | lunge | nogi | żadne |
| Wtorek | Uginanie nóg leżąc | 3 | isolation | nogi | żadne |
| Wtorek | Wspięcia na palce stojąc | 3 | isolation | nogi | żadne |
| Wtorek | Crunch na maszynie z linką | 3 | core | brzuch | żadne |
| Czwartek | Wyciskanie sztangi na ławce skosnej | 4 | horizontal_push | klatka | PCHANIE |
| Czwartek | Podciąganie nachwytem | 4 | vertical_pull | plecy | CIĄGNIĘCIE |
| Czwartek | Wiosłowanie sztangą w opadzie tułowia | 4 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Czwartek | Rozpiętki na bramie (kabel dolny) | 3 | isolation | klatka | PCHANIE |
| Czwartek | Unoszenie hantli bokiem | 4 | isolation | barki | żadne |
| Czwartek | Odwrotne rozpiętki na maszynie (rear delt fly) | 3 | isolation | barki | CIĄGNIĘCIE |
| Czwartek | Uginania młotkowe | 3 | isolation | biceps | CIĄGNIĘCIE |
| Czwartek | French press ze sztangą stojąc | 3 | isolation | triceps | PCHANIE |
| Piątek | Rumuński martwy ciąg ze sztangą | 3 | hinge | nogi | żadne |
| Piątek | Leg press | 4 | squat | nogi | żadne |
| Piątek | Wejścia na ławkę z hantlami | 3 | lunge | nogi | żadne |
| Piątek | Wyprosty nóg na maszynie | 3 | isolation | nogi | żadne |
| Piątek | Wspięcia na palce stojąc | 3 | isolation | nogi | żadne |
| Piątek | Pallof press na wyciągu | 3 | core | brzuch | żadne |
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
| barki boczne (side_delts) | 8 | 8-12 |
| biceps (biceps) | 6 | 6-10 |
| triceps (triceps) | 6 | 6-10 |
| czworogłowe (quads) | 14 | 10-14 |
| dwugłowe (hamstrings) | 9 | 8-12 |
| łydki (calves) | 6 | 6-10 |

## persona 7 pure bodyweight (3 dni, siłownia)
- Split: `full_body_3` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: masa własna
- Dni treningowe: 3/3 | Niewypełnione: 0
- Diagnostyka: Brak ćwiczeń ciągnących bez drążka, stołu lub gum. Dodaj sprzęt w profilu, aby plan zawierał wiosłowanie i podciąganie. Uwaga: niektóre grupy poniżej celu objętości.

- Balans pchanie/ciągnięcie: Pchanie = 9 serii, Ciągnięcie = 6 serii (stosunek ciągnięcie/pchanie = 0.67)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad z masą własną | 3 | 10-15 | squat | - |
| Poniedziałek | full_body_a | Mostek biodrowy | 3 | 12-15 | hinge | - |
| Poniedziałek | full_body_a | Pompki klasyczne | 3 | 8-15 | horizontal_push | - |
| Poniedziałek | full_body_a | Superman | 3 | 10-15 | isolation | - |
| Poniedziałek | full_body_a | Prone Y-T-W raises | 3 | 10-15 | isolation | - |
| Poniedziałek | full_body_a | Plank przedni | 3 | 45-60 s | core | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Środa | full_body_b | Dobry poranek bez obciążenia | 3 | 10-15 | hinge | - |
| Środa | full_body_b | Pompki diamentowe na kolanach | 3 | 8-12 | horizontal_push | - |
| Środa | full_body_b | Cobra w leżeniu przodem | 3 | 10-15 | isolation | - |
| Środa | full_body_b | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 32 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | full_body_a | Pompki wąskie | 3 | 8-12 | horizontal_push | - |
| Piątek | full_body_a | Wall sit | 3 | 30-45 s | squat | - |
| Piątek | full_body_a | Reverse snow angel | 3 | 10-15 | isolation | - |
| Piątek | full_body_a | Dead bug | 3 | 10/strona | core | - |
| | | **Szacowany czas sesji: 35 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)
| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Przysiad z masą własną | 3 | squat | nogi | żadne |
| Poniedziałek | Mostek biodrowy | 3 | hinge | nogi | żadne |
| Poniedziałek | Pompki klasyczne | 3 | horizontal_push | klatka | PCHANIE |
| Poniedziałek | Superman | 3 | isolation | plecy | CIĄGNIĘCIE |
| Poniedziałek | Prone Y-T-W raises | 3 | isolation | barki | CIĄGNIĘCIE |
| Poniedziałek | Plank przedni | 3 | core | brzuch | żadne |
| Środa | Dobry poranek bez obciążenia | 3 | hinge | plecy | CIĄGNIĘCIE |
| Środa | Pompki diamentowe na kolanach | 3 | horizontal_push | triceps | PCHANIE |
| Środa | Cobra w leżeniu przodem | 3 | isolation | plecy | CIĄGNIĘCIE |
| Środa | Wspięcia na palce stojąc | 2 | isolation | nogi | żadne |
| Piątek | Pompki wąskie | 3 | horizontal_push | triceps | PCHANIE |
| Piątek | Wall sit | 3 | squat | nogi | żadne |
| Piątek | Reverse snow angel | 3 | isolation | barki | CIĄGNIĘCIE |
| Piątek | Dead bug | 3 | core | brzuch | żadne |
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
| barki boczne (side_delts) | 0 | 6-8 |
| biceps (biceps) | 0 | 4-7 |
| triceps (triceps) | 6 | 4-7 |
| czworogłowe (quads) | 6 | 7-10 |
| dwugłowe (hamstrings) | 0 | 6-8 |
| łydki (calves) | 2 | 4-7 |

## intermediate gym 5d (5 dni, siłownia)
- Split: `upper_lower_push_pull_legs_5` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 5/5 | Niewypełnione: 0
- Diagnostyka: -

- Balans pchanie/ciągnięcie: Pchanie = 27 serii, Ciągnięcie = 29 serii (stosunek ciągnięcie/pchanie = 1.07)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
| Poniedziałek | upper_a | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
| Poniedziałek | upper_a | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
| Poniedziałek | upper_a | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
| Poniedziałek | upper_a | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
| Poniedziałek | upper_a | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
| Poniedziałek | upper_a | Uginania na wyciągu | 3 | 12-15 | isolation | - |
| Poniedziałek | upper_a | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 70 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Wtorek | lower_a | Przysiad ze sztangą | 4 | 6-8 | squat | - |
| Wtorek | lower_a | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
| Wtorek | lower_a | Wykroki bułgarskie (na ławce) | 3 | 8/strona | lunge | - |
| Wtorek | lower_a | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
| Wtorek | lower_a | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
| Wtorek | lower_a | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Środa | push | Wyciskanie sztangi na ławce skosnej | 4 | 6-8 | horizontal_push | - |
| Środa | push | Wyciskanie żołnierskie (military press) ze sztangą | 4 | 6-8 | vertical_push | - |
| Środa | push | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
| Środa | push | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
| Środa | push | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
| Środa | push | Triceps kick-back hantlem | 3 | 12-15/strona | isolation | - |
| | | **Szacowany czas sesji: 58 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | pull | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
| Piątek | pull | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
| Piątek | pull | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
| Piątek | pull | Uginania ze sztangą stojąc | 3 | 8-10 | isolation | - |
| Piątek | pull | Uginania młotkowe | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Sobota | legs | Leg press | 4 | 10-12 | squat | - |
| Sobota | legs | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
| Sobota | legs | Wykroki w marszu z hantlami | 3 | 10/strona | lunge | - |
| Sobota | legs | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
| Sobota | legs | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
| Sobota | legs | Pallof press na wyciągu | 3 | 10-12 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)
| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Wyciskanie sztangi leżąc | 4 | horizontal_push | klatka | PCHANIE |
| Poniedziałek | Wiosłowanie na maszynie siedząc (cable row) | 3 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Poniedziałek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | barki | PCHANIE |
| Poniedziałek | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | vertical_pull | plecy | CIĄGNIĘCIE |
| Poniedziałek | Unoszenie hantli bokiem | 4 | isolation | barki | żadne |
| Poniedziałek | Face pull na wyciągu (z liną) | 3 | isolation | barki | CIĄGNIĘCIE |
| Poniedziałek | Uginania na wyciągu | 3 | isolation | biceps | CIĄGNIĘCIE |
| Poniedziałek | Prostowanie ramion na wyciągu | 3 | isolation | triceps | PCHANIE |
| Wtorek | Przysiad ze sztangą | 4 | squat | nogi | żadne |
| Wtorek | Rumuński martwy ciąg z hantlami | 3 | hinge | nogi | żadne |
| Wtorek | Wykroki bułgarskie (na ławce) | 3 | lunge | nogi | żadne |
| Wtorek | Uginanie nóg leżąc | 3 | isolation | nogi | żadne |
| Wtorek | Wspięcia na palce stojąc | 3 | isolation | nogi | żadne |
| Wtorek | Crunch na maszynie z linką | 3 | core | brzuch | żadne |
| Środa | Wyciskanie sztangi na ławce skosnej | 4 | horizontal_push | klatka | PCHANIE |
| Środa | Wyciskanie żołnierskie (military press) ze sztangą | 4 | vertical_push | barki | PCHANIE |
| Środa | Rozpiętki na bramie (kabel dolny) | 3 | isolation | klatka | PCHANIE |
| Środa | Unoszenie hantli bokiem | 4 | isolation | barki | żadne |
| Środa | French press ze sztangą stojąc | 3 | isolation | triceps | PCHANIE |
| Środa | Triceps kick-back hantlem | 3 | isolation | triceps | PCHANIE |
| Piątek | Wiosłowanie sztangą w opadzie tułowia | 4 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Piątek | Podciąganie nachwytem | 4 | vertical_pull | plecy | CIĄGNIĘCIE |
| Piątek | Face pull na wyciągu (z liną) | 3 | isolation | barki | CIĄGNIĘCIE |
| Piątek | Uginania ze sztangą stojąc | 3 | isolation | biceps | CIĄGNIĘCIE |
| Piątek | Uginania młotkowe | 3 | isolation | biceps | CIĄGNIĘCIE |
| Sobota | Leg press | 4 | squat | nogi | żadne |
| Sobota | Rumuński martwy ciąg ze sztangą | 3 | hinge | nogi | żadne |
| Sobota | Wykroki w marszu z hantlami | 3 | lunge | nogi | żadne |
| Sobota | Wyprosty nóg na maszynie | 3 | isolation | nogi | żadne |
| Sobota | Wspięcia na palce stojąc | 3 | isolation | nogi | żadne |
| Sobota | Pallof press na wyciągu | 3 | core | brzuch | żadne |
| **SUMA** | | | | | **Pchanie: 27, Ciągnięcie: 29 (ratio: 1.07)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową
| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 11 |
| plecy | 2 | 14 |
| barki | 3 | 21 |
| biceps | 2 | 9 |
| triceps | 2 | 9 |
| nogi | 2 | 32 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)
| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 11 | 10-14 |
| plecy (back) | 14 | 12-16 |
| barki boczne (side_delts) | 8 | 8-12 |
| biceps (biceps) | 9 | 6-10 |
| triceps (triceps) | 9 | 6-10 |
| czworogłowe (quads) | 17 | 10-14 |
| dwugłowe (hamstrings) | 9 | 8-12 |
| łydki (calves) | 6 | 6-10 |

## intermediate gym 6d (6 dni, siłownia)
- Split: `push_pull_legs_x2_6` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 6/6 | Niewypełnione: 0
- Diagnostyka: -

- Balans pchanie/ciągnięcie: Pchanie = 33 serii, Ciągnięcie = 32 serii (stosunek ciągnięcie/pchanie = 0.97)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | push | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
| Poniedziałek | push | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
| Poniedziałek | push | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
| Poniedziałek | push | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
| Poniedziałek | push | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| Poniedziałek | push | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 55 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Wtorek | pull | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
| Wtorek | pull | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
| Wtorek | pull | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
| Wtorek | pull | Uginania na wyciągu | 3 | 12-15 | isolation | - |
| Wtorek | pull | Uginania młotkowe | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 42 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Środa | legs | Leg press | 4 | 10-12 | squat | - |
| Środa | legs | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
| Środa | legs | Wykroki w marszu z hantlami | 3 | 10/strona | lunge | - |
| Środa | legs | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
| Środa | legs | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
| Środa | legs | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Czwartek | push | Wyciskanie sztangi na ławce skosnej | 4 | 6-8 | horizontal_push | - |
| Czwartek | push | Wyciskanie żołnierskie (military press) ze sztangą | 4 | 6-8 | vertical_push | - |
| Czwartek | push | Rozpiętki na maszynie (pec deck) | 3 | 12-15 | isolation | - |
| Czwartek | push | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
| Czwartek | push | Francuskie wyciskanie hantli oburącz zza głowy | 3 | 10-12 | isolation | - |
| Czwartek | push | Triceps kick-back hantlem | 3 | 12-15/strona | isolation | - |
| | | **Szacowany czas sesji: 58 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | pull | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
| Piątek | pull | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
| Piątek | pull | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
| Piątek | pull | Uginania ze sztangą stojąc | 3 | 8-10 | isolation | - |
| Piątek | pull | Uginania hantlami naprzemiennie | 3 | 10/strona | isolation | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Sobota | legs | Front squat | 4 | 6-8 | squat | - |
| Sobota | legs | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
| Sobota | legs | Wejścia na ławkę z hantlami | 3 | 10/strona | lunge | - |
| Sobota | legs | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
| Sobota | legs | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
| Sobota | legs | Pallof press na wyciągu | 3 | 10-12 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)
| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Wyciskanie sztangi leżąc | 4 | horizontal_push | klatka | PCHANIE |
| Poniedziałek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | barki | PCHANIE |
| Poniedziałek | Rozpiętki na bramie (kabel dolny) | 3 | isolation | klatka | PCHANIE |
| Poniedziałek | Unoszenie hantli bokiem | 4 | isolation | barki | żadne |
| Poniedziałek | Prostowanie ramion na wyciągu | 3 | isolation | triceps | PCHANIE |
| Poniedziałek | French press ze sztangą stojąc | 3 | isolation | triceps | PCHANIE |
| Wtorek | Wiosłowanie na maszynie siedząc (cable row) | 3 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Wtorek | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | vertical_pull | plecy | CIĄGNIĘCIE |
| Wtorek | Face pull na wyciągu (z liną) | 3 | isolation | barki | CIĄGNIĘCIE |
| Wtorek | Uginania na wyciągu | 3 | isolation | biceps | CIĄGNIĘCIE |
| Wtorek | Uginania młotkowe | 3 | isolation | biceps | CIĄGNIĘCIE |
| Środa | Leg press | 4 | squat | nogi | żadne |
| Środa | Rumuński martwy ciąg z hantlami | 3 | hinge | nogi | żadne |
| Środa | Wykroki w marszu z hantlami | 3 | lunge | nogi | żadne |
| Środa | Uginanie nóg leżąc | 3 | isolation | nogi | żadne |
| Środa | Wspięcia na palce stojąc | 3 | isolation | nogi | żadne |
| Środa | Crunch na maszynie z linką | 3 | core | brzuch | żadne |
| Czwartek | Wyciskanie sztangi na ławce skosnej | 4 | horizontal_push | klatka | PCHANIE |
| Czwartek | Wyciskanie żołnierskie (military press) ze sztangą | 4 | vertical_push | barki | PCHANIE |
| Czwartek | Rozpiętki na maszynie (pec deck) | 3 | isolation | klatka | PCHANIE |
| Czwartek | Unoszenie hantli bokiem | 4 | isolation | barki | żadne |
| Czwartek | Francuskie wyciskanie hantli oburącz zza głowy | 3 | isolation | triceps | PCHANIE |
| Czwartek | Triceps kick-back hantlem | 3 | isolation | triceps | PCHANIE |
| Piątek | Wiosłowanie sztangą w opadzie tułowia | 4 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Piątek | Podciąganie nachwytem | 4 | vertical_pull | plecy | CIĄGNIĘCIE |
| Piątek | Face pull na wyciągu (z liną) | 3 | isolation | barki | CIĄGNIĘCIE |
| Piątek | Uginania ze sztangą stojąc | 3 | isolation | biceps | CIĄGNIĘCIE |
| Piątek | Uginania hantlami naprzemiennie | 3 | isolation | biceps | CIĄGNIĘCIE |
| Sobota | Front squat | 4 | squat | nogi | żadne |
| Sobota | Rumuński martwy ciąg ze sztangą | 3 | hinge | nogi | żadne |
| Sobota | Wejścia na ławkę z hantlami | 3 | lunge | nogi | żadne |
| Sobota | Wyprosty nóg na maszynie | 3 | isolation | nogi | żadne |
| Sobota | Wspięcia na palce stojąc | 3 | isolation | nogi | żadne |
| Sobota | Pallof press na wyciągu | 3 | core | brzuch | żadne |
| **SUMA** | | | | | **Pchanie: 33, Ciągnięcie: 32 (ratio: 0.97)** |

### weekly_summary

#### Serie i sesje na grupę mięśniową
| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 14 |
| plecy | 2 | 14 |
| barki | 4 | 21 |
| biceps | 2 | 12 |
| triceps | 2 | 12 |
| nogi | 2 | 32 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)
| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 14 | 10-14 |
| plecy (back) | 14 | 12-16 |
| barki boczne (side_delts) | 8 | 8-12 |
| biceps (biceps) | 12 | 6-10 |
| triceps (triceps) | 12 | 6-10 |
| czworogłowe (quads) | 14 | 10-14 |
| dwugłowe (hamstrings) | 9 | 8-12 |
| łydki (calves) | 6 | 6-10 |

## intermediate gym 1d (1 dni, siłownia)
- Split: `full_body_1` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 1/1 | Niewypełnione: 0
- Diagnostyka: Uwaga: niektóre grupy poniżej celu objętości.

- Balans pchanie/ciągnięcie: Pchanie = 7 serii, Ciągnięcie = 8 serii (stosunek ciągnięcie/pchanie = 1.14)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_1_ext | Przysiad ze sztangą | 4 | 6-8 | squat | - |
| Poniedziałek | full_body_1_ext | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
| Poniedziałek | full_body_1_ext | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
| Poniedziałek | full_body_1_ext | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
| Poniedziałek | full_body_1_ext | Wiosłowanie na maszynie siedząc (cable row) | 4 | 10-12 | horizontal_pull | - |
| Poniedziałek | full_body_1_ext | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 4 | 10-12 | vertical_pull | - |
| Poniedziałek | full_body_1_ext | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 68 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)
| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Przysiad ze sztangą | 4 | squat | nogi | żadne |
| Poniedziałek | Rumuński martwy ciąg z hantlami | 3 | hinge | nogi | żadne |
| Poniedziałek | Wyciskanie sztangi leżąc | 4 | horizontal_push | klatka | PCHANIE |
| Poniedziałek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | barki | PCHANIE |
| Poniedziałek | Wiosłowanie na maszynie siedząc (cable row) | 4 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Poniedziałek | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 4 | vertical_pull | plecy | CIĄGNIĘCIE |
| Poniedziałek | Crunch na maszynie z linką | 3 | core | brzuch | żadne |
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
| barki boczne (side_delts) | 0 | 8-12 |
| biceps (biceps) | 0 | 6-10 |
| triceps (triceps) | 0 | 6-10 |
| czworogłowe (quads) | 4 | 10-14 |
| dwugłowe (hamstrings) | 3 | 8-12 |
| łydki (calves) | 0 | 6-10 |

## beginner gym 4d (4 dni, siłownia)
- Split: `upper_lower_4` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 4/4 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa klatka: 6 serii, cel 7-12 (brakuje 1). Grupa barki boczne: 3 serii, cel 6-10 (brakuje 3).

- Balans pchanie/ciągnięcie: Pchanie = 15 serii, Ciągnięcie = 18 serii (stosunek ciągnięcie/pchanie = 1.20)

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 3 | 6-8 | horizontal_push | - |
| Poniedziałek | upper_a | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
| Poniedziałek | upper_a | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
| Poniedziałek | upper_a | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
| Poniedziałek | upper_a | Uginania na wyciągu | 3 | 12-15 | isolation | - |
| Poniedziałek | upper_a | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Wtorek | lower_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
| Wtorek | lower_a | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
| Wtorek | lower_a | Wejścia na ławkę z hantlami | 3 | 10/strona | lunge | - |
| Wtorek | lower_a | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
| Wtorek | lower_a | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| Wtorek | lower_a | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Czwartek | upper_b | Wyciskanie hantli na skosie dodatnim | 3 | 8-10 | horizontal_push | - |
| Czwartek | upper_b | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
| Czwartek | upper_b | Wiosłowanie hantlami na ławce skosnej | 3 | 10-12 | horizontal_pull | - |
| Czwartek | upper_b | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
| Czwartek | upper_b | Uginania młotkowe | 3 | 10-12 | isolation | - |
| Czwartek | upper_b | Triceps kick-back hantlem | 3 | 12-15/strona | isolation | - |
| | | **Szacowany czas sesji: 50 min** | | | | |

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Piątek | lower_b | Hip thrust z hantlem | 3 | 10-15 | hinge | - |
| Piątek | lower_b | Leg press | 3 | 10-12 | squat | - |
| Piątek | lower_b | Wykrok w tył | 3 | 10/strona | lunge | - |
| Piątek | lower_b | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
| Piątek | lower_b | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| Piątek | lower_b | Pallof press na wyciągu | 3 | 10-12 | core | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)
| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |
|-------|-----------|-------|---------------|--------------|--------------|
| Poniedziałek | Wyciskanie sztangi leżąc | 3 | horizontal_push | klatka | PCHANIE |
| Poniedziałek | Wiosłowanie na maszynie siedząc (cable row) | 3 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Poniedziałek | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | vertical_pull | plecy | CIĄGNIĘCIE |
| Poniedziałek | Unoszenie hantli bokiem | 3 | isolation | barki | żadne |
| Poniedziałek | Uginania na wyciągu | 3 | isolation | biceps | CIĄGNIĘCIE |
| Poniedziałek | Prostowanie ramion na wyciągu | 3 | isolation | triceps | PCHANIE |
| Wtorek | Przysiad goblet z hantlem | 3 | squat | nogi | żadne |
| Wtorek | Rumuński martwy ciąg z hantlami | 3 | hinge | nogi | żadne |
| Wtorek | Wejścia na ławkę z hantlami | 3 | lunge | nogi | żadne |
| Wtorek | Uginanie nóg leżąc | 3 | isolation | nogi | żadne |
| Wtorek | Wspięcia na palce stojąc | 2 | isolation | nogi | żadne |
| Wtorek | Crunch na maszynie z linką | 3 | core | brzuch | żadne |
| Czwartek | Wyciskanie hantli na skosie dodatnim | 3 | horizontal_push | klatka | PCHANIE |
| Czwartek | Wyciskanie hantli nad głowę siedząc | 3 | vertical_push | barki | PCHANIE |
| Czwartek | Wiosłowanie hantlami na ławce skosnej | 3 | horizontal_pull | plecy | CIĄGNIĘCIE |
| Czwartek | Face pull na wyciągu (z liną) | 3 | isolation | barki | CIĄGNIĘCIE |
| Czwartek | Uginania młotkowe | 3 | isolation | biceps | CIĄGNIĘCIE |
| Czwartek | Triceps kick-back hantlem | 3 | isolation | triceps | PCHANIE |
| Piątek | Hip thrust z hantlem | 3 | hinge | nogi | żadne |
| Piątek | Leg press | 3 | squat | nogi | żadne |
| Piątek | Wykrok w tył | 3 | lunge | nogi | żadne |
| Piątek | Wyprosty nóg na maszynie | 3 | isolation | nogi | żadne |
| Piątek | Wspięcia na palce stojąc | 2 | isolation | nogi | żadne |
| Piątek | Pallof press na wyciągu | 3 | core | brzuch | żadne |
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
| barki boczne (side_delts) | 3 | 6-8 |
| biceps (biceps) | 6 | 4-7 |
| triceps (triceps) | 6 | 4-7 |
| czworogłowe (quads) | 12 | 7-10 |
| dwugłowe (hamstrings) | 6 | 6-8 |
| łydki (calves) | 4 | 4-7 |

