// ===========================================================================
// EVOLVE FITNESS AI - SEED DATA v3.0
// ===========================================================================
// Zweryfikowana, profesjonalna baza danych:
// - 50 Posiłków dietetycznych (MEAL_DB) ze składnikami, makro i przepisami
// - 48 Ćwiczeń siłowych (EXERCISE_DB) z biomechaniką, wskazówkami i progresją
// - 50 Drilli sportowych (SPORT_DRILLS) dla 5 dyscyplin olimpijskich
// ===========================================================================

const MEAL_DB = {
  "sniadanie": [
    {
      "id": "meal_sn_001",
      "name": "Owsianka proteinowa z borówkami i masłem migdałowym",
      "role": "Śniadanie węglowodanowo-białkowe — idealne przed aktywnym dniem",
      "protein": 32,
      "carbs": 65,
      "fat": 12,
      "fiber": 9,
      "kcal": 496,
      "prepTime": 8,
      "allergens": [
        "gluten",
        "orzechy"
      ],
      "tags": [
        "owies",
        "borowki",
        "wysokobialkowe"
      ],
      "ingredients": [
        {
          "item": "Płatki owsiane górskie",
          "amount": "80g"
        },
        {
          "item": "Mleko migdałowe lub krowie 1.5%",
          "amount": "250ml"
        },
        {
          "item": "Odżywka białkowa (WPC/izolat waniliowy)",
          "amount": "30g"
        },
        {
          "item": "Świeże lub mrożone borówki",
          "amount": "100g"
        },
        {
          "item": "Masło migdałowe 100%",
          "amount": "15g (1 łyżka)"
        },
        {
          "item": "Cynamon cejloński",
          "amount": "szczypta"
        }
      ],
      "recipe": "1. Płatki zalej mlekiem i gotuj na małym ogniu przez 4-5 minut do zgęstnienia.\n2. Zdejmij z ognia, odczekaj minutę i energicznie wymieszaj z odżywką białkową (nie gotuj białka).\n3. Przełóż do miski, posyp borówkami, dodaj łyżkę masła migdałowego i oprósz cynamonem.",
      "mealTiming": "morning"
    },
    {
      "id": "meal_sn_002",
      "name": "Jajecznica z 3 jaj na maśle klarowanym z awokado i chlebem żytnim",
      "role": "Klasyczne śniadanie białkowo-tłuszczowe — stabilna energia i sytość",
      "protein": 28,
      "carbs": 34,
      "fat": 26,
      "fiber": 7,
      "kcal": 482,
      "prepTime": 10,
      "allergens": [
        "jaja",
        "gluten"
      ],
      "tags": [
        "jajka",
        "awokado",
        "pieczywo-zytnie"
      ],
      "ingredients": [
        {
          "item": "Jaja ściółkowe lub wolny wybieg",
          "amount": "3 sztuki (L)"
        },
        {
          "item": "Masło klarowane (ghee)",
          "amount": "5g (pół łyżeczki)"
        },
        {
          "item": "Chleb żytni na zakwasie 100%",
          "amount": "70g (2 kromki)"
        },
        {
          "item": "Dojrzałe awokado Hass",
          "amount": "50g (1/3 sztuki)"
        },
        {
          "item": "Szczypiorek świeży",
          "amount": "10g"
        },
        {
          "item": "Sól morska i świeżo mielony pieprz",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Jaja roztrzep w miseczce ze szczyptą soli i pieprzu.\n2. Na patelni rozgrzej masło klarowane na małym ogniu.\n3. Wlej masę jajeczną i delikatnie przesuwaj łopatką przez 2-3 minuty, aż jajecznica będzie kremowa.\n4. Podawaj z chlebem żytnim obłożonym plastrami awokado i posiekanym szczypiorkiem.",
      "mealTiming": "morning"
    },
    {
      "id": "meal_sn_003",
      "name": "Szakszuka z pomidorami malinowymi, papryką i fetą",
      "role": "Śniadanie śródziemnomorskie bogate w likopen, potas i białko",
      "protein": 24,
      "carbs": 28,
      "fat": 20,
      "fiber": 6,
      "kcal": 388,
      "prepTime": 15,
      "allergens": [
        "jaja",
        "nabiał",
        "gluten"
      ],
      "tags": [
        "wegetarianskie",
        "szakszuka",
        "pomidory"
      ],
      "ingredients": [
        {
          "item": "Jaja świeże",
          "amount": "2 sztuki"
        },
        {
          "item": "Pomidory krojone (świeże lub passata)",
          "amount": "250g"
        },
        {
          "item": "Papryka czerwona",
          "amount": "60g (1/3 sztuki)"
        },
        {
          "item": "Cebula szalotka i ząbek czosnku",
          "amount": "40g"
        },
        {
          "item": "Ser feta prawdziwy P.D.O.",
          "amount": "30g"
        },
        {
          "item": "Oliwa z oliwek extra virgin",
          "amount": "5g"
        },
        {
          "item": "Kumin mielony i słodka papryka",
          "amount": "po 1/2 łyżeczki"
        },
        {
          "item": "Grzanka z chleba orkiszowego",
          "amount": "40g (1 kromka)"
        }
      ],
      "recipe": "1. Na oliwie podsmaż drobno posiekaną szalotkę, czosnek i paprykę pokrojoną w kostkę.\n2. Dodaj kumin i paprykę słodką, smaż 30 sekund do uwolnienia aromatu.\n3. Wlej pomidory, zredukuj sos przez 6-8 minut do zagęszczenia.\n4. Zrób 2 wgłębienia, wbij w nie jaja, posyp pokruszoną fetą.\n5. Przykryj i gotuj na minimalnym ogniu przez 4-5 minut (białka ścięte, żółtka płynne). Podawaj z grzanką.",
      "mealTiming": "morning"
    },
    {
      "id": "meal_sn_004",
      "name": "Placuszki twarogowe (syrniki) z malinami i jogurtem greckim",
      "role": "Wysokobiałkowe śniadanie deserowe — aż 38g pełnowartościowego białka",
      "protein": 38,
      "carbs": 42,
      "fat": 9,
      "fiber": 5,
      "kcal": 401,
      "prepTime": 15,
      "allergens": [
        "nabiał",
        "jaja",
        "gluten"
      ],
      "tags": [
        "twarog",
        "wysokobialkowe",
        "na-slodko"
      ],
      "ingredients": [
        {
          "item": "Twaróg półtłusty lub klinek chudy",
          "amount": "200g"
        },
        {
          "item": "Jajko całe",
          "amount": "1 sztuka"
        },
        {
          "item": "Mąka owsiana lub orkiszowa",
          "amount": "30g (2 łyżki)"
        },
        {
          "item": "Erytrytol lub odrobina miodu",
          "amount": "15g"
        },
        {
          "item": "Jogurt grecki 0% lub 2%",
          "amount": "80g"
        },
        {
          "item": "Maliny świeże lub rozmrożone",
          "amount": "80g"
        },
        {
          "item": "Ekstrakt z wanilii",
          "amount": "kilka kropel"
        }
      ],
      "recipe": "1. Twaróg rozgnieć widelcem z jajkiem, erytrytolem, wanilią i mąką owsianą na zwartą masę.\n2. Uformuj zwilżonymi dłońmi 4-5 okrągłych placuszków.\n3. Smaż na patelni teflonowej na małym ogniu po 3-4 minuty z każdej strony pod przykryciem na minimalnej ilości tłuszczu.\n4. Podawaj z kleksem jogurtu greckiego i malinami.",
      "mealTiming": "morning"
    },
    {
      "id": "meal_sn_005",
      "name": "Kanapki z pastą z wędzonego łososia, twarogu i ogórka kiszonego",
      "role": "Śniadanie bogate w kwasy Omega-3 EPA/DHA i probiotyki",
      "protein": 34,
      "carbs": 38,
      "fat": 14,
      "fiber": 6,
      "kcal": 414,
      "prepTime": 7,
      "allergens": [
        "ryby",
        "nabiał",
        "gluten"
      ],
      "tags": [
        "omega-3",
        "losos",
        "pieczywo-razowe"
      ],
      "ingredients": [
        {
          "item": "Chleb żytni pełnoziarnisty",
          "amount": "80g (2 kromki)"
        },
        {
          "item": "Łosoś wędzony na gorąco lub zimno",
          "amount": "80g"
        },
        {
          "item": "Twaróg chudy mielony lub serek wiejski lekki",
          "amount": "100g"
        },
        {
          "item": "Ogórek kiszony",
          "amount": "60g (1 sztuka)"
        },
        {
          "item": "Koper świeży",
          "amount": "1 łyżka posiekanego"
        },
        {
          "item": "Pieprz czarny i sok z cytryny",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Rozdrobnij łososia widelcem i połącz z twarogiem, łyżeczką soku z cytryny i koperkiem.\n2. Dopraw pieprzem (łosoś jest już słony, więc soli nie trzeba).\n3. Posmaruj pastą kromki żytniego chleba.\n4. Udekoruj plasterkami ogórka kiszonego.",
      "mealTiming": "morning"
    },
    {
      "id": "meal_sn_006",
      "name": "Tosty francuskie na białkach z bananem i cynamonem",
      "role": "Lekkie, beztłuszczowe tosty białkowe — świetne przed porannym treningiem",
      "protein": 30,
      "carbs": 62,
      "fat": 4,
      "fiber": 6,
      "kcal": 404,
      "prepTime": 10,
      "allergens": [
        "jaja",
        "gluten"
      ],
      "tags": [
        "przedtreningowe",
        "niskotluszczowe",
        "tosty"
      ],
      "ingredients": [
        {
          "item": "Chleb tostowy pełnoziarnisty lub brioszka fit",
          "amount": "70g (2 grube kromki)"
        },
        {
          "item": "Białka jaj płynne lub z 3 jaj",
          "amount": "120g"
        },
        {
          "item": "Mleko 1.5%",
          "amount": "40ml"
        },
        {
          "item": "Banan dojrzały",
          "amount": "100g (1 sztuka)"
        },
        {
          "item": "Cynamon i kardamon",
          "amount": "1/2 łyżeczki"
        },
        {
          "item": "Syrop klonowy bez cukru lub odrobina miodu",
          "amount": "10g"
        }
      ],
      "recipe": "1. W głębokim talerzu roztrzep białka z mlekiem, cynamonem i kardamonem.\n2. Zamocz kromki chleba z obu stron, by dobrze nasiąknęły masą.\n3. Smaż na rozgrzanej, suchej patelni nieprzywierającej po 2-3 minuty z każdej strony na złoty kolor.\n4. Podawaj z pokrojonym w plastry bananem i delikatną strużką syropu.",
      "mealTiming": "morning"
    },
    {
      "id": "meal_sn_007",
      "name": "Smoothie bowl z mango, marakują i izolatem serwatkowym",
      "role": "Orzeźwiające, enzymatyczne śniadanie antyoksydacyjne",
      "protein": 31,
      "carbs": 54,
      "fat": 6,
      "fiber": 7,
      "kcal": 394,
      "prepTime": 6,
      "allergens": [
        "nabiał"
      ],
      "tags": [
        "smoothie",
        "witaminy",
        "lekkostrawne"
      ],
      "ingredients": [
        {
          "item": "Mrożone kawałki mango",
          "amount": "150g"
        },
        {
          "item": "Pół banana mrożonego",
          "amount": "60g"
        },
        {
          "item": "Izolat białka serwatkowego (WPI neutralny lub mango)",
          "amount": "30g"
        },
        {
          "item": "Woda kokosowa lub napój migdałowy",
          "amount": "120ml"
        },
        {
          "item": "Nasiona chia",
          "amount": "10g"
        },
        {
          "item": "Płatki kokosa nieprażone",
          "amount": "10g"
        }
      ],
      "recipe": "1. Do blendera kielichowego wrzuć mrożone mango, banana, izolat i dolej wodę kokosową.\n2. Zblenduj na gęsty, kremowy mus (jak sorbet).\n3. Przełóż do miski, udekoruj chia i płatkami kokosowymi.",
      "mealTiming": "morning"
    },
    {
      "id": "meal_sn_008",
      "name": "Gofry białkowo-owsiane z musem truskawkowym",
      "role": "Komfortowe śniadanie weekendowe o profilu dietetycznym",
      "protein": 33,
      "carbs": 48,
      "fat": 8,
      "fiber": 6,
      "kcal": 396,
      "prepTime": 12,
      "allergens": [
        "jaja",
        "gluten",
        "nabiał"
      ],
      "tags": [
        "gofry",
        "fit-deser",
        "truskawki"
      ],
      "ingredients": [
        {
          "item": "Mąka owsiana zmielona z płatków",
          "amount": "50g"
        },
        {
          "item": "Odżywka białkowa waniliowa",
          "amount": "25g"
        },
        {
          "item": "Jajko całe",
          "amount": "1 sztuka"
        },
        {
          "item": "Mleko lub woda gazowana",
          "amount": "70ml"
        },
        {
          "item": "Proszek do pieczenia",
          "amount": "1/2 łyżeczki"
        },
        {
          "item": "Truskawki zblendowane na mus",
          "amount": "120g"
        }
      ],
      "recipe": "1. Wymieszaj mąkę, odżywkę, proszek, jajko i mleko/wodę gazowaną do gładkiej konsystencji ciasta.\n2. Rozgrzej gofrownicę, lekko spryskaj oliwą.\n3. Piecz porcję ciasta przez 4-5 minut do chrupkości.\n4. Podawaj z ciepłym musem truskawkowym.",
      "mealTiming": "morning"
    },
    {
      "id": "meal_sn_009",
      "name": "Kasza jaglana na mleku sojowym z prażonym jabłkiem i orzechami włoskimi",
      "role": "Alkalizujące śniadanie rozgrzewające z wolno uwalnianą energią",
      "protein": 18,
      "carbs": 68,
      "fat": 15,
      "fiber": 8,
      "kcal": 479,
      "prepTime": 15,
      "allergens": [
        "orzechy",
        "soja"
      ],
      "tags": [
        "weganskie",
        "jaglanka",
        "orzechy-wloskie"
      ],
      "ingredients": [
        {
          "item": "Kasza jaglana sucha (przepłukana wrzątkiem)",
          "amount": "60g"
        },
        {
          "item": "Napój sojowy wzbogacany wapniem",
          "amount": "250ml"
        },
        {
          "item": "Jabłko starte na grubych oczkach",
          "amount": "150g (1 sztuka)"
        },
        {
          "item": "Orzechy włoskie posiekane",
          "amount": "20g"
        },
        {
          "item": "Cynamon i goździki mielone",
          "amount": "1/2 łyżeczki"
        }
      ],
      "recipe": "1. Kaszę przepłucz na sitku wrzątkiem (pozbycie się goryczki).\n2. Ugotuj w napoju sojowym na małym ogniu przez 12 minut pod przykryciem.\n3. Na osobnej patelni podduś jabłko z cynamonem i odrobiną wody przez 3 minuty.\n4. Połącz jaglankę z duszonym jabłkiem i posyp orzechami włoskimi.",
      "mealTiming": "morning"
    },
    {
      "id": "meal_sn_010",
      "name": "Omlet hiszpański z młodymi ziemniakami, indykiem i szpinakiem",
      "role": "Gęste odżywczo śniadanie siłowe — świetne na regenerację potreningową",
      "protein": 36,
      "carbs": 35,
      "fat": 16,
      "fiber": 4,
      "kcal": 428,
      "prepTime": 14,
      "allergens": [
        "jaja"
      ],
      "tags": [
        "omlet",
        "ziemniaki",
        "wysokobialkowe"
      ],
      "ingredients": [
        {
          "item": "Jaja całe",
          "amount": "3 sztuki"
        },
        {
          "item": "Ziemniaki ugotowane wcześniej (pokrojone w plastry)",
          "amount": "150g"
        },
        {
          "item": "Pierś z indyka pieczona w ziołach (kostka)",
          "amount": "60g"
        },
        {
          "item": "Świeży szpinak baby",
          "amount": "40g"
        },
        {
          "item": "Oliwa z oliwek",
          "amount": "5g"
        },
        {
          "item": "Czosnek granulowany i sól",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Na patelni z oliwą podsmaż plastry ugotowanych ziemniaków i indyka przez 2 minuty.\n2. Dodaj szpinak, aż zwiędnie (30 sekund).\n3. Zalej roztrzepanymi jajami doprawionymi solą i czosnkiem.\n4. Smaż pod przykryciem na małym ogniu przez 5 minut, aż masa się zetnie.",
      "mealTiming": "morning"
    }
  ],
  "obiad": [
    {
      "id": "meal_ob_001",
      "name": "Pieczona pierś z kurczaka w ziołach prowansalskich z batatami i brokułem",
      "role": "Złoty standard posiłku sportowego — optymalny bilans makroskładników",
      "protein": 46,
      "carbs": 58,
      "fat": 11,
      "fiber": 9,
      "kcal": 515,
      "prepTime": 25,
      "allergens": [],
      "tags": [
        "kurczak",
        "bataty",
        "czysty-posilek"
      ],
      "ingredients": [
        {
          "item": "Pierś z kurczaka zagrodowego",
          "amount": "180g"
        },
        {
          "item": "Bataty (słodkie ziemniaki)",
          "amount": "250g"
        },
        {
          "item": "Brokuł świeży",
          "amount": "150g"
        },
        {
          "item": "Oliwa z oliwek extra virgin",
          "amount": "10g (1 łyżka)"
        },
        {
          "item": "Zioła prowansalskie, papryka wędzona, sól",
          "amount": "po 1/2 łyżeczki"
        }
      ],
      "recipe": "1. Piekarnik nagrzej do 200°C.\n2. Bataty pokrój w słupki, wymieszaj z 5g oliwy i papryką wędzoną.\n3. Pierś z kurczaka natrzyj resztą oliwy, solą i ziołami prowansalskimi.\n4. Piecz bataty i kurczaka na blasze z papierem do pieczenia przez 22-25 minut.\n5. W międzyczasie ugotuj różyczki brokuła na parze przez 5 minut al dente.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_002",
      "name": "Łosoś atlantycki pieczony z komosą ryżową (quinoa) i szparagami",
      "role": "Posiłek pro-regeneracyjny: przeciwzapalne Omega-3, magnez i selen",
      "protein": 42,
      "carbs": 44,
      "fat": 20,
      "fiber": 7,
      "kcal": 524,
      "prepTime": 20,
      "allergens": [
        "ryby"
      ],
      "tags": [
        "losos",
        "quinoa",
        "omega-3"
      ],
      "ingredients": [
        {
          "item": "Filet z łososia świeżego",
          "amount": "160g"
        },
        {
          "item": "Komosa ryżowa (quinoa) sucha",
          "amount": "60g"
        },
        {
          "item": "Szparagi zielone lub fasolka szparagowa",
          "amount": "150g"
        },
        {
          "item": "Cytryna i świeży koperek",
          "amount": "1/2 sztuki"
        },
        {
          "item": "Sól morska i pieprz cytrynowy",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Quinoa opłucz i ugotuj w proporcji 1:2 w lekko osolonej wodzie przez 15 minut.\n2. Łososia skrop sokiem z cytryny, oprósz solą i pieprzem cytrynowym.\n3. Szparagi pozbaw twardych końców.\n4. Ułóż rybę i szparagi w naczyniu żaroodpornym, piecz w 190°C przez 14 minut.\n5. Podawaj łososia na poduszce z komosy z zielonymi szparagami i koperkiem.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_003",
      "name": "Meksykański bowl z mielonym indykiem, czarną fasolą i salsą pomidorową",
      "role": "Posiłek wysokobłonnikowy z kompleksem witamin z grupy B i żelaza",
      "protein": 44,
      "carbs": 62,
      "fat": 12,
      "fiber": 13,
      "kcal": 532,
      "prepTime": 18,
      "allergens": [],
      "tags": [
        "indyk",
        "fasola",
        "mexican-bowl"
      ],
      "ingredients": [
        {
          "item": "Chude mięso mielone z piersi indyka",
          "amount": "170g"
        },
        {
          "item": "Ryż basmati brązowy lub biały gotowany",
          "amount": "130g (ok. 50g suchego)"
        },
        {
          "item": "Czarna fasola z puszki (opłukana)",
          "amount": "100g"
        },
        {
          "item": "Kukurydza słodka",
          "amount": "50g"
        },
        {
          "item": "Pomidory krojone z kolendrą i limonką",
          "amount": "100g"
        },
        {
          "item": "Przyprawa meksykańska (kumin, kolendra, oregano, chili)",
          "amount": "1 łyżeczka"
        },
        {
          "item": "Olej z awokado lub rzepakowy",
          "amount": "5g"
        }
      ],
      "recipe": "1. Na patelni rozgrzej olej, podsmaż mięso mielone z indyka z przyprawami meksykańskimi przez 6 minut.\n2. Dodaj czarną fasolę i kukurydzę, wymieszaj i podgrzewaj 2 minuty.\n3. W misce ułóż ugotowany ryż, na nim porcję mięsa z fasolą.\n4. Udekoruj świeżą salsą pomidorową z kolendrą i sokiem z limonki.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_004",
      "name": "Polędwiczki wieprzowe w sosie kurkowym z kaszą gryczaną niepaloną",
      "role": "Chude mięso bogate w tiaminę (wit. B1) i cynk połączone z rutyną z gryki",
      "protein": 45,
      "carbs": 52,
      "fat": 12,
      "fiber": 8,
      "kcal": 496,
      "prepTime": 22,
      "allergens": [
        "nabiał"
      ],
      "tags": [
        "poledwiczka",
        "kasza-gryczana",
        "grzyby"
      ],
      "ingredients": [
        {
          "item": "Polędwiczka wieprzowa oczyszczona",
          "amount": "170g"
        },
        {
          "item": "Kasza gryczana biała (niepalona) sucha",
          "amount": "60g"
        },
        {
          "item": "Kurki lub pieczarki brunatne",
          "amount": "100g"
        },
        {
          "item": "Jogurt grecki lub śmietanka 12% lekka",
          "amount": "40g"
        },
        {
          "item": "Cebula szalotka",
          "amount": "30g"
        },
        {
          "item": "Oliwa z oliwek",
          "amount": "5g"
        },
        {
          "item": "Natka pietruszki świeża",
          "amount": "1 łyżka"
        }
      ],
      "recipe": "1. Kaszę gryczaną ugotuj w osolonym wrzątku przez 12-14 minut.\n2. Polędwiczkę pokrój w medaliony o grubości 2 cm, delikatnie spłaszcz dłonią.\n3. Obsmaż na oliwie po 2 minuty z każdej strony na dużym ogniu, zdejmij na talerz.\n4. Na tej samej patelni zeszklij szalotkę i grzyby, zredukuj płyn, dodaj jogurt grecki rozrobiony z odrobiną wody z kaszy.\n5. Włóż mięso z powrotem do sosu na 2 minuty na mały ogień. Posyp natką.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_005",
      "name": "Dorsz atlantycki na parze z puree ziemniaczanym i surówką z kiszonej kapusty",
      "role": "Lekkostrawny obiad niskotłuszczowy wspierający mikrobiotę jelitową",
      "protein": 40,
      "carbs": 48,
      "fat": 6,
      "fiber": 7,
      "kcal": 406,
      "prepTime": 20,
      "allergens": [
        "ryby",
        "nabiał"
      ],
      "tags": [
        "dorsz",
        "probiotyki",
        "niskotluszczowe"
      ],
      "ingredients": [
        {
          "item": "Polędwica z dorsza atlantyckiego",
          "amount": "200g"
        },
        {
          "item": "Ziemniaki mączyste",
          "amount": "250g"
        },
        {
          "item": "Mleko 1.5%",
          "amount": "40ml"
        },
        {
          "item": "Kapusta kiszona z marchewką",
          "amount": "150g"
        },
        {
          "item": "Olej lniany tłoczony na zimno",
          "amount": "5g"
        },
        {
          "item": "Koperek, gałka muszkatołowa, pieprz biały",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Ziemniaki ugotuj do miękkości, utłucz z ciepłym mlekiem, szczyptą soli i gałki muszkatołowej na aksamitne puree.\n2. Dorsza dopraw solą, pieprzem białym i koperkiem, ugotuj na parze (8-10 minut).\n3. Kapustę kiszoną odciśnij z nadmiaru soku, wymieszaj z olejem lnianym i świeżo mielonym pieprzem.\n4. Podawaj delikatną rybę z puree i chrupiącą surówką.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_006",
      "name": "Stir-fry z wołowiny ligawy z warzywami crunchy i makaronem ryżowym",
      "role": "Szybki posiłek azjatycki — wysoka zawartość kreatyny naturalnej i żelaza hemowego",
      "protein": 44,
      "carbs": 56,
      "fat": 13,
      "fiber": 6,
      "kcal": 517,
      "prepTime": 15,
      "allergens": [
        "soja",
        "sezam"
      ],
      "tags": [
        "wolowina",
        "stir-fry",
        "azjatyckie"
      ],
      "ingredients": [
        {
          "item": "Wołowina chuda (ligawa lub polędwica)",
          "amount": "160g"
        },
        {
          "item": "Makaron ryżowy wstążki",
          "amount": "60g suchego"
        },
        {
          "item": "Papryka, cukinia, marchew w słupkach",
          "amount": "150g"
        },
        {
          "item": "Sos sojowy o obniżonej zawartości soli",
          "amount": "20ml"
        },
        {
          "item": "Olej sezamowy",
          "amount": "5g"
        },
        {
          "item": "Świeży imbir i czosnek",
          "amount": "po 1 łyżeczce startych"
        },
        {
          "item": "Nasiona sezamu prażone",
          "amount": "5g"
        }
      ],
      "recipe": "1. Makaron zalej wrzątkiem na 5 minut, odcedź.\n2. Wołowinę pokrój w bardzo cienkie paski w poprzek włókien.\n3. W woku lub głębokiej patelni rozgrzej olej sezamowy, wrzuć wołowinę na bardzo mocny ogień na 2 minuty, zdejmij.\n4. Wrzuć imbir, czosnek i warzywa — smaż mieszając przez 3-4 minuty (mają pozostać chrupiące).\n5. Dodaj wołowinę, makaron i sos sojowy, wymieszaj na ogniu przez 1 minutę. Posyp sezamem.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_007",
      "name": "Makaron pełnoziarnisty z krewetkami, pomidorkami cherry i czosnkiem",
      "role": "Lekki posiłek śródziemnomorski bogaty w jod, astaksantynę i cynk",
      "protein": 36,
      "carbs": 58,
      "fat": 10,
      "fiber": 8,
      "kcal": 466,
      "prepTime": 16,
      "allergens": [
        "skorupiaki",
        "gluten"
      ],
      "tags": [
        "krewetki",
        "makaron",
        "lekkie"
      ],
      "ingredients": [
        {
          "item": "Krewetki królewskie obrane (oczyszczone)",
          "amount": "180g"
        },
        {
          "item": "Makaron pełnoziarnisty tagliatelle lub penne",
          "amount": "70g suchego"
        },
        {
          "item": "Pomidorki cherry przekrojone na pół",
          "amount": "120g"
        },
        {
          "item": "Czosnek w cienkich plasterkach",
          "amount": "2 ząbki"
        },
        {
          "item": "Oliwa z oliwek extra virgin",
          "amount": "8g"
        },
        {
          "item": "Świeża bazylia i natka pietruszki",
          "amount": "garść"
        },
        {
          "item": "Płatki chili i sok z cytryny",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Makaron ugotuj al dente w osolonej wodzie.\n2. Na patelni rozgrzej oliwę na średnim ogniu, dodaj plasterki czosnku i płatki chili (smaż 45 sekund, nie przypal czosnku).\n3. Włóż krewetki i smaż po 1.5 minuty z każdej strony do różowego koloru.\n4. Dodaj pomidorki cherry, odrobinę wody z gotowania makaronu i duś 2 minuty.\n5. Wrzuć makaron na patelnię, wymieszaj z ziołami i sokiem z cytryny.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_008",
      "name": "Curry z ciecierzycą, batatem, szpinakiem i mlekiem kokosowym light",
      "role": "Pełnowartościowy wegański obiad gęsty w mikroskładniki i polifenole",
      "protein": 20,
      "carbs": 74,
      "fat": 14,
      "fiber": 15,
      "kcal": 502,
      "prepTime": 25,
      "allergens": [],
      "tags": [
        "weganskie",
        "curry",
        "ciecierzyca"
      ],
      "ingredients": [
        {
          "item": "Ciecierzyca gotowana (ze słoika/puszki)",
          "amount": "180g"
        },
        {
          "item": "Batat pokrojony w kostkę",
          "amount": "150g"
        },
        {
          "item": "Mleczko kokosowe light (6-7% tłuszczu)",
          "amount": "150ml"
        },
        {
          "item": "Świeży szpinak baby",
          "amount": "60g"
        },
        {
          "item": "Ryż basmati",
          "amount": "50g suchego"
        },
        {
          "item": "Pasta curry żółta lub czerwona",
          "amount": "15g (1 czubata łyżka)"
        },
        {
          "item": "Świeża kolendra i sok z limonki",
          "amount": "do podania"
        }
      ],
      "recipe": "1. Ryż ugotuj na sypko.\n2. W rondelku podsmaż pastę curry na sucho przez 1 minutę.\n3. Dodaj kostki batata i zalej mleczkiem kokosowym oraz 50ml wody. Gotuj 12 minut do miękkości batata.\n4. Wsyp ciecierzycę i duś kolejne 4 minuty.\n5. Na koniec wrzuć szpinak, aż zmniejszy objętość. Podawaj z ryżem basmati, limonką i kolendrą.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_009",
      "name": "Pieczona pierś z indyka w marynacie musztardowo-miodowej z kaszą pęczak",
      "role": "Wysokobiałkowe danie obiadowe o niskim indeksie glikemicznym",
      "protein": 48,
      "carbs": 54,
      "fat": 9,
      "fiber": 10,
      "kcal": 489,
      "prepTime": 25,
      "allergens": [
        "gorczyca",
        "gluten"
      ],
      "tags": [
        "indyk",
        "kasza-peczak",
        "niski-ig"
      ],
      "ingredients": [
        {
          "item": "Filet z piersi indyka",
          "amount": "180g"
        },
        {
          "item": "Kasza pęczak sucha",
          "amount": "60g"
        },
        {
          "item": "Musztarda Dijon lub ziarnista",
          "amount": "15g"
        },
        {
          "item": "Miód naturalny",
          "amount": "5g"
        },
        {
          "item": "Marchew i seler naciowy w słupkach",
          "amount": "140g"
        },
        {
          "item": "Oliwa z oliwek",
          "amount": "5g"
        }
      ],
      "recipe": "1. Pęczak ugotuj w osolonym wrzątku przez 20 minut.\n2. Wymieszaj musztardę z miodem, solą i oliwą — posmaruj marynatą filet z indyka.\n3. Warzywa rozłóż obok mięsa na blasze do pieczenia.\n4. Piecz w temperaturze 185°C przez 22 minuty (mięso soczyste w środku).\n5. Podawaj pokrojony filet z ugotowanym pęczakiem i pieczonymi warzywami.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_010",
      "name": "Burger wołowy w bułce pełnoziarnistej z pieczonymi frytkami z selera",
      "role": "Zdrowa alternatywa fast-foodu — wysokie białko, niska kaloryczność frytek",
      "protein": 44,
      "carbs": 48,
      "fat": 15,
      "fiber": 9,
      "kcal": 503,
      "prepTime": 20,
      "allergens": [
        "gluten",
        "sezam"
      ],
      "tags": [
        "burger",
        "wolowina",
        "frytki-z-selera"
      ],
      "ingredients": [
        {
          "item": "Mielony antrykot lub chuda wołowina 90/10",
          "amount": "160g"
        },
        {
          "item": "Bułka burgerowa grahamka/pełnoziarnista",
          "amount": "70g (1 sztuka)"
        },
        {
          "item": "Korzeń selera obrany (frytki)",
          "amount": "250g"
        },
        {
          "item": "Oliwa z oliwek do frytek",
          "amount": "5g"
        },
        {
          "item": "Plastry pomidora, czerwonej cebuli i ogórka kiszonego",
          "amount": "60g"
        },
        {
          "item": "Liść sałaty rzymskiej i sos jogurtowo-musztardowy",
          "amount": "30g"
        }
      ],
      "recipe": "1. Seler pokrój w słupki frytek, skrop oliwą, oprósz papryką wędzoną i piecz w 210°C przez 20 minut na chrupko.\n2. Z mięsa uformuj burgera o grubości 2 cm, dopraw tylko solą i świeżym pieprzem z zewnątrz.\n3. Smaż na mocno rozgrzanej patelni grillowej po 3 minuty z każdej strony.\n4. Bułkę przekrój i podpiecz na sucho. Złóż burgera z sosem, sałatą, mięsem i warzywami. Podawaj z frytkami z selera.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_011",
      "name": "Tofu chrupiące pieczone z brokułem, brązowym ryżem i sosem orzechowym",
      "role": "Zrównoważony obiad roślinny z pełnym profilem aminokwasowym",
      "protein": 28,
      "carbs": 60,
      "fat": 18,
      "fiber": 11,
      "kcal": 514,
      "prepTime": 22,
      "allergens": [
        "soja",
        "orzechy"
      ],
      "tags": [
        "weganskie",
        "tofu",
        "sos-orzechowy"
      ],
      "ingredients": [
        {
          "item": "Tofu naturalne twarde (odciśnięte)",
          "amount": "180g"
        },
        {
          "item": "Mąka kukurydziana lub skrobia z tapioki",
          "amount": "10g"
        },
        {
          "item": "Ryż brązowy gotowany",
          "amount": "130g (ok. 50g suchego)"
        },
        {
          "item": "Różyczki brokuła",
          "amount": "150g"
        },
        {
          "item": "Masło orzechowe 100%",
          "amount": "15g"
        },
        {
          "item": "Sos sojowy, czosnek i sok z limonki",
          "amount": "do sosu"
        }
      ],
      "recipe": "1. Tofu pokrój w kostkę, obtocz w skrobi kukurydzianej i piecz w 200°C przez 18 minut na chrupko.\n2. Brokuł ugotuj na parze przez 4-5 minut.\n3. Wymieszaj masło orzechowe z sosem sojowym, startym czosnkiem, limonką i 2 łyżkami ciepłej wody.\n4. W misce ułóż ryż, brokuł, chrupiące tofu i polej aksamitnym sosem orzechowym.",
      "mealTiming": "any"
    },
    {
      "id": "meal_ob_012",
      "name": "Gulasz z udźca indyka z warzywami korzeniowymi i kopytkami z ricottą",
      "role": "Rozgrzewające comfort-food o wysokiej zawartości kolagenu i białka",
      "protein": 46,
      "carbs": 50,
      "fat": 12,
      "fiber": 7,
      "kcal": 492,
      "prepTime": 30,
      "allergens": [
        "nabiał",
        "gluten"
      ],
      "tags": [
        "indyk",
        "gulasz",
        "regeneracja"
      ],
      "ingredients": [
        {
          "item": "Udziec z indyka bez skóry pokrojony w gulasz",
          "amount": "170g"
        },
        {
          "item": "Marchew, pietruszka, por pokrojone",
          "amount": "150g"
        },
        {
          "item": "Kopytka lub gnocchi pełnoziarniste",
          "amount": "130g"
        },
        {
          "item": "Olej rzepakowy tłoczony na zimno",
          "amount": "5g"
        },
        {
          "item": "Liść laurowy, ziele angielskie, majeranek",
          "amount": "do smaku"
        },
        {
          "item": "Passata pomidorowa lub bulion warzywny",
          "amount": "150ml"
        }
      ],
      "recipe": "1. Kawałki indyka obsmaż na oleju w garnku z grubym dnem.\n2. Dodaj warzywa, liść laurowy i ziele angielskie, zalej passatą i odrobiną wody.\n3. Duś na wolnym ogniu pod przykryciem przez 25 minut do kruchości mięsa.\n4. W osobnym garnku ugotuj kopytka (2-3 minuty od wypłynięcia).\n5. Podawaj gulasz posypany majerankiem z ciepłymi kopytkami.",
      "mealTiming": "any"
    }
  ],
  "kolacja": [
    {
      "id": "meal_kol_001",
      "name": "Sałatka z tuńczykiem w sosie własnym, jajkiem na twardo i oliwkami",
      "role": "Lekka kolacja białkowa z kwasami tłuszczowymi wspomagającymi sen",
      "protein": 36,
      "carbs": 12,
      "fat": 14,
      "fiber": 4,
      "kcal": 318,
      "prepTime": 8,
      "allergens": [
        "ryby",
        "jaja"
      ],
      "tags": [
        "tunczyk",
        "salatka",
        "low-carb"
      ],
      "ingredients": [
        {
          "item": "Tuńczyk w sosie własnym (odsączony)",
          "amount": "120g"
        },
        {
          "item": "Jajko ugotowane na twardo",
          "amount": "1 sztuka"
        },
        {
          "item": "Mix sałat z rukolą i roszponką",
          "amount": "80g"
        },
        {
          "item": "Pomidorki koktajlowe",
          "amount": "80g"
        },
        {
          "item": "Oliwki czarne lub zielone Kalamata",
          "amount": "25g (ok. 6-7 sztuk)"
        },
        {
          "item": "Oliwa z oliwek extra virgin",
          "amount": "5g"
        },
        {
          "item": "Sok z cytryny i oregano",
          "amount": "do dressingu"
        }
      ],
      "recipe": "1. W misce ułóż porcję miksu sałat.\n2. Dodaj odsączonego tuńczyka, przekrojone pomidorki koktajlowe i oliwki.\n3. Jajko obierz, przekrój na ćwiartki i ułóż na wierzchu.\n4. Skrop oliwą wymieszaną z sokiem z cytryny i oregano.",
      "mealTiming": "evening"
    },
    {
      "id": "meal_kol_002",
      "name": "Twaróg wiejski ze szczypiorkiem, rzodkiewką i chlebem żytnim",
      "role": "Źródło kazeiny micelarnej — stopniowe uwalnianie aminokwasów przez noc",
      "protein": 34,
      "carbs": 32,
      "fat": 7,
      "fiber": 5,
      "kcal": 327,
      "prepTime": 6,
      "allergens": [
        "nabiał",
        "gluten"
      ],
      "tags": [
        "twarog",
        "kazeina",
        "nocna-regeneracja"
      ],
      "ingredients": [
        {
          "item": "Twaróg chudy lub półtłusty klinek",
          "amount": "180g"
        },
        {
          "item": "Jogurt naturalny gęsty 2%",
          "amount": "50g"
        },
        {
          "item": "Rzodkiewki starte lub pokrojone",
          "amount": "60g (4 sztuki)"
        },
        {
          "item": "Szczypiorek świeży posiekany",
          "amount": "15g"
        },
        {
          "item": "Chleb żytni na zakwasie",
          "amount": "60g (1 duża kromka)"
        },
        {
          "item": "Sól morska i pieprz czarny",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Twaróg rozgnieć widelcem z jogurtem naturalnym na jednolitą masę.\n2. Dodaj posiekaną rzodkiewkę i szczypiorek, dopraw solą i pieprzem.\n3. Podawaj ze świeżą kromką chleba żytniego.",
      "mealTiming": "evening"
    },
    {
      "id": "meal_kol_003",
      "name": "Sałatka z grillowaną piersią kurczaka, awokado i pestkami dyni",
      "role": "Kolacja keto/low-carb bogata w cynk, magnez i nienasycone kwasy tłuszczowe",
      "protein": 38,
      "carbs": 10,
      "fat": 18,
      "fiber": 6,
      "kcal": 354,
      "prepTime": 12,
      "allergens": [],
      "tags": [
        "kurczak",
        "awokado",
        "pestki-dyni"
      ],
      "ingredients": [
        {
          "item": "Pierś z kurczaka grillowana",
          "amount": "140g"
        },
        {
          "item": "Awokado dojrzałe",
          "amount": "60g (ok. 1/3 sztuki)"
        },
        {
          "item": "Szpinak baby i roszponka",
          "amount": "70g"
        },
        {
          "item": "Ogórek zielony w plastrach",
          "amount": "80g"
        },
        {
          "item": "Pestki dyni uprażone na sucho",
          "amount": "15g"
        },
        {
          "item": "Sos winegret lekki (oliwa 5g + ocet jabłkowy + musztarda)",
          "amount": "15g"
        }
      ],
      "recipe": "1. Pierś z kurczaka pokrój w plastry po upieczeniu/grillowaniu.\n2. W salaterce połącz szpinak, roszponkę i ogórek.\n3. Ułóż plastry kurczaka i kostki awokado.\n4. Posyp prażonymi pestkami dyni i polej lekkim sosem winegret.",
      "mealTiming": "evening"
    },
    {
      "id": "meal_kol_004",
      "name": "Wrap pełnoziarnisty z pieczonym indykiem, hummusem i warzywami",
      "role": "Wygodna i zbilansowana kolacja o równomiernym profilu makro",
      "protein": 30,
      "carbs": 38,
      "fat": 11,
      "fiber": 7,
      "kcal": 371,
      "prepTime": 7,
      "allergens": [
        "gluten",
        "sezam"
      ],
      "tags": [
        "wrap",
        "hummus",
        "indyk"
      ],
      "ingredients": [
        {
          "item": "Tortilla pełnoziarnista",
          "amount": "60g (1 sztuka)"
        },
        {
          "item": "Pieczona pierś z indyka (wędlina domowa)",
          "amount": "90g"
        },
        {
          "item": "Hummus klasyczny z tahini",
          "amount": "30g (1 czubata łyżka)"
        },
        {
          "item": "Papryka czerwona w paseczkach",
          "amount": "50g"
        },
        {
          "item": "Kiełki rzodkiewki lub brokuła",
          "amount": "15g"
        },
        {
          "item": "Sałata lodowa chrupiąca",
          "amount": "30g"
        }
      ],
      "recipe": "1. Placek tortilli podgrzej przez 20 sekund na suchej patelni, aby zmiękł.\n2. Rozsmaruj hummus na całej powierzchni.\n3. Ułóż liść sałaty, plastry indyka, paski papryki i świeże kiełki.\n4. Zwiń ciasno w rulon, przekrój po skosie na pół.",
      "mealTiming": "evening"
    },
    {
      "id": "meal_kol_005",
      "name": "Zupa krem z pieczonych pomidorów i papryki z mozzarellą light",
      "role": "Lekkostrawna, rozgrzewająca zupa z wysoką zawartością antyoksydantów",
      "protein": 24,
      "carbs": 26,
      "fat": 9,
      "fiber": 6,
      "kcal": 281,
      "prepTime": 15,
      "allergens": [
        "nabiał"
      ],
      "tags": [
        "zupa-krem",
        "likopen",
        "lekkostrawne"
      ],
      "ingredients": [
        {
          "item": "Pomidory krojone z puszki lub pieczone",
          "amount": "350g"
        },
        {
          "item": "Papryka czerwona upieczona bez skórki",
          "amount": "100g"
        },
        {
          "item": "Mozzarella light w kulce",
          "amount": "80g"
        },
        {
          "item": "Czosnek i świeża bazylia",
          "amount": "garść"
        },
        {
          "item": "Oliwa z oliwek",
          "amount": "5g"
        },
        {
          "item": "Grzanka z chleba żytniego",
          "amount": "30g (1 cienka kromka)"
        }
      ],
      "recipe": "1. W rondelku podgrzej pomidory, pieczoną paprykę, czosnek i zblenduj na aksamitny krem.\n2. Dopraw solą, pieprzem i łyżeczką oliwy.\n3. Wlej krem do miski, porwij na wierzch mozzarellę light, by lekko się rozpuściła.\n4. Posyp liśćmi świeżej bazylii i zjedz z chrupiącą grzanką.",
      "mealTiming": "evening"
    },
    {
      "id": "meal_kol_006",
      "name": "Sałatka z grillowanym serem halloumi, pieczonym burakiem i orzechami",
      "role": "Kolacja wegetariańska bogata w azotany rozszerzające naczynia krwionośne",
      "protein": 22,
      "carbs": 24,
      "fat": 17,
      "fiber": 5,
      "kcal": 337,
      "prepTime": 10,
      "allergens": [
        "nabiał",
        "orzechy"
      ],
      "tags": [
        "halloumi",
        "burak",
        "wegetarianskie"
      ],
      "ingredients": [
        {
          "item": "Ser halloumi (wersja light lub klasyczna)",
          "amount": "70g"
        },
        {
          "item": "Burak ugotowany lub upieczony (kostka)",
          "amount": "120g"
        },
        {
          "item": "Rukola świeża",
          "amount": "60g"
        },
        {
          "item": "Orzechy włoskie posiekane",
          "amount": "15g"
        },
        {
          "item": "Krem balsamiczny bez dodatku cukru",
          "amount": "1 łyżeczka"
        }
      ],
      "recipe": "1. Halloumi pokrój w plastry i zgrilluj na suchej patelni grillowej po 2 minuty z każdej strony na złoty kolor.\n2. Na talerzu ułóż rukolę i kostki buraka.\n3. Połóż ciepły ser halloumi, posyp orzechami włoskimi i skrop kremem balsamicznym.",
      "mealTiming": "evening"
    },
    {
      "id": "meal_kol_007",
      "name": "Zapiekanka warzywna z cukinią, brokułem i sosem jajeczno-jogurtowym",
      "role": "Objętościowa kolacja redukcyjna o znikomym obciążeniu trawiennym",
      "protein": 26,
      "carbs": 18,
      "fat": 10,
      "fiber": 7,
      "kcal": 266,
      "prepTime": 20,
      "allergens": [
        "jaja",
        "nabiał"
      ],
      "tags": [
        "niskokaloryczne",
        "objetosciowe",
        "warzywa"
      ],
      "ingredients": [
        {
          "item": "Cukinia pokrojona w półplasterki",
          "amount": "180g"
        },
        {
          "item": "Brokuł podzielony na małe różyczki",
          "amount": "120g"
        },
        {
          "item": "Jaja całe",
          "amount": "2 sztuki"
        },
        {
          "item": "Jogurt grecki 2%",
          "amount": "60g"
        },
        {
          "item": "Czosnek, oregano, sól ziołowa",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Warzywa ułóż w małym naczyniu żaroodpornym.\n2. Jaja roztrzep z jogurtem greckim, czosnkiem i przyprawami.\n3. Zalej warzywa masą jajeczną.\n4. Piecz w temperaturze 190°C przez 18-20 minut do ścięcia i zarumienienia.",
      "mealTiming": "evening"
    },
    {
      "id": "meal_kol_008",
      "name": "Tatar z wędzonego łososia z szalotką, kaparami i grzanką orkiszową",
      "role": "Wykwintna kolacja bogata w witaminę D3 i zdrowe tłuszcze",
      "protein": 28,
      "carbs": 26,
      "fat": 12,
      "fiber": 4,
      "kcal": 324,
      "prepTime": 8,
      "allergens": [
        "ryby",
        "gluten"
      ],
      "tags": [
        "tatar-z-lososia",
        "kwasy-omega",
        "wit-d"
      ],
      "ingredients": [
        {
          "item": "Łosoś wędzony wysokiej jakości drobno posiekany",
          "amount": "110g"
        },
        {
          "item": "Szalotka posiekana w drobną kosteczkę",
          "amount": "20g"
        },
        {
          "item": "Kapary ze słoika odsączone",
          "amount": "15g"
        },
        {
          "item": "Sok z cytryny i oliwa z oliwek",
          "amount": "po 5g"
        },
        {
          "item": "Chleb orkiszowy opieczony na tosterze",
          "amount": "50g (1 grubsza kromka)"
        }
      ],
      "recipe": "1. Posiekanego łososia wymieszaj z szalotką, posiekanymi kaparami, oliwą i sokiem z cytryny.\n2. Dopraw świeżo mielonym pieprzem kolorowym.\n3. Uformuj w ringu kucharskim na talerzu.\n4. Podawaj z ciepłą, chrupiącą grzanką orkiszową.",
      "mealTiming": "evening"
    },
    {
      "id": "meal_kol_009",
      "name": "Sałatka Cezar Fit z grillowanym indykiem i płatkami parmezanu",
      "role": "Klasyczny smak w wersji odchudzonej z sosem na bazie jogurtu",
      "protein": 36,
      "carbs": 14,
      "fat": 11,
      "fiber": 3,
      "kcal": 299,
      "prepTime": 10,
      "allergens": [
        "nabiał",
        "ryby"
      ],
      "tags": [
        "cezar",
        "fit-salatka",
        "indyk"
      ],
      "ingredients": [
        {
          "item": "Pierś z indyka grillowana w ziołach",
          "amount": "130g"
        },
        {
          "item": "Sałata rzymska chrupiąca",
          "amount": "100g"
        },
        {
          "item": "Parmezan P.D.O. starty w cienkie płatki",
          "amount": "15g"
        },
        {
          "item": "Jogurt naturalny gęsty",
          "amount": "40g"
        },
        {
          "item": "Filecik anchois roztarty na pastę lub sos Worcestershire",
          "amount": "pół łyżeczki"
        },
        {
          "item": "Czosnek i sok z cytryny",
          "amount": "do dressingu"
        }
      ],
      "recipe": "1. Sałatę rzymską porwij na kawałki do miski.\n2. Przygotuj sos: wymieszaj jogurt, roztarte anchois, czosnek i sok z cytryny.\n3. Wymieszaj sałatę z sosem.\n4. Na wierzchu ułóż ciepłe paski grillowanego indyka i oprósz płatkami parmezanu.",
      "mealTiming": "evening"
    },
    {
      "id": "meal_kol_010",
      "name": "Serek wiejski lekki na słono z pomidorem malinowym, czarnuszką i słupkami ogórka",
      "role": "Błyskawiczna kolacja (3 minuty) idealna po późnym powrocie do domu",
      "protein": 28,
      "carbs": 12,
      "fat": 6,
      "fiber": 3,
      "kcal": 214,
      "prepTime": 3,
      "allergens": [
        "nabiał"
      ],
      "tags": [
        "szybkie",
        "serek-wiejski",
        "czarnuszka"
      ],
      "ingredients": [
        {
          "item": "Serek wiejski lekki (3% tłuszczu)",
          "amount": "200g (1 opakowanie)"
        },
        {
          "item": "Pomidor malinowy dojrzały",
          "amount": "150g (1 sztuka)"
        },
        {
          "item": "Ogórek gruntowy lub szklarniowy",
          "amount": "80g"
        },
        {
          "item": "Nasiona czarnuszki",
          "amount": "1 łyżeczka"
        },
        {
          "item": "Oliwa z oliwek",
          "amount": "3g"
        },
        {
          "item": "Sól morska gruboziarnista",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Serek wiejski przełóż do miseczki.\n2. Dodaj pokrojonego w grubą kostkę pomidora i plasterki ogórka.\n3. Skrop odrobiną oliwy i obficie posyp aromatyczną czarnuszką.",
      "mealTiming": "evening"
    }
  ],
  "przedtreningowy": [
    {
      "id": "meal_pre_001",
      "name": "Banan z masłem orzechowym na waflach ryżowych",
      "role": "Szybka energia glikemiczna bez obciążania żołądka (45 min przed treningiem)",
      "protein": 8,
      "carbs": 44,
      "fat": 8,
      "fiber": 4,
      "kcal": 280,
      "prepTime": 3,
      "allergens": [
        "orzechy"
      ],
      "tags": [
        "przedtreningowe",
        "szybkie",
        "banan"
      ],
      "ingredients": [
        {
          "item": "Wafle ryżowe pełnoziarniste",
          "amount": "30g (3 sztuki)"
        },
        {
          "item": "Masło orzechowe 100%",
          "amount": "15g (1 łyżka)"
        },
        {
          "item": "Banan dojrzały w plastrach",
          "amount": "100g (1 sztuka)"
        },
        {
          "item": "Szczypta soli morskiej",
          "amount": "dla równowagi elektrolitowej"
        }
      ],
      "recipe": "1. Posmaruj wafle ryżowe masłem orzechowym.\n2. Ułóż plastry banana na wierzchu.\n3. Oprósz minimalną szczyptą soli morskiej.",
      "mealTiming": "pre"
    },
    {
      "id": "meal_pre_002",
      "name": "Kleik ryżowy z izolatem białkowym i malinami",
      "role": "Lekkostrawne węglowodany złożone + czyste białko serwatkowe (60 min przed wysiłkiem)",
      "protein": 26,
      "carbs": 52,
      "fat": 2,
      "fiber": 4,
      "kcal": 330,
      "prepTime": 5,
      "allergens": [
        "nabiał"
      ],
      "tags": [
        "kleik-ryzowy",
        "izolat",
        "przedtreningowe"
      ],
      "ingredients": [
        {
          "item": "Kaszka ryżowa błyskawiczna lub kleik",
          "amount": "60g"
        },
        {
          "item": "Izolat białka serwatkowego (WPI)",
          "amount": "25g"
        },
        {
          "item": "Maliny świeże lub mrożone",
          "amount": "60g"
        },
        {
          "item": "Woda gorąca (nie wrzątek)",
          "amount": "200ml"
        }
      ],
      "recipe": "1. Kaszkę ryżową zalej gorącą wodą i wymieszaj do uzyskania gładkiego kremu.\n2. Odczekaj 2 minuty, wsyp izolat i wymieszaj trzepaczką.\n3. Posyp malinami.",
      "mealTiming": "pre"
    },
    {
      "id": "meal_pre_003",
      "name": "Tost pszenny z dżemem 100% z czarnej porzeczki i ricottą",
      "role": "Fruktoza + glukoza do nasycenia glikogenu wątrobowego i mięśniowego",
      "protein": 11,
      "carbs": 48,
      "fat": 5,
      "fiber": 3,
      "kcal": 281,
      "prepTime": 4,
      "allergens": [
        "gluten",
        "nabiał"
      ],
      "tags": [
        "tost",
        "ricotta",
        "weglowodany"
      ],
      "ingredients": [
        {
          "item": "Chleb pszenny jasny lub graham",
          "amount": "60g (2 kromki)"
        },
        {
          "item": "Ser ricotta lekki",
          "amount": "40g"
        },
        {
          "item": "Dżem 100% z owoców (bez dodatku cukru)",
          "amount": "30g (2 łyżeczki)"
        }
      ],
      "recipe": "1. Kromki chleba opiecz w tosterze na złoty kolor.\n2. Posmaruj delikatną ricottą i nałóż warstwę dżemu owocowego.",
      "mealTiming": "pre"
    },
    {
      "id": "meal_pre_004",
      "name": "Energetyczny shake daktylowo-kawowy z mlekiem owsianym",
      "role": "Naturalna kofeina + szybkie cukry proste z daktyli — naturalny pre-workout",
      "protein": 14,
      "carbs": 50,
      "fat": 3,
      "fiber": 4,
      "kcal": 283,
      "prepTime": 5,
      "allergens": [
        "nabiał"
      ],
      "tags": [
        "kofeina",
        "daktyle",
        "pre-workout"
      ],
      "ingredients": [
        {
          "item": "Daktyle suszone bez pestek (namoczone 5 min w ciepłej wodzie)",
          "amount": "40g (4 sztuki)"
        },
        {
          "item": "Espresso świeżo zaparzone (wystudzone)",
          "amount": "50ml"
        },
        {
          "item": "Mleko owsiane lub krowie 1.5%",
          "amount": "200ml"
        },
        {
          "item": "Odżywka białkowa wanilia lub czekolada",
          "amount": "15g (pół miarki)"
        }
      ],
      "recipe": "1. Włóż namoczone daktyle, espresso, mleko i białko do blendera.\n2. Zblenduj na najwyższych obrotach przez 40 sekund na gładki napój.",
      "mealTiming": "pre"
    },
    {
      "id": "meal_pre_005",
      "name": "Baton owsiany domowy z miodem, żurawiną i nasionami chia",
      "role": "Poręczna przekąska przedtreningowa do zjedzenia w biegu na trening",
      "protein": 7,
      "carbs": 42,
      "fat": 6,
      "fiber": 5,
      "kcal": 250,
      "prepTime": 5,
      "allergens": [
        "gluten"
      ],
      "tags": [
        "baton-owsiany",
        "w-biegu",
        "energia"
      ],
      "ingredients": [
        {
          "item": "Płatki owsiane drobne",
          "amount": "40g"
        },
        {
          "item": "Miód pszczeli",
          "amount": "15g"
        },
        {
          "item": "Żurawina suszona",
          "amount": "15g"
        },
        {
          "item": "Nasiona chia",
          "amount": "5g"
        }
      ],
      "recipe": "1. Płatki wymieszaj z podgrzanym miodem, żurawiną i chia.\n2. Ugnieć w foremce w zwarty prostokątny batonik.",
      "mealTiming": "pre"
    },
    {
      "id": "meal_pre_006",
      "name": "Mus jabłkowo-bananowy z cynamonem i chrupkami orkiszowymi",
      "role": "Błyskawiczne trawienie — idealne gdy zostało mniej niż 40 minut do wysiłku",
      "protein": 5,
      "carbs": 50,
      "fat": 1,
      "fiber": 5,
      "kcal": 229,
      "prepTime": 3,
      "allergens": [
        "gluten"
      ],
      "tags": [
        "lekkostrawne",
        "mus",
        "szybkie-cukry"
      ],
      "ingredients": [
        {
          "item": "Mus 100% jabłko-banan (ze słoiczka lub świeżo starty)",
          "amount": "180g"
        },
        {
          "item": "Orkisz ekspandowany (chrupki)",
          "amount": "20g"
        },
        {
          "item": "Cynamon cejloński",
          "amount": "szczypta"
        }
      ],
      "recipe": "1. Mus wyłóż do miseczki, wsyp chrupki orkiszowe i oprósz cynamonem. Zjedz od razu.",
      "mealTiming": "pre"
    }
  ],
  "potreningowy": [
    {
      "id": "meal_post_001",
      "name": "Shake regeneracyjny: Izolat WPI + banan + woda kokosowa",
      "role": "Maksymalizacja MPS (syntezy białek) i natychmiastowe uzupełnienie elektrolitów",
      "protein": 32,
      "carbs": 42,
      "fat": 1,
      "fiber": 3,
      "kcal": 305,
      "prepTime": 3,
      "allergens": [
        "nabiał"
      ],
      "tags": [
        "izolat",
        "regeneracja",
        "elektrolity"
      ],
      "ingredients": [
        {
          "item": "Izolat białka serwatkowego (WPI)",
          "amount": "35g"
        },
        {
          "item": "Dojrzały banan",
          "amount": "120g"
        },
        {
          "item": "Woda kokosowa 100%",
          "amount": "250ml"
        },
        {
          "item": "Szczypta soli morskiej",
          "amount": "dla sodu"
        }
      ],
      "recipe": "1. Wlej wodę kokosową do shakera/blendera, dodaj banana, izolat i szczyptę soli.\n2. Zblenduj przez 20 sekund i wypij do 30 minut po zakończeniu wysiłku.",
      "mealTiming": "post"
    },
    {
      "id": "meal_post_002",
      "name": "Pudding ryżowy z jagodami i twarogiem zblendowanym na krem",
      "role": "Połączenie szybkiej resyntezy glikogenu z pełnym kompleksem aminokwasów",
      "protein": 35,
      "carbs": 55,
      "fat": 3,
      "fiber": 4,
      "kcal": 387,
      "prepTime": 6,
      "allergens": [
        "nabiał"
      ],
      "tags": [
        "pudding",
        "twarog",
        "okno-anaboliczne"
      ],
      "ingredients": [
        {
          "item": "Płatki ryżowe błyskawiczne",
          "amount": "60g"
        },
        {
          "item": "Twaróg chudy",
          "amount": "130g"
        },
        {
          "item": "Jagody lub borówki",
          "amount": "80g"
        },
        {
          "item": "Miód lub erytrytol",
          "amount": "10g"
        },
        {
          "item": "Ciepła woda lub mleko 0.5%",
          "amount": "150ml"
        }
      ],
      "recipe": "1. Płatki ryżowe zalej wrzątkiem/ciepłym mlekiem na 3 minuty.\n2. Twaróg zblenduj ze słodzikiem i odrobiną wody na aksamitny sernikowy krem.\n3. Połącz płatki ryżowe z kremem twarogowym i posyp jagodami.",
      "mealTiming": "post"
    },
    {
      "id": "meal_post_003",
      "name": "Bułka grahamka z pieczoną piersią kurczaka, pomidorem i rukolą",
      "role": "Klasyczny stały posiłek potreningowy do zabrania ze sobą w torbie",
      "protein": 36,
      "carbs": 44,
      "fat": 4,
      "fiber": 6,
      "kcal": 356,
      "prepTime": 5,
      "allergens": [
        "gluten"
      ],
      "tags": [
        "kanapka",
        "kurczak",
        "na-wynos"
      ],
      "ingredients": [
        {
          "item": "Bułka grahamka",
          "amount": "80g (1 sztuka)"
        },
        {
          "item": "Pieczona pierś z kurczaka w plastrach",
          "amount": "120g"
        },
        {
          "item": "Pomidor w grubych plastrach",
          "amount": "80g"
        },
        {
          "item": "Musztarda łagodna",
          "amount": "10g"
        },
        {
          "item": "Rukola",
          "amount": "garść"
        }
      ],
      "recipe": "1. Bułkę przekrój, posmaruj musztardą.\n2. Włóż plastry pieczonego kurczaka, pomidora i rukolę.",
      "mealTiming": "post"
    },
    {
      "id": "meal_post_004",
      "name": "Kurczak z białym ryżem jaśminowym i sosem pomidorowym",
      "role": "Kultowy posiłek kulturystyczny — najwyższa przyswajalność i zero obciążenia żołądka",
      "protein": 44,
      "carbs": 60,
      "fat": 4,
      "fiber": 3,
      "kcal": 452,
      "prepTime": 15,
      "allergens": [],
      "tags": [
        "kurczak-ryz",
        "lekkostrawne",
        "czysta-masa"
      ],
      "ingredients": [
        {
          "item": "Pierś z kurczaka gotowana na parze lub duszona",
          "amount": "170g"
        },
        {
          "item": "Ryż jaśminowy gotowany",
          "amount": "180g (ok. 65g suchego)"
        },
        {
          "item": "Passata pomidorowa z bazylią",
          "amount": "100ml"
        },
        {
          "item": "Zioła, sól morska",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Ugotuj ryż jaśminowy na miękko.\n2. Pierś z kurczaka podduś w passacie pomidorowej z ziołami przez 10 minut.\n3. Podawaj kurczaka w sosie z ryżem.",
      "mealTiming": "post"
    },
    {
      "id": "meal_post_005",
      "name": "Bowl z tuńczykiem, białym ryżem, ogórkiem i sosem sojowym",
      "role": "Posiłek beztłuszczowy sprzyjający szybkiemu wyrzutowi insuliny i odnowie",
      "protein": 38,
      "carbs": 52,
      "fat": 2,
      "fiber": 3,
      "kcal": 378,
      "prepTime": 6,
      "allergens": [
        "ryby",
        "soja"
      ],
      "tags": [
        "tunczyk",
        "ryz",
        "szybkie"
      ],
      "ingredients": [
        {
          "item": "Tuńczyk w kawałkach w sosie własnym",
          "amount": "140g"
        },
        {
          "item": "Ryż biały basmati ugotowany",
          "amount": "160g"
        },
        {
          "item": "Ogórek świeży w kostce",
          "amount": "80g"
        },
        {
          "item": "Sos sojowy tamari",
          "amount": "15ml"
        },
        {
          "item": "Szczypiorek",
          "amount": "1 łyżka"
        }
      ],
      "recipe": "1. W misce ułóż ciepły ryż basmati.\n2. Na wierzch wyłóż odsączonego tuńczyka i świeżego ogórka.\n3. Skrop sosem sojowym i posyp szczypiorkiem.",
      "mealTiming": "post"
    },
    {
      "id": "meal_post_006",
      "name": "Kaszka manna na chudym mleku z odżywką białkową i borówkami",
      "role": "Błyskawiczne wchłanianie — delikatne dla przewodu pokarmowego po ciężkich przysiadach",
      "protein": 32,
      "carbs": 58,
      "fat": 3,
      "fiber": 3,
      "kcal": 387,
      "prepTime": 6,
      "allergens": [
        "gluten",
        "nabiał"
      ],
      "tags": [
        "kasza-manna",
        "lekkie",
        "izolat"
      ],
      "ingredients": [
        {
          "item": "Kasza manna",
          "amount": "50g"
        },
        {
          "item": "Mleko 1.5% lub napój sojowy",
          "amount": "250ml"
        },
        {
          "item": "Odżywka białkowa waniliowa WPC/WPI",
          "amount": "25g"
        },
        {
          "item": "Borówki amerykańskie",
          "amount": "80g"
        }
      ],
      "recipe": "1. Kaszę manną wsyp do gotującego się mleka i mieszaj energicznie przez 2 minuty do zgęstnienia.\n2. Zdejmij z ognia, odczekaj minutę i wymieszaj z odżywką białkową.\n3. Udekoruj borówkami.",
      "mealTiming": "post"
    }
  ],
  "przekaska": [
    {
      "id": "meal_prz_001",
      "name": "Pudding chia na mleku migdałowym z musem malinowym",
      "role": "Przekąska bogata w błonnik rozpuszczalny, wapń i kwasy Omega-3 ALA",
      "protein": 8,
      "carbs": 18,
      "fat": 12,
      "fiber": 11,
      "kcal": 212,
      "prepTime": 5,
      "allergens": [
        "orzechy"
      ],
      "tags": [
        "chia",
        "blonnik",
        "superfoods"
      ],
      "ingredients": [
        {
          "item": "Nasiona szałwii hiszpańskiej (chia)",
          "amount": "25g"
        },
        {
          "item": "Napój migdałowy bez cukru",
          "amount": "150ml"
        },
        {
          "item": "Maliny zblendowane z erytrytolem",
          "amount": "80g"
        }
      ],
      "recipe": "1. Nasiona chia wymieszaj dokładnie z napojem migdałowym i odstaw do lodówki na minimum 30 minut (najlepiej na noc).\n2. Na wierzch wyłóż mus malinowy.",
      "mealTiming": "any"
    },
    {
      "id": "meal_prz_002",
      "name": "Kefir naturalny z nasionami słonecznika i garścią jagód",
      "role": "Naturalny probiotyk wspierający mikrobiotę i odporność",
      "protein": 14,
      "carbs": 18,
      "fat": 9,
      "fiber": 4,
      "kcal": 209,
      "prepTime": 2,
      "allergens": [
        "nabiał"
      ],
      "tags": [
        "kefir",
        "probiotyk",
        "jagody"
      ],
      "ingredients": [
        {
          "item": "Kefir naturalny gęsty",
          "amount": "250ml"
        },
        {
          "item": "Nasiona słonecznika łuskane",
          "amount": "15g"
        },
        {
          "item": "Jagody świeże lub mrożone",
          "amount": "60g"
        }
      ],
      "recipe": "1. Do szklanki wlej zimny kefir.\n2. Wsyp jagody i uprażone na sucho ziarna słonecznika.",
      "mealTiming": "any"
    },
    {
      "id": "meal_prz_003",
      "name": "Słupki marchwi i selera naciowego z hummusem klasycznym",
      "role": "Chrupiąca przekąska niskokaloryczna zaspokajająca potrzebę żucia na redukcji",
      "protein": 7,
      "carbs": 22,
      "fat": 10,
      "fiber": 8,
      "kcal": 206,
      "prepTime": 5,
      "allergens": [
        "sezam"
      ],
      "tags": [
        "warzywa",
        "hummus",
        "chrupiace"
      ],
      "ingredients": [
        {
          "item": "Marchew świeża",
          "amount": "100g (1 sztuka)"
        },
        {
          "item": "Seler naciowy",
          "amount": "80g (2 łodygi)"
        },
        {
          "item": "Hummus klasyczny z oliwą",
          "amount": "50g (2 łyżki)"
        }
      ],
      "recipe": "1. Warzywa pokrój w podłużne słupki.\n2. Nabieraj hummus bezpośrednio słupkami warzyw.",
      "mealTiming": "any"
    },
    {
      "id": "meal_prz_004",
      "name": "Domowe kulki mocy daktylowo-orzechowe z kakao",
      "role": "Zdrowy zamiennik słodyczy bez dodatku cukru — magnez i potas",
      "protein": 6,
      "carbs": 28,
      "fat": 10,
      "fiber": 5,
      "kcal": 226,
      "prepTime": 10,
      "allergens": [
        "orzechy"
      ],
      "tags": [
        "kulki-mocy",
        "daktyle",
        "kakao"
      ],
      "ingredients": [
        {
          "item": "Daktyle suszone",
          "amount": "40g"
        },
        {
          "item": "Orzechy nerkowca lub migdały",
          "amount": "20g"
        },
        {
          "item": "Prawdziwe ciemne kakao 100%",
          "amount": "8g (1 łyżka)"
        }
      ],
      "recipe": "1. Zblenduj daktyle z orzechami i kakao na zwartą, plastyczną masę.\n2. Uformuj w dłoniach 3 kulki i schłodź w lodówce.",
      "mealTiming": "any"
    },
    {
      "id": "meal_prz_005",
      "name": "Garść orzechów włoskich z kostką gorzkiej czekolady 85%",
      "role": "Wysoka gęstość polifenoli i wsparcie funkcji poznawczych mózgu",
      "protein": 5,
      "carbs": 8,
      "fat": 20,
      "fiber": 3,
      "kcal": 232,
      "prepTime": 1,
      "allergens": [
        "orzechy"
      ],
      "tags": [
        "keto",
        "orzechy-wloskie",
        "czekolada"
      ],
      "ingredients": [
        {
          "item": "Orzechy włoskie łuskane połówki",
          "amount": "25g"
        },
        {
          "item": "Czekolada gorzka 85% kakao",
          "amount": "15g (1 duża kostka)"
        }
      ],
      "recipe": "1. Gotowa przekąska do zjedzenia między posiłkami lub do popołudniowej kawy.",
      "mealTiming": "any"
    },
    {
      "id": "meal_prz_006",
      "name": "Dwa jajka na twardo z sosem jogurtowo-ziołowym i szczypiorkiem",
      "role": "Prosta przekąska białkowa z choliną wspierającą pracę wątroby i układu nerwowego",
      "protein": 15,
      "carbs": 3,
      "fat": 11,
      "fiber": 0,
      "kcal": 171,
      "prepTime": 8,
      "allergens": [
        "jaja",
        "nabiał"
      ],
      "tags": [
        "jajka",
        "cholina",
        "szybkie-bialko"
      ],
      "ingredients": [
        {
          "item": "Jaja ugotowane na twardo",
          "amount": "2 sztuki"
        },
        {
          "item": "Jogurt naturalny gęsty",
          "amount": "30g"
        },
        {
          "item": "Szczypiorek posiekany",
          "amount": "1 łyżka"
        },
        {
          "item": "Sól i pieprz",
          "amount": "do smaku"
        }
      ],
      "recipe": "1. Jaja obierz, przekrój na połówki.\n2. Polej sosem z jogurtu, soli, pieprzu i posyp szczypiorkiem.",
      "mealTiming": "any"
    }
  ]
};

const EXERCISE_DB = {
  "klatka": [
    {
      "name": "Wyciskanie sztangi leżąc (Bench Press)",
      "sets": 4,
      "reps": 6,
      "weight": 70,
      "tags": [
        "sztanga",
        "lawka",
        "wielostawowe"
      ],
      "muscles": "Klatka piersiowa (część mostkowa), przedni akton mięśnia naramiennego, triceps",
      "desc": "Królewskie ćwiczenie wielostawowe górnej części ciała budujące siłę bezwzględną i gęstość mięśni piersiowych.",
      "difficulty": 3,
      "equipment": [
        "Sztanga olimpijska 20kg",
        "Ławka pozioma",
        "Stojaki ze szpilkami asekuracyjnymi"
      ],
      "technique": "1. Połóż się na ławce tak, by oczy były bezpośrednio pod gryfem. Stopy postaw całą powierzchnią stabilnie na ziemi.\n2. Ściągnij łopatki w dół i do kręgosłupa (retrakcja i depresja), tworząc stabilny mostek piersiowy.\n3. Chwyć sztangę nieco szerzej niż szerokość barków (przedramiona pionowo w dolnej fazie). Zdejmij gryf ze stojaków.\n4. Weź głęboki wdech do brzucha (manewr Valsalvy), napnij pośladki i brzuch.\n5. Kontrolowanym ruchem opuszczaj sztangę po delikatnym łuku do dolnej linii mostka (ok. 3 sekundy). Łokcie prowadź pod kątem 45-60° do tułowia.\n6. Wypchnij sztangę dynamicznie w górę do pozycji wyjściowej, wydychając powietrze w końcowej fazie.",
      "cues": [
        "Złam gryf w dłoniach dla rotacji zewnętrznej",
        "Wbij stopy w podłoże (leg drive)",
        "Łopatki przyklejone do ławki przez całą serię",
        "Prowadź łokcie pod kątem 60°, nie rozpychaj ich na boki pod kątem 90°"
      ],
      "tempo": "3-1-1-0",
      "restSec": 150,
      "progressionTip": "Zasada podwójnej progresji: gdy wykonasz 4 serie po 6 powtórzeń z zachowaniem idealnej techniki, dodaj 2.5 kg w kolejnym tygodniu."
    },
    {
      "name": "Wyciskanie hantli na ławce ze skosem dodatnim (30°)",
      "sets": 4,
      "reps": 10,
      "weight": 22,
      "tags": [
        "hantle",
        "skos",
        "gora-klatki"
      ],
      "muscles": "Górna część klatki piersiowej (obojczykowa), przedni akton barku, triceps",
      "desc": "Kluczowe ćwiczenie na rozwój górnej części klatki piersiowej z większym zakresem ruchu i swobodą stawów barkowych niż sztanga.",
      "difficulty": 3,
      "equipment": [
        "Para hantli",
        "Ławka z regulacją kąta (ustawiona na 30-35°)"
      ],
      "technique": "1. Ustaw oparcie ławki pod kątem 30° (nie wyżej niż 35°, by uniknąć dominacji przedniego barku).\n2. Usiądź z hantlami na kolanach, przy kładzeniu się na plecy pomóż sobie kolanami poderwać hantle do pozycji startowej.\n3. Ściągnij łopatki, klatka wypięta do przodu. Hantle trzymaj na wysokości górnej części mostka z lekkim skosem dłoni (semi-chwyt neutralny).\n4. Opuszczaj hantle głęboko, kontrolując rozciągnięcie włókien obojczykowych (3 sekundy).\n5. Wyciskaj po łuku ku górze i do środka, nie zderzając hantli na szczycie.",
      "cues": [
        "Kąt ławki nie większy niż 30-35°",
        "Ściśnij klatkę w punkcie szczytowym",
        "Głębokie rozciągnięcie na dole bez bólu w stawie"
      ],
      "tempo": "3-0-1-0",
      "restSec": 90,
      "progressionTip": "Dąż do wykonania 4x10 z danym ciężarem. Po osiągnięciu pułapu zwiększ ciężar hantli o 2 kg na rękę."
    },
    {
      "name": "Dipsy na poręczach z pochyleniem tułowia (Chest Dips)",
      "sets": 3,
      "reps": 8,
      "weight": 0,
      "tags": [
        "masa-ciala",
        "porecze",
        "dół-klatki"
      ],
      "muscles": "Dolna i środkowa część klatki piersiowej, triceps, przedni bark, stabilizatory łopatki",
      "desc": "Pompka na poręczach z celowym pochyleniem tułowia to jedno z najpotężniejszych ćwiczeń z masą ciała na masę dołu klatki.",
      "difficulty": 4,
      "equipment": [
        "Poręcze równoległe (dip station)",
        "Pas z łańcuchem do obciążenia (opcjonalnie)"
      ],
      "technique": "1. Chwyć poręcze, zablokuj ramiona i zawiśnij w powietrzu.\n2. Pochyl tułów do przodu pod kątem ok. 30°, ugnij kolana i skrzyżuj stopy, brodę przyciągnij lekko do klatki.\n3. Uginając ramiona, opuszczaj ciało w dół, pozwalając łokciom rozchodzić się lekko na boki, aż poczujesz pełne rozciągnięcie klatki (kąt w łokciach minimum 90°).\n4. Z dołu dynamicznie wyciśnij ciało w górę, zachowując pochylenie tułowia przez cały zakres ruchu.",
      "cues": [
        "Utrzymuj pochylenie tułowia w przód",
        "Nie unoś barków do uszu (aktywna depresja)",
        "Zejdź do kąta 90° w łokciu"
      ],
      "tempo": "3-1-1-0",
      "restSec": 120,
      "progressionTip": "Gdy zrobisz 3 serie po 10 powtórzeń z masą własnego ciała, zacznij dokładać obciążenie na pasie od 2.5–5 kg."
    },
    {
      "name": "Wyciskanie hantli na ławce poziomej z supinacją",
      "sets": 3,
      "reps": 12,
      "weight": 20,
      "tags": [
        "hantle",
        "lawka",
        "izolacja-masy"
      ],
      "muscles": "Klatka piersiowa (część środkowa i mostkowa), triceps",
      "desc": "Wariant wyciskania z rotacją dłoni, który zwiększa skurcz szczytowy włókien klatki w fazie koncentrycznej.",
      "difficulty": 2,
      "equipment": [
        "Para hantli",
        "Ławka pozioma"
      ],
      "technique": "1. Połóż się na ławce, hantle w dłoniach w chwycie nachwytem.\n2. Opuszczaj powoli na boki klatki do pełnego rozciągnięcia.\n3. Wyciskając w górę, płynnie obracaj dłonie do chwytu neutralnego (palce skierowane do siebie), mocno zaciskając klatkę na górze.",
      "cues": [
        "Płynna rotacja w trakcie wypychania",
        "Kontrolowany opust przez 3 sekundy",
        "Zachowaj mostek"
      ],
      "tempo": "3-0-1-1",
      "restSec": 75,
      "progressionTip": "Idealne ćwiczenie do pracy w zakresie 10-12 powtórzeń pod kątem hipertrofii."
    },
    {
      "name": "Rozpiętki na bramie z linkami wyciągu (Cable Crossover)",
      "sets": 3,
      "reps": 15,
      "weight": 12,
      "tags": [
        "wyciag",
        "izolacja",
        "pompa"
      ],
      "muscles": "Klatka piersiowa (włókna mostkowe i przymostkowe), mięsień piersiowy mniejszy",
      "desc": "Doskonałe ćwiczenie izolowane zapewniające stałe napięcie mechaniczne w całym zakresie ruchu dzięki oporowi linek.",
      "difficulty": 2,
      "equipment": [
        "Brama z dwoma wyciągami regulowanymi",
        "Uchwyty pojedyncze D-handle"
      ],
      "technique": "1. Ustaw bloczki na wysokości klatki lub nieco wyżej. Chwyć uchwyty, zrób krok w przód w wykroku dla stabilności.\n2. Pochyl lekko tułów, ręce lekko ugięte w łokciach (kąt stały przez całe ćwiczenie).\n3. Przywiedź dłonie przed siebie po szerokim łuku, krzyżując lekko nadgarstki i spinając klatkę na 1 sekundę.\n4. Wracaj powoli, czując głębokie rozciąganie mięśni piersiowych.",
      "cues": [
        "Wyobraź sobie, że obejmujesz wielkie drzewo",
        "Łokcie zablokowane w lekkim zgięciu",
        "Zatrzymaj ruch na 1 sek w pełnym spięciu"
      ],
      "tempo": "2-0-1-1",
      "restSec": 60,
      "progressionTip": "Skup się na czuciu mięśniowym (mind-muscle connection), a nie na biciu rekordów ciężaru."
    },
    {
      "name": "Pompki klasyczne z nogami na podwyższeniu (Decline Push-ups)",
      "sets": 3,
      "reps": 15,
      "weight": 0,
      "tags": [
        "kalistenika",
        "pompki",
        "gora-klatki"
      ],
      "muscles": "Górna klatka piersiowa, triceps, mięsień zębaty przedni, core",
      "desc": "Zaawansowany wariant pompki przenoszący większy procent masy ciała na obręcz barkową i górne rejony klatki.",
      "difficulty": 2,
      "equipment": [
        "Ławka, skrzynia plyometryczna lub stabilne krzesło",
        "Mata do ćwiczeń"
      ],
      "technique": "1. Oprzyj stopy na podwyższeniu (wysokość 30-45 cm), dłonie rozstaw na podłodze nieco szerzej niż barki.\n2. Napnij pośladki i brzuch — ciało musi tworzyć idealną linię prostą od pięt po czubek głowy.\n3. Uginając łokcie w tył (pod kątem 45°), opuszczaj klatkę piersiową tuż nad samą podłogę.\n4. Zepchnij się dynamicznie w górę, nie tracąc napięcia w pośladkach.",
      "cues": [
        "Brzuch jak ze stali — nie opuszczaj bioder",
        "Głowa w przedłużeniu kręgosłupa",
        "Pełen zakres ruchu klatką do ziemi"
      ],
      "tempo": "2-1-1-0",
      "restSec": 60,
      "progressionTip": "Gdy zrobisz 3x15 z łatwością, załóż kamizelkę obciążeniową lub poproś partnera o talerz 5-10 kg na plecy."
    },
    {
      "name": "Wyciskanie na maszynie Hammer Strength (Chest Press)",
      "sets": 3,
      "reps": 10,
      "weight": 60,
      "tags": [
        "maszyna",
        "bezpieczenstwo",
        "hipertrofia"
      ],
      "muscles": "Klatka piersiowa całościowo, triceps",
      "desc": "Bezpieczna praca w zbieżnym torze ruchu pozwalająca na bezpieczny trening do załamania mięśniowego bez asekuranta.",
      "difficulty": 1,
      "equipment": [
        "Maszyna Hammer Strength lub Plate-Loaded Chest Press"
      ],
      "technique": "1. Dostosuj wysokość siedziska tak, by uchwyty znajdowały się na wysokości środkowej linii mostka.\n2. Oprzyj plecy i pośladki o oparcie, stopy stabilnie na ziemi.\n3. Wypchnij ciężar przed siebie bez przeprostu w stawach łokciowych.\n4. Opuszczaj ciężar powoli przez 3 sekundy do poziomu klatki.",
      "cues": [
        "Plecy i potylica dociśnięte do oparcia",
        "Płynny ruch bez szarpania",
        "Nie blokuj łokci w przeproście"
      ],
      "tempo": "3-0-1-0",
      "restSec": 75,
      "progressionTip": "Świetne ćwiczenie na drop-sety lub końcówkę treningu klatki."
    },
    {
      "name": "Przenoszenie hantla nad głową w leżeniu w poprzek ławki (Pullover)",
      "sets": 3,
      "reps": 12,
      "weight": 18,
      "tags": [
        "hantel",
        "rozciaganie",
        "zebaty-przedni"
      ],
      "muscles": "Klatka piersiowa, mięsień najszerszy grzbietu, mięsień zębaty przedni, głowa długa tricepsa",
      "desc": "Klasyczne ćwiczenie 'złotej ery' kulturystyki rozszerzające klatkę piersiową i rozciągające włókna mięśniowe.",
      "difficulty": 3,
      "equipment": [
        "Jeden hantel",
        "Ławka pozioma"
      ],
      "technique": "1. Połóż się górną częścią pleców w poprzek ławki, biodra opuść lekko w dół, stopy stabilnie na ziemi.\n2. Chwyć hantel oburącz od spodu za talerz (dłonie ułożone w trójkąt wokół rączki) i wyprostuj ręce nad klatką.\n3. Z lekko ugiętymi łokciami opuszczaj hantel po łuku za głowę, biorąc głęboki wdech i rozciągając żebra.\n4. Wracaj hantlem nad klatkę, napinając mięśnie piersiowe i zębate.",
      "cues": [
        "Biodra trzymaj poniżej poziomu ławki",
        "Ruch zachodzi w stawach barkowych, nie łokciowych",
        "Głęboki wdech w fazie opuszczania"
      ],
      "tempo": "3-1-1-0",
      "restSec": 75,
      "progressionTip": "Nie przesadzaj z ciężarem — priorytetem jest głębokie rozciągnięcie i kontrola toru ruchu."
    }
  ],
  "plecy": [
    {
      "name": "Martwy ciąg klasyczny (Deadlift)",
      "sets": 4,
      "reps": 5,
      "weight": 100,
      "tags": [
        "sztanga",
        "wielostawowe",
        "tylna-tasma"
      ],
      "muscles": "Prostowniki grzbietu, najszerszy grzbietu, czworoboczny, pośladki, dwugłowe ud, przedramiona",
      "desc": "Fundament siły człowieka angażujący całą tylną taśmę powięziową i budujący potężną gęstość grzbietu.",
      "difficulty": 4,
      "equipment": [
        "Sztanga olimpijska",
        "Talerze bumper/olimpijskie",
        "Magnezja"
      ],
      "technique": "1. Stań ze stopami na szerokość bioder, gryf nad środkiem stóp (ok. 2-3 cm od goleni).\n2. Zegnij biodra (hip hinge) i ugnij kolana, chwytając sztangę nachwytem tuż przy zewnętrznej stronie nóg.\n3. Dociśnij klatkę do przodu, ściągnij najszersze grzbietu ('schowaj łopatki do tylnych kieszeni spodni'). Zdejmij luz ze sztangi (kliknięcie).\n4. Weź potężny wdech do brzucha, wytwórz tłocznię brzuszną (bracing).\n5. Odepchnij podłogę nogami, prowadząc sztangę pionowo tuż przy goleniach i udach.\n6. W pełnym wyproście napnij pośladki — nie odchylaj tułowia w tył (hiperextensja). Odłóż ciężar kontrolując ruch bioder w tył.",
      "cues": [
        "Pchaj podłogę stopami, nie ciągnij plecami",
        "Sztanga sunie po goleniach",
        "Zdejmij luz z gryfu przed oderwaniem",
        "Głowa w pozycji neutralnej (patrz 2-3m przed siebie)"
      ],
      "tempo": "2-0-1-1",
      "restSec": 180,
      "progressionTip": "Zwiększaj obciążenie o 5 kg co 2-3 tygodnie, dbając o nienaganną linię lędźwi."
    },
    {
      "name": "Podciąganie na drążku nachwytem (Pull-ups)",
      "sets": 4,
      "reps": 8,
      "weight": 0,
      "tags": [
        "drazek",
        "kalistenika",
        "szerokosc-plecow"
      ],
      "muscles": "Mięsień najszerszy grzbietu, obły większy, ramienno-promieniowy, czworoboczny dolny",
      "desc": "Najlepsze ćwiczenie na szerokość pleców (sylwetka w kształcie litery V) z masą własnego ciała.",
      "difficulty": 4,
      "equipment": [
        "Drążek do podciągania",
        "Guma powerband (opcja regesyjna)",
        "Pas z obciążeniem (opcja progresyjna)"
      ],
      "technique": "1. Złap drążek nachwytem na szerokość nieco szerszą niż barki.\n2. Zawiśnij w pełnym rozciągnięciu (dead hang), po czym zainicjuj ruch ściągnięciem łopatek w dół (aktywny zwis).\n3. Prowadź łokcie pionowo w dół i lekko w tył, ciągnąc klatkę piersiową do drążka, aż broda minie poziom gryfu.\n4. Opuść się powoli pod pełną kontrolą do pełnego wyprostu ramion (3 sekundy).",
      "cues": [
        "Ciągnij łokciami w dół ku biodrom",
        "Nie bujaj ciałem (brak kippingu)",
        "Wypnij klatkę ku drążkowi na szczycie"
      ],
      "tempo": "3-0-1-1",
      "restSec": 120,
      "progressionTip": "Jeśli zrobisz 4x8 z czystą techniką, dołóż 2.5–5 kg na pasie. Jeśli nie robisz 1 powtórzenia — zacznij od negatywów (sam powolny opust) lub gumy."
    },
    {
      "name": "Wiosłowanie sztangą w opadzie tułowia (Barbell Bent-over Row)",
      "sets": 4,
      "reps": 8,
      "weight": 60,
      "tags": [
        "sztanga",
        "wioslowanie",
        "grubosc-plecow"
      ],
      "muscles": "Mięsień najszerszy grzbietu, czworoboczny (część środkowa i dolna), równoległoboczne, tylny akton barku",
      "desc": "Podstawowe ćwiczenie budujące grubość i masę mięśniową całego grzbietu.",
      "difficulty": 3,
      "equipment": [
        "Sztanga olimpijska",
        "Zaciski"
      ],
      "technique": "1. Chwyć sztangę nachwytem na szerokość barków. Wyprostuj się, po czym wykonaj zawias biodrowy (hip hinge), pochylając tułów pod kątem ok. 45° do podłoża.\n2. Kolana lekko ugięte, plecy idealnie proste, brzuch mocno napięty.\n3. Przyciągaj sztangę po udach w kierunku dolnej części brzucha/pępka, prowadząc łokcie blisko tułowia.\n4. Na szczycie ściśnij łopatki na 1 sekundę, po czym opuść sztangę z pełną kontrolą.",
      "cues": [
        "Prowadź łokcie za siebie",
        "Nie prostuj tułowia w trakcie ciągnięcia (brak szarpania)",
        "Głowa neutralnie z kręgosłupem"
      ],
      "tempo": "2-1-1-1",
      "restSec": 90,
      "progressionTip": "Gdy zrobisz 4 serie po 8 powtórzeń bez bujania tułowiem, dodaj 2.5 kg."
    },
    {
      "name": "Wiosłowanie hantlem jednorącz w oparciu o ławkę (One-Arm Dumbbell Row)",
      "sets": 3,
      "reps": 10,
      "weight": 26,
      "tags": [
        "hantle",
        "unilateralne",
        "izolacja"
      ],
      "muscles": "Mięsień najszerszy grzbietu, obły większy, czworoboczny, bicepsy",
      "desc": "Ćwiczenie unilateralne wyrównujące asymetrie siłowe i pozwalające na potężne rozciągnięcie najszerszego.",
      "difficulty": 2,
      "equipment": [
        "Hantel",
        "Ławka pozioma"
      ],
      "technique": "1. Jedno kolano i dłoń oprzyj stabilnie na ławce. Druga noga stoi pewnie na podłożu z boku.\n2. W wolnej dłoni trzymaj hantel w zwisie pionowym.\n3. Pociągnij hantel po łuku w kierunku biodra (nie pionowo do pachy!), skupiając się na pracy łokcia.\n4. Na dole pozwól łopatce opaść i poczuj rozciągnięcie najszerszego grzbietu.",
      "cues": [
        "Ciągnij hantel do kieszeni spodni",
        "Tułów równolegle do podłogi, nie rotuj klatki",
        "Ruch inicjuj łopatką i łokciem"
      ],
      "tempo": "2-0-1-1",
      "restSec": 75,
      "progressionTip": "Zwiększaj ciężar hantla o 2 kg po osiągnięciu 3x12 na każdą rękę."
    },
    {
      "name": "Ściąganie drążka wyciągu górnego do klatki (Lat Pulldown)",
      "sets": 4,
      "reps": 10,
      "weight": 55,
      "tags": [
        "wyciag",
        "szerokosc",
        "kontrola"
      ],
      "muscles": "Mięsień najszerszy grzbietu, dwugłowy ramienia, czworoboczny",
      "desc": "Doskonałe narzędzie do akumulacji objętości treningowej na najszerszy grzbietu z precyzyjną regulacją ciężaru.",
      "difficulty": 2,
      "equipment": [
        "Wyciąg górny (Lat pulldown machine)",
        "Szeroki drążek profilowany"
      ],
      "technique": "1. Usiądź na siedzisku, zablokuj uda pod wałkami tak, by stopy stały mocno na podłożu.\n2. Chwyć drążek nachwytem szerzej niż barki. Odchyl tułów o 10-15° w tył.\n3. Ściągaj drążek płynnym ruchem do górnej części mostka, kierując łokcie w dół i lekko w tył.\n4. Zatrzymaj na ułamek sekundy przy klatce, po czym kontroluj powrót ciężaru w górę przez 3 sekundy.",
      "cues": [
        "Klatka do przodu na spotkanie z drążkiem",
        "Ciągnij łokciami, nie dłońmi",
        "Rozciągnij plecy na samej górze"
      ],
      "tempo": "3-0-1-1",
      "restSec": 75,
      "progressionTip": "Gdy wykonasz 4x10 z pełną kontrolą, przesuń zawleczkę o 5 kg w dół na stosie."
    },
    {
      "name": "Wiosłowanie na wyciągu dolnym do brzucha (Seated Cable Row)",
      "sets": 3,
      "reps": 12,
      "weight": 50,
      "tags": [
        "wyciag-dolny",
        "chwyt-neutralny",
        "srodek-plecow"
      ],
      "muscles": "Mięśnie równoległoboczne, czworoboczny (środek), najszerszy grzbietu, tylny bark",
      "desc": "Buduje głębokie bruzdy między łopatkami i wzmacnia posturalne mięśnie cofające barki (retrakcja).",
      "difficulty": 2,
      "equipment": [
        "Wyciąg dolny",
        "Uchwyt wąski trójkątny (V-bar)"
      ],
      "technique": "1. Usiądź, oprzyj stopy na platformie (kolana lekko ugięte, nie blokuj w przeproście).\n2. Złap uchwyt, wyprostuj tułów prostopadle do podłogi.\n3. Ściągaj uchwyt do dolnej części brzucha, wypinając klatkę i cofając łopatki.\n4. Wracając, pozwól łopatkom rozejść się na boki, ale nie zaokrąglaj lędźwi.",
      "cues": [
        "Nie bujaj tułowiem w przód i w tył",
        "Ściśnij łopatki jakbyś chciał zgnieść orzech",
        "Barki trzymaj nisko"
      ],
      "tempo": "2-1-1-1",
      "restSec": 60,
      "progressionTip": "Świetne ćwiczenie na pauzę izometryczną (2 sekundy przy brzuchu)."
    },
    {
      "name": "Face Pulls na wyciągu górnym z liną",
      "sets": 3,
      "reps": 15,
      "weight": 20,
      "tags": [
        "prehab",
        "zdrowe-barki",
        "rotatory"
      ],
      "muscles": "Tylny akton mięśnia naramiennego, mięśnie stożka rotatorów (podgrzebieniowy, obły mniejszy), czworoboczny",
      "desc": "Najważniejsze ćwiczenie prehabilitacyjne na zdrowie barków, eliminujące wady postawy (protrakcję barków).",
      "difficulty": 2,
      "equipment": [
        "Wyciąg z regulacją wysokości",
        "Lina do tricepsa (triceps rope)"
      ],
      "technique": "1. Ustaw wyciąg na wysokości oczu lub czoła. Chwyć końce liny kciukami skierowanymi w tył (chwyt młotkowy/odwrócony).\n2. Zrób krok w tył. Pociągnij środek liny w kierunku nasady nosa/czoła, rozrywając końce liny na boki.\n3. Na końcu ruchu wykonaj rotację zewnętrzną w barkach — dłonie powinny znaleźć się wyżej niż łokcie.\n4. Przytrzymaj spięcie przez 1-2 sekundy.",
      "cues": [
        "Rozrywaj linę na boki",
        "Dłonie wyżej niż łokcie na końcu ruchu (litera W)",
        "Poczuj palenie z tyłu barków i między łopatkami"
      ],
      "tempo": "2-1-1-2",
      "restSec": 60,
      "progressionTip": "Nigdy nie używaj zbyt dużego ciężaru — liczy się perfekcyjna rotacja zewnętrzna i spięcie."
    },
    {
      "name": "Wznosy tułowia na ławce rzymskiej (Hyperextensions)",
      "sets": 3,
      "reps": 12,
      "weight": 0,
      "tags": [
        "lawka-rzymska",
        "prostowniki",
        "posladki"
      ],
      "muscles": "Mięśnie prostowniki grzbietu, mięśnie pośladkowe wielkie, kulszowo-goleniowe",
      "desc": "Buduje pancerny dół pleców i uczy prawidłowego wzorca hinge bez osiowego obciążania kręgosłupa.",
      "difficulty": 2,
      "equipment": [
        "Ławka rzymska (pod kątem 45° lub pozioma)",
        "Talerz do obciążenia (opcjonalnie)"
      ],
      "technique": "1. Ustaw poduszkę ławki tuż poniżej kolców biodrowych, by umożliwić swobodne zgięcie w stawie biodrowym.\n2. Skrzyżuj ramiona na klatce piersiowej. Opuść tułów w dół, zginając się w biodrach.\n3. Unoś tułów w górę siłą pośladków i prostowników, aż ciało znajdzie się w jednej linii z nogami.\n4. Nie przeprostowuj kręgosłupa na szczycie.",
      "cues": [
        "Zatrzymaj ruch w linii prostej z nogami",
        "Ściśnij mocno pośladki na górze",
        "Płynny ruch bez szarpania"
      ],
      "tempo": "2-1-1-1",
      "restSec": 60,
      "progressionTip": "Gdy 3x15 z masą ciała jest łatwe, trzymaj przy klatce talerz 5-10 kg."
    }
  ],
  "nogi": [
    {
      "name": "Przysiad ze sztangą na plecach (Back Squat)",
      "sets": 4,
      "reps": 6,
      "weight": 85,
      "tags": [
        "sztanga",
        "wielostawowe",
        "krol-cwiczen"
      ],
      "muscles": "Czworogłowe ud, pośladkowe wielkie, przywodziciele, dwugłowe ud, core",
      "desc": "Niezaprzeczalny król wszystkich ćwiczeń siłowych rozwijający maksymalną siłę kończyn dolnych i gęstość kośćca.",
      "difficulty": 4,
      "equipment": [
        "Klatka/rack do przysiadów",
        "Sztanga olimpijska",
        "Pasy/buty ciężarowe (opcja)"
      ],
      "technique": "1. Podejdź pod sztangę na stojaku, oprzyj ją na mięśniach czworobocznych (high bar) lub na tylnych aktonach barku (low bar).\n2. Chwyć gryf wąsko, wbij łopatki i zdejmij sztangę ze stojaka dwoma krokami w tył.\n3. Ustaw stopy nieco szerzej niż szerokość barków, palce delikatnie skierowane na zewnątrz (15-30°).\n4. Weź potężny wdech przeponowy, zablokuj brzuch (bracing).\n5. Równocześnie zginaj biodra i kolana, schodząc poniżej linii kolan (pełna głębokość parallel lub poniżej), pilnując by kolana podążały w linii palców stóp.\n6. Wstań eksplozywnie, rozpychając podłogę stopami w bok.",
      "cues": [
        "Rozpychaj kolana na zewnątrz",
        "Klatka dumnie w przód",
        "Ciężar rozłożony na trzech punktach stopy (pięta, nasada dużego i małego palca)",
        "Głębokość poniżej kąta prostego"
      ],
      "tempo": "3-1-1-0",
      "restSec": 180,
      "progressionTip": "Dokładaj 2.5–5 kg co 2 tygodnie przy zachowaniu tej samej głębokości i stabilności tułowia."
    },
    {
      "name": "Rumuński martwy ciąg z hantlami lub sztangą (RDL - Romanian Deadlift)",
      "sets": 4,
      "reps": 8,
      "weight": 70,
      "tags": [
        "dwuglowe",
        "posladki",
        "zawias-biodrowy"
      ],
      "muscles": "Mięśnie kulszowo-goleniowe (dwugłowe ud), pośladkowy wielki, prostowniki grzbietu",
      "desc": "Najlepsze ćwiczenie rozwijające tył uda i pośladki w oparciu o czysty wzorzec zawiasu biodrowego (hip hinge).",
      "difficulty": 3,
      "equipment": [
        "Sztanga olimpijska lub para ciężkich hantli"
      ],
      "technique": "1. Stań ze sztangą w dłoniach, stopy na szerokość bioder, kolana odblokowane (lekko ugięte pod stałym kątem ok. 15-20°).\n2. Inicjuj ruch cofaniem bioder w tył, jakbyś chciał zamknąć pośladkami drzwi za sobą.\n3. Prowadź sztangę/hantle tuż przy udach i piszczelach do poziomu poniżej rzepek kolanowych, czując maksymalne napięcie z tyłu ud.\n4. Z dołu wypchnij biodra w przód, napinając pośladki na szczycie.",
      "cues": [
        "Pchaj biodra maksymalnie w tył",
        "Gryf szoruje po nogach",
        "Plecy sztywne jak deska",
        "Ruch zatrzymaj gdy biodra przestają cofać się w tył"
      ],
      "tempo": "3-1-1-0",
      "restSec": 120,
      "progressionTip": "Zwiększaj ciężar tylko wtedy, gdy czujesz pracę dwugłowych, a nie ból w odcinku lędźwiowym."
    },
    {
      "name": "Wykroki chodzone z hantlami (Walking Lunges)",
      "sets": 3,
      "reps": 12,
      "weight": 16,
      "tags": [
        "unilateralne",
        "hantle",
        "stabilizacja"
      ],
      "muscles": "Czworogłowe ud, pośladkowe, przywodziciele, stabilizatory miednicy",
      "desc": "Dynamiczne ćwiczenie unilateralne budujące siłę funkcjonalną, równowagę i twardość mięśni czworogłowych oraz pośladków.",
      "difficulty": 3,
      "equipment": [
        "Para hantli",
        "Przestrzeń min. 10-15 metrów do marszu"
      ],
      "technique": "1. Chwyć hantle po bokach tułowia, wyprostuj sylwetkę.\n2. Zrób duży krok w przód, schodząc biodrami pionowo w dół, aż kolano nogi zakrocznej niemal dotknie podłoża (kąt 90° w obu kolanach).\n3. Odepchnij się z pięty nogi wykrocznej i płynnym ruchem przejdź do kroku drugą nogą.\n4. Utrzymuj tułów pionowo lub z bardzo lekkim pochyleniem w przód.",
      "cues": [
        "Kolano nogi z przodu stabilne (nie ucieka do środka)",
        "Ciężar na pięcie nogi przedniej",
        "Krok odpowiednio długi (kąt 90°)"
      ],
      "tempo": "2-0-1-0",
      "restSec": 90,
      "progressionTip": "Licz powtórzenia na każdą nogę (12 kroków na stronę = 24 łącznie)."
    },
    {
      "name": "Przysiad bułgarski z hantlami (Bulgarian Split Squat)",
      "sets": 3,
      "reps": 10,
      "weight": 14,
      "tags": [
        "bulgary",
        "pośladki",
        "bezlitosne"
      ],
      "muscles": "Czworogłowy uda, pośladkowy wielki i średni, dwugłowy",
      "desc": "Uważany przez trenerów za jedno z najskuteczniejszych (i najbardziej wymagających) ćwiczeń na rozbudowę nóg i pośladków.",
      "difficulty": 4,
      "equipment": [
        "Ławka pozioma lub step",
        "Para hantli"
      ],
      "technique": "1. Stań tyłem do ławki, oprzyj grzbiet jednej stopy na ławce. Noga z przodu wysunięta do stabilnego wykroku.\n2. Schodź pionowo w dół, uginając przednie kolano, aż udo znajdzie się równolegle do ziemi.\n3. Naciskając całą stopą (zwłaszcza piętą) przedniej nogi, wróć do góry.",
      "cues": [
        "90% ciężaru spoczywa na nodze przedniej",
        "Noga na ławce służy tylko do balansu",
        "Pochyl lekko tułów by mocniej zaangażować pośladek"
      ],
      "tempo": "3-1-1-0",
      "restSec": 90,
      "progressionTip": "Zacznij od samej masy ciała, by opanować równowagę, zanim sięgniesz po hantle."
    },
    {
      "name": "Wypychanie ciężaru na suwnicy skośnej (Leg Press 45°)",
      "sets": 4,
      "reps": 12,
      "weight": 140,
      "tags": [
        "suwnica",
        "masa",
        "bezpieczne-dla-kregoslupa"
      ],
      "muscles": "Mięsień czworogłowy uda, pośladki",
      "desc": "Umożliwia przeciążenie czworogłowych ogromnym ciężarem bez osiowego obciążania odcinka lędźwiowego kręgosłupa.",
      "difficulty": 2,
      "equipment": [
        "Suwnica skośna 45°",
        "Talerze olimpijskie"
      ],
      "technique": "1. Usiądź na suwnicy, dociśnij plecy i pośladki do oparcia.\n2. Ustaw stopy na środku platformy na szerokość bioder.\n3. Zwolnij blokadę, opuszczaj platformę głęboko, kontrolując ruch kolan na zewnątrz.\n4. Zatrzymaj ruch zanim pośladki zaczną odrywać się od oparcia (butt wink).\n5. Wypchnij platformę stopami, nie blokując kolan w przeproście.",
      "cues": [
        "Nigdy nie blokuj kolan na górze (zostaw lekki luz)",
        "Pośladki przyklejone do siedziska",
        "Kontrola w fazie opustu"
      ],
      "tempo": "3-1-1-0",
      "restSec": 90,
      "progressionTip": "Doskonałe narzędzie do serii łączonych lub pauz na dole platformy."
    },
    {
      "name": "Uginanie nóg leżąc na maszynie (Lying Leg Curl)",
      "sets": 3,
      "reps": 12,
      "weight": 40,
      "tags": [
        "maszyna",
        "dwuglowe",
        "izolacja"
      ],
      "muscles": "Mięsień dwugłowy uda (obie głowy), mięsień półścięgnisty, półbłoniasty",
      "desc": "Izolowane zgięcie w stawie kolanowym — niezbędne uzupełnienie martwych ciągów dla pełnego rozwoju tyłu ud.",
      "difficulty": 1,
      "equipment": [
        "Maszyna do uginania nóg leżąc"
      ],
      "technique": "1. Połóż się na brzuchu na maszynie, wałek oprzyj tuż nad ścięgnami Achillesa.\n2. Kolana ustaw w osi obrotu ramienia maszyny. Chwyć uchwyty i dociśnij miednicę do ławki.\n3. Ugnij nogi w kolanach, przyciągając wałek w stronę pośladków.\n4. Przytrzymaj pełne spięcie na 1 sekundę i opuszczaj przez 3 sekundy.",
      "cues": [
        "Nie unoś bioder z ławki podczas uginania",
        "Stopy w pozycji neutralnej lub zadarte (dorsiflexion)",
        "Płynny opust bez uderzania ciężarów"
      ],
      "tempo": "3-0-1-1",
      "restSec": 60,
      "progressionTip": "Wykonaj 12 powtórzeń, a na ostatnim powtórzeniu przytrzymaj izometrię przez 5 sekund."
    },
    {
      "name": "Prostowanie nóg siedząc na maszynie (Leg Extensions)",
      "sets": 3,
      "reps": 15,
      "weight": 45,
      "tags": [
        "czworoglowe",
        "izolacja",
        "pompa"
      ],
      "muscles": "Mięsień czworogłowy uda (zwłaszcza mięsień prosty uda - rectus femoris)",
      "desc": "Idealne ćwiczenie dopalające czworogłowe w skróconej pozycji mięśnia z silnym bodźcem metabolicznym.",
      "difficulty": 1,
      "equipment": [
        "Maszyna do prostowania nóg siedząc"
      ],
      "technique": "1. Usiądź głęboko w fotelu, plecy oparte, wałek oparty na dolnej części goleni.\n2. Wyprostuj nogi do pełnego skurczu czworogłowych, zatrzymując ruch na szczycie na 1 sekundę.\n3. Opuszczaj powoli pod kontrolą mięśniową.",
      "cues": [
        "Zatrzymaj ruch na szczycie i dopnij czwórki",
        "Nie odrywaj ud od siedziska",
        "Płynna praca"
      ],
      "tempo": "2-0-1-1",
      "restSec": 60,
      "progressionTip": "Świetne na rozgrzewkę przed przysiadami lub jako finisher treningu nóg."
    },
    {
      "name": "Wspięcia na palce stojąc na maszynie lub ze sztangą (Standing Calf Raise)",
      "sets": 4,
      "reps": 15,
      "weight": 70,
      "tags": [
        "lydki",
        "brzuchaty",
        "wytrzymalosc"
      ],
      "muscles": "Mięsień brzuchaty łydki (gastrocnemius), mięsień płaszkowaty",
      "desc": "Buduje twarde, wysokie łydki dzięki pracy w pełnym rozciągnięciu stawu skokowego.",
      "difficulty": 2,
      "equipment": [
        "Maszyna do wspięć stojąc lub podest ze sztangą"
      ],
      "technique": "1. Stań przodostopiem na krawędzi podestu, poduszki maszyny na barkach.\n2. Opuść pięty maksymalnie w dół poniżej poziomu podestu, rozciągając łydki przez 2 sekundy.\n3. Wybij się mocno na palce (wysoki wspięcie), spinając łydki na 1 sekundę na szczycie.",
      "cues": [
        "Pauza 2 sekundy na samym dole (eliminacja energii sprężystej ścięgna)",
        "Maksymalny wspięcie na paluch",
        "Kolana proste ale nie zablokowane"
      ],
      "tempo": "2-2-1-1",
      "restSec": 60,
      "progressionTip": "Sekretem rozwoju łydek jest pauza w dole eliminująca odbicie ścięgna Achillesa."
    }
  ],
  "barki": [
    {
      "name": "Wyciskanie żołnierskie sztangi stojąc (Overhead Press - OHP)",
      "sets": 4,
      "reps": 6,
      "weight": 45,
      "tags": [
        "sztanga",
        "barki",
        "sila-bezwzgledna"
      ],
      "muscles": "Przedni i boczny akton mięśnia naramiennego, triceps, góra klatki, core",
      "desc": "Klasyczny sprawdzian siły pionowej budujący potężną obręcz barkową i żelazną stabilizację tułowia.",
      "difficulty": 4,
      "equipment": [
        "Sztanga olimpijska",
        "Stojaki"
      ],
      "technique": "1. Zdejmij sztangę ze stojaków na wysokość obojczyków. Chwyt nieco szerszy niż barki, przedramiona pionowo pod gryfem.\n2. Napnij pośladki, brzuch i uda — ciało tworzy sztywną kolumnę.\n3. Cofnij delikatnie brodę, by sztanga minęła twarz w linii prostej.\n4. Wypchnij sztangę pionowo nad głowę, blokując ramiona i 'wsuwając' głowę pod sztangę na szczycie.",
      "cues": [
        "Zablokuj pośladki jak skała",
        "Pionowy tor sztangi",
        "Wsuń głowę pod gryf na szczycie (lockout)",
        "Łokcie lekko przed sztangą"
      ],
      "tempo": "2-1-1-0",
      "restSec": 150,
      "progressionTip": "OHP bardzo szybko weryfikuje siłę — progresuj mikrotalerzami (1.25 kg na stronę)."
    },
    {
      "name": "Wyciskanie hantli siedząc z oparciem (Seated Dumbbell Press)",
      "sets": 4,
      "reps": 10,
      "weight": 22,
      "tags": [
        "hantle",
        "barki",
        "hipertrofia"
      ],
      "muscles": "Przedni i boczny akton naramiennego, triceps",
      "desc": "Pozwala na pełne skupienie się na pracy barków bez konieczności stabilizowania tułowia w pozycji stojącej.",
      "difficulty": 2,
      "equipment": [
        "Para hantli",
        "Ławka z oparciem pionowym (80-85°)"
      ],
      "technique": "1. Usiądź na ławce (oparcie ustawione na 80-85°, lekko odchylone od pionu).\n2. Unieś hantle na wysokość uszu w chwycie pół-neutralnym.\n3. Wyciskaj hantle po łuku w górę, zbliżając je do siebie nad głową, ale bez zderzania.\n4. Opuszczaj do poziomu uszu, kontrolując ruch przez 3 sekundy.",
      "cues": [
        "Oparcie lekko odchylone (ochrona barków)",
        "Łokcie nie uciekają za linię tułowia",
        "Głowa oparta stabilnie"
      ],
      "tempo": "3-0-1-0",
      "restSec": 90,
      "progressionTip": "Zwiększ ciężar hantli o 2 kg po osiągnięciu 4x10 z pełną kontrolą."
    },
    {
      "name": "Wznosy hantli bokiem stojąc (Lateral Raises)",
      "sets": 4,
      "reps": 12,
      "weight": 10,
      "tags": [
        "boczny-akton",
        "szerokosc-barkow",
        "izolacja"
      ],
      "muscles": "Boczny akton mięśnia naramiennego (lateral deltoid)",
      "desc": "Kluczowe ćwiczenie budujące szerokość barków ('barki jak kule armatnie').",
      "difficulty": 2,
      "equipment": [
        "Para hantli"
      ],
      "technique": "1. Stań w lekkim rozkroku, pochyl tułów dosłownie o 5-10° w przód.\n2. Trzymaj hantle po bokach ud, łokcie zablokowane w minimalnym ugięciu.\n3. Unoś hantle w płaszczyźnie łopatki (scaption - ok. 30° w przód od linii ciała) do poziomu barków.\n4. Prowadź ruch łokciami, nie nadgarstkami. Opuszczaj powoli.",
      "cues": [
        "Unoś hantle łokciami, nie dłońmi",
        "Wylewaj wodę z dzbanka na szczycie (mały palec lekko w górę)",
        "Nie szarp tułowiem"
      ],
      "tempo": "2-0-1-1",
      "restSec": 60,
      "progressionTip": "Pracuj w wyższych zakresach powtórzeń (12-15) z perfekcyjną techniką."
    },
    {
      "name": "Wznosy ramion na wyciągu bokiem (Cable Lateral Raise)",
      "sets": 3,
      "reps": 15,
      "weight": 7,
      "tags": [
        "wyciag",
        "stale-napiecie",
        "izolacja"
      ],
      "muscles": "Boczny akton mięśnia naramiennego",
      "desc": "Zapewnia stałe napięcie mechaniczne od samego dołu ruchu, gdzie hantle nie stawiają żadnego oporu.",
      "difficulty": 2,
      "equipment": [
        "Wyciąg dolny",
        "Uchwyt pojedynczy D-handle lub mankiet na nadgarstek"
      ],
      "technique": "1. Ustaw bloczek wyciągu na dole. Stań bokiem, linkę poprowadź za plecami lub przed sobą.\n2. Unoś ramię bokiem do poziomu równoległego z podłogą.\n3. Przytrzymaj szczytowy skurcz przez 1 sekundę i powoli opuszczaj.",
      "cues": [
        "Stałe napięcie przez cały zakres",
        "Uchwyt luźno w dłoni",
        "Czysta praca bocznego barku"
      ],
      "tempo": "2-1-1-1",
      "restSec": 60,
      "progressionTip": "Użycie mankietu na nadgarstek wyłącza przedramię i maksymalizuje izolację barku."
    },
    {
      "name": "Wznosy hantli w opadzie tułowia (Rear Delt Flyes)",
      "sets": 4,
      "reps": 15,
      "weight": 8,
      "tags": [
        "tyl-barku",
        "postawa",
        "3d-look"
      ],
      "muscles": "Tylny akton mięśnia naramiennego, mięśnie równoległoboczne, podgrzebieniowy",
      "desc": "Dopełnia trójwymiarowy wygląd barku i przeciwdziała wadom postawy wynikającym z pracy biurowej.",
      "difficulty": 2,
      "equipment": [
        "Para lekkich hantli"
      ],
      "technique": "1. Wykonaj opad tułowia (prawie równolegle do podłogi), plecy proste, kolana ugięte.\n2. Hantle wiszą swobodnie pod klatką piersiową, dłonie skierowane do siebie.\n3. Unoś ramiona na boki po łuku, skupiając się na pracy tylnej części barku, nie ściągając nadmiernie łopatek.\n4. Opuszczaj powoli z pełną kontrolą.",
      "cues": [
        "Ruch jak rozpiętki na odwrót",
        "Wyobraź sobie, że odpychasz ściany dłońmi na boki",
        "Głowa neutralnie"
      ],
      "tempo": "2-0-1-1",
      "restSec": 60,
      "progressionTip": "Tylny bark kocha wysoką objętość i serie z pauzą izometryczną."
    },
    {
      "name": "Wyciskanie Arnolda (Arnold Press)",
      "sets": 3,
      "reps": 10,
      "weight": 18,
      "tags": [
        "arnoldki",
        "rotacja",
        "wszystkie-aktony"
      ],
      "muscles": "Przedni i boczny akton naramiennego, triceps, stożek rotatorów",
      "desc": "Kultowe ćwiczenie Arnolda Schwarzeneggera łączące wyciskanie z rotacją w stawie ramiennym.",
      "difficulty": 3,
      "equipment": [
        "Para hantli",
        "Ławka z oparciem"
      ],
      "technique": "1. Usiądź na ławce. Hantle trzymaj przed klatką piersiową w chwycie podchwytem (dłonie skierowane do twarzy).\n2. Rozpoczynając wyciskanie w górę, jednocześnie obracaj dłonie na zewnątrz.\n3. Na szczycie dłonie są w pozycji klasycznego wyciskania (nachwyt).\n4. Wracając, płynnie powtórz rotację w odwrotnym kierunku.",
      "cues": [
        "Płynny ruch obrotowy podczas wyciskania",
        "Nie opuszczaj łokci zbyt nisko",
        "Pełna kontrola w każdym punkcie toru"
      ],
      "tempo": "3-0-1-0",
      "restSec": 75,
      "progressionTip": "Wymaga mniejszego ciężaru niż klasyczne wyciskanie hantli ze względu na dłuższą drogę ruchu."
    },
    {
      "name": "Wyciskanie na maszynie Smitha zza karku / z przodu",
      "sets": 3,
      "reps": 10,
      "weight": 40,
      "tags": [
        "smith",
        "stabilnosc",
        "akcent-przedni"
      ],
      "muscles": "Przedni akton barku, triceps, górne czwórogłowe grzbietu",
      "desc": "Umożliwia izolację barków bez martwienia się o stabilizację w osi przód-tył.",
      "difficulty": 2,
      "equipment": [
        "Maszyna Smitha",
        "Ławka z oparciem"
      ],
      "technique": "1. Ustaw ławkę na maszynie Smitha tak, by gryf opuszczał się tuż przed nosem/do obojczyków.\n2. Chwyć gryf nachwytem, odepchnij i zdejmij z haków.\n3. Opuszczaj do poziomu brody, po czym dynamicznie wyciskaj w górę.",
      "cues": [
        "Ruch w linii pionowej prowadnic",
        "Nie odbijaj od obojczyków",
        "Płynna praca"
      ],
      "tempo": "3-0-1-0",
      "restSec": 75,
      "progressionTip": "Świetne do technik zaawansowanych jak rest-pause."
    },
    {
      "name": "Szrugsy ze sztangą lub hantlami (Shrugs)",
      "sets": 4,
      "reps": 12,
      "weight": 80,
      "tags": [
        "kaptury",
        "czworoboczny",
        "grubosc-szyi"
      ],
      "muscles": "Górna część mięśnia czworobocznego (kaptury)",
      "desc": "Izolowane unoszenie obręczy barkowej budujące potężne mięśnie czworoboczne.",
      "difficulty": 2,
      "equipment": [
        "Sztanga olimpijska lub ciężkie hantle"
      ],
      "technique": "1. Chwyć sztangę nachwytem na szerokość barków, stań prosto.\n2. Unoś barki pionowo w górę ku uszom (jak gest 'nie wiem').\n3. Zatrzymaj maksymalny skurcz na 2 sekundy na samej górze.\n4. Opuść barki powoli w dół do pełnego rozciągnięcia. Nigdy nie kręć barkami w kółko!",
      "cues": [
        "Ruch czysto pionowy góra-dół (nigdy nie kręć barkami!)",
        "Zatrzymaj na 2 sekundy na górze",
        "Pełne rozciągnięcie na dole"
      ],
      "tempo": "2-2-1-0",
      "restSec": 60,
      "progressionTip": "Kluczem jest pauza izometryczna, a nie bezmyślne szarpanie ciężarem."
    }
  ],
  "ramiona": [
    {
      "name": "Uginanie przedramion ze sztangą łamaną stojąc (EZ-Bar Curl)",
      "sets": 3,
      "reps": 10,
      "weight": 30,
      "tags": [
        "biceps",
        "sztanga-lamana",
        "klasyk"
      ],
      "muscles": "Mięsień dwugłowy ramienia (biceps - głowa krótka i długa), mięsień ramienny",
      "desc": "Podstawowe ćwiczenie na masę bicepsa. Gryf łamany chroni nadgarstki przed przeciążeniem.",
      "difficulty": 2,
      "equipment": [
        "Sztanga łamana (EZ-bar)",
        "Zaciski"
      ],
      "technique": "1. Chwyć sztangę łamaną podchwytem w miejscach wygięcia, stań stabilnie ze stopami na szerokość bioder.\n2. Łokcie przyciśnięte do boków tułowia, łopatki ściągnięte.\n3. Uginaj przedramiona, unosząc sztangę po łuku do klatki piersiowej bez bujania tułowiem.\n4. Na szczycie mocno zepnij bicepsy na 1 sekundę i powoli opuszczaj przez 3 sekundy do pełnego wyprostu.",
      "cues": [
        "Łokcie zablokowane w jednym punkcie przy żebrach",
        "Zero bujania tułowiem (brak oszukiwania)",
        "Kontrolowany opust przez 3 sekundy"
      ],
      "tempo": "3-0-1-1",
      "restSec": 75,
      "progressionTip": "Gdy zrobisz 3x10 z idealną formą, dołóż 1.25 kg na stronę."
    },
    {
      "name": "Uginanie hantli z supinacją na ławce ze skosem dodatnim (Incline Dumbbell Curl)",
      "sets": 3,
      "reps": 10,
      "weight": 12,
      "tags": [
        "biceps",
        "dluga-glowa",
        "rozciagniecie"
      ],
      "muscles": "Głowa długa bicepsa (odpowiedzialna za tzw. 'szczyt bicepsa')",
      "desc": "Ułożenie rąk za osią ciała zapewnia bezkonkurencyjne rozciągnięcie głowy długiej mięśnia dwugłowego.",
      "difficulty": 3,
      "equipment": [
        "Para hantli",
        "Ławka ustawiona pod kątem 45-60°"
      ],
      "technique": "1. Połóż się na ławce skośnej, ramiona zwisają swobodnie pionowo w dół z hantlami w dłoniach.\n2. Uginaj przedramiona, w trakcie unoszenia wykonując pełną supinację nadgarstka (kieruj mały palec ku górze i na zewnątrz).\n3. Ściśnij biceps na szczycie i opuszczaj bardzo powoli do pełnego rozciągnięcia ramienia.",
      "cues": [
        "Ramiona wiszą pionowo za tułowiem",
        "Maksymalna supinacja nadgarstka",
        "Nie unoś łokci w przód podczas uginania"
      ],
      "tempo": "3-1-1-1",
      "restSec": 60,
      "progressionTip": "Świetne ćwiczenie na budowę szczytu bicepsa (biceps peak)."
    },
    {
      "name": "Uginanie młotkowe hantli stojąc (Hammer Curl)",
      "sets": 3,
      "reps": 12,
      "weight": 14,
      "tags": [
        "ramienny",
        "chwyt-mlotkowy",
        "grubosc-ramienia"
      ],
      "muscles": "Mięsień ramienny (brachialis), mięsień ramienno-promieniowy (przedramię), głowa długa bicepsa",
      "desc": "Rozwój mięśnia ramiennego leżącego pod bicepsem, który 'wypycha' biceps w górę, zwiększając obwód ramienia.",
      "difficulty": 2,
      "equipment": [
        "Para hantli"
      ],
      "technique": "1. Trzymaj hantle chwytem neutralnym (palce skierowane do siebie, kciuki w górę).\n2. Uginaj przedramiona równocześnie lub naprzemiennie, utrzymując stały chwyt młotkowy.\n3. Dopnij mięśnie na górze i opuszczaj z kontrolą.",
      "cues": [
        "Kciuki prowadzą ruch w górę",
        "Mocny uścisk dłoni na hantli",
        "Stabilny tułów"
      ],
      "tempo": "2-0-1-1",
      "restSec": 60,
      "progressionTip": "Pozwala na użycie nieco większego ciężaru niż klasyczne uginanie z supinacją."
    },
    {
      "name": "Uginanie przedramion na modlitewniku ze sztangą (Preacher Curl)",
      "sets": 3,
      "reps": 10,
      "weight": 25,
      "tags": [
        "modlitewnik",
        "izolacja",
        "krotka-glowa"
      ],
      "muscles": "Głowa krótka bicepsa, mięsień ramienny",
      "desc": "Całkowicie eliminuje możliwość oszukiwania ciałem, gwarantując chirurgiczną izolację bicepsa.",
      "difficulty": 2,
      "equipment": [
        "Ławka modlitewnik (Preacher bench)",
        "Sztanga łamana"
      ],
      "technique": "1. Usiądź na modlitewniku, oprzyj pachy o krawędź oparcia, ramiona spoczywają płasko na poduszce.\n2. Chwyć sztangę łamaną podchwytem.\n3. Uginaj przedramiona ku górze, zatrzymując ruch tuż przed pionem (by nie tracić napięcia na bicepsie).\n4. Opuszczaj powoli, nie blokując łokci gwałtownie na samym dole.",
      "cues": [
        "Pachy dociśnięte do szczytu modlitewnika",
        "Nie odrywaj ramion od poduszki",
        "Nie przeprostowuj gwałtownie łokci na dole"
      ],
      "tempo": "3-0-1-0",
      "restSec": 60,
      "progressionTip": "Zatrzymaj ruch na dole 1 cm przed pełnym przeprostem w celu ochrony torebki stawowej."
    },
    {
      "name": "Wyciskanie francuskie sztangą łamaną leżąc (Skull Crushers)",
      "sets": 4,
      "reps": 10,
      "weight": 30,
      "tags": [
        "triceps",
        "francuskie",
        "dluga-glowa"
      ],
      "muscles": "Wszystkie trzy głowy tricepsa (zwłaszcza głowa przyśrodkowa i długa)",
      "desc": "Fundamentalne ćwiczenie budujące masę tricepsa, który stanowi 60% obwodu ramienia.",
      "difficulty": 3,
      "equipment": [
        "Ławka pozioma",
        "Sztanga łamana"
      ],
      "technique": "1. Połóż się na ławce, sztangę trzymaj wąskim nachwytem nad klatką. Odchyl ramiona lekko w stronę głowy (kąt ok. 75-80° do tułowia).\n2. Uginając same łokcie, opuszczaj gryf w kierunku czoła lub tuż za czubek głowy.\n3. Łokcie trzymaj wąsko — nie pozwól im rozjeżdżać się na boki.\n4. Prostuj ramiona dynamicznie, dopinając triceps na szczycie.",
      "cues": [
        "Łokcie wąsko przez całą serię",
        "Ruch zachodzi wyłącznie w stawie łokciowym",
        "Opuszczaj za czubek głowy dla lepszego rozciągnięcia"
      ],
      "tempo": "3-1-1-0",
      "restSec": 75,
      "progressionTip": "Zawsze używaj gryfu łamanego dla komfortu łokci i nadgarstków."
    },
    {
      "name": "Prostowanie ramion na wyciągu z liną (Cable Rope Pushdown)",
      "sets": 3,
      "reps": 12,
      "weight": 22,
      "tags": [
        "wyciag",
        "lina",
        "boczna-glowa"
      ],
      "muscles": "Głowa boczna i przyśrodkowa tricepsa (tzw. podkowa tricepsa)",
      "desc": "Kultowe ćwiczenie rzeźbiące zewnętrzną część tricepsa z możliwością rozszerzenia liny na dole.",
      "difficulty": 1,
      "equipment": [
        "Wyciąg górny",
        "Lina do tricepsa"
      ],
      "technique": "1. Chwyć końce liny, stań stabilnie w lekkim pochyleniu tułowia, łokcie przyklejone do talii.\n2. Prostuj ramiona w dół, a w końcowej fazie ruchu rozszerz końce liny na boki, mocno dopinając triceps.\n3. Wracaj kontrolując ciężar do kąta 90° w łokciu.",
      "cues": [
        "Rozszerzaj linę na dole na boki",
        "Łokcie nieruchomo przyklejone do boków",
        "Zatrzymaj spięcie na 1 sekundę"
      ],
      "tempo": "2-0-1-1",
      "restSec": 60,
      "progressionTip": "Świetne jako pierwsze ćwiczenie na dogrzanie łokci lub jako pompujący finisher."
    },
    {
      "name": "Wyciskanie sztangi leżąc wąskim chwytem (Close-Grip Bench Press)",
      "sets": 3,
      "reps": 8,
      "weight": 60,
      "tags": [
        "sztanga",
        "wielostawowe",
        "sila-tricepsa"
      ],
      "muscles": "Triceps (wszystkie głowy), przedni bark, klatka piersiowa",
      "desc": "Najcięższe ćwiczenie wielostawowe na triceps pozwalające na użycie największych obciążeń.",
      "difficulty": 3,
      "equipment": [
        "Sztanga olimpijska",
        "Ławka pozioma",
        "Stojaki"
      ],
      "technique": "1. Połóż się na ławce. Chwyć sztangę na szerokość barków (ok. 30-40 cm rozstawu dłoni — nie węziej, by nie łamać nadgarstków).\n2. Opuszczaj gryf do dolnej części mostka, prowadząc łokcie bardzo blisko tułowia.\n3. Wyciskaj ciężar dynamicznie, skupiając się na wyproście w łokciach siłą tricepsów.",
      "cues": [
        "Chwyt na szerokość barków (nie za wąsko!)",
        "Łokcie suną wzdłuż żeber",
        "Wypchnij siłą tricepsów"
      ],
      "tempo": "3-0-1-0",
      "restSec": 90,
      "progressionTip": "Idealne ćwiczenie łączące budowę siły wyciskania leżąc z gigantyczną masą tricepsów."
    },
    {
      "name": "Pompki w podporze tyłem na ławce (Bench Dips)",
      "sets": 3,
      "reps": 15,
      "weight": 0,
      "tags": [
        "lawka",
        "masa-ciala",
        "wypalenie"
      ],
      "muscles": "Triceps, przedni bark",
      "desc": "Świetne ćwiczenie z masą ciała do wykonania w dowolnym miejscu, silnie pompujące triceps.",
      "difficulty": 2,
      "equipment": [
        "Ławka pozioma lub krzesło"
      ],
      "technique": "1. Oprzyj dłonie na krawędzi ławki tuż przy biodrach, nogi wyprostowane przed sobą oparte na piętach.\n2. Zsuń biodra z ławki i uginaj łokcie w tył, opuszczając ciało pionowo w dół do kąta 90° w łokciach.\n3. Wyciśnij się do góry, prostując ramiona.",
      "cues": [
        "Plecy blisko krawędzi ławki",
        "Łokcie zginają się w tył, nie na boki",
        "Nie schodź poniżej 90° w łokciach (ochrona barków)"
      ],
      "tempo": "2-0-1-1",
      "restSec": 60,
      "progressionTip": "Możesz położyć stopy na drugiej ławce lub poprosić o talerz na uda dla zwiększenia oporu."
    }
  ],
  "brzuch": [
    {
      "name": "Allahy — spięcia brzucha na wyciągu klęcząc (Cable Crunch)",
      "sets": 4,
      "reps": 12,
      "weight": 40,
      "tags": [
        "wyciag",
        "brzuch",
        "progresywne-przeciazenie"
      ],
      "muscles": "Mięsień prosty brzucha (zwłaszcza górna część)",
      "desc": "Jedno z nielicznych ćwiczeń na brzuch pozwalające na precyzyjne, liniowe dokładanie ciężaru i hipertrofię 'kostek'.",
      "difficulty": 2,
      "equipment": [
        "Wyciąg górny",
        "Lina do tricepsa",
        "Mata pod kolana"
      ],
      "technique": "1. Uklęknij przed wyciągiem górnym, trzymając linę przyłożoną po obu stronach głowy przy skroniach.\n2. Biodra zablokowane sztywno w jednym punkcie (ruch NIE polega na siadaniu na pięty!).\n3. Wykonaj zgięcie kręgosłupa siłą mięśni brzucha, przyciągając łokcie w kierunku kolan i zwijając tułów w kłębek.\n4. Wypuść całe powietrze z płuc w dolnej fazie i przytrzymaj maksymalne spięcie przez 1 sekundę.\n5. Wracaj powoli, kontrolując rozciągnięcie mięśni prostych.",
      "cues": [
        "Zwijaj kręgosłup jak dywan, nie zginaj się w biodrach",
        "Biodra nieruchomo nad kolanami",
        "Pełen wydech w punkcie maksymalnego spięcia"
      ],
      "tempo": "2-1-1-1",
      "restSec": 60,
      "progressionTip": "Gdy zrobisz 4x15 z danym ciężarem, przesuń zawleczkę o 2.5–5 kg w dół."
    },
    {
      "name": "Unoszenie nóg w zwisie na drążku (Hanging Leg Raise)",
      "sets": 4,
      "reps": 10,
      "weight": 0,
      "tags": [
        "drazek",
        "dol-brzucha",
        "kalistenika"
      ],
      "muscles": "Dolna część mięśnia prostego brzucha, mięśnie skośne, zginacze bioder",
      "desc": "Najskuteczniejsze ćwiczenie na dół brzucha i kontrolę miednicy w przestrzeni.",
      "difficulty": 4,
      "equipment": [
        "Drążek do podciągania"
      ],
      "technique": "1. Zawiśnij nachwytem na drążku z aktywną obręczą barkową (łopatki lekko ściągnięte).\n2. Napnij pośladki, po czym unoś wyprostowane (lub lekko ugięte) nogi w górę.\n3. Kluczowy moment: podwiń miednicę (retroversja) i unieś stopy minimum do wysokości bioder lub do samego drążka.\n4. Opuszczaj nogi powoli, nie pozwalając ciału na bujanie.",
      "cues": [
        "Podwiń miednicę na szczycie (pokaż pośladki komuś stojącemu z przodu)",
        "Zero bujania (jeśli bujasz — zatrzymaj się)",
        "Powolny opust przez 3 sekundy"
      ],
      "tempo": "3-0-1-1",
      "restSec": 75,
      "progressionTip": "Wersja regresyjna: unoszenie ugiętych kolan do klatki (Hanging Knee Raise)."
    },
    {
      "name": "Deska klasyczna z aktywnym spięciem (RKC Plank)",
      "sets": 3,
      "reps": 1,
      "weight": 0,
      "tags": [
        "izometria",
        "core",
        "stabilizacja"
      ],
      "muscles": "Mięsień poprzeczny brzucha (transversus abdominis), prosty brzucha, pośladki, czworoboczne",
      "desc": "Wersja RKC to maksymalne spięcie całego ciała generujące potężną siłę gorsetu mięśniowego w 20-30 sekund.",
      "difficulty": 3,
      "equipment": [
        "Mata do ćwiczeń"
      ],
      "technique": "1. Przyjmij pozycję podporu przodem na przedramionach i palcach stóp.\n2. Łokcie ustaw bezpośrednio pod barkami, zaciśnij pięści.\n3. Ściągnij łopatki, napnij pośladki na 100%, podwiń miednicę pod siebie.\n4. Spróbuj izometrycznie przyciągać łokcie w stronę stóp, a stopy w stronę łokci — generując maksymalne napięcie.\n5. Oddychaj płytko, utrzymując żelazne napięcie przez 20-30 sekund.",
      "cues": [
        "Ściśnij pośladki jakbyś trzymał monetę",
        "Przyciągaj łokcie do palców stóp (aktywny wektor siły)",
        "Ciało w idealnej linii prostej"
      ],
      "tempo": "izometria 30s",
      "restSec": 60,
      "progressionTip": "Lepiej zrobić 30 sekund maksymalnego spięcia RKC niż 3 minuty biernego wiszenia w stawie."
    },
    {
      "name": "Kółko gimnastyczne (Ab Wheel Rollout)",
      "sets": 3,
      "reps": 8,
      "weight": 0,
      "tags": [
        "kolko",
        "antyekstensja",
        "zaawansowane"
      ],
      "muscles": "Mięsień prosty brzucha, mięsień poprzeczny, najszerszy grzbietu",
      "desc": "Potężne ćwiczenie antyekstensyjne kręgosłupa budujące pancerną ścianę brzucha.",
      "difficulty": 4,
      "equipment": [
        "Kółko do ćwiczeń brzucha (Ab wheel)",
        "Mata pod kolana"
      ],
      "technique": "1. Uklęknij na macie, chwyć kółko oburącz pod klatką piersiową.\n2. Zaokrąglij lekko górę pleców, podwiń miednicę i napnij brzuch.\n3. Płynnie tocz kółko w przód, opuszczając ciało jak najniżej nad podłogę bez wyginania lędźwi w łuk.\n4. Siłą mięśni brzucha przyciągnij kółko z powrotem do pozycji wyjściowej.",
      "cues": [
        "Nie pozwól lędźwiom opaść w dół (żelazna miednica)",
        "Wracaj siłą brzucha, nie bioder",
        "Zacznij od mniejszego zakresu ruchu (np. do ściany)"
      ],
      "tempo": "3-1-1-0",
      "restSec": 90,
      "progressionTip": "Jeśli odczuwasz odcinek lędźwiowy, zmniejsz zakres ruchu, kładąc przeszkodę (np. ścianę) przed kółkiem."
    },
    {
      "name": "Pallof Press na wyciągu (Antyrotacja Core)",
      "sets": 3,
      "reps": 10,
      "weight": 15,
      "tags": [
        "antyrotacja",
        "zdrowy-kregoslup",
        "funkcjonalne"
      ],
      "muscles": "Mięśnie skośne brzucha, mięsień poprzeczny, stabilizatory miednicy",
      "desc": "Fundament treningu funkcjonalnego — uczy ciało przeciwstawiania się siłom rotacyjnym działającym na kręgosłup.",
      "difficulty": 2,
      "equipment": [
        "Wyciąg z regulacją wysokości lub guma oporowa"
      ],
      "technique": "1. Ustaw bloczek wyciągu na wysokości mostka. Chwyć uchwyt oburącz przy klatce i odejdź 2 kroki w bok.\n2. Stań stabilnie na lekko ugiętych nogach, biodra i barki skierowane prosto przed siebie.\n3. Wypchnij dłonie prosto przed siebie na wysokość mostka, przeciwstawiając się sile obracającej cię w stronę wyciągu.\n4. Wytrzymaj 2 sekundy w pełnym wyproście ramion i powoli przyciągnij dłonie do mostka.",
      "cues": [
        "Biodra i barki ani drgną — zero rotacji",
        "Zatrzymaj wyprost na 2 sekundy",
        "Oddychaj spokojnie przeponą"
      ],
      "tempo": "2-2-1-0",
      "restSec": 60,
      "progressionTip": "Wykonaj 10 powtórzeń na prawą i lewą stronę."
    },
    {
      "name": "Russian Twists z talerzem lub piłką lekarską",
      "sets": 3,
      "reps": 15,
      "weight": 10,
      "tags": [
        "skosne",
        "talerz",
        "dynamika"
      ],
      "muscles": "Mięśnie skośne wewnętrzne i zewnętrzne brzucha, mięsień prosty",
      "desc": "Dynamiczna rotacja tułowia z obciążeniem budująca silne skosy i moc rotacyjną.",
      "difficulty": 2,
      "equipment": [
        "Talerz olimpijski 5-10kg lub piłka lekarska",
        "Mata"
      ],
      "technique": "1. Usiądź na podłodze, ugnij kolana i unieś stopy kilka centymetrów nad ziemię (pozycja V-sit).\n2. Trzymaj talerz oburącz przy klatce piersiowej.\n3. Wykonaj kontrolowany obrót tułowia w prawo, dotykając talerzem podłogi przy biodrze.\n4. Następnie płynnie przenieś ciężar na lewą stronę.",
      "cues": [
        "Obracaj całą klatkę piersiową, nie tylko same ręce",
        "Nogi stabilne, nie bujaj nimi na boki",
        "Oddychaj rytmicznie z każdym skrętem"
      ],
      "tempo": "1-0-1-0",
      "restSec": 60,
      "progressionTip": "Licz 15 powtórzeń na każdą stronę (łącznie 30 skrętów w serii)."
    },
    {
      "name": "Deadbug (Martwy Robak) z gumą oporową",
      "sets": 3,
      "reps": 12,
      "weight": 0,
      "tags": [
        "rehabilitacja",
        "kontrola-miednicy",
        "gleboki-core"
      ],
      "muscles": "Mięsień poprzeczny brzucha, dno miednicy, wielodzielny",
      "desc": "Złoty standard rehabilitacyjny uczący dysocjacji ruchu kończyn przy zachowaniu stabilnego kręgosłupa.",
      "difficulty": 2,
      "equipment": [
        "Mata do ćwiczeń"
      ],
      "technique": "1. Połóż się na plecach, ręce wyciągnięte pionowo w górę, nogi ugięte pod kątem 90° w biodrach i kolanach.\n2. Wciśnij odcinek lędźwiowy w podłogę (miednica podwinięta, zero szczeliny pod plecami).\n3. Powoli opuszczaj prawą rękę za głowę i lewą nogę nad podłogę, nie pozwalając lędźwiom oderwać się od ziemi.\n4. Wróć do pozycji wyjściowej i powtórz dla przeciwnej pary kończyn.",
      "cues": [
        "Lędźwie zabetonowane w podłodze przez cały czas",
        "Ruch powolny i precyzyjny",
        "Płynny wydech przy prostowaniu kończyn"
      ],
      "tempo": "3-1-3-0",
      "restSec": 45,
      "progressionTip": "Jeśli lędźwie odrywają się od ziemi, nie opuszczaj nogi tak nisko."
    },
    {
      "name": "Dragon Flag (Flaga Smoka)",
      "sets": 3,
      "reps": 6,
      "weight": 0,
      "tags": [
        "bruce-lee",
        "ekstremalne",
        "elita-core"
      ],
      "muscles": "Cały gorset mięśniowy brzucha, prostowniki grzbietu, najszerszy grzbietu",
      "desc": "Legendarne ćwiczenie Bruce'a Lee uważane za jeden z najtrudniejszych testów siły mięśni brzucha na świecie.",
      "difficulty": 5,
      "equipment": [
        "Ławka pozioma z solidnym uchwytem za głową"
      ],
      "technique": "1. Połóż się na ławce, chwyć rękami krawędzie ławki tuż za głową.\n2. Wyrzuć całe ciało pionowo w górę, opierając się jedynie na górnej części łopatek.\n3. Utrzymując ciało sztywne jak strzała (od stóp po barki w linii prostej), opuszczaj je powoli w dół.\n4. Zatrzymaj ciało tuż nad ławką i unieś z powrotem bez załamywania bioder.",
      "cues": [
        "Ciało sztywne jak deska — zero zgięcia w biodrach",
        "Opierasz się tylko na łopatkach",
        "Zacznij od samej fazy negatywnej (powolnego opuszczania)"
      ],
      "tempo": "4-1-1-0",
      "restSec": 120,
      "progressionTip": "Zanim wykonasz pełną wersję, opanuj opuszczanie z ugiętymi kolanami (Tuck Dragon Flag)."
    }
  ]
};

var SPORT_DRILLS = {
  "koszykowka": {
    "emoji": "🏀",
    "Rzuty": {
      "emoji": "🎯",
      "label": "Rzuty i skuteczność",
      "drills": [
        {
          "id": "bball_rzuty_001",
          "name": "Rzuty z 5 stref po obwodzie (50 rzutów)",
          "category": "Rzuty",
          "sport": "Koszykówka",
          "difficulty": "beginner",
          "duration": "20 min",
          "sets": "5 stref × 10 rzutów (rogi, skrzydła, szczyt łuku)",
          "total_attempts": 50,
          "equipment": [
            "Piłka do koszykówki (rozmiar 7)",
            "Kosz z siatką"
          ],
          "muscles": [
            "mięsień trójgłowy ramienia",
            "naramienny przedni",
            "czworogłowy uda",
            "zginacze nadgarstka"
          ],
          "muscle_group": "ramiona, nogi, stabilizacja core",
          "description": "Systematyczny trening mechaniki rzutu ze stałych pozycji obwodowych. Buduje powtarzalną pamięć mięśniową i pozwala dokładnie zmierzyć skuteczność w poszczególnych sektorach boiska.",
          "courtPosition": "Pięć punktów wokół linii rzutów za 3 punkty: lewy róg (corner 0°), lewe skrzydło (wing 45°), szczyt łuku (top of the key 90°), prawe skrzydło (wing 45°), prawy róg (corner 0°).",
          "execution": "1. Ustaw się w pierwszej strefie (lewy róg). Stopy rozstaw na szerokość barków, lekko zwrócone w stronę kosza (10-15°).\n2. Wykonaj 10 rzutów z miejsca. Pilnuj stałego punktu wypuszczenia piłki (set point na wysokości czoła/oka rzucającego).\n3. Po każdych 10 rzutach zapisz liczbę trafień i przejdź do kolejnej strefy.\n4. Utrzymuj pełne wykończenie rzutu ręką rzucającą (follow-through) do momentu, aż piłka wpadnie do kosza.",
          "biomechanics": "Siła rzutu generowana jest z nóg (dip kolan) i przenoszona płynnym ruchem przez biodra i tułów do nadgarstka. Łokieć ręki rzucającej znajduje się pod piłką w jednej płaszczyźnie z kolanem i stopą. Ręka wspomagająca odpada od piłki tuż przed wypuszczeniem, nie popychając jej kciukiem.",
          "commonErrors": [
            "Pchanie piłki z klatki piersiowej zamiast płynnego wypchnięcia od dołu ku górze",
            "Uciekanie łokcia na zewnątrz (chicken wing)",
            "Kciuk ręki wspomagającej popychający piłkę",
            "Opuszczanie ręki rzucającej natychmiast po wyrzucie"
          ],
          "benefits": [
            "Budowa powtarzalnego łuku i rotacji piłki",
            "Identyfikacja słabszych sektorów na boisku",
            "Podstawa skuteczności meczowej"
          ],
          "target_pct": 60,
          "progression_tip": "Gdy osiągniesz 35/50 (70%) w 3 kolejnych sesjach, przejdź do rzutów po jednym koźle lub catch-and-shoot zbiegając do pozycji.",
          "tags": [
            "rzuty",
            "strefy",
            "mechanika",
            "podstawy"
          ]
        },
        {
          "id": "bball_rzuty_002",
          "name": "Rzuty wolne pod presją zmęczeniową (30 rzutów)",
          "category": "Rzuty",
          "sport": "Koszykówka",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "3 serie po 10 rzutów (przeplatane sprintem 20m po niecelnym)",
          "total_attempts": 30,
          "equipment": [
            "Piłka do koszykówki",
            "Linia rzutów wolnych"
          ],
          "muscles": [
            "czworogłowe ud",
            "naramienne",
            "mięśnie oddechowe",
            "przedramiona"
          ],
          "muscle_group": "nogi, koncentracja, oddech",
          "description": "Rzuty osobiste wykonywane w warunkach podwyższonego tętna z wypracowaną, niezmienną rutyną przedrzutową, symulującą końcówkę zaciętego meczu.",
          "courtPosition": "Linia rzutów wolnych (4.60m od tablicy).",
          "execution": "1. Podejdź do linii rzutów wolnych, ustaw stopy w stałej pozycji (palec stopy rzucającej naprzeciwko środka obręczy).\n2. Wykonaj swoją stałą rutynę (np. 3 kozły, głęboki wdech przeponowy, uniesienie wzroku na tylną część obręczy).\n3. Oddaj rzut z pełnym wykończeniem nadgarstka.\n4. Kara za pudło: natychmiastowy sprint do linii środkowej i powrót przed kolejnym rzutem.",
          "biomechanics": "Kontrola oddechu i obniżenie środka ciężkości. Wdech przy przygotowaniu, spokojny wydech podczas ruchu w górę. Ciało porusza się w idealnej pionowej linii.",
          "commonErrors": [
            "Pośpiech i brak stałej rutyny",
            "Rzucanie na bezdechu przy wysokim tętnie",
            "Niestabilne ułożenie stóp na linii"
          ],
          "benefits": [
            "Odporność psychiczna pod presją",
            "Automatyzacja techniki w warunkach zmęczenia",
            "Wzrost procentu osobistych w meczu"
          ],
          "target_pct": 75,
          "progression_tip": "Cel mistrzowski: 26/30 (86%). Jeśli trafisz 10/10 w serii, kończysz serię bez karnych sprintów.",
          "tags": [
            "osobiste",
            "rutyna",
            "presja",
            "mental"
          ]
        },
        {
          "id": "bball_rzuty_003",
          "name": "Catch and shoot po ścięciu do skrzydła",
          "category": "Rzuty",
          "sport": "Koszykówka",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 5 rzutów z każdego skrzydła",
          "total_attempts": 20,
          "equipment": [
            "Piłka",
            "Kosz",
            "Partner podający lub rzut piłki z rotacją wsteczną solo"
          ],
          "muscles": [
            "czworogłowe",
            "łydki",
            "core",
            "barki"
          ],
          "muscle_group": "dynamika, nogi, ramiona",
          "description": "Rzut natychmiast po dynamicznym wyjściu na pozycję i chwycie piłki, minimalizując czas od odebrania podania do oddania rzutu (<0.7 sekundy).",
          "courtPosition": "Ścięcie ze strefy podkoszowej w kierunku skrzydła (45°) na dystans 6-7 metrów.",
          "execution": "1. Rozpocznij ruch pod koszem, wykonaj ostry zwód i sprintem wybiegnij na skrzydło.\n2. Przyjmij podanie z przygotowanymi stopami (krok 1-2: wewnętrzna noga pierwsza, zewnętrzna druga).\n3. Obniż biodra w momencie chwytu, nie wykonuj żadnego kozła.\n4. Wypchnij się w górę w płynnym rzucie wyskoku (jumper).",
          "biomechanics": "Hamowanie liniowe i natychmiastowa konwersja energii pędu poziomego w wyskok pionowy. Ramiona i piłka już w trakcie chwytu wędrują wprost do set-pointu.",
          "commonErrors": [
            "Łapanie piłki na prostych nogach i dopiero potem uginanie",
            "Dodatkowy zbędny kozioł po chwycie",
            "Wychylenie tułowia w stronę podania w locie"
          ],
          "benefits": [
            "Błyskawiczne uwalnianie rzutu przed blokiem obrońcy",
            "Praca nóg w pełnym biegu",
            "Gotowość strzelecka"
          ],
          "target_pct": 65,
          "progression_tip": "Dodaj obrońcę wykonującego close-out z ręką uniesioną w górę dla symulacji obrony.",
          "tags": [
            "catch-and-shoot",
            "ruch-bez-pilki",
            "praca-nog"
          ]
        },
        {
          "id": "bball_rzuty_004",
          "name": "Mid-range Pull-up Jumper po jednym koźle",
          "category": "Rzuty",
          "sport": "Koszykówka",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "4 serie po 6 rzutów (naprzemiennie po koźle w prawo i w lewo)",
          "total_attempts": 24,
          "equipment": [
            "Piłka",
            "Kosz",
            "Pachołek jako obrońca"
          ],
          "muscles": [
            "łydki",
            "czworogłowe",
            "pośladki",
            "core"
          ],
          "muscle_group": "eksplozywność, wyskok, koordynacja",
          "description": "Zatrzymanie na 2 tempa z kozła i rzut z półdystansu z wyskoku. Zabójcza broń przeciwko obronie cofającej się pod kosz.",
          "courtPosition": "Strefa 4-5 metrów od kosza po wejściu z obwodu.",
          "execution": "1. Atakuj pachołek dynamicznym kozłem prawą lub lewą ręką.\n2. Wykonaj ostre zatrzymanie naskokiem (jump stop) lub na 2 tempa tuż za przeszkodą.\n3. Wysoko wyskocz w pionie z idealną równowagą tułowia.\n4. Oddaj rzut w najwyższym punkcie wyskoku (na szczycie paraboli).",
          "biomechanics": "Stabilizacja kręgosłupa przez mocne napięcie mięśni brzucha zapobiega opadaniu lub przechylaniu w locie. Lądowanie dokładnie w tym samym punkcie co wybicie.",
          "commonErrors": [
            "Wypuszczanie piłki podczas opadania z wyskoku",
            "Pochylanie tułowia do przodu po zatrzymaniu",
            "Zbyt długi krok hamujący"
          ],
          "benefits": [
            "Niezależność od rzutów za 3 i wjazdów pod kosz",
            "Wysoki punkt wypuszczenia trudny do zablokowania"
          ],
          "target_pct": 60,
          "progression_tip": "Wprowadź zmianę kierunku przed pull-upem (crossover + pull-up).",
          "tags": [
            "pull-up",
            "pol-dystans",
            "zatrzymanie",
            "wyskok"
          ]
        }
      ]
    },
    "Drybling": {
      "emoji": "⚡",
      "label": "Kontrola piłki i kozioł",
      "drills": [
        {
          "id": "bball_drib_001",
          "name": "Slalom z crossoverem i zmianą pod nogami",
          "category": "Drybling",
          "sport": "Koszykówka",
          "difficulty": "beginner",
          "duration": "15 min",
          "sets": "6 powtórzeń całego toru (po 3 na stronę dominującą)",
          "total_attempts": 6,
          "equipment": [
            "Piłka do koszykówki",
            "5 pachołków w linii prostej co 1.5m"
          ],
          "muscles": [
            "przedramiona",
            "czworogłowe",
            "pośladki",
            "skośne brzucha"
          ],
          "muscle_group": "przedramiona, nogi, zwinność",
          "description": "Rozwój niskiego, agresywnego kozła ze zmianami kierunku na małej przestrzeni bez patrzenia na piłkę.",
          "courtPosition": "Linia boczna boiska lub przestrzeń od linii końcowej do połowy.",
          "execution": "1. Ustaw 5 pachołków w odstępach 1.5 metra.\n2. Na każdym pachołku wykonaj niską, dynamiczną zmianę ręki: pachołek 1 (przed sobą), pachołek 2 (pod nogami), pachołek 3 (za plecami), pachołek 4 (in-and-out).\n3. Po minięciu ostatniego pachołka wykonaj eksplozywne przyspieszenie na 5 metrów z dwutaktem do kosza.",
          "biomechanics": "Nisko położony środek ciężkości (biodra poniżej poziomu kolan obrońcy). Dłoń na boku i górze piłki, wbijanie piłki mocno w parkiet.",
          "commonErrors": [
            "Wzrok wbity w piłkę zamiast obserwacji boiska",
            "Za wysoki kozioł powyżej linii bioder",
            "Brak obniżenia bioder przy zmianie"
          ],
          "benefits": [
            "Pewność prowadzenia piłki pod presją",
            "Rozszerzenie pola widzenia",
            "Szybkość pracy rąk"
          ],
          "target_pct": 85,
          "progression_tip": "Załóż rękawiczki śliskie lub owiń piłkę reklamówką, by drastycznie utrudnić chwyt.",
          "tags": [
            "slalom",
            "crossover",
            "kontrola",
            "pacholki"
          ]
        },
        {
          "id": "bball_drib_002",
          "name": "Kozłowanie dwiema piłkami jednocześnie (High-Low & Synchro)",
          "category": "Drybling",
          "sport": "Koszykówka",
          "difficulty": "intermediate",
          "duration": "12 min",
          "sets": "3 serie po 45 sekund: synchronicznie, na przemian, jedna wysoko-druga nisko",
          "total_attempts": 3,
          "equipment": [
            "Dwie piłki do koszykówki"
          ],
          "muscles": [
            "przedramiona",
            "barki",
            "core",
            "koordynacja półkulowa"
          ],
          "muscle_group": "koordynacja, przedramiona, barki",
          "description": "Najlepsze ćwiczenie neuro-koordynacyjne na zrównoważenie umiejętności ręki słabszej i silniejszej.",
          "courtPosition": "Dowolne wolne miejsce na parkiecie, pozycja w miejscu.",
          "execution": "1. Przyjmij szeroką pozycję koszykarską (triple threat stance).\n2. Kozłuj obiema piłkami jednocześnie na wysokość kolan przez 45 sekund.\n3. Zmień na kozioł naprzemienny (jedna w górze, druga na dole).\n4. Wykonaj kozioł asymetryczny: prawa ręka mocny kozioł do barku, lewa ręka błyskawiczny kozioł tuż nad parkietem.",
          "biomechanics": "Dysocjacja motoryczna lewej i prawej półkuli mózgowej. Sztywny nadgarstek z miękkimi, aktywnymi palcami absorbującymi uderzenie.",
          "commonErrors": [
            "Utrata rytmu po kilku sekundach",
            "Patrzenie na jedną z piłek",
            "Wyprost kolan w trakcie zmęczenia"
          ],
          "benefits": [
            "Idealne zbalansowanie ręki słabszej",
            "Potężne wzmocnienie siły palców i przedramion"
          ],
          "target_pct": 80,
          "progression_tip": "Dodaj marsz w przód i w tył podczas kozłowania dwiema piłkami.",
          "tags": [
            "dwie-pilki",
            "koordynacja",
            "slabsza-reka"
          ]
        },
        {
          "id": "bball_drib_003",
          "name": "In-and-Out + Hesitation (Zwód zawieszenia) z wejściem pod kosz",
          "category": "Drybling",
          "sport": "Koszykówka",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 6 powtórzeń (wykończenie prawym i lewym layupem)",
          "total_attempts": 24,
          "equipment": [
            "Piłka",
            "Kosz"
          ],
          "muscles": [
            "czworogłowe",
            "łydki",
            "pośladki",
            "ramiona"
          ],
          "muscle_group": "zmiana-tempa, przyspieszenie, zwód",
          "description": "Zwód zmiany tempa: udanie próby rzutu (hesitation) połączone z fałszywym crossoverem (in-and-out) i nagłym wybuchem do kosza.",
          "courtPosition": "Skrzydło 45° za linią 3 punktów, atak strefy podkoszowej.",
          "execution": "1. Rozpocznij kozioł ku obrońcy w średnim tempie.\n2. Na odległość 1.5m wykonaj ruch in-and-out dłonią nad piłką, jednocześnie unosząc lekko tułów i zerkając na obręcz (sugerując rzut).\n3. Gdy obrońca uniesie środek ciężkości, obniż biodra i wykonaj potężny krok wybuchowy obok niego, kończąc akcję layupem o tablicę.",
          "biomechanics": "Kontrast prędkości: spowolnienie do 20% prędkości maksymalnej i natychmiastowe przyspieszenie do 100% w jednym kroku.",
          "commonErrors": [
            "Brak spojrzenia na obręcz (obrońca nie kupuje zwodu)",
            "Noszenie piłki (dłoń nie może znaleźć się pod piłką)",
            "Zbyt wolny pierwszy krok po zwodzie"
          ],
          "benefits": [
            "Mijanie obrońcy bez konieczności zmiany ręki",
            "Elitarna kontrola tempa gry"
          ],
          "target_pct": 75,
          "progression_tip": "Zakończ akcję floaterem (rzutem łezką) ponad wyimaginowanym środkowym rywali.",
          "tags": [
            "hesitation",
            "in-and-out",
            "layup",
            "zmiana-tempa"
          ]
        }
      ]
    },
    "Obrona": {
      "emoji": "🛡️",
      "label": "Obrona i praca nóg",
      "drills": [
        {
          "id": "bball_obr_001",
          "name": "Krok odstawno-dostawny 'Zygzak' na całym boisku (Zig-Zag Defensive Slides)",
          "category": "Obrona",
          "sport": "Koszykówka",
          "difficulty": "intermediate",
          "duration": "12 min",
          "sets": "5 długości boiska na 100% intensywności z przerwą 60 sek",
          "total_attempts": 5,
          "equipment": [
            "Boisko do koszykówki",
            "Stoper"
          ],
          "muscles": [
            "pośladkowy średni",
            "czworogłowe",
            "przywodziciele",
            "łydki",
            "core"
          ],
          "muscle_group": "nogi, biodra, kondycja defensywna",
          "description": "Fundamentalny trening poruszania się w postawie obronnej z gwałtowną zmianą kierunku pod kątem 45° (drop-step).",
          "courtPosition": "Całe boisko od linii końcowej do końcowej po przekątnych (zygzakiem od linii bocznej do środka).",
          "execution": "1. Przyjmij niską postawę obronną: stopy szeroko, pośladki nisko, klatka wypięta, ręce aktywne w bok.\n2. Wykonuj dynamiczne kroki odstawno-dostawne po skosie (krok nogą kierunkową, dostawienie drugiej bez łączenia stóp!).\n3. Na linii bocznej wykonaj ostry drop-step (otwarcie biodra nogą zakroczną) i zmień kierunek po skosie w stronę środka boiska.\n4. Przejdź całe boisko bez krzyżowania nóg.",
          "biomechanics": "Zakaz krzyżowania nóg i zakaz podskakiwania. Głowa i tułów poruszają się w jednej poziomej płaszczyźnie bez wahań pionowych.",
          "commonErrors": [
            "Łączenie stóp lub krzyżowanie nóg (utrata balansu)",
            "Wstawanie z nóg przy zmęczeniu",
            "Opuszczanie rąk"
          ],
          "benefits": [
            "Nie do przejścia w obronie 1 na 1 na obwodzie",
            "Piekielna wytrzymałość mięśniowa nóg"
          ],
          "target_pct": 90,
          "progression_tip": "Dodaj partnera z piłką, który zmienia tempo i kierunek, a Twoim zadaniem jest dotrzymać mu kroku klatką piersiową.",
          "tags": [
            "obrona",
            "zygzak",
            "drop-step",
            "praca-nog"
          ]
        },
        {
          "id": "bball_obr_002",
          "name": "Close-out z odskokiem i kontestowaniem rzutu",
          "category": "Obrona",
          "sport": "Koszykówka",
          "difficulty": "beginner",
          "duration": "10 min",
          "sets": "3 serie po 8 powtórzeń (4 prawe, 4 lewe skrzydło)",
          "total_attempts": 24,
          "equipment": [
            "Kosz",
            "Linia 3 punktów"
          ],
          "muscles": [
            "łydki",
            "czworogłowe",
            "core"
          ],
          "muscle_group": "szybkość reakcji, hamowanie, skoczność",
          "description": "Technika doskoku do strzelca na obwodzie z błyskawicznym wyhamowaniem drobnymi krokami (choppy steps), uniemożliwiająca minięcie.",
          "courtPosition": "Start z trumny (pomalowanego pola), doskok na obwód (linia 3 punktów).",
          "execution": "1. Rozpocznij w strefie podkoszowej w pozycji asekuracji (help defense).\n2. Na komendę wykonaj 2 długie, sprinterskie kroki ku strzelcowi na obwodzie.\n3. Ostatnie 1.5 metra wyhamuj serią szybkich, drobnych kroczków (stutter steps), obniżając środek ciężkości.\n4. Wyciągnij jedną rękę wysoko w górę kontestując rzut, druga ręka nisko zabezpiecza minięcie.\n5. Natychmiast bądź gotowy na krok w tył w razie wjazdu rywala.",
          "biomechanics": "Konwersja sprintu w stabilną bazę. Wyciągnięcie ręki bez skoku w przód (uniknięcie faulu przy rzucie).",
          "commonErrors": [
            "Wypadanie w powietrze na zwód rzutu (fly-by)",
            "Brak drobnych kroków hamujących i wpadanie w atakującego",
            "Doskok na prostych nogach"
          ],
          "benefits": [
            "Eliminacja czystych rzutów rywali za 3 punkty",
            "Brak fauli przy rzutach"
          ],
          "target_pct": 85,
          "progression_tip": "Po wyhamowaniu wykonaj natychmiastowy ślizg obronny w kierunku wjazdu partnera.",
          "tags": [
            "close-out",
            "kontestowanie",
            "obrona-obwodu"
          ]
        }
      ]
    },
    "Podania": {
      "emoji": "🤝",
      "label": "Podania i taktyka",
      "drills": [
        {
          "id": "bball_poda_001",
          "name": "Podania do ściany: Chest Pass, Bounce Pass i Push Pass (100 podań)",
          "category": "Podania",
          "sport": "Koszykówka",
          "difficulty": "beginner",
          "duration": "10 min",
          "sets": "100 podań na czas: 40 klatka, 30 kozioł, 30 jednorącz push-pass",
          "total_attempts": 100,
          "equipment": [
            "Piłka do koszykówki",
            "Płaska ściana murowana lub rebounder"
          ],
          "muscles": [
            "triceps",
            "naramienny przedni",
            "nadgarstki",
            "piersiowe"
          ],
          "muscle_group": "ramiona, klatka, nadgarstki",
          "description": "Budowa siły i szybkości podania z poprawnym ruchem nadgarstków (thumbs down) i natychmiastowym chwytem piłki.",
          "courtPosition": "Dystans 3-4 metry od gładkiej ściany.",
          "execution": "1. CHEST PASS (40x): Wypchnij piłkę od klatki, dłonie obracają się tak, by kciuki po podaniu wskazywały podłogę.\n2. BOUNCE PASS (30x): Celuj piłką w podłogę na 2/3 odległości do ściany, by po odbiciu trafiła na wysokość klatki.\n3. PUSH PASS (30x): Podanie z kozła jednorącz (jak podanie z pick-and-rolla obok obrońcy).",
          "biomechanics": "Dynamiczne zgięcie dłoniowe w stawach nadgarstkowych generuje wsteczną rotację piłki (backspin), stabilizującą lot.",
          "commonErrors": [
            "Kciuki skierowane do góry po podaniu",
            "Zbyt wolny lot piłki",
            "Brak kroku w przód w stronę podania"
          ],
          "benefits": [
            "Ostre, bezpieczne podania trudne do przechwycenia",
            "Siła palców i dłoni"
          ],
          "target_pct": 95,
          "progression_tip": "Zmierz czas wykonania 100 celnych podań. Cel: poniżej 90 sekund.",
          "tags": [
            "podania",
            "sciana",
            "chest-pass",
            "bounce-pass"
          ]
        },
        {
          "id": "bball_takt_001",
          "name": "Pick and Roll: Czytanie obrony (Drop vs Hedge vs Switch)",
          "category": "Podania",
          "sport": "Koszykówka",
          "difficulty": "advanced",
          "duration": "20 min",
          "sets": "4 serie po 6 akcji (różne warianty reakcji obrony)",
          "total_attempts": 24,
          "equipment": [
            "Piłka",
            "Kosz",
            "3 graczy (rozgrywający, stawiający zasłonę, obrońca)"
          ],
          "muscles": [
            "całe ciało",
            "wzrok",
            "podejmowanie decyzji"
          ],
          "muscle_group": "decyzyjność, zwinność, przyspieszenie",
          "description": "Praktyczne opanowanie najpopularniejszej akcji dwójkowej współczesnej koszykówki z czytaniem bioder obrońcy.",
          "courtPosition": "Szczyt łuku za 3 punkty i strefa podkoszowa.",
          "execution": "1. Rozgrywający czeka na nieruchomą zasłonę od wysokiego gracza.\n2. Przechodzi tuż przy ramieniu stawiającego zasłonę (bark w bark), uniemożliwiając przeciśnięcie się obrońcy.\n3. Czyta reakcję: jeśli obrońca zostaje w tyle (Drop) -> pull-up jumper; jeśli podwaja (Trap/Hedge) -> podanie lobem lub kozłem do ścinającego partnera (Roll); jeśli obrona się cofa -> rzut za 3.",
          "biomechanics": "Ciasne minięcie zasłony bez wolnej przestrzeni. Zmiana rytmu kozła i ochrona piłki ciałem.",
          "commonErrors": [
            "Zbyt wczesne minięcie zasłony, zanim partner się ustawi (faul w ataku)",
            "Zostawienie przestrzeni między sobą a zasłoną",
            "Brak obserwacji stóp drugiego obrońcy"
          ],
          "benefits": [
            "Baza taktyczna do gry w lidze lub turniejach 3x3",
            "Elitarne czytanie gry"
          ],
          "target_pct": 75,
          "progression_tip": "Graj w pełnym kontakcie 2 na 2 z ograniczeniem czasu akcji do 7 sekund.",
          "tags": [
            "pick-and-roll",
            "taktyka",
            "decyzyjnosc",
            "gra-dwojkowa"
          ]
        }
      ]
    }
  },
  "pilka_nozna": {
    "emoji": "⚽",
    "Prowadzenie i zwody": {
      "emoji": "👟",
      "label": "Prowadzenie piłki i drybling",
      "drills": [
        {
          "id": "fball_drib_001",
          "name": "Slalom między pachołkami obiema nogami (Wewnętrzna / Zewnętrzna)",
          "category": "Prowadzenie i zwody",
          "sport": "Piłka nożna",
          "difficulty": "beginner",
          "duration": "15 min",
          "sets": "6 powtórzeń (3x noga prawa, 3x noga lewa/naprzemiennie)",
          "total_attempts": 6,
          "equipment": [
            "Piłka nożna (rozmiar 5)",
            "6-8 pachołków ustawionych w linii co 1m"
          ],
          "muscles": [
            "czworogłowe",
            "łydki",
            "mięśnie piszczelowe",
            "przywodziciele"
          ],
          "muscle_group": "stawy skokowe, zwinność, czucie piłki",
          "description": "Klasyczny tor techniczny budujący miękkie czucie piłki przy każdym kroku zewnętrzną i wewnętrzną częścią stopy.",
          "courtPosition": "Dowolny odcinek boiska o długości 10-12 metrów.",
          "execution": "1. Prowadź piłkę przez slalom pachołków, dotykając jej przy każdym kroku.\n2. Wokół pachołka manewruj na zmianę zewnętrznym i wewnętrznym podbiciem.\n3. Głowa uniesiona — patrz przed siebie, nie tylko pod nogi.\n4. Po minięciu ostatniego pachołka przyspiesz na odcinku 5 metrów z piłką przy nodze.",
          "biomechanics": "Ugięte kolana, nisko położony środek ciężkości. Dotknięcia piłki zablokowanym, ale elastycznym stawem skokowym.",
          "commonErrors": [
            "Zbyt mocne wypuszczanie piłki (kontakt co 3-4 kroki)",
            "Wzrok skierowany wyłącznie w ziemię",
            "Prowadzenie tylko jedną nogą"
          ],
          "benefits": [
            "Ciasna kontrola piłki pod pressingiem",
            "Czucie piłki obiema stopami"
          ],
          "target_pct": 85,
          "progression_tip": "Zmierz czas przejazdu przez slalom. Za dotknięcie pachołka dodaj 2 sekundy kary.",
          "tags": [
            "slalom",
            "czucie-pilki",
            "obie-nogi",
            "podstawy"
          ]
        },
        {
          "id": "fball_drib_002",
          "name": "Zwód pojedynczy ciałem (Body Feint) + dynamiczne wyjście",
          "category": "Prowadzenie i zwody",
          "sport": "Piłka nożna",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 6 prób (naprzemiennie zwód w lewo i w prawo)",
          "total_attempts": 24,
          "equipment": [
            "Piłka",
            "Manekin treningowy lub tyczka"
          ],
          "muscles": [
            "pośladkowy średni",
            "czworogłowe",
            "skośne brzucha",
            "łydki"
          ],
          "muscle_group": "biodra, dynamika, balans",
          "description": "Balans ciałem imitujący ruch w jedną stronę połączony z natychmiastowym zabraniem piłki zewnętrzną częścią stopy w stronę przeciwną.",
          "courtPosition": "Strefa przed polem karnym (20-25 metrów od bramki).",
          "execution": "1. Prowadź piłkę w tempie w stronę manekina.\n2. Na odległość 1.5 metra zrób zdecydowany krok w lewo, obniżając lewe ramię i kolano (markowanie ruchu).\n3. Nie dotykając piłki lewą stopą, dynamicznie przenieś ciężar ciała i zewnętrzną częścią prawej stopy zetnij w prawo.\n4. Zakończ akcję strzałem na bramkę lub podaniem.",
          "biomechanics": "Szybki transfer wektora siły z lewej nogi na prawą. Wiarygodność zwodu zależy od pochylenia barku i głowy.",
          "commonErrors": [
            "Wykonanie zwodu za blisko obrońcy (uderzenie w niego)",
            "Brak pochylenia tułowia (obrońca nie reaguje)",
            "Za wolne odejście po zwodzie"
          ],
          "benefits": [
            "Prosty i niesamowicie skuteczny zwód na każdym poziomie rozgrywek",
            "Łatwe wyjście na pozycję strzelecką"
          ],
          "target_pct": 75,
          "progression_tip": "Wprowadź podwójny balans ciałem (Double Body Feint) przed odejściem.",
          "tags": [
            "balans-cialem",
            "drybling",
            "odejscie",
            "1v1"
          ]
        },
        {
          "id": "fball_drib_003",
          "name": "Kontrola piłki z powietrza (First Touch — różne strefy)",
          "category": "Prowadzenie i zwody",
          "sport": "Piłka nożna",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 6 podań górą (przyjęcie udem, klatką, prostym i wewnętrznym podbiciem)",
          "total_attempts": 24,
          "equipment": [
            "Piłka",
            "Partner narzucający lub ściana odbijająca"
          ],
          "muscles": [
            "przywodziciele",
            "czworogłowe",
            "brzuch",
            "mięśnie stopy"
          ],
          "muscle_group": "czucie, koordynacja, przyjęcie",
          "description": "Amortyzacja opadającej piłki z natychmiastowym jej ukierunkowaniem do przodu w pierwszym kontakcie (tzw. przyjęcie kierunkowe).",
          "courtPosition": "Środek pola gry.",
          "execution": "1. Partner wyrzuca piłkę górą z odległości 15-20 metrów.\n2. Wyjdź na spotkanie z piłką, oceń trajektorię lotu.\n3. W momencie kontaktu z amortyzacją 'zgaś' piłkę stopą, udem lub klatką piersiową.\n4. Piłka po przyjęciu musi spaść nie dalej niż 50 cm od Twojej stopy, gotowa do strzału lub podania.",
          "biomechanics": "Cofnięcie stopy/uda w ułamku sekundy kontaktu (absorpcja energii kinetycznej pocisku). Rozluźnienie mięśni kontaktowych.",
          "commonErrors": [
            "Sztywna noga odbijająca piłkę na kilka metrów jak od ściany",
            "Brak oceny rotacji piłki w powietrzu",
            "Czekanie w miejscu zamiast ataku piłki"
          ],
          "benefits": [
            "Płynność gry i zyskanie 1 sekundy przewagi nad doskakującym rywalem",
            "Fundament nowoczesnego futbolu"
          ],
          "target_pct": 80,
          "progression_tip": "Przyjmuj piłkę z jednoczesnym obrotem o 180° tyłem do kierunku podania.",
          "tags": [
            "first-touch",
            "przyjecie",
            "pilka-z-powietrza"
          ]
        },
        {
          "id": "fball_drib_004",
          "name": "Zwód nożyce (Stepover / Pedały) z przyspieszeniem",
          "category": "Prowadzenie i zwody",
          "sport": "Piłka nożna",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 6 prób na manekinie",
          "total_attempts": 24,
          "equipment": [
            "Piłka",
            "Pachołek lub manekin"
          ],
          "muscles": [
            "przywodziciele",
            "czworogłowe",
            "biodra",
            "łydki"
          ],
          "muscle_group": "zwinność, biodra, oszukanie obrońcy",
          "description": "Przełożenie stopy nad toczącą się piłką od wewnątrz na zewnątrz, imitujące uderzenie lub zmianę kierunku, z wyjściem w drugą stronę.",
          "courtPosition": "Strefa skrzydłowa lub przed polem karnym.",
          "execution": "1. Prowadź piłkę prosto na obrońcę w średnim tempie.\n2. Na 1.5 metra przełóż prawą nogę nad piłką ruchem łukowym od lewej do prawej bez dotykania piłki, obniżając prawe ramię.\n3. Zewnętrzną częścią lewej stopy zabierz piłkę ostro w lewo obok obrońcy.\n4. Zrób 3 wybuchowe kroki przyspieszenia.",
          "biomechanics": "Szerokie zatoczenie koła stopą nad piłką z zamarkowaniem strzału. Obniżenie biodra po stronie zwodu prowokuje reakcję obrońcy.",
          "commonErrors": [
            "Zahaczenie stopą o piłkę podczas przekładania",
            "Brak obniżenia barku",
            "Wykonanie zwodu w miejscu zamiast w ruchu"
          ],
          "benefits": [
            "Kultowy zwód Ronaldo / Cristiano paraliżujący obrońców",
            "Mijanie rywala na pełnej szybkości"
          ],
          "target_pct": 80,
          "progression_tip": "Wykonaj podwójne nożyce (Double Stepover): najpierw prawa noga, potem lewa i wyjście w prawo.",
          "tags": [
            "stepover",
            "nozyce",
            "zwod",
            "drybling"
          ]
        }
      ]
    },
    "Strzały": {
      "emoji": "🎯",
      "label": "Strzały i wykończenie",
      "drills": [
        {
          "id": "fball_strz_001",
          "name": "Strzał prostym podbiciem z 16 metrów w boczne strefy bramki",
          "category": "Strzały",
          "sport": "Piłka nożna",
          "difficulty": "intermediate",
          "duration": "20 min",
          "sets": "4 serie po 5 strzałów (2 serie prawa noga, 2 serie lewa noga)",
          "total_attempts": 20,
          "equipment": [
            "Piłki (min. 5 sztuk)",
            "Pełnowymiarowa bramka z siatką"
          ],
          "muscles": [
            "czworogłowy uda",
            "prosty brzucha",
            "biodrowo-lędźwiowy",
            "pośladki"
          ],
          "muscle_group": "siła nóg, core, precyzja",
          "description": "Mocny, płaski strzał z linii pola karnego zablokowanym stawem skokowym, celowany tuż przy słupkach bramki.",
          "courtPosition": "Linia 16 metrów na wprost i ze skosów bramki.",
          "execution": "1. Wypuść piłkę na 1-2 metry przed siebie po skosie.\n2. Nabieg pod kątem ok. 30°. Stopa postawna ląduje stabilnie 15-20 cm obok piłki, palce skierowane na cel.\n3. Uderz środkiem prostego podbicia (na sznurowadłach), zablokuj staw skokowy.\n4. Przenieś ciężar ciała nad piłkę (klatka pochylona, by piłka nie poszybowała nad poprzeczką).\n5. Kontynuuj ruch nogi uderzającej w kierunku celu.",
          "biomechanics": "Sztywny staw skokowy (maksymalny transfer energii). Pochylenie tułowia nad piłką determinuje niską trajektorię lotu. Ręka przeciwna uniesiona w bok dla balansu.",
          "commonErrors": [
            "Odchylanie tułowia w tył (piłka leci w trybuny)",
            "Stopa postawna za daleko lub za blisko piłki",
            "Luźny staw skokowy przy uderzeniu"
          ],
          "benefits": [
            "Potężna siła uderzenia nie do obrony dla bramkarza",
            "Czysta technika mechaniki strzału"
          ],
          "target_pct": 65,
          "progression_tip": "Celuj wyłącznie w obszar 1 metra od każdego ze słupków (dolne rogi).",
          "tags": [
            "strzaly",
            "proste-podbicie",
            "16m",
            "precyzja"
          ]
        },
        {
          "id": "fball_strz_002",
          "name": "Uderzenie wewnętrzną częścią stopy z rotacją (Rogal w długi róg)",
          "category": "Strzały",
          "sport": "Piłka nożna",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 5 strzałów ze skraju pola karnego",
          "total_attempts": 20,
          "equipment": [
            "Piłki",
            "Bramka"
          ],
          "muscles": [
            "przywodziciele",
            "czworogłowy",
            "biodra"
          ],
          "muscle_group": "staw skokowy, rotacja, technika",
          "description": "Techniczny strzał mierzony wewnętrzną częścią stopy z nadaniem piłce silnej rotacji bocznej, omijającej ręce bramkarza.",
          "courtPosition": "Narożnik pola karnego (lewa strona dla prawonożnego, prawa dla lewonożnego).",
          "execution": "1. Prowadź piłkę ze skrzydła do środka wzdłuż linii 16 metrów.\n2. Stopa postawna ustawiona obok piłki, biodra otwarte ku bramce.\n3. Uderz wewnętrzną częścią stopy, 'zawijając' piłkę po łuku od zewnętrznej strony ku długiemu słupkowi.\n4. Zadbaj o rotację piłki (piłka musi kręcić się wokół własnej osi).",
          "biomechanics": "Efekt Magnusa: różnica ciśnień powietrza wywołana rotacją zakrzywia tor lotu piłki w stronę długiego rogu.",
          "commonErrors": [
            "Zbyt centralne uderzenie (brak rotacji)",
            "Zbyt mała siła strzału (łatwy łup dla bramkarza)",
            "Złe ustawienie stopy postawnej"
          ],
          "benefits": [
            "Zabójcza skuteczność przy zejściu ze skrzydła do środka",
            "Omijanie obrońców blokujących strzał"
          ],
          "target_pct": 70,
          "progression_tip": "Zawieś w górnym rogu bramki znacznik lub małą tarczę i celuj w 'okienko'.",
          "tags": [
            "rogal",
            "rotacja",
            "wewnetrzna-stopa",
            "technika"
          ]
        },
        {
          "id": "fball_strz_003",
          "name": "Strzał z woleja po dośrodkowaniu z bocznego sektora",
          "category": "Strzały",
          "sport": "Piłka nożna",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "4 serie po 5 dośrodkowań (wykończenie z pierwszej piłki)",
          "total_attempts": 20,
          "equipment": [
            "Piłki",
            "Bramka",
            "Partner dośrodkowujący ze skrzydła"
          ],
          "muscles": [
            "całe nogi",
            "brzuch",
            "plecy",
            "koordynacja"
          ],
          "muscle_group": "timing, koordynacja, eksplozywność",
          "description": "Wykończenie akcji uderzeniem z powietrza bez uprzedniego kozła piłki o murawę.",
          "courtPosition": "Strefa 11-13 metrów od bramki po dośrodkowaniu z wysokości pola karnego.",
          "execution": "1. Wbiegaj w pole karne w tempie zgrany z dośrodkowaniem partnera.\n2. Skup wzrok w 100% na opadającej piłce.\n3. Przenieś ciężar ciała na nogę postawną, unoś zgiętą nogę uderzającą równolegle do ziemi.\n4. W momencie kontaktu uderz prostym lub zewnętrznym podbiciem na wysokości biodra/kolana, kierując piłkę w dół ku bramce.",
          "biomechanics": "Prawidłowy timing: kontakt w najwyższym punkcie trajektorii nogi. Tułów pochylony nad piłką, by nie poleciała w górę.",
          "commonErrors": [
            "Zamykanie oczu lub odwracanie głowy przed strzałem",
            "Zbyt wczesny zamach nogą",
            "Odchylenie pleców w tył"
          ],
          "benefits": [
            "Spektakularne bramki meczowe",
            "Najwyższy poziom koordynacji oko-noga"
          ],
          "target_pct": 55,
          "progression_tip": "Wykonaj uderzenie z półwoleja (tuż po koźle piłki od murawy).",
          "tags": [
            "wolej",
            "dosrodkowanie",
            "wykonczenie",
            "timing"
          ]
        }
      ]
    },
    "Podania i gra pozycyjna": {
      "emoji": "🔄",
      "label": "Podania i kontrola tempa",
      "drills": [
        {
          "id": "fball_pod_001",
          "name": "Rondo 4v2 / Dziadek na jeden i dwa kontakty",
          "category": "Podania i gra pozycyjna",
          "sport": "Piłka nożna",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 rundy po 3 minuty z intensywną zmianą obrońców",
          "total_attempts": 12,
          "equipment": [
            "Piłka",
            "4 pachołki wyznaczające kwadrat 8x8m",
            "Oznaczniki"
          ],
          "muscles": [
            "przywodziciele",
            "czworogłowe",
            "łydki",
            "percepcja"
          ],
          "muscle_group": "szybkość myślenia, nogi, zwinność",
          "description": "Sztandarowe ćwiczenie akademii FC Barcelony (La Masia) uczące tworzenia linii podania, gry na 1 kontakt i pressingu.",
          "courtPosition": "Kwadrat 8x8 lub 10x10 metrów w dowolnym miejscu boiska.",
          "execution": "1. 4 zawodników na obwodzie kwadratu utrzymuje posiadanie piłki, 2 zawodników w środku próbuje ją odebrać.\n2. Gra na maksymalnie 2 kontakty (docelowo 1 kontakt).\n3. Zawodnik podający natychmiast przesuwa się wzdłuż linii, by dać partnerowi opcję podania po trójkącie.\n4. Strata piłki lub błąd skutkuje wejściem do środka.",
          "biomechanics": "Otwarta postawa ciała (open body shape) umożliwiająca widzenie całego kwadratu przed przyjęciem piłki.",
          "commonErrors": [
            "Stanie w miejscu po oddaniu podania",
            "Zbyt wolne podania dające obrońcom czas na doskok",
            "Przyjęcie piłki pod siebie zamiast kierunkowego"
          ],
          "benefits": [
            "Błyskawiczny proces podejmowania decyzji (<0.3s)",
            "Precyzja podań pod skrajną presją rywala"
          ],
          "target_pct": 85,
          "progression_tip": "Ogranicz grę ściśle do jednego kontaktu (one-touch) dla wszystkich graczy na obwodzie.",
          "tags": [
            "rondo",
            "la-masia",
            "jeden-kontakt",
            "trojkaty"
          ]
        },
        {
          "id": "fball_pod_002",
          "name": "Przerzut krzyżowy na 30-40 metrów (Cross-field Diagonal)",
          "category": "Podania i gra pozycyjna",
          "sport": "Piłka nożna",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "4 serie po 5 przerzutów z obu nóg",
          "total_attempts": 20,
          "equipment": [
            "Piłki",
            "Partner lub strefa z pachołków 5x5m po przekątnej boiska"
          ],
          "muscles": [
            "czworogłowy",
            "biodrowy",
            "przywodziciele",
            "core"
          ],
          "muscle_group": "siła uderzenia, precyzja daleka, biodro",
          "description": "Długie podanie górą zmieniające ciężar gry na wolne skrzydło z nadaniem piłce odpowiedniej paraboli i rotacji wstecznej.",
          "courtPosition": "Z jednego skrzydła/półprzestrzeni na drugą stronę boiska (dystans 35 metrów).",
          "execution": "1. Podejdź do piłki pod kątem 45°.\n2. Stopa postawna stabilnie z boku, tułów lekko odchylony w bok i w tył.\n3. Uderz dolną część piłki wewnętrzną częścią prostego podbicia, 'podcinając' ją w górę.\n4. Nadaj piłce backspin, by opadając łagodnie zwolniła na nodze partnera.",
          "biomechanics": "Podcięcie piłki poniżej środka ciężkości. Rotacja wsteczna stabilizuje trajektorię lotu na wietrze.",
          "commonErrors": [
            "Uderzenie za wysoko (piłka leci płasko i za nisko)",
            "Zbyt słaby zamach nogi",
            "Brak rotacji wstecznej"
          ],
          "benefits": [
            "Błyskawiczna zmiana strony gry i ominięcie bloku defensywnego rywali"
          ],
          "target_pct": 70,
          "progression_tip": "Partner musi przyjąć piłkę w biegu bez zwalniania kroku.",
          "tags": [
            "przerzut",
            "dlugie-podanie",
            "przekatna",
            "rotacja"
          ]
        }
      ]
    },
    "Motoryka": {
      "emoji": "⚡",
      "label": "Szybkość i motoryka piłkarska",
      "drills": [
        {
          "id": "fball_mot_001",
          "name": "Drabinka koordynacyjna z wyjściem do sprintu i strzału",
          "category": "Motoryka",
          "sport": "Piłka nożna",
          "difficulty": "beginner",
          "duration": "15 min",
          "sets": "6 powtórzeń (różne wzorce kroków: icky shuffle, in-out, dwa do środka)",
          "total_attempts": 6,
          "equipment": [
            "Drabinka zwinnościowa",
            "Piłka",
            "Bramka"
          ],
          "muscles": [
            "łydki",
            "czworogłowe",
            "biodra",
            "reakcja nerwowa"
          ],
          "muscle_group": "szybkość stóp, przyspieszenie, koordynacja",
          "description": "Praca nad częstotliwością pracy stóp na drabince połączona z natychmiastowym przejściem do sprintu 10m i uderzenia na bramkę.",
          "courtPosition": "Odcinek przed polem karnym.",
          "execution": "1. Pokonaj drabinkę maksymalną częstotliwością kroków na palcach (np. Icky Shuffle).\n2. Na ostatnim szczeblu wykonaj eksplozywne wyjście z niskich nóg w sprint 10m.\n3. Dopadnij do piłki toczącej się przed bramką i oddaj strzał w pełnym biegu.",
          "biomechanics": "Praca na przodostopiu (krótki czas kontaktu z podłożem <0.15s). Płynne przejście z ruchów koordynacyjnych do biegu sprinterskiego.",
          "commonErrors": [
            "Haczenie stopami o szczeble drabinki",
            "Wzrok w dół zamiast przed siebie",
            "Zwalnianie przed samym strzałem"
          ],
          "benefits": [
            "Błyskawiczne 'szybkie stopy' w polu karnym",
            "Poprawa dynamiki pierwszych 3 kroków"
          ],
          "target_pct": 90,
          "progression_tip": "Trener rzuca piłkę w nieprzewidywalną stronę w momencie wyjścia z drabinki.",
          "tags": [
            "drabinka",
            "szybkosc",
            "motoryka",
            "sprint"
          ]
        },
        {
          "id": "fball_mot_002",
          "name": "Sprint wahadłowy (Shuttle Run 5-10-15m) z piłką",
          "category": "Motoryka",
          "sport": "Piłka nożna",
          "difficulty": "intermediate",
          "duration": "12 min",
          "sets": "4 serie z przerwą 90 sekund (pełna regeneracja fosfagenowa)",
          "total_attempts": 4,
          "equipment": [
            "3 pachołki na dystansach 5m, 10m, 15m",
            "Piłka"
          ],
          "muscles": [
            "czworogłowe",
            "dwugłowe",
            "pośladki",
            "łydki"
          ],
          "muscle_group": "wytrzymałość beztlenowa, hamowanie, zwrotność",
          "description": "Maksymalny test zwrotności piłkarskiej (Agility) z nawrotami o 180° i kontrolą futbolówki.",
          "courtPosition": "Długość 15 metrów na murawie.",
          "execution": "1. Start ze stacji 0: sprint z piłką do 5m, zwrot o 180° i powrót na start.\n2. Bez zatrzymania sprint do 10m, zwrot i powrót.\n3. Sprint do 15m i powrót na linię startu z maksymalną prędkością.",
          "biomechanics": "Głębokie hamowanie ekscentryczne mięśniem czworogłowym przed nawrotem. Obniżenie środka ciężkości i dotknięcie dłonią linii nawrotu.",
          "commonErrors": [
            "Zbyt szerokie łuki przy nawrotach zamiast ostrego pivotu",
            "Utrata kontroli nad piłką w nawrocie",
            "Odpuszczanie na ostatnich 5 metrach"
          ],
          "benefits": [
            "Budowa specyficznej wydolności interwałowej meczu piłkarskiego",
            "Moc hamowania ekscentrycznego"
          ],
          "target_pct": 85,
          "progression_tip": "Zmierz czas całkowity testu. Cel: poniżej 16.5 sekundy.",
          "tags": [
            "wahadlo",
            "zwrotnosc",
            "interwal",
            "hamowanie"
          ]
        }
      ]
    }
  },
  "tenis": {
    "emoji": "🎾",
    "Forehand i Backhand": {
      "emoji": "🎾",
      "label": "Uderzenia z głębi kortu",
      "drills": [
        {
          "id": "tenis_fh_001",
          "name": "Forehand Crosscourt po koźle w strefę głęboką (20 uderzeń)",
          "category": "Forehand i Backhand",
          "sport": "Tenis",
          "difficulty": "intermediate",
          "duration": "20 min",
          "sets": "4 serie po 20 uderzeń ze strefy końcowej",
          "total_attempts": 80,
          "equipment": [
            "Rakieta tenisowa",
            "Piłki tenisowe (koszyk)",
            "Stożki oznaczające strefę docelową"
          ],
          "muscles": [
            "rotatory tułowia",
            "naramienny",
            "przedramię",
            "pośladki"
          ],
          "muscle_group": "rotacja tułowia, barki, praca nóg",
          "description": "Podstawowe uderzenie konstrukcyjne w tenisie: mocny, bezpieczny topspin po przekątnej lądujący w głębokim metrze kortu rywala.",
          "courtPosition": "Za linią końcową (baseline) po prawej stronie (dla praworęcznego).",
          "execution": "1. Pozycja wyjściowa (split-step) w momencie uderzenia piłki przez partnera/maszynę.\n2. Wczesny skręt barków (unit turn) z odprowadzeniem rakiety w pętli (loop).\n3. Praca nóg: postawa półotwarta (semi-open stance). Opadnięcie główki rakiety poniżej poziomu piłki.\n4. Uderzenie z dołu do góry z nadaniem rotacji awansującej (topspin). Wykończenie nad lewym barkiem (windshield wiper).",
          "biomechanics": "Kinetic chain: siła generowana ze skrętnego odepchnięcia prawej nogi, przenoszona przez rotację bioder i klatki na ramię i nadgarstek.",
          "commonErrors": [
            "Uderzenie samą ręką bez rotacji tułowia",
            "Spóźniony zamach rakiety",
            "Płaska trajektoria bez marginesu bezpieczeństwa nad siatką"
          ],
          "benefits": [
            "Bezpieczna regularność wymian z głębi kortu",
            "Spychanie rywala głęboką piłką za linię końcową"
          ],
          "target_pct": 70,
          "progression_tip": "Umieść cel 1 metr przed linią końcową rywala — piłka musi lądować w wyznaczonym korytarzu.",
          "tags": [
            "forehand",
            "topspin",
            "crosscourt",
            "regularnosc"
          ]
        },
        {
          "id": "tenis_bh_001",
          "name": "Backhand po linii (Down-the-line — oburęczny lub jednoręczny)",
          "category": "Forehand i Backhand",
          "sport": "Tenis",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "4 serie po 15 uderzeń po linii",
          "total_attempts": 60,
          "equipment": [
            "Rakieta",
            "Piłki"
          ],
          "muscles": [
            "najszerszy grzbietu",
            "core",
            "przedramiona",
            "czworogłowe"
          ],
          "muscle_group": "plecy, ramiona, koordynacja",
          "description": "Uderzenie zmieniające kierunek wymiany z przekątnej na linię boczną — uderzenie kończące punkt lub otwierające kort.",
          "courtPosition": "Lewy narożnik kortu za linią końcową.",
          "execution": "1. Split-step, szybki zwrot barków bokiem do siatki (closed/neutral stance).\n2. Punkt kontaktu wysunięty mocno przed ciało (zwłaszcza przy jednoręcznym backhandzie).\n3. Prowadzenie rakiety wzdłuż linii bocznej z pełnym wyprostem ramion i uniesieniem tułowia w górę.",
          "biomechanics": "Wczesny kontakt przed przednim kolanem. Ręka niedominująca (przy oburęcznym) wykonuje 70% pracy napędowej jak leworęczny forehand.",
          "commonErrors": [
            "Spóźniony punkt kontaktu (piłka trafiona za linią bioder)",
            "Otwieranie barków zbyt wcześnie",
            "Uderzenie w siatkę (nad siatką piłka musi przejść min. 50 cm wyżej niż przy linii)"
          ],
          "benefits": [
            "Element zaskoczenia rywala",
            "Otwarcie wolnej przestrzeni na korcie"
          ],
          "target_pct": 65,
          "progression_tip": "Ćwicz po uprzednim odegraniu krótkiego crossa przez partnera.",
          "tags": [
            "backhand",
            "po-linii",
            "atak",
            "precision"
          ]
        },
        {
          "id": "tenis_fh_002",
          "name": "Forehand Inside-Out z obejściem piłki na stronę lewą",
          "category": "Forehand i Backhand",
          "sport": "Tenis",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "3 serie po 15 powtórzeń",
          "total_attempts": 45,
          "equipment": [
            "Rakieta",
            "Piłki"
          ],
          "muscles": [
            "pośladki",
            "łydki",
            "core",
            "barki"
          ],
          "muscle_group": "praca nóg, szybkość, rotacja",
          "description": "Obejście piłki lecącej na backhand i zagranie agresywnego forehandu po krosie w stronę backhandu rywala.",
          "courtPosition": "Środek i lewa strona kortu.",
          "execution": "1. Rozpoznaj wolniejszą piłkę lecącą na stronę backhandową.\n2. Wykonaj szybkie kroki odstawne w tył i w lewo wokół piłki (dropper footwork).\n3. Ustaw się w postawie otwartej (open stance) i uderz mocny forehand po przekątnej w prawy róg rywala.",
          "biomechanics": "Wymaga doskonałej pracy nóg po łuku. Załadunek ciężaru ciała na prawą nogę i eksplozywny obrót miednicy.",
          "commonErrors": [
            "Zbyt wolne obejście piłki i uderzenie w ciasnej pozycji",
            "Brak równowagi przy uderzeniu",
            "Uderzenie w aut na szerokość"
          ],
          "benefits": [
            "Wykorzystanie najsilniejszej broni (forehandu) na 80% powierzchni kortu"
          ],
          "target_pct": 65,
          "progression_tip": "Zmieniaj kierunek: 2 uderzenia Inside-Out, 1 uderzenie Inside-In (po linii).",
          "tags": [
            "inside-out",
            "obejscie",
            "agresja",
            "forehand"
          ]
        },
        {
          "id": "tenis_fh_003",
          "name": "Skrót z rotacją wsteczną (Drop Shot) z głębi kortu",
          "category": "Forehand i Backhand",
          "sport": "Tenis",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "4 serie po 10 skrótów z imitacji mocnego forehandu",
          "total_attempts": 40,
          "equipment": [
            "Rakieta",
            "Piłki"
          ],
          "muscles": [
            "przedramię",
            "palce",
            "nadgarstek",
            "czucie"
          ],
          "muscle_group": "czucie dłoni, maskowanie, miękkość",
          "description": "Zabójczo zamaskowane uderzenie: pełen zamach sugerujący mocny topspin z nagłym otwarciem rakiety i miękkim podcięciem piłki tuż za siatkę.",
          "courtPosition": "Środek kortu (strefa no man's land) lub tuż za linią końcową.",
          "execution": "1. Wykonaj pełny zamach do forehandu, by rywal cofnął się w obronie.\n2. W ostatniej chwili przed kontaktem otwórz płaszczyznę strun rakiety.\n3. Muśnij piłkę od spodu z ruchem do przodu i w dół, nadając potężny backspin (rotację wsteczną).\n4. Piłka po przejściu tuż nad taśmą siatki powinna mieć minimalny odbicie (zgasnąć w korcie).",
          "biomechanics": "Maksymalne rozluźnienie nadgarstka i dłoni w momencie kontaktu (chwyt na skali 2/10). Amortyzacja prędkości piłki rywala.",
          "commonErrors": [
            "Zbyt wczesne pokazanie zamiaru skrótu (rywal już biegnie do siatki)",
            "Zbyt sztywna ręka (piłka odbija się wysoko)",
            "Uderzenie w siatkę"
          ],
          "benefits": [
            "Zdobywanie punktów bez wysiłku z cofniętym rywalem",
            "Złamanie rytmu gry przeciwnika"
          ],
          "target_pct": 65,
          "progression_tip": "Piłka po koźle nie może odbić się wyżej niż do wysokości kolan.",
          "tags": [
            "skrot",
            "drop-shot",
            "maskowanie",
            "backspin"
          ]
        }
      ]
    },
    "Serwis i Return": {
      "emoji": "⚡",
      "label": "Serwis i Return",
      "drills": [
        {
          "id": "tenis_srv_001",
          "name": "Precyzja serwisu w strefę T oraz do narożnika (Wide)",
          "category": "Serwis i Return",
          "sport": "Tenis",
          "difficulty": "intermediate",
          "duration": "20 min",
          "sets": "4 serie po 12 serwisów (po 6 na stronę przewagi i równowagi)",
          "total_attempts": 48,
          "equipment": [
            "Rakieta",
            "Piłki (koszyk)",
            "Pachołki w rogach karo serwisowego"
          ],
          "muscles": [
            "stożek rotatorów",
            "triceps",
            "najszerszy grzbietu",
            "łydki",
            "brzuch"
          ],
          "muscle_group": "barki, wyskok, łydki, koordynacja",
          "description": "Najważniejsze uderzenie w tenisie rozpoczynające każdy punkt — trening celności pierwszego i drugiego serwisu.",
          "courtPosition": "Linia końcowa, strefa środkowa (obok znacznika środka).",
          "execution": "1. Ustawienie stóp pod kątem 45° do linii końcowej, chwyt kontynentalny (młotkowy).\n2. Płynny, stabilny wyrzut piłki (toss) lekko przed sobą na wysokość wyciągniętej rakiety.\n3. Ugięcie kolan w pozycji 'trophy pose', opadnięcie rakiety za plecy (drapanie po plecach).\n4. Wyszarpnięcie w górę, pronacja nadgarstka i przedramienia w punkcie kontaktu w najwyższym punkcie.\n5. Lądowanie na nodze wykrocznej wewnątrz kortu.",
          "biomechanics": "Pronacja przedramienia w ułamku sekundy przed uderzeniem odpowiada za prędkość i rotację. Płynny ruch wahadłowy bez zatrzymywania rakiety.",
          "commonErrors": [
            "Chwyt forehandowy (tzw. patelnia) zamiast kontynentalnego",
            "Niestabilny wyrzut piłki w różne strony",
            "Brak ugięcia kolan i brak wyskoku"
          ],
          "benefits": [
            "Darmowe punkty z asów i serwisów wygrywających",
            "Dyktowanie warunków od pierwszej piłki"
          ],
          "target_pct": 65,
          "progression_tip": "Po 24 płaskich pierwszych serwisach wykonaj 24 drugie serwisy z rotacją awansującą (Kick Serve).",
          "tags": [
            "serwis",
            "as",
            "karo",
            "pronacja"
          ]
        },
        {
          "id": "tenis_ret_001",
          "name": "Blokowany Return z szybkiego pierwszego serwisu",
          "category": "Serwis i Return",
          "sport": "Tenis",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 8 returnów z serwisu partnera",
          "total_attempts": 32,
          "equipment": [
            "Rakieta",
            "Piłki",
            "Partner serwujący z pełną siłą"
          ],
          "muscles": [
            "przedramiona",
            "czworogłowe",
            "barki",
            "czas reakcji"
          ],
          "muscle_group": "refleks, przedramiona, stabilność",
          "description": "Kompaktowy, skrócony zamach wykorzystujący prędkość piłki rywala do natychmiastowego odegrania głęboko pod linię końcową.",
          "courtPosition": "1 metr za linią końcową po stronie karo serwisowego.",
          "execution": "1. Naskok (split-step) dokładnie w ułamku sekundy, gdy rakieta serwującego uderza w piłkę.\n2. Bardzo krótki zamach — sam skręt tułowia bez odprowadzania rakiety daleko w tył.\n3. Zablokowanie nadgarstka i pchnięcie piłki z przodu przed sobą w środek kortu lub pod nogi wbiegającego rywala.",
          "biomechanics": "Użycie pędu piłki nadchodzącej (brak potrzeby generowania własnej siły zamachem). Sztywna dźwignia przedramię-rakieta.",
          "commonErrors": [
            "Zbyt długi zamach z głębi kortu (spóźnienie na szybki serwis)",
            "Brak split-stepu (brak czasu na reakcję)",
            "Luźny nadgarstek przy kontakcie"
          ],
          "benefits": [
            "Neutralizacja najgroźniejszej broni rywala",
            "Natychmiastowe wejście w wymianę"
          ],
          "target_pct": 70,
          "progression_tip": "Celuj returnem w wyznaczony kwadrat o wymiarach 2x2m na środku linii końcowej.",
          "tags": [
            "return",
            "blok",
            "refleks",
            "split-step"
          ]
        },
        {
          "id": "tenis_srv_002",
          "name": "Slice Serve (Serwis rotacyjny wyrzucający rywala z kortu)",
          "category": "Serwis i Return",
          "sport": "Tenis",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "3 serie po 10 serwisów ze strefy deuce (przewagi)",
          "total_attempts": 30,
          "equipment": [
            "Rakieta",
            "Piłki"
          ],
          "muscles": [
            "stożek rotatorów",
            "przedramię",
            "skośne brzucha"
          ],
          "muscle_group": "rotacja boczna, barki, precyzja",
          "description": "Serwis z silną rotacją boczną, który po koźle ucieka gwałtownie w bok, otwierając cały kort do skończenia piłki.",
          "courtPosition": "Prawa strona linii końcowej (karo przewagi).",
          "execution": "1. Wyrzut piłki nieco bardziej w prawo niż przy serwisie płaskim (na godzinę 1:00).\n2. Omiataj piłkę rakietą po jej prawej zewnętrznej stronie (szczotkowanie od zewnątrz do środka).\n3. Po koźle piłka ucieka nisko w stronę trybun bocznych.",
          "biomechanics": "Kąt natarcia strun 30-45° względem toru lotu piłki nadaje prędkość kątową boczną.",
          "commonErrors": [
            "Wyrzucenie piłki za bardzo za głowę",
            "Płaskie uderzenie bez nadania cięcia",
            "Brak wykończenia po lewej stronie tułowia"
          ],
          "benefits": [
            "Całkowite wyrzucenie rywala poza korytarz deblowy",
            "Łatwy wolej kończący w pusty kort"
          ],
          "target_pct": 65,
          "progression_tip": "Połącz z natychmiastowym wbiegnięciem do siatki na wolej (Serve and Volley).",
          "tags": [
            "slice-serve",
            "rotacja-boczna",
            "otwarcie-kortu"
          ]
        }
      ]
    },
    "Wolej i praca przy siatce": {
      "emoji": "🕸️",
      "label": "Gra przy siatce",
      "drills": [
        {
          "id": "tenis_vol_001",
          "name": "Wolej Forehandowy i Backhandowy w seriach szybkiej reakcji",
          "category": "Wolej i praca przy siatce",
          "sport": "Tenis",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 16 wolejów naprzemiennych z partnerem z głębi kortu",
          "total_attempts": 64,
          "equipment": [
            "Rakieta",
            "Piłki",
            "Partner grający mocne piłki z linii końcowej"
          ],
          "muscles": [
            "przedramiona",
            "naramienne",
            "czworogłowe",
            "łydki"
          ],
          "muscle_group": "refleks, ramiona, stabilność nóg",
          "description": "Gra bez koźla przy siatce: krótki ruch pchnięcia (punch volley) zablokowanym nadgarstkiem i aktywnym krokiem w przód.",
          "courtPosition": "Strefa 2-3 metry od siatki w środkowej części kortu.",
          "execution": "1. Pozycja gotowości z rakietą uniesioną wysoko przed klatką piersiową, chwyt kontynentalny.\n2. Wykonaj split-step w momencie uderzenia piłki przez partnera.\n3. Zero zamachu w tył! Wykonaj krótki krok nogą przeciwną w stronę piłki (lewa noga dla woleja forehandowego) i zablokuj główkę rakiety pod kątem lekko otwartym.\n4. 'Przebij' piłkę krótkim ruchem do przodu w dół.",
          "biomechanics": "Brak zamachu wstecznego. Sztywny nadgarstek (kąt 90° między przedramieniem a trzonkiem rakiety).",
          "commonErrors": [
            "Wykonywanie zamachu jak do uderzenia z głębi kortu",
            "Opadanie główki rakiety poniżej nadgarstka",
            "Stanie na prostych nogach w bezruchu"
          ],
          "benefits": [
            "Błyskawiczne kończenie wymian przy siatce",
            "Pewność gry w deblu"
          ],
          "target_pct": 75,
          "progression_tip": "Graj na przemian wolej głęboki i skrót tuż za siatkę (drop volley).",
          "tags": [
            "wolej",
            "punch",
            "siatka",
            "chwyt-kontynentalny"
          ]
        },
        {
          "id": "tenis_vol_002",
          "name": "Smash (Smecz znad głowy) po lobie rywala",
          "category": "Wolej i praca przy siatce",
          "sport": "Tenis",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 6 smeczów z cofaniem się",
          "total_attempts": 24,
          "equipment": [
            "Rakieta",
            "Piłki",
            "Partner grający wysokie l資源 (loby)"
          ],
          "muscles": [
            "łydki",
            "brzuch",
            "triceps",
            "barki"
          ],
          "muscle_group": "skoczność, ramiona, koordynacja wzrokowa",
          "description": "Agresywne uderzenie kończące wysoką piłkę rywala ruchem przypominającym serwis w wyskoku.",
          "courtPosition": "Strefa 3-5 metrów od siatki z wycofaniem krokami dostawnymi.",
          "execution": "1. Gdy rywal gra loba, natychmiast obróć się bokiem do siatki.\n2. Wycofuj się krokami krzyżowymi/odstawnymi w tył, wskazując piłkę palcem lewej ręki uniesionej w górę.\n3. Rakieta w pozycji za głową (jak do serwisu).\n4. Wybij się w górę i uderz piłkę w najwyższym punkcie przed sobą, wbijając ją mocno w kort przeciwnika.",
          "biomechanics": "Lewa ręka śledzi piłkę i stabilizuje pozycję barków. Uderzenie przed głową, nigdy za plecami.",
          "commonErrors": [
            "Wycofywanie się tyłem na prostych nogach (zagrożenie upadkiem)",
            "Uderzenie za plecami z utratą siły",
            "Brak skrętu bokiem"
          ],
          "benefits": [
            "100% punktów wygranych z nieudanych lobów rywala"
          ],
          "target_pct": 80,
          "progression_tip": "Wykonaj smecz z wyskoku nożycowego (scissor kick) przy głębokim lobie.",
          "tags": [
            "smash",
            "smecz",
            "lob",
            "zabojcza-skutecznosc"
          ]
        },
        {
          "id": "tenis_vol_003",
          "name": "Praca nóg na linii końcowej — ósemki wokół pachołków",
          "category": "Wolej i praca przy siatce",
          "sport": "Tenis",
          "difficulty": "beginner",
          "duration": "10 min",
          "sets": "5 serii po 45 sekund z maksymalną intensywnością",
          "total_attempts": 5,
          "equipment": [
            "2 pachołki rozstawione na 3 metry",
            "Stoper"
          ],
          "muscles": [
            "łydki",
            "czworogłowe",
            "pośladki",
            "biodra"
          ],
          "muscle_group": "szybkość stóp, koordynacja, wytrzymałość",
          "description": "Trening poruszania się specyficznego dla tenisa ziemnego (drobne kroczki regeneracyjne i naskoki).",
          "courtPosition": "Środek linii końcowej.",
          "execution": "1. Biegaj po torze ósemki wokół dwóch pachołków bez obracania tułowia plecami do siatki.\n2. Przy każdym nawrocie wykonaj markowany ruch forehandu lub backhandu na ugiętych nogach.\n3. Utrzymuj nieustanny rytm drobnych kroków na przedniej części stóp.",
          "biomechanics": "Brak kontaktu pięty z podłożem podczas przyspieszania. Ciągła gotowość do zmiany kierunku.",
          "commonErrors": [
            "Krzyżowanie nóg w niebezpieczny sposób",
            "Wstawanie z pozycji niskiej",
            "Zwalnianie za pachołkiem"
          ],
          "benefits": [
            "Brak spóźnień do uderzeń w 3. secie meczu"
          ],
          "target_pct": 90,
          "progression_tip": "Trener pokazuje kolory stożków, wymuszając natychmiastową zmianę kierunku obrotu.",
          "tags": [
            "praca-nog",
            "footwork",
            "osemka",
            "kondycja"
          ]
        }
      ]
    }
  },
  "boks": {
    "emoji": "🥊",
    "Podstawy i ciosy proste": {
      "emoji": "👊",
      "label": "Ciosy proste i poruszanie",
      "drills": [
        {
          "id": "box_jab_001",
          "name": "Jab (Lewy prosty) z krokiem w przód i powrotem do gardy",
          "category": "Podstawy i ciosy proste",
          "sport": "Boks",
          "difficulty": "beginner",
          "duration": "15 min",
          "sets": "3 rundy po 3 minuty (przerwa 60 sek)",
          "total_attempts": 150,
          "equipment": [
            "Bandaże bokserskie",
            "Rękawice bokserskie",
            "Lustro treningowe"
          ],
          "muscles": [
            "naramienny",
            "triceps",
            "łydki",
            "core",
            "zębaty przedni"
          ],
          "muscle_group": "ramiona, barki, szybkość wyprowadzenia",
          "description": "Najważniejszy cios w boksie. Służy do mierzenia dystansu, rozbijania gardy, przygotowania ataku i powstrzymywania naporu rywala.",
          "courtPosition": "Pozycja bokserska (stójka) przed lustrem lub na środku ringu.",
          "execution": "1. Przyjmij prawidłową pozycję bokserską: lewy bark i lewa noga z przodu, broda schowana przy obojczyku, prawa ręka przyklejona do szczęki.\n2. Wyprowadź lewy prosty ruchem rotacyjnym przedramienia, jednocześnie wykonując krótki krok przednią nogą (5-10 cm).\n3. W momencie trafienia zaciśnij pięść, obróć nadgarstek (kostki palców poziomo), lewy bark uniesiony osłania podbródek od lewej strony.\n4. Błyskawicznie cofnij rękę tą samą drogą do gardy, dostawiając tylną nogę.",
          "biomechanics": "Cios wyprowadzany ze skrętu stopy i biodra. Zasada prostej linii (nie opuszczaj ręki przed zadaniem ciosu — zero telegrafowania).",
          "commonErrors": [
            "Opuszczanie prawej ręki podczas bicia lewą (odsłonięcie szczęki)",
            "Telegrafowanie ciosu przez cofnięcie łokcia w tył przed wyprowadzeniem",
            "Brak rotacji dłoni w ostatniej fazie",
            "Pozostawianie ręki w celu po uderzeniu"
          ],
          "benefits": [
            "Kontrola dystansu w walce",
            "Podstawa 90% skutecznych kombinacji"
          ],
          "target_pct": 90,
          "progression_tip": "Wykonaj podwójny jab (1-1) ze zmianą poziomu (dół na tułów, góra na szczękę).",
          "tags": [
            "jab",
            "lewy-prosty",
            "garda",
            "fundament"
          ]
        },
        {
          "id": "box_jab_002",
          "name": "Kombinacja 1-2 (Lewy prosty + Prawy prosty Cross)",
          "category": "Podstawy i ciosy proste",
          "sport": "Boks",
          "difficulty": "beginner",
          "duration": "15 min",
          "sets": "3 rundy po 3 minuty na ciężkim worku bokserskim",
          "total_attempts": 100,
          "equipment": [
            "Rękawice bokserskie",
            "Ciężki worek bokserski",
            "Bandaże"
          ],
          "muscles": [
            "pośladki",
            "skośne brzucha",
            "naramienne",
            "triceps",
            "łydki"
          ],
          "muscle_group": "pełny łańcuch kinematyczny, rotacja, siła",
          "description": "Klasyczna, najbardziej nokautująca kombinacja podstawowa boksu. Jab oślepia rywala, prawy krzyżowy (cross) niesie pełną masę ciała.",
          "courtPosition": "Dystans wyciągniętej ręki od worka bokserskiego.",
          "execution": "1. Wyprowadź dynamiczny lewy prosty (1).\n2. Gdy lewa ręka wraca do ochrony podbródka, zainicjuj prawy prosty (2) z obrotu prawej stopy i prawego biodra.\n3. Pchnij prawe ramię prosto w cel, obracając tułów pod kątem 45°.\n4. Głowa pozostaje w osi pionowej, lewa ręka szczelnie chroni lewą stronę szczęki.\n5. Po uderzeniu natychmiast wróć do neutralnej pozycji obronnej.",
          "biomechanics": "Prawdziwa siła prawego prostego pochodzi z obrotu prawej pięty na zewnątrz i dynamicznego wyprostu prawego biodra.",
          "commonErrors": [
            "Wyprowadzanie prawego prostego z opuszczoną lewą ręką",
            "Brak skrętu tylnej stopy (cios bity z samego ramienia bez siły)",
            "Wpadanie na worek z utratą równowagi"
          ],
          "benefits": [
            "Budowa potężnej siły nokautującej",
            "Płynne łączenie ciosów w sekwencje"
          ],
          "target_pct": 85,
          "progression_tip": "Dodaj po kombinacji natychmiastowe odejście pod kątem 45° (pivot na lewej nodze).",
          "tags": [
            "1-2",
            "kombinacja",
            "cross",
            "nokaut"
          ]
        },
        {
          "id": "box_jab_003",
          "name": "Kroki bokserskie (Footwork: Step-slide i Pivot o 90°)",
          "category": "Podstawy i ciosy proste",
          "sport": "Boks",
          "difficulty": "beginner",
          "duration": "12 min",
          "sets": "3 rundy po 3 minuty poruszania się w kwadracie i pivotów",
          "total_attempts": 3,
          "equipment": [
            "Lustro",
            "Taśmy na podłodze wyznaczające linie"
          ],
          "muscles": [
            "łydki",
            "czworogłowe",
            "stawy skokowe"
          ],
          "muscle_group": "lekkość stóp, balans, unikanie ciosów",
          "description": "W boksie ciosy zadają ręce, ale wygrywają nogi. Nauka poruszania się w 4 kierunkach bez utraty stabilnej bazy.",
          "courtPosition": "Pusta przestrzeń ringu.",
          "execution": "1. Ruch w przód zaczynasz ZAWSZE od przedniej nogi, tylna dostawia.\n2. Ruch w tył zaczynasz od tylnej nogi, przednia dostawia.\n3. Ruch w lewo od lewej nogi, ruch w prawo od prawej nogi.\n4. PIVOT: Przenieś ciężar na przednią stopę i zakręć tylną nogą o 90° w bok, schodząc z linii ciosu nacierającego rywala.",
          "biomechanics": "Nigdy nie łącz stóp (odstęp min. szerokości barków). Ciężar ciała rozłożony 50/50 na przednich częściach stóp.",
          "commonErrors": [
            "Krzyżowanie stóp (jeden cios przewraca)",
            "Ciężkie stąpanie na piętach zamiast sprężystych kroków",
            "Wstawanie z pozycji bokserskiej"
          ],
          "benefits": [
            "Niewidzialność dla rywala w ringu",
            "Zawsze w pozycji gotowej do ataku i obrony"
          ],
          "target_pct": 90,
          "progression_tip": "Zadawaj jaba w trakcie każdego kroku w przód i w tył.",
          "tags": [
            "footwork",
            "kroki",
            "pivot",
            "balans"
          ]
        }
      ]
    },
    "Ciosy sierpowe i z dołu": {
      "emoji": "💥",
      "label": "Haki i podbródkowe",
      "drills": [
        {
          "id": "box_hook_001",
          "name": "Lewy sierp na głowę (Lead Hook) z transferem ciężaru",
          "category": "Ciosy sierpowe i z dołu",
          "sport": "Boks",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 20 powtórzeń na tarczy lub worku",
          "total_attempts": 80,
          "equipment": [
            "Rękawice",
            "Worek bokserski lub tarcze trenerskie"
          ],
          "muscles": [
            "skośne brzucha",
            "piersiowy",
            "naramienny",
            "biodro"
          ],
          "muscle_group": "rotacja korpusu, eksplozywność, klatka",
          "description": "Jeden z najgroźniejszych ciosów w historii boksu. Uderzenie po poziomym łuku z potężną rotacją bioder.",
          "courtPosition": "Półdystans od celu.",
          "execution": "1. Z pozycji bokserskiej przenieś lekko ciężar na przednią nogę (załadowanie biodra).\n2. Unieś lewy łokieć do poziomu barku (kąt 90° w stawie łokciowym).\n3. Skręć lewą stopę, lewe kolano i biodro dynamicznie w prawo, jakbyś gasił papierosa butem na podłodze.\n4. Cios uderza z boku w szczękę lub ucho. Prawa ręka przyklejona do brody.\n5. Zatrzymaj cios na środku linii celu — nie przestrzeliwuj w próżnię.",
          "biomechanics": "Ramię tworzy sztywną 'ramę' o kącie 90°. Całą siłę uderzenia generuje gwałtowne zahamowanie obrotu bioder.",
          "commonErrors": [
            "Zbyt szeroki zamach zza pleców (telegrafowanie)",
            "Opadanie łokcia poniżej poziomu pięści",
            "Opuszczanie prawej ręki z gardy"
          ],
          "benefits": [
            "Cios niewidoczny poza linią wzroku rywala",
            "Potęga nokautująca w półdystansie"
          ],
          "target_pct": 80,
          "progression_tip": "Połącz lewy sierp na dół (wątroba) z natychmiastowym lewym sierpem na górę (szczęka).",
          "tags": [
            "sierp",
            "hook",
            "rotacja-biodra",
            "pol-dystans"
          ]
        },
        {
          "id": "box_hook_002",
          "name": "Hak na wątrobę (Liver Punch) z obniżeniem pozycji",
          "category": "Ciosy sierpowe i z dołu",
          "sport": "Boks",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "3 rundy po 3 minuty na worku z akcentem na dolny lewy sektor",
          "total_attempts": 60,
          "equipment": [
            "Rękawice",
            "Worek bokserski"
          ],
          "muscles": [
            "skośne brzucha",
            "najszerszy grzbietu",
            "czworogłowy"
          ],
          "muscle_group": "tułów, biodro, precyzja kątowa",
          "description": "Cios kończący walkę paraliżującym bólem układu nerwowego. Uderzenie pod kątem 45° pod prawe żebra rywala.",
          "courtPosition": "Bliski półdystans.",
          "execution": "1. Zejdź lekko na nogach w lewo pod ciosem rywala (slip w lewo).\n2. Skręć biodro i wbij lewą pięść pod kątem 45° od dołu do góry w prawy bok tułowia rywala (pod łokieć).\n3. Dłoń ustawiona w pół-supinacji (kciuk w górę lub na zewnątrz).\n4. Natychmiast wróć do wysokiej gardy.",
          "biomechanics": "Wektor siły skierowany pod kątem 45° w górę w kierunku prawego barku rywala, penetrujący narząd wątroby.",
          "commonErrors": [
            "Płaski cios w brzuch zamiast podcięcia pod żebra pod kątem 45°",
            "Pochylanie głowy w dół przy zejściu",
            "Brak osłony prawej strony twarzy"
          ],
          "benefits": [
            "Paraliż przepony i nóg rywala",
            "Skuteczne przełamanie twardych przeciwników"
          ],
          "target_pct": 75,
          "progression_tip": "Zadawaj po zamarkowaniu prawego prostego na górę (feint cross -> liver shot).",
          "tags": [
            "watroba",
            "hak",
            "liver-shot",
            "paraliz"
          ]
        },
        {
          "id": "box_hook_003",
          "name": "Prawy podbródkowy (Rear Uppercut) z defensywnym balansem",
          "category": "Ciosy sierpowe i z dołu",
          "sport": "Boks",
          "difficulty": "intermediate",
          "duration": "12 min",
          "sets": "4 serie po 15 uderzeń na tarczy lub worku podbródkowym",
          "total_attempts": 60,
          "equipment": [
            "Rękawice",
            "Tarcze profilowane do podbródkowych"
          ],
          "muscles": [
            "biceps",
            "czworogłowy",
            "pośladki",
            "przedni bark"
          ],
          "muscle_group": "nogi, biceps, eksplozywność pionowa",
          "description": "Cios bity pionowo od dołu rozbijający podwójną gardę i unoszący głowę pochylającego się przeciwnika.",
          "courtPosition": "Dystans zwarty (w klinczu lub półdystansie).",
          "execution": "1. Ugnij prawe kolano, obniżając prawe ramię dosłownie o 10 cm (nie opuszczaj ręki do pasa!).\n2. Eksploduj z prawej nogi w górę, wbijając pięść pionowo między rękawice rywala w podbródek.\n3. Dłoń skierowana wnętrzem do Twojej twarzy (pełna supinacja).\n4. Lewa ręka zabetonowana przy lewym policzku.",
          "biomechanics": "Siła ciosu pochodzi z wyprostu nóg w pionie, a nie z machnięcia ramieniem z dołu.",
          "commonErrors": [
            "Opuszczanie ręki poniżej pasa przed ciosem (widoczne z kilometra)",
            "Odchylanie głowy w tył podczas uderzania",
            "Brak wyprostu z nóg"
          ],
          "benefits": [
            "Idealna odpowiedź na rywala nurkującego nisko głową",
            "Otwarcie gardy pod lewy sierp"
          ],
          "target_pct": 80,
          "progression_tip": "Połącz w mordercze kombo: Prawy podbródkowy + Lewy sierp na szczękę (Uppercut-Hook).",
          "tags": [
            "uppercut",
            "podbrodkowy",
            "rozbicie-gardy",
            "pol-dystans"
          ]
        }
      ]
    },
    "Obrona i uniki": {
      "emoji": "🛡️",
      "label": "Obrona, rotacje i uniki",
      "drills": [
        {
          "id": "box_def_001",
          "name": "Uniki rotacyjne (Rolls / Weaves) pod zawieszoną liną",
          "category": "Obrona i uniki",
          "sport": "Boks",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "3 rundy po 3 minuty poruszania się wzdłuż liny bokserskiej",
          "total_attempts": 3,
          "equipment": [
            "Lina bokserska (sznurek rozciągnięty na wysokości brody w ringu)"
          ],
          "muscles": [
            "czworogłowe",
            "skośne brzucha",
            "prostowniki grzbietu"
          ],
          "muscle_group": "nogi, tułów, elastyczność kręgosłupa",
          "description": "Klasyczny trening unikania ciosów sierpowych poprzez zejście pod ciosem po paraboli (litera U) z pracą nóg Mike'a Tysona (Peek-a-boo).",
          "courtPosition": "Wzdłuż 5-metrowej liny rozciągniętej na środku ringu.",
          "execution": "1. Stań w pozycji bokserskiej z liną tuż przy Twoim lewym ramieniu.\n2. Wykonaj zejście na nogach pod liną, rysując głową kształt litery U.\n3. Wynurz się po drugiej stronie liny z naładowanym biodrem gotowym do natychmiastowej riposty ciosem sierpowym.\n4. Zrób krok w przód i powtórz zejście w drugą stronę.",
          "biomechanics": "Zgięcie zachodzi w stawach kolanowych i biodrowych. Plecy pozostają proste — nigdy nie zginaj się w pasie z głową w dół!",
          "commonErrors": [
            "Zginanie się w pasie i patrzenie w podłogę (wystawienie się na podbródkowy)",
            "Zbyt płytkie zejście i zawadzanie głową o linę",
            "Opuszczanie rąk przy zejściu"
          ],
          "benefits": [
            "Schodzenie z linii ognia z jednoczesnym przygotowaniem kontrataku",
            "Niesamowita elastyczność i siła nóg"
          ],
          "target_pct": 85,
          "progression_tip": "Po każdym wynurzeniu się spod liny wyprowadź cios kontrujący (Roll -> Hook).",
          "tags": [
            "roll",
            "weave",
            "lina",
            "peek-a-boo",
            "uniki"
          ]
        },
        {
          "id": "box_def_002",
          "name": "Uniki w bok (Slip) z natychmiastową ripostą z prawej ręki",
          "category": "Obrona i uniki",
          "sport": "Boks",
          "difficulty": "intermediate",
          "duration": "12 min",
          "sets": "4 serie po 15 powtórzeń na tarczy",
          "total_attempts": 60,
          "equipment": [
            "Rękawice",
            "Tarcze z trenerem symulującym ciosy proste"
          ],
          "muscles": [
            "skośne brzucha",
            "barki",
            "łydki"
          ],
          "muscle_group": "tułów, refleks, reakcja",
          "description": "Zejście z linii prostego ciosu rywala dosłownie o 5-10 cm obok ucha z równoczesnym wbiciem ciosu w otwartego rywala.",
          "courtPosition": "Dystans walki w stójce.",
          "execution": "1. Na prosty cios rywala wykonaj rotacyjny skręt barków, przepuszczając cios tuż obok prawego ucha (slip na zewnątrz).\n2. Ciężar ciała ląduje na prawej nodze.\n3. Z odbicia prawej stopy wystrzel prawy prosty lub prawy sierp na odsłoniętą szczękę rywala.",
          "biomechanics": "Minimalizm ruchu: odchylenie głowy tylko o tyle, by cios minął cel (5 cm wystarczy). Im mniejszy ruch, tym szybszy kontratak.",
          "commonErrors": [
            "Zbyt wielki odskok uniemożliwiający zadanie kontry",
            "Zamykanie oczu przed nadlatującym ciosem",
            "Brak równowagi po uniku"
          ],
          "benefits": [
            "Najwyższa sztuka bokserska: sprawić by rywal przestrzelił i natychmiast za to zapłacił"
          ],
          "target_pct": 80,
          "progression_tip": "Trener zadaje losowo lewy lub prawy prosty — reaguj właściwym slipem.",
          "tags": [
            "slip",
            "kontra",
            "refleks",
            "riposta"
          ]
        },
        {
          "id": "box_def_003",
          "name": "Walka z cieniem (Shadowboxing) z pełną wizualizacją rywala",
          "category": "Obrona i uniki",
          "sport": "Boks",
          "difficulty": "beginner",
          "duration": "15 min",
          "sets": "3 rundy po 3 minuty (R1: sam jab i footwork, R2: kombinacje 3-ciosowe, R3: obrona i kontratak)",
          "total_attempts": 3,
          "equipment": [
            "Lustro treningowe",
            "Stoper bokserski",
            "Bandaże"
          ],
          "muscles": [
            "całe ciało",
            "układ krążenia",
            "mózg"
          ],
          "muscle_group": "kondycja, pamięć ruchowa, płynność",
          "description": "Najczystsza forma treningu bokserskiego budująca płynność, styl, wyobraźnię taktyczną i technikę bez oporu worka.",
          "courtPosition": "Przed lustrem lub na pustym ringu.",
          "execution": "1. Włącz zegar bokserski na rundy 3-minutowe.\n2. Poruszaj się lekko na nogach, wyobrażając sobie konkretne akcje rywala.\n3. Wyprowadzaj ciosy na 100% techniki z pełnym wydechem (syknięciem) przy każdym uderzeniu.\n4. Po każdej kombinacji wykonaj unik, zmianę kąta i natychmiastowe odejście na bezpieczny dystans.",
          "biomechanics": "Hamowanie ciosów siłą mięśni antagonistycznych bez przeprostowywania łokci w powietrzu.",
          "commonErrors": [
            "Brak skupienia i 'machanie rękami' bez wizualizacji rywala",
            "Stanie w miejscu w bezruchu między ciosami",
            "Przeprostowywanie łokci na siłę w powietrzu"
          ],
          "benefits": [
            "Budowa rytmu i ekonomii poruszania się w ringu",
            "Kondycja bez obciążania stawów uderzeniami w twardy cel"
          ],
          "target_pct": 95,
          "progression_tip": "Weź do rąk małe hantelki 0.5–1 kg w drugiej rundzie dla podkręcenia wytrzymałości barków.",
          "tags": [
            "shadowboxing",
            "cien",
            "plynnosc",
            "kondycja"
          ]
        },
        {
          "id": "box_def_004",
          "name": "Parowanie ciosu (Parry) dłonią z kontrą prawym prostym lub sierpem",
          "category": "Obrona i uniki",
          "sport": "Boks",
          "difficulty": "intermediate",
          "duration": "12 min",
          "sets": "4 serie po 15 powtórzeń na tarczy/z partnerem",
          "total_attempts": 60,
          "equipment": [
            "Rękawice",
            "Tarcze bokserskie"
          ],
          "muscles": [
            "nadgarstki",
            "naramienne",
            "triceps",
            "core"
          ],
          "muscle_group": "refleks, precyzja obrony, riposta",
          "description": "Najekonomiczniejsza obrona w boksie: delikatne strącenie nadlatującego ciosu rywala otwartą rękawicą z natychmiastowym ciosem w powstałą lukę.",
          "courtPosition": "Dystans walki w stójce.",
          "execution": "1. Z wysokiej gardy, na nadlatujący lewy prosty rywala wykonaj krótki ruch prawej dłoni (5 cm) strącający jego rękawicę w dół i do środka.\n2. Otwiera to głowę przeciwnika na bezpośredni cios.\n3. Natychmiast po sparowaniu wyprowadź lewy sierp na szczękę lub lewy prosty w odsłonięty cel.",
          "biomechanics": "Ruch parowania nie przekracza 5-10 cm od twarzy. Zbyt dalekie wyciągnięcie ręki odsłania własną szczękę na cios zwrotny.",
          "commonErrors": [
            "Sięganie ręką daleko do przodu po cios (tzw. łapanie much)",
            "Odsłanianie gardy przy parowaniu",
            "Zbyt późna riposta"
          ],
          "benefits": [
            "Minimalny wydatek energetyczny w obronie",
            "Błyskawiczne kreowanie okazji do nokautu"
          ],
          "target_pct": 85,
          "progression_tip": "Ćwicz z partnerem, który zadaje jaba w nieprzewidywalnych momentach z różną siłą.",
          "tags": [
            "parry",
            "parowanie",
            "kontra",
            "ekonomia"
          ]
        }
      ]
    }
  },
  "siatkowka": {
    "emoji": "🏐",
    "Zagrywka": {
      "emoji": "🚀",
      "label": "Zagrywka i celność",
      "drills": [
        {
          "id": "vball_srv_001",
          "name": "Zagrywka szybująca (Float Serve) w strefy 1 i 5",
          "category": "Zagrywka",
          "sport": "Siatkówka",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 10 zagrywek (celowanie w materace ułożone w narożnikach)",
          "total_attempts": 40,
          "equipment": [
            "Piłka do siatkówki",
            "Siatka o regulaminowej wysokości",
            "Materace/znaczniki w strefach 1 i 5"
          ],
          "muscles": [
            "naramienny",
            "triceps",
            "core",
            "piersiowy"
          ],
          "muscle_group": "ramię, stabilizacja nadgarstka, precyzja",
          "description": "Zagrywka bez rotacji, w której piłka pod wpływem zawirowań powietrza gwałtownie zmienia tor lotu przed samym odbiorem.",
          "courtPosition": "Za linią końcową (strefa zagrywki 9 metrów od siatki).",
          "execution": "1. Stań stabilnie za linią końcową, lewa noga z przodu (dla praworęcznych).\n2. Wyrzuć piłkę na wysokość ok. 1-1.5 metra stabilnie przed siebie lewą ręką (zero rotacji piłki przy wyrzucie!).\n3. Wykonaj krótki zamach — łokieć wysoko na wysokości ucha, dłoń otwarta i sztywna jak deska.\n4. Uderz nasadą dłoni dokładnie w geometryczny środek piłki z gwałtownym zatrzymaniem ręki w momencie kontaktu (brak follow-through!).",
          "biomechanics": "Brak rotacji piłki wywołuje niestabilność aerodynamiczną Kármána — piłka 'pływa' w powietrzu i nagle spada tuż przed przyjmującym.",
          "commonErrors": [
            "Zawijanie nadgarstka nad piłkę (nadanie rotacji topspin zamiast floata)",
            "Zbyt wysoki lub niestabilny wyrzut",
            "Kontynuacja ruchu ręki po uderzeniu"
          ],
          "benefits": [
            "Najtrudniejsza zagrywka do dokładnego przyjęcia we współczesnej siatkówce",
            "Wymuszenie błędów i asy serwisowe"
          ],
          "target_pct": 70,
          "progression_tip": "Wykonaj zagrywkę typu Float z wyskoku (Jump Float) z 3-krokowego naskoku.",
          "tags": [
            "float",
            "zagrywka",
            "brak-rotacji",
            "as"
          ]
        },
        {
          "id": "vball_srv_002",
          "name": "Zagrywka z wyskoku na siłę (Power Jump Serve)",
          "category": "Zagrywka",
          "sport": "Siatkówka",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "4 serie po 8 zagrywek z maksymalną siłą",
          "total_attempts": 32,
          "equipment": [
            "Piłka",
            "Siatka"
          ],
          "muscles": [
            "czworogłowe",
            "łydki",
            "brzuch",
            "barki"
          ],
          "muscle_group": "wyskok, dynamika, siła uderzenia",
          "description": "Potężna zagrywka atakująca z rotacją awansującą (topspin) przekraczająca prędkość 100 km/h.",
          "courtPosition": "3-4 metry za linią końcową boiska.",
          "execution": "1. Wyrzuć piłkę wysoko na 3-4 metry w głąb boiska z mocną rotacją topspin.\n2. Wykonaj dynamiczny 3-krokowy rozbieg siatkarski i wyskocz z obu nóg za linią końcową.\n3. Traf piłkę w najwyższym punkcie wyskoku, nakrywając ją dłonią i nadgarstkiem od góry do dołu.\n4. Wyląduj miękko na ugiętych nogach wewnątrz boiska.",
          "biomechanics": "Transfer prędkości rozbiegu w wyskok pionowy. Kąt natarcia ręki i załamanie tułowia generują potężną prędkość liniową piłki.",
          "commonErrors": [
            "Zły wyrzut zmuszający do uderzenia za głową",
            "Przekroczenie linii końcowej przed wyskokiem (błąd stóp)",
            "Uderzenie w siatkę"
          ],
          "benefits": [
            "Bezpośrednie zdobywanie punktów z zagrywki",
            "Odrzucenie rywala daleko od siatki"
          ],
          "target_pct": 60,
          "progression_tip": "Mierz prędkość piłki radarem — celuj w powtarzalne >90 km/h.",
          "tags": [
            "jump-serve",
            "moc",
            "topspin",
            "atak-z-zagrywki"
          ]
        }
      ]
    },
    "Przyjęcie i obrona": {
      "emoji": "🛡️",
      "label": "Przyjęcie i gra obronna",
      "drills": [
        {
          "id": "vball_rec_001",
          "name": "Przyjęcie zagrywki sposobem dolnym do strefy rozgrywającego (strefa 2/3)",
          "category": "Przyjęcie i obrona",
          "sport": "Siatkówka",
          "difficulty": "intermediate",
          "duration": "20 min",
          "sets": "4 serie po 12 przyjęć zagrywki trenera/maszyny",
          "total_attempts": 48,
          "equipment": [
            "Piłka",
            "Kosz na piłki przy siatce oznaczający strefę idealnego dogrania"
          ],
          "muscles": [
            "czworogłowe",
            "barki",
            "przedramiona",
            "stabilizatory bioder"
          ],
          "muscle_group": "nogi, przedramiona, platforma",
          "description": "Klucz do wygrania meczu siatkarskiego: perfekcyjne dogranie piłki na wysokość 1 metra nad siatkę między strefę 2 i 3 do rąk rozgrywającego.",
          "courtPosition": "Strefa 5 lub 6 (linia przyjęcia 6-7 metrów od siatki).",
          "execution": "1. Niska postawa: stopy szeroko, kolana ugięte, tułów pochylony, ręce rozłączone w gotowości.\n2. W momencie uderzenia zagrywki wykonaj split-step i przesuń się na nogach za linię lotu piłki.\n3. Złóż platformę przedramion (ręka w rękę, kciuki równolegle w dół, łokcie zablokowane i wyprostowane).\n4. Nie machaj ramionami w górę! Użyj nóg do amortyzacji i skieruj płaszczyznę przedramion pod kątem w stronę strefy 2/3.",
          "biomechanics": "Kąt odbicia równa się kątowi padania. Płaszczyzna przedramion stabilna — ruch wyprowadzany z wyprostu kolan, nie z unoszenia barków.",
          "commonErrors": [
            "Machanie ramionami do góry w momencie kontaktu (piłka leci za siatkę lub w sufit)",
            "Zginanie łokci",
            "Przyjmowanie na stojąco bez obniżenia nóg"
          ],
          "benefits": [
            "Umożliwienie rozgrywającemu rozegrania kombinacyjnego ataku na pojedynczym bloku"
          ],
          "target_pct": 75,
          "progression_tip": "Oceniaj przyjęcie w skali siatkarskiej: # (perfekcyjne w punkt), + (pozytywne), ! (negatywne), - (błąd). Cel: >65% przyjęcia pozytywnego.",
          "tags": [
            "przyjecie",
            "dogranie",
            "platforma",
            "sposob-dolny"
          ]
        },
        {
          "id": "vball_rec_002",
          "name": "Obrona po ataku w padzie (Dig & Pancake)",
          "category": "Przyjęcie i obrona",
          "sport": "Siatkówka",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "4 serie po 8 obron trudnych piłek atakowanych ze skrzydła",
          "total_attempts": 32,
          "equipment": [
            "Piłki",
            "Nakolanniki siatkarskie"
          ],
          "muscles": [
            "czworogłowe",
            "core",
            "naramienne",
            "pośladki"
          ],
          "muscle_group": "refleks, elastyczność, upadki",
          "description": "Ratowanie piłki lecącej z potężną prędkością w parkiet z bezpiecznym ześlizgiem na klatkę piersiową lub wsunięciem dłoni pod piłkę (pancake).",
          "courtPosition": "Tylna linia obrony (strefy 1, 5, 6).",
          "execution": "1. Obniż środek ciężkości maksymalnie nisko nad parkiet.\n2. W momencie uderzenia piłki wykonaj dynamiczny wypad w bok lub w przód.\n3. Podbij piłkę jedną lub dwoma rękami w górę na środek boiska.\n4. Wykonaj bezpieczny pad na parkiet (ześlizg na brzuch/biodro) amortyzowany rękami, nie uderzając kolanami o twardy parkiet.",
          "biomechanics": "Ekstremalnie szybkie zejście środka ciężkości. Dłoń w technice pancake kładziona płasko grzbietem do parkietu — piłka odbija się od kości śródręcza.",
          "commonErrors": [
            "Lęk przed upadkiem skutkujący spóźnioną reakcją",
            "Lądowanie bezpośrednio na rzepkach kolanowych",
            "Podbijanie piłki w siatkę zamiast wysoko w górę do środka"
          ],
          "benefits": [
            "Podrywanie beznadziejnych piłek i budowanie morale całej drużyny"
          ],
          "target_pct": 70,
          "progression_tip": "Trener atakuje z podestu z odległości 6 metrów — czas reakcji poniżej 0.4 sekundy.",
          "tags": [
            "obrona",
            "dig",
            "pancake",
            "pad",
            "ofiarnosc"
          ]
        },
        {
          "id": "vball_rec_003",
          "name": "Wystawa sposobem górnym (Overhand Set) z wyskoku i z miejsca",
          "category": "Przyjęcie i obrona",
          "sport": "Siatkówka",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 15 wystaw do skrzydła i do środka",
          "total_attempts": 60,
          "equipment": [
            "Piłka",
            "Tarcza na siatce do precyzyjnego rozegrania"
          ],
          "muscles": [
            "palce i nadgarstki",
            "triceps",
            "czworogłowe",
            "barki"
          ],
          "muscle_group": "palce, nadgarstki, miękkość chwytu",
          "description": "Precyzyjne skierowanie piłki opuszkami palców w idealne tempo dla atakującego na skrzydle lub na środku siatki.",
          "courtPosition": "Strefa 2/3 (pozycja rozgrywającego).",
          "execution": "1. Szybko ustaw się pod spadającą piłką, stopy stabilnie na szerokość bioder.\n2. Unieś dłonie nad czoło, palce ułożone w koszyczek na kształt piłki (kciuki i palce wskazujące tworzą trójkąt).\n3. Przyjmij piłkę miękko na opuszki wszystkich 10 palców.\n4. Jednoczesnym wyprostem nóg i ramion wypchnij piłkę w kierunku antenki na skrzydło.",
          "biomechanics": "Czysty kontakt wyłącznie opuszkami palców bez dźwięku klapnięcia i bez przetrzymania (eliminacja błędu piłki rzuconej/podwójnej).",
          "commonErrors": [
            "Kontakt z piłką przed klatką zamiast nad czołem",
            "Nierównomierny kontakt rąk (błąd piłki podwójnej)",
            "Brak pracy nóg przy wypchnięciu"
          ],
          "benefits": [
            "Aksamitna wystawa umożliwiająca potężny atak ponad blokiem"
          ],
          "target_pct": 85,
          "progression_tip": "Wykonaj wystawę z wyskoku (Jump Set), co skraca czas lotu piłki do skrzydła o 0.3 sekundy.",
          "tags": [
            "wystawa",
            "rozegranie",
            "sposob-gorny",
            "palce"
          ]
        }
      ]
    },
    "Atak i blok": {
      "emoji": "💥",
      "label": "Atak i gra na siatce",
      "drills": [
        {
          "id": "vball_atk_001",
          "name": "Atak ze skrzydła po rozbiegu 3-krokowym (Kierunek: skos i prosta)",
          "category": "Atak i blok",
          "sport": "Siatkówka",
          "difficulty": "intermediate",
          "duration": "20 min",
          "sets": "4 serie po 8 ataków (4 po prostej, 4 po ciasnym skosie)",
          "total_attempts": 32,
          "equipment": [
            "Piłka",
            "Siatka",
            "Wystawiający"
          ],
          "muscles": [
            "czworogłowe",
            "pośladki",
            "brzuch",
            "naramienny",
            "najszerszy"
          ],
          "muscle_group": "skoczność, dynamika ramienia, rotacja tułowia",
          "description": "Koronny element ofensywny siatkówki: dynamiczny rozbieg, wyskok ponad siatkę i mocne zbicie piłki w pole przeciwnika.",
          "courtPosition": "Lewe lub prawe skrzydło (strefa 4 lub 2).",
          "execution": "1. Wyczekaj moment wystawy: rozpocznij rozbieg (dla praworęcznego: krok lewą, długi krok prawą i dostawienie lewej z hamowaniem).\n2. Potężny zamach oburącz w tył i eksplozywny wyskok w górę (nie w siatkę!).\n3. W powietrzu pozycja łuku (napięty brzuch, łokieć ręki atakującej wysoko z tyłu).\n4. Uderz piłkę w najwyższym punkcie wyciągniętą ręką, zamykając nadgarstek nad piłką w stronę podłoża.",
          "biomechanics": "Konwersja energii poziomej rozbiegu w wyskok pionowy na dwóch ostatnich krokach (plant & block step). Dynamiczny skurcz mięśni brzucha (ruch jak scyzoryk).",
          "commonErrors": [
            "Wpadanie w siatkę po wyskoku (brak hamowania ostatnim krokiem)",
            "Zbyt wczesny rozbieg (czekanie na piłkę na dole)",
            "Uderzenie ugiętą ręką w łokciu"
          ],
          "benefits": [
            "Zdobywanie bezpośrednich punktów atakiem ponad lub obok bloku rywali"
          ],
          "target_pct": 70,
          "progression_tip": "Umieść blokera naprzeciwko i ćwicz obijanie rąk bloku w aut (tooling the block).",
          "tags": [
            "atak",
            "rozbieg",
            "zbicie",
            "skrzydlo",
            "wyskok"
          ]
        },
        {
          "id": "vball_atk_002",
          "name": "Blok podwójny z przemieszczeniem krokiem odstawno-dostawnym",
          "category": "Atak i blok",
          "sport": "Siatkówka",
          "difficulty": "intermediate",
          "duration": "15 min",
          "sets": "4 serie po 6 przemieszczeń z wyskokiem blokującym",
          "total_attempts": 24,
          "equipment": [
            "Siatka siatkarska"
          ],
          "muscles": [
            "czworogłowe",
            "łydki",
            "naramienne",
            "dłonie"
          ],
          "muscle_group": "wyskok, barki, czytanie gry",
          "description": "Zorganizowanie szczelnego muru nad siatką: dobieg środkowego do skrzydłowego i przełożenie rąk na stronę rywala.",
          "courtPosition": "Przy samej siatce (środek -> skrzydło).",
          "execution": "1. Postawa przy siatce: dłonie na wysokości barków palcami w górę, pół metra od siatki.\n2. Odczytaj kierunek wystawy i przemieść się 2 dynamicznymi krokami do skrzydła.\n3. Wyskocz pionowo razem ze skrzydłowym, tworząc zwarty blok bez dziury między rękami.\n4. Przełóż sztywne, szeroko rozstawione dłonie głęboko przez siatkę na stronę rywala (penatracja siatki).",
          "biomechanics": "Penetracja nad siatką: dłonie skierowane w dół ku środkowi boiska przeciwnika. Ramiona dociśnięte do uszu.",
          "commonErrors": [
            "Dotknięcie siatki brzuchem lub ramieniem",
            "Dziura między rękami blokujących (piłka przelatuje pomiędzy)",
            "Skok w bok zamiast w pionie (ryzyko skręcenia kostki partnera)"
          ],
          "benefits": [
            "Zatrzymanie ataku rywala bezpośrednim blokiem punktowym (monster block)"
          ],
          "target_pct": 75,
          "progression_tip": "Trener atakuje z podestu — Twoim celem jest odbicie piłki pod kątem prosto w parkiet rywala.",
          "tags": [
            "blok",
            "penatracja",
            "siatka",
            "monster-block"
          ]
        },
        {
          "id": "vball_atk_003",
          "name": "Atak z drugiej linii (Pipe ze strefy 6)",
          "category": "Atak i blok",
          "sport": "Siatkówka",
          "difficulty": "advanced",
          "duration": "15 min",
          "sets": "4 serie po 6 ataków z wyskoku zza linii 3 metrów",
          "total_attempts": 24,
          "equipment": [
            "Piłka",
            "Siatka",
            "Wystawiający"
          ],
          "muscles": [
            "czworogłowe",
            "pośladki",
            "brzuch",
            "naramienny"
          ],
          "muscle_group": "skoczność daleka, wyskok, moc zbicia",
          "description": "Atak z głębi pola: przyjmujący nabiega zza linii 3 metrów na szybką piłkę wystawioną na środek siatki, mijając opadający blok rywala.",
          "courtPosition": "Strefa 6 (środek boiska zza linii 3m).",
          "execution": "1. Wystawiający gra szybką piłkę na wysokość 1 metra nad siatką w centralnej strefie.\n2. Atakujący wykonuje agresywny rozbieg i odbija się z obu nóg ZANIM dotknie linii 3 metrów.\n3. Lot w powietrzu do przodu i w górę — uderzenie piłki nad siatką z pełną siłą w wolne strefy parkietu.",
          "biomechanics": "Połączenie wyskoku w dal i w pion. Siła uderzenia zwielokrotniona pędem lotu całego ciała.",
          "commonErrors": [
            "Przekroczenie linii 3 metrów przy wyskoku (błąd dotknięcia linii)",
            "Spóźniony nabieg (pipe wymaga ekspresowego timingu)",
            "Uderzenie w siatkę z powodu zbyt płaskiej paraboli lotu"
          ],
          "benefits": [
            "Najtrudniejszy atak do obrony i zablokowania we współczesnej siatkówce",
            "Rozciągnięcie bloku rywala"
          ],
          "target_pct": 65,
          "progression_tip": "Zgrywaj timing z rozgrywającym tak, byś był już w powietrzu w momencie wypuszczenia piłki z jego dłoni.",
          "tags": [
            "pipe",
            "druga-linia",
            "3-metry",
            "nowoczesna-siatkowka"
          ]
        }
      ]
    }
  }
};

// Aliasy dyscyplin sportowych dla 100% interoperacyjności z SPORT_ID_MAP i resolveSportId():
const _bball = SPORT_DRILLS['koszykowka'] || SPORT_DRILLS['basketball'];
SPORT_DRILLS['basketball'] = SPORT_DRILLS['koszykówka'] = SPORT_DRILLS['koszykowka'] = _bball;

const _fball = SPORT_DRILLS['pilka_nozna'] || SPORT_DRILLS['football'];
SPORT_DRILLS['football'] = SPORT_DRILLS['piłka nożna'] = SPORT_DRILLS['pilka_nozna'] = SPORT_DRILLS['pilkanozna'] = _fball;

const _tennis = SPORT_DRILLS['tenis'] || SPORT_DRILLS['tennis'];
SPORT_DRILLS['tennis'] = SPORT_DRILLS['tenis'] = _tennis;

const _boxing = SPORT_DRILLS['boks'] || SPORT_DRILLS['boxing'];
SPORT_DRILLS['boxing'] = SPORT_DRILLS['boks'] = _boxing;

const _vball = SPORT_DRILLS['siatkowka'] || SPORT_DRILLS['siatkówka'] || SPORT_DRILLS['volleyball'];
SPORT_DRILLS['volleyball'] = SPORT_DRILLS['siatkówka'] = SPORT_DRILLS['siatkowka'] = _vball;

if (typeof window !== 'undefined') {
  window.MEAL_DB = MEAL_DB;
  window.EXERCISE_DB = EXERCISE_DB;
  window.SPORT_DRILLS = SPORT_DRILLS;
}

console.log('[EVOLVE Seed Data v3.0] Załadowano pomyślnie: ' +
  Object.values(MEAL_DB).reduce((a,b)=>a+b.length,0) + ' posiłków, ' +
  Object.values(EXERCISE_DB).reduce((a,b)=>a+b.length,0) + ' ćwiczeń, ' +
  50 + ' drilli sportowych ✅');
