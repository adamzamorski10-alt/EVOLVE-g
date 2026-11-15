# Próbki planów treningowych – generator v2 (szablony sesji oparte na wzorcach ruchu)

Generowane realnym kodem z `PLAN_GENERATOR=v2` (`app.plan.deterministic.build_deterministic_plan` → `build_split_plan`).
Serie są liczbami całkowitymi (pierwsze ćwiczenie złożone sesji dostaje górną wartość zakresu, pozostałe dolną).
estimated_minutes = suma serii × 2,5 min + 5 min.

## persona 1 (początkujący, 3 dni, masa, pełna siłownia)
- Split: `full_body_3` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 3/3 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa dwugłowe: 3 serii, cel 6-8 (brakuje 3).

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
|  |  | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 48 min** | | | | |
| Środa | full_body_b | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wyciskanie hantli na skosie dodatnim | 4 | 8-10 | horizontal_push | - |
|  |  | Wiosłowanie hantlem jednostronnie | 3 | 8-12/strona | horizontal_pull | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Plank przedni | 3 | 45-60 s | core | - |
| | | **Szacowany czas sesji: 45 min** | | | | |
| Piątek | full_body_a | Leg press | 4 | 10-12 | squat | - |
|  |  | Wyciskanie hantli na ławce płaskiej | 3 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie hantlami w opadzie tułowia | 3 | 8-12 | horizontal_pull | - |
|  |  | Unoszenie hantli przodem | 3 | 10-12 | isolation | - |
|  |  | Dead bug | 3 | 10/strona | core | - |
| | | **Szacowany czas sesji: 45 min** | | | | |

### weekly_summary

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 3 | 11 |
| plecy | 3 | 12 |
| barki | 2 | 7 |
| biceps | 0 | 0 |
| triceps | 0 | 0 |
| nogi | 3 | 10 |
| brzuch | 3 | 9 |

## persona 2 (2 dni, hantle + ławka)
- Split: `full_body_2` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: hantle, ławka
- Dni treningowe: 2/2 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa barki boczne: 4 serii, cel 6-8 (brakuje 2). Grupa czworogłowe: 3 serii, cel 7-10 (brakuje 4). Grupa dwugłowe: 3 serii, cel 6-8 (brakuje 3).

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad goblet z hantlem | 3 | 8-12 | squat | - |
|  |  | Wyciskanie hantli na skosie dodatnim | 4 | 8-10 | horizontal_push | - |
|  |  | Wiosłowanie hantlem jednostronnie | 3 | 8-12/strona | horizontal_pull | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | Plank przedni | 3 | 45-60 s | core | - |
| | | **Szacowany czas sesji: 48 min** | | | | |
| Czwartek | full_body_b | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wyciskanie hantli na ławce płaskiej | 3 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie hantlami w opadzie tułowia | 3 | 8-12 | horizontal_pull | - |
|  |  | Superman | 3 | 10-15 | isolation | - |
|  |  | Dead bug | 3 | 10/strona | core | - |
| | | **Szacowany czas sesji: 42 min** | | | | |

### weekly_summary

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 7 |
| plecy | 2 | 9 |
| barki | 1 | 4 |
| biceps | 0 | 0 |
| triceps | 0 | 0 |
| nogi | 2 | 6 |
| brzuch | 2 | 6 |

## persona 3 (średniozaawansowany, 4 dni, masa, pełna siłownia)
- Split: `upper_lower_4` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 4/4 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa klatka: 8 serii, cel 10-14 (brakuje 2). Grupa biceps: 3 serii, cel 6-10 (brakuje 3). Grupa łydki: 4 serii, cel 6-10 (brakuje 2).

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | Face pull na wyciągu (z liną) | 4 | 15-20 | isolation | - |
|  |  | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 65 min** | | | | |
| Wtorek | lower_a | Przysiad ze sztangą | 4 | 6-8 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wykroki bułgarskie (na ławce) | 3 | 8/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 4 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 55 min** | | | | |
| Czwartek | upper_b | Wyciskanie hantli na skosie dodatnim | 4 | 8-10 | horizontal_push | - |
|  |  | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
|  |  | Arnold press | 3 | 10-12 | vertical_push | - |
|  |  | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
|  |  | Odwrotne rozpiętki na maszynie (rear delt fly) | 3 | 12-15 | isolation | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 65 min** | | | | |
| Piątek | lower_b | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
|  |  | Leg press | 4 | 10-12 | squat | - |
|  |  | Wykrok w tył | 3 | 10/strona | lunge | - |
|  |  | Kettlebell swing | 4 | 15 | hinge | - |
|  |  | Mostek biodrowy | 3 | 12-15 | hinge | - |
|  |  | Unoszenie nóg w zwisie na drążku | 3 | 8-12 | core | - |
| | | **Szacowany czas sesji: 55 min** | | | | |

