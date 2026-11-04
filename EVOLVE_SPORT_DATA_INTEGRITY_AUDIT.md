# Audyt integralności danych modułu Sport

Data audytu: 2026-11-04  
Gałąź: `feat/sport-data-integrity`

## Etap 0 — weryfikacja znalezisk

| # | Status | Dowód w kodzie | Wniosek |
|---|---|---|---|
| 1 | Częściowo potwierdzone | `index.html:35608-35619` mapuje elementy assessmentu jawnie; `close` nie jest mapowane na `three`, ale wynik pozostaje w `athlete.assessment`, a nie w historii prób. | Literalne „close → three” nie występuje w aktualnej wersji; problem braku osobnych prób testu potwierdzony. |
| 2 | Potwierdzone | `index.html:34473-34506` najpierw używa nazwy drilla, domyślnie przypisuje rzuty do `ft`, a rogi/skrzydła rozróżnia heurystycznie. | Strefa jawna jest nadpisywana przez nazwę. |
| 3 | Potwierdzone | `app/models.py:77-105`, `app/fitness/routes.py:911`; `index.html:35608-35648`. | Assessment jest JSON-em użytkownika i nie jest `DrillResultDB`. |
| 4 | Potwierdzone | `index.html:35443-35469` | Oceny są rekonstruowane z `name.includes(...)`, w tym z przypadkowej cyfry `3`. |
| 5 | Potwierdzone | `index.html:35262-35318` zapisuje `al_…` tylko przez `saveSt`; `index.html:35186-35204` pomija DELETE dla `al_`/`sl_`. | Ręczne logi nie są trwale zapisywane na serwerze. |
| 6 | Potwierdzone | `index.html:35554`, `index.html:35654` | Brak wyboru pozycji zastępuje ją sugestią. |
| 7 | Potwierdzone | `index.html:35328-35336`, `index.html:35443-35469` | `defense` i `condition` nie są liczone; ogólna ocena uśrednia dowolne dostępne ratingi. |
| 8 | Potwierdzone | `index.html:35617-35634` oraz `index.html:35443-35469` | Assessment miesza się ze starą oceną, a render nadpisuje `ratings` historią bez okna czasowego. |
| 9 | Potwierdzone | `index.html:35625`, `index.html:35480-35484`, `index.html:34499-34507` | Sprint/wyskok i progi są lokalnymi heurystykami; procent rzutu nie ma skali kotwic. |
| 10 | Potwierdzone | `index.html:35495-35504` | Pewność jest wyliczana z `history.length`, bez liczby prób i świeżości. |
| 11 | Potwierdzone | `index.html:35127-35145`, `index.html:35199-35200`, `index.html:24409-24430` | Dane użytkownika trafiają do `innerHTML` bez konsekwentnego escapowania. JWT jest przechowywany w `localStorage` w `index.html:35200` i wielu innych miejscach. |
| 12 | Potwierdzone | `index.html:22018`, `index.html:24409`, `index.html:25056`, `index.html:27544` | Istnieją cztery definicje/aliasy; ostatni zapis globalny wygrywa. |
| 13 | Potwierdzone | `index.html:35526`, `index.html:35535-35555`; profil użytkownika ma te pola w `app/models.py:17-34`. | Formularz sportowy kopiuje dane profilu, a płeć jest tekstem. |

## Istniejący model i endpointy

`DrillResultDB` (`app/models.py:548-605`) przechowuje jedną sesję drilla, ale nie ma `source`,
`test_run_id`, `zone`, `category` o kontrolowanym słowniku, `client_id`, `value`/`unit`
ani pól do idempotencji. `POST /app/drill-result`, `GET /app/drill-history` i
`DELETE /app/drill-result/{id}` (`app/fitness/routes.py:1358-1550`) są ograniczone do
`DrillResultDB` i sprawdzają własność przy odczycie/usunięciu, lecz zapis nie realizuje
nowego kontraktu prób ani idempotencji.

Profil (`GET/PUT /app/profile`, `app/fitness/routes.py:850-935`) jest właściwym miejscem
do danych demograficznych, ale `basketball_profile_json` nie powinien być źródłem historii.

## Decyzja schematu

Dodaję osobną tabelę `SportAttemptDB` oraz opcjonalny identyfikator test-run w tym samym
modelu, zamiast rozszerzać `DrillResultDB`. `DrillResultDB` jest używany przez istniejące
progresje i starsze endpointy; jego semantyka to sesja drilla, podczas gdy nowy kontrakt
opisuje pojedyncze próby, pomiary i częściowo zapisany test. Osobna tabela pozwala zachować
kompatybilność i wykonać idempotentną migrację bez niszczenia istniejących danych.

## Zakres wariantu testu

Test zachowuje osiem grup z istniejącego UI: osobiste, layup/close, mid-range,
trójka z trzech stref (szczyt, skrzydło, róg), kozłowanie, sprint i wyskok.
Każda grupa zapisuje osobne próby; sprint i wyskok zapisują `value`/`unit`.
Nie dodaję obrony ani kondycji do testu bazowego, ponieważ obecny dokument nie zawiera
ich pomiaru — API zwraca dla nich „brak testu” do czasu jawnego logu.
