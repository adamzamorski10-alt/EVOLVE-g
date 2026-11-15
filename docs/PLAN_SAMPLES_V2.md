# Próbki planów treningowych – generator v2 (szablony sesji oparte na wzorcach ruchu)

Generowane realnym kodem z `PLAN_GENERATOR=v2` (`app.plan.deterministic.build_deterministic_plan` → `build_split_plan`).
Serie są liczbami całkowitymi (pierwsze ćwiczenie złożone sesji dostaje górną wartość zakresu, pozostałe dolną).
estimated_minutes = suma serii × 2,5 min + 5 min.

## persona 1 (początkujący, 3 dni, masa, pełna siłownia)
- Split: `full_body_3` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 3/3 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa klatka: 6 serii, cel 7-10 (brakuje 1). Grupa czworogłowe: 6 serii, cel 7-10 (brakuje 1). Grupa dwugłowe: 3 serii, cel 6-8 (brakuje 3).

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
|  |  | Wyciskanie sztangi leżąc | 3 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

| Środa | full_body_b | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

| Piątek | full_body_a | Leg press | 3 | 10-12 | squat | - |
|  |  | Wyciskanie hantli na skosie dodatnim | 3 | 8-10 | horizontal_push | - |
|  |  | Wiosłowanie hantlem jednostronnie | 3 | 8-12/strona | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 6 |
| plecy | 3 | 9 |
| barki | 3 | 9 |
| biceps | 0 | 0 |
| triceps | 0 | 0 |
| nogi | 3 | 15 |
| brzuch | 1 | 3 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 6 | 7-10 |
| plecy (back) | 9 | 8-11 |
| barki (side_delts) | 9 | 6-8 |
| biceps | 0 | 4-7 |
| triceps | 0 | 4-7 |
| czworogłowe (quads) | 6 | 7-10 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 3 | 6-8 |
| łydki (calves) | 6 | 4-7 |

## persona 2 (2 dni, hantle + ławka)
- Split: `full_body_2` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: hantle, ławka
- Dni treningowe: 2/2 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa klatka: 6 serii, cel 7-10 (brakuje 1). Grupa plecy: 3 serii, cel 8-11 (brakuje 5). Grupa czworogłowe: 3 serii, cel 7-10 (brakuje 4). Grupa dwugłowe: 3 serii, cel 6-8 (brakuje 3).

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
|  |  | Wyciskanie hantli na skosie dodatnim | 3 | 8-10 | horizontal_push | - |
|  |  | Wiosłowanie hantlem jednostronnie | 3 | 8-12/strona | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

| Czwartek | full_body_b | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Wyciskanie hantli na ławce płaskiej | 3 | 6-8 | horizontal_push | - |
|  |  | Plank przedni | 3 | 45-60 s | core | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 6 |
| plecy | 1 | 3 |
| barki | 2 | 6 |
| biceps | 0 | 0 |
| triceps | 0 | 0 |
| nogi | 2 | 10 |
| brzuch | 1 | 3 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 6 | 7-10 |
| plecy (back) | 3 | 8-11 |
| barki (side_delts) | 6 | 6-8 |
| biceps | 0 | 4-7 |
| triceps | 0 | 4-7 |
| czworogłowe (quads) | 3 | 7-10 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 3 | 6-8 |
| łydki (calves) | 4 | 4-7 |

## persona 3 (średniozaawansowany, 4 dni, masa, pełna siłownia)
- Split: `upper_lower_4` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 4/4 | Niewypełnione: 0
- Diagnostyka: -

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
|  |  | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
|  |  | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 68 min** | | | | |

| Wtorek | lower_a | Przysiad ze sztangą | 4 | 6-8 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wykroki bułgarskie (na ławce) | 3 | 8/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Czwartek | upper_b | Wyciskanie hantli na skosie dodatnim | 4 | 8-10 | horizontal_push | - |
|  |  | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
|  |  | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Odwrotne rozpiętki na maszynie (rear delt fly) | 3 | 12-15 | isolation | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
|  |  | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 72 min** | | | | |