### weekly_summary

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 8 |
| plecy | 2 | 14 |
| barki | 2 | 17 |
| biceps | 1 | 3 |
| triceps | 2 | 6 |
| nogi | 2 | 34 |
| brzuch | 2 | 6 |

## persona 7 (masa własna, 3 dni)
- Split: `full_body_3` | Cel: masa mięśniowa | Poziom: początkujący | Sprzęt: masa własna
- Dni treningowe: 3/3 | Niewypełnione: 0
- Diagnostyka: Uwaga: niektóre grupy poniżej celu objętości.

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad z masą własną | 3 | 10-15 | squat | - |
|  |  | Pompki klasyczne | 3 | 8-15 | horizontal_push | - |
|  |  | Superman | 3 | 10-15 | isolation | - |
|  |  | Reverse snow angel | 3 | 10-15 | isolation | - |
|  |  | Plank przedni | 3 | 45-60 s | core | - |
| | | **Szacowany czas sesji: 42 min** | | | | |
| Środa | full_body_b | Mostek biodrowy | 3 | 12-15 | hinge | - |
|  |  | Pompki na kolanach | 3 | 10-15 | horizontal_push | - |
|  |  | Dobry poranek bez obciążenia | 3 | 10-15 | hinge | - |
|  |  | Dead bug | 3 | 10/strona | core | - |
|  |  | Pompki wąskie | 3 | 8-15 | horizontal_push | - |
| | | **Szacowany czas sesji: 42 min** | | | | |
| Piątek | full_body_a | Wspięcia na palce stojąc | 4 | 15-20 | isolation | - |
|  |  | Prone Y-T-W raises | 3 | 10-15 | isolation | - |
|  |  | Bird dog | 3 | 10/strona | core | - |
|  |  | Przysiad z masą własną | 3 | 10-15 | squat | - |
| | | **Szacowany czas sesji: 38 min** | | | | |

### weekly_summary

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 6 |
| plecy | 2 | 6 |
| barki | 2 | 6 |
| biceps | 0 | 0 |
| triceps | 1 | 3 |
| nogi | 3 | 13 |
| brzuch | 3 | 9 |

## 5 dni siłownia (średniozaawansowany)
- Split: `upper_lower_push_pull_legs_5` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 5/5 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa łydki: 4 serii, cel 6-10 (brakuje 2).

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | upper_a | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | Face pull na wyciągu (z liną) | 4 | 15-20 | isolation | - |
|  |  | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 65 min** | | | | |
| Wtorek | lower_a | Przysiad ze sztangą | 4 | 6-8 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wykroki bułgarskie (na ławce) | 3 | 8/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 4 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 55 min** | | | | |
| Środa | push | Wyciskanie hantli na skosie dodatnim | 4 | 8-10 | horizontal_push | - |
|  |  | Arnold press | 3 | 10-12 | vertical_push | - |
|  |  | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
|  |  | Triceps kick-back hantlem | 3 | 12-15/strona | isolation | - |
|  |  | Odwrotne rozpiętki na maszynie (rear delt fly) | 3 | 12-15 | isolation | - |
|  |  | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 52 min** | | | | |
| Piątek | pull | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
|  |  | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
|  |  | Unoszenie hantli przodem | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 48 min** | | | | |
| Sobota | legs | Leg press | 4 | 10-12 | squat | - |
|  |  | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
|  |  | Wykrok w tył | 3 | 10/strona | lunge | - |
|  |  | Kettlebell swing | 4 | 15 | hinge | - |
|  |  | Mostek biodrowy | 3 | 12-15 | hinge | - |
|  |  | Unoszenie nóg w zwisie na drążku | 3 | 8-12 | core | - |
| | | **Szacowany czas sesji: 55 min** | | | | |

### weekly_summary

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 11 |
| plecy | 2 | 14 |
| barki | 3 | 20 |
| biceps | 1 | 6 |
| triceps | 2 | 9 |
| nogi | 2 | 34 |
| brzuch | 2 | 6 |

## 6 dni siłownia (średniozaawansowany)
- Split: `push_pull_legs_x2_6` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 6/6 | Niewypełnione: 0
- Diagnostyka: Objętość poniżej celu: Grupa łydki: 4 serii, cel 6-10 (brakuje 2).

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | push | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Prostowanie ramion na wyciągu | 3 | 12-15 | isolation | - |
|  |  | French press ze sztangą stojąc | 3 | 10-12 | isolation | - |
|  |  | Unoszenie hantli bokiem | 4 | 12-15 | isolation | - |
|  |  | Rozpiętki na bramie (kabel dolny) | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 55 min** | | | | |
| Wtorek | pull | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Ściąganie drążka wyciągu do klatki (szeroki chwyt) | 3 | 10-12 | vertical_pull | - |
|  |  | Uginania na wyciągu | 3 | 12-15 | isolation | - |
|  |  | Uginania młotkowe | 3 | 10-12 | isolation | - |
|  |  | Face pull na wyciągu (z liną) | 4 | 15-20 | isolation | - |
| | | **Szacowany czas sesji: 45 min** | | | | |
| Środa | legs | Leg press | 4 | 10-12 | squat | - |
|  |  | Rumuński martwy ciąg z hantlami | 3 | 8-10 | hinge | - |
|  |  | Wykroki bułgarskie (na ławce) | 3 | 8/strona | lunge | - |
|  |  | Uginanie nóg leżąc | 3 | 10-12 | isolation | - |
|  |  | Wspięcia na palce stojąc | 4 | 15-20 | isolation | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 55 min** | | | | |
| Czwartek | push | Wyciskanie hantli na skosie dodatnim | 4 | 8-10 | horizontal_push | - |
|  |  | Arnold press | 3 | 10-12 | vertical_push | - |
|  |  | Francuskie wyciskanie hantli oburącz zza głowy | 3 | 10-12 | isolation | - |
|  |  | Triceps kick-back hantlem | 3 | 12-15/strona | isolation | - |
|  |  | Odwrotne rozpiętki na maszynie (rear delt fly) | 3 | 12-15 | isolation | - |
| | | **Szacowany czas sesji: 45 min** | | | | |
| Piątek | pull | Wiosłowanie sztangą w opadzie tułowia | 4 | 6-8 | horizontal_pull | - |
|  |  | Podciąganie nachwytem | 4 | 6-10 | vertical_pull | - |
|  |  | Uginania ze sztangą stojąc | 4 | 8-10 | isolation | - |
|  |  | Uginania hantlami naprzemiennie | 3 | 10/strona | isolation | - |
|  |  | Unoszenie hantli przodem | 3 | 10-12 | isolation | - |
| | | **Szacowany czas sesji: 50 min** | | | | |
| Sobota | legs | Front squat | 4 | 6-8 | squat | - |
|  |  | Rumuński martwy ciąg ze sztangą | 3 | 8-10 | hinge | - |
|  |  | Wykrok w tył | 3 | 10/strona | lunge | - |
|  |  | Kettlebell swing | 4 | 15 | hinge | - |
|  |  | Mostek biodrowy | 3 | 12-15 | hinge | - |
|  |  | Unoszenie nóg w zwisie na drążku | 3 | 8-12 | core | - |
| | | **Szacowany czas sesji: 55 min** | | | | |

### weekly_summary

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 2 | 11 |
| plecy | 2 | 14 |
| barki | 4 | 20 |
| biceps | 2 | 13 |
| triceps | 2 | 12 |
| nogi | 2 | 34 |
| brzuch | 2 | 6 |

## 1 dzień siłownia (średniozaawansowany)
- Split: `full_body_1` | Cel: masa mięśniowa | Poziom: średniozaawansowany | Sprzęt: sztanga, hantle, maszyny, wyciąg, ławka, poręcze, siłownia
- Dni treningowe: 1/1 | Niewypełnione: 0
- Diagnostyka: Uwaga: niektóre grupy poniżej celu objętości.

| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |
|-------|-------|-------------|-------|-------------|---------------|-------------|
| Poniedziałek | full_body_a | Przysiad ze sztangą | 4 | 6-8 | squat | - |
|  |  | Wyciskanie sztangi leżąc | 4 | 6-8 | horizontal_push | - |
|  |  | Wiosłowanie na maszynie siedząc (cable row) | 3 | 10-12 | horizontal_pull | - |
|  |  | Wyciskanie hantli nad głowę siedząc | 3 | 8-10 | vertical_push | - |
|  |  | Crunch na maszynie z linką | 3 | 15-20 | core | - |
| | | **Szacowany czas sesji: 48 min** | | | | |

### weekly_summary

| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |
|-----------------|------------------|--------------------------|
| klatka | 1 | 4 |
| plecy | 1 | 3 |
| barki | 1 | 3 |
| biceps | 0 | 0 |
| triceps | 0 | 0 |
| nogi | 1 | 4 |
| brzuch | 1 | 3 |