| Piątek | lower_b | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
|  |  | Leg press | 4 | 10-12 | squat | - |
|  |  | Wykrok w tył | 3 | 10/strona | lunge | - |
|  |  | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Unoszenie nóg w zwisie na drążku | 3 | 8-12 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 11 |
| plecy | 2 | 14 |
| barki | 2 | 15 |
| biceps | 1 | 6 |
| triceps | 2 | 6 |
| nogi | 2 | 32 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 11 | 10-14 |
| plecy (back) | 14 | 12-16 |
| barki (side_delts) | 15 | 8-12 |
| biceps | 6 | 6-10 |
| triceps | 6 | 6-10 |
| czworogłowe (quads) | 17 | 10-14 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 9 | 8-12 |
| łydki (calves) | 6 | 6-10 |

## persona 7 (masa własna, 3 dni)
- Split: `full_body_3` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: masa własna
- Dni treningowe: 3/3 | Niewypełnione: 0
- Diagnostyka: Uwaga: niektóre grupy poniżej celu objętości.

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad z masą własną | 3 | 10-15 | squat | - |
|  |  | Pompki klasyczne | 3 | 8-15 | horizontal_push | - |
|  |  | Prone Y-T-W raises | 3 | 10-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
|  |  | Plank przedni | 3 | 45-60 s | core | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

| Środa | full_body_b | Mostek biodrowy | 3 | 12-15 | hinge | - |
|  |  | Dead bug | 3 | 10/strona | core | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 25 min** | | | | |

| Piątek | full_body_a | Wall sit | 3 | 30-45 s | squat | - |
|  |  | Reverse snow angel | 3 | 10-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
|  |  | Bird dog | 3 | 10/strona | core | - |
| | | **Szacowany czas sesji: 32 min** | | | | |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 1 | 3 |
| plecy | 0 | 0 |
| barki | 2 | 6 |
| biceps | 0 | 0 |
| triceps | 0 | 0 |
| nogi | 3 | 15 |
| brzuch | 3 | 9 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 3 | 7-10 |
| plecy (back) | 0 | 8-11 |
| barki (side_delts) | 6 | 6-8 |
| biceps | 0 | 4-7 |
| triceps | 0 | 4-7 |
| czworogłowe (quads) | 6 | 7-10 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 3 | 6-8 |
| łydki (calves) | 6 | 4-7 |

## 5 dni siłownia (średniozaawansowany)
- Split: `upper_lower_push_pull_legs_5` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 5/5 | Niewypełnione: 0
- Diagnostyka: -

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
|  |  | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
|  |  | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 68 min** | | | | |

| Wtorek | lower_a | Przysiad ze sztangą | 4 | 6-8 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wykroki bułgarskie (na ławce) | 3 | 8/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Środa | push | Wyciskanie hantli na skosie dodatnim | 4 | 8-10 | horizontal_push | - |
|  |  | Arnold press | 3 | 10-12 | vertical_push | - |
|  |  | Rozpiętki na maszynie (pec deck) | 3 | 12-15 | isolation | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
|  |  | Triceps kick-back hantlem | 3 | 12-15/strona | isolation | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Piątek | pull | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
|  |  | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

| Sobota | legs | Leg press | 4 | 10-12 | squat | - |
|  |  | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
|  |  | Wykrok w tył | 3 | 10/strona | lunge | - |
|  |  | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Unoszenie nóg w zwisie na drążku | 3 | 8-12 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 14 |
| plecy | 2 | 14 |
| barki | 2 | 15 |
| biceps | 1 | 6 |
| triceps | 2 | 9 |
| nogi | 2 | 32 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 14 | 10-14 |
| plecy (back) | 14 | 12-16 |
| barki (side_delts) | 15 | 8-12 |
| biceps | 6 | 6-10 |
| triceps | 9 | 6-10 |
| czworogłowe (quads) | 17 | 10-14 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 9 | 8-12 |
| łydki (calves) | 6 | 6-10 |

## 6 dni siłownia (średniozaawansowany)
- Split: `push_pull_legs_x2_6` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 6/6 | Niewypełnione: 0
- Diagnostyka: -

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | push | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
|  |  | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Wtorek | pull | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Face pull na wyciągu (z liną) | 3 | 15-20 | isolation | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 42 min** | | | | |

| Środa | legs | Leg press | 4 | 10-12 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wykroki bułgarskie (na ławce) | 3 | 8/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Czwartek | push | Wyciskanie hantli na skosie dodatnim | 4 | 8-10 | horizontal_push | - |
|  |  | Arnold press | 3 | 10-12 | vertical_push | - |
|  |  | Rozpiętki na maszynie (pec deck) | 3 | 12-15 | isolation | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Francuskie wyciskanie hantli oburącz zza głowy | 3 | 10-12 | isolation | - |
|  |  | Triceps kick-back hantlem | 3 | 12-15/strona | isolation | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

| Piątek | pull | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
|  |  | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
|  |  | Uginania ze sztangą stojąc | 3 | 8-10 | isolation | - |
|  |  | Uginania hantlami naprzemiennie | 3 | 10/strona | isolation | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

| Sobota | legs | Front squat | 4 | 6-8 | squat | - |
|  |  | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
|  |  | Wykrok w tył | 3 | 10/strona | lunge | - |
|  |  | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Unoszenie nóg w zwisie na drążku | 3 | 8-12 | core | - |
| | | **Szacowany czas sesji: 52 min** | | | | |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 14 |
| plecy | 2 | 14 |
| barki | 3 | 15 |
| biceps | 2 | 12 |
| triceps | 2 | 12 |
| nogi | 2 | 32 |
| brzuch | 2 | 6 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 14 | 10-14 |
| plecy (back) | 14 | 12-16 |
| barki (side_delts) | 15 | 8-12 |
| biceps | 12 | 6-10 |
| triceps | 12 | 6-10 |
| czworogłowe (quads) | 17 | 10-14 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 9 | 8-12 |
| łydki (calves) | 6 | 6-10 |

## 1 dzień siłownia (średniozaawansowany)
- Split: `full_body_1` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 1/1 | Niewypełnione: 0
- Diagnostyka: Uwaga: niektóre grupy poniżej celu objętości.

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad ze sztangą | 4 | 6-8 | squat | - |
|  |  | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 3 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 55 min** | | | | |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 1 | 4 |
| plecy | 1 | 3 |
| barki | 1 | 3 |
| biceps | 0 | 0 |
| triceps | 0 | 0 |
| nogi | 1 | 7 |
| brzuch | 1 | 3 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 4 | 10-14 |
| plecy (back) | 3 | 12-16 |
| barki (side_delts) | 3 | 8-12 |
| biceps | 0 | 6-10 |
| triceps | 0 | 6-10 |
| czworogłowe (quads) | 4 | 10-14 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 0 | 8-12 |
| łydki (calves) | 3 | 6-10 |

## początkujący 4 dni (siłownia)
- Split: `upper_lower_4` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 4/4 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa klatka: 6 serii, cel 7-10 (brakuje 1).

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 3 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 42 min** | | | | |

| Wtorek | lower_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wykrok w tył | 3 | 10/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

| Czwartek | upper_b | Wyciskanie hantli na skosie dodatnim | 3 | 8-10 | horizontal_push | - |
|  |  | Wiosłowanie hantlem jednostronnie | 3 | 8-12/strona | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 3 | 12-15 | isolation | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 42 min** | | | | |

| Piątek | lower_b | Mostek biodrowy | 3 | 12-15 | hinge | - |
|  |  | Leg press | 3 | 10-12 | squat | - |
|  |  | Wyprosty nóg na maszynie | 3 | 12-15 | isolation | - |
|  |  | Wspięcia na palce stojąc | 2 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 40 min** | | | | |

### weekly_summary

#### Serie i sesje na grupę mięśniową

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 6 |
| plecy | 2 | 9 |
| barki | 2 | 9 |
| biceps | 1 | 6 |
| triceps | 0 | 0 |
| nogi | 2 | 25 |
| brzuch | 1 | 3 |

#### Serie na mięsień (podgrupy)

| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |
|--------------------|--------------------------|---------------------|
| klatka (chest) | 6 | 7-10 |
| plecy (back) | 9 | 8-11 |
| barki (side_delts) | 9 | 6-8 |
| biceps | 6 | 4-7 |
| triceps | 0 | 4-7 |
| czworogłowe (quads) | 12 | 7-10 |
| dwugłowe/kulszowo-goleniowe (hamstrings) | 9 | 6-8 |
| łydki (calves) | 4 | 4-7 |
