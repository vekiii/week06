# Week 6 RAG — evidence

Proširena verzija nad knjigom *The Prince*. Sledećih pet sekcija i nazivi podstavki prate tačan obrazac iz `Week 6 RAG Homework Starter.pdf`. Izlazi su stvarno izvršeni i sačuvani; komande se pokreću iz root-a projekta, osim posebno označenih starter testova.

1. Outcome 1: Chunking impact
   - Config A: `chunk_size=140`, `overlap=30` karaktera, `top_k=3`, `min_score=0.5`.
   - Config B: `chunk_size=500`, `overlap=80` karaktera, isti `top_k=3` i `min_score=0.5`.
   - Retrieval difference summary:

     Isti upit u oba slučaja: **When is it safer to be feared than loved?** Obe konfiguracije pronalaze direktnu tvrdnju u XVII poglavlju, sa najboljim skorom 1.000. A citira `prince-section-018-chunk-022` (139 karaktera), B citira `prince-section-018-chunk-007` (500 karaktera). B uključuje celo pitanje i objašnjenje da je teško spojiti ljubav i strah, dok A počinje usred reči. Obe konfiguracije ipak mogu preseći reči i rečenice na granicama. Broj chunk-ova u knjizi je 2703 za A i 804 za B. U top-3 nema potpuno jednakih tekstova; rezultati 2 i 3 ponavljaju 30 karaktera kod A i 80 kod B. Veći overlap ovde povećava redundantnost naslova.

     Zaključak važi za ovaj upit; menjali smo veličinu i overlap zajedno, pa ne izdvajamo njihov pojedinačni efekat. ID citata mora se proveravati uz istu konfiguraciju i korpus. [Detaljno poređenje i komande](phase-8-chunking-experiment.md), [izlaz A](experiments/phase-8/140-30.txt), [izlaz B](experiments/phase-8/500-80.txt), [parametri i puni rezultati](experiments/phase-8/results.json).

2. Outcome 2: Top-k retrieval
   - Query: `When is it safer to be feared than loved?`
   - Top-k output:

     Konfiguracija `140/30`, prag odgovora `0.5`. Pune komande i izlazi nalaze se ispod za top-3 i u [top-2 izlazu](submission/top-2.txt). Za top-2 koristiti istu supported komandu iz Outcome 5 uz `--top-k 2`.

     | k | Rang | Chunk ID | Skor | Poglavlje |
     |---:|---:|---|---:|---|
     | 2 | 1 | `prince-section-018-chunk-022` | 1.000 | XVII |
     | 2 | 2 | `prince-section-018-chunk-000` | 0.667 | XVII |
     | 3 | 1 | `prince-section-018-chunk-022` | 1.000 | XVII |
     | 3 | 2 | `prince-section-018-chunk-000` | 0.667 | XVII |
     | 3 | 3 | `prince-section-018-chunk-001` | 0.667 | XVII |

   - Why ranking is correct:

     Tokeni posle NFKC/casefold normalizacije i uklanjanja stop-reči su `safer`, `feared`, `loved`. Skor je udeo jedinstvenih query termina prisutnih u chunk-u: prvi poklapa 3/3, druga dva 2/3. Ponavljanje reči ne povećava skor. Rezultati se sortiraju opadajuće, a izjednačenja po rastućem chunk ID-u. Zato `chunk-000` prethodi `chunk-001`. Top-2 je prefiks top-3, a nulti rezultati se izostavljaju. To dokazuje redosled prema definisanom leksičkom skoru; samo poklapanje reči ne dokazuje da tekst odgovara pitanju. [Dodatno poređenje k=5, 7 i 10](phase-4-retrieval.md).

3. Outcome 3: Citation quality
   - Supported query: `When is it safer to be feared than loved?`
   - Answer with citations:

     `Answer` je doslovni evidence odlomak, bez LLM parafraze. `References` navodi isti ID, poglavlje, izvor i citat:

     ```text
     Answer:
     Evidence excerpt from the book: "em in one person, it is much safer to be feared than loved, when, of the two, either must be dispensed with. Because this is to be asserted" [prince-section-018-chunk-022]
     References:
     - [prince-section-018-chunk-022] CHAPTER XVII. - https://www.gutenberg.org/ebooks/1232
       Evidence excerpt: "em in one person, it is much safer to be feared than loved, when, of the two, either must be dispensed with. Because this is to be asserted"
     ```

   - Retrieved chunk IDs:

     `prince-section-018-chunk-022`, `prince-section-018-chunk-000`, `prince-section-018-chunk-001`. Odgovor citira samo prvi od ovih rezultata. Njegov tekst eksplicitno kaže da je sigurnije biti feared than loved kada jedno od ta dva mora biti žrtvovano. Kompletni odlomci su prikazani u Outcome 5.

4. Outcome 4: Refusal behavior
   - Unsupported query: `Who won the World Cup in 1958?`
   - Retrieved context:

     ```text
     - [prince-section-001-chunk-083] INTRODUCTION
       score=0.250
       , when Venice lost in one day all that she had won in eight hundred years. Florence had a difficult part to play during these events, compli
     - [prince-section-001-chunk-150] INTRODUCTION
       score=0.250
       ssance among the nations of Europe. Whilst it is idle to protest against the world-wide and evil signification of his name, it may be pointe
     - [prince-section-004-chunk-019] CHAPTER III.
       score=0.250
       surrections on the borders; but to cause him to lose it a second time it was necessary to bring the whole world against him, and that his ar
     ```

     Sva tri rezultata imaju skor 0.250. Poklapaju poneku opštu reč (`won` ili `world`), ali ne daju podatak o prvenstvu 1958. Najbolji skor je ispod praga 0.5. Sistem zadržava rezultate za debug i odbija odgovor bez citata.

   - Refusal output:

     ```text
     Answer:
     I do not have enough evidence in the retrieved book passages to answer this question.
     Reason: Best lexical score 0.25 is below the configured minimum 0.50.
     References:
     None (no citation is made).
     ```

5. Outcome 5: Final evidence pair
   - Supported case command + output

     ```sh
     python -m src.cli --corpus the-prince --corpus-path data/book.txt --question "When is it safer to be feared than loved?" --chunk-size 140 --overlap 30 --top-k 3 --min-score 0.5 --show-scores
     ```

     ```text
     Corpus: the-prince (data\book.txt)
     Question: When is it safer to be feared than loved?
     Configuration: chunk_size=140 chars, overlap=30 chars, top_k=3, min_score=0.50
     
     Answer:
     Evidence excerpt from the book: "em in one person, it is much safer to be feared than loved, when, of the two, either must be dispensed with. Because this is to be asserted" [prince-section-018-chunk-022]
     References:
     - [prince-section-018-chunk-022] CHAPTER XVII. - https://www.gutenberg.org/ebooks/1232
       Evidence excerpt: "em in one person, it is much safer to be feared than loved, when, of the two, either must be dispensed with. Because this is to be asserted"
     
     Retrieved context:
     - [prince-section-018-chunk-022] CHAPTER XVII.
       score=1.000
       em in one person, it is much safer to be feared than loved, when, of the two, either must be dispensed with. Because this is to be asserted
     - [prince-section-018-chunk-000] CHAPTER XVII.
       score=0.667
       CONCERNING CRUELTY AND CLEMENCY, AND WHETHER IT IS BETTER TO BE LOVED THAN FEARED
     - [prince-section-018-chunk-001] CHAPTER XVII.
       score=0.667
       BETTER TO BE LOVED THAN FEARED
     
     Coming now to the other qualities mentioned above, I say that every prince ought to desire to be considered
     ```

   - Unsupported case command + output

     ```sh
     python -m src.cli --corpus the-prince --corpus-path data/book.txt --question "Who won the World Cup in 1958?" --chunk-size 140 --overlap 30 --top-k 3 --min-score 0.5 --show-scores
     ```

     ```text
     Corpus: the-prince (data\book.txt)
     Question: Who won the World Cup in 1958?
     Configuration: chunk_size=140 chars, overlap=30 chars, top_k=3, min_score=0.50
     
     Answer:
     I do not have enough evidence in the retrieved book passages to answer this question.
     Reason: Best lexical score 0.25 is below the configured minimum 0.50.
     References:
     None (no citation is made).
     
     Retrieved context:
     - [prince-section-001-chunk-083] INTRODUCTION
       score=0.250
       , when Venice lost in one day all that she had won in eight hundred years. Florence had a difficult part to play during these events, compli
     - [prince-section-001-chunk-150] INTRODUCTION
       score=0.250
       ssance among the nations of Europe. Whilst it is idle to protest against the world-wide and evil signification of his name, it may be pointe
     - [prince-section-004-chunk-019] CHAPTER III.
       score=0.250
       surrections on the borders; but to cause him to lose it a second time it was necessary to bring the whole world against him, and that his ar
     ```

## Testovi i reprodukcija

Aplikacija koristi Python standardnu biblioteku; `pytest` je potreban za testove. Kreirati lokalni virtualenv i instalirati `requirements.txt`. Za CLI koristiti Python iz tog okruženja ili aktivirati okruženje pre navedenih komandi. Primer na Windows-u:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.evaluation
```

Na macOS/Linux-u koristiti `.venv/bin/python`. Završna provera: **37 passed**; evaluacija **5/5 passed**. Sačuvani izlazi: [testovi](submission/tests.txt) i [evaluacija](submission/evaluation.txt). Evaluacioni slučajevi su u `data/evaluation.json` i proveravaju očekivano poglavlje i termine u citiranom odlomku, odnosno refusal bez referenci.

**Ručna provera korisnika na Windows-u (2026-10-12):** `37 passed in 0.61s`. Prvi pokušaj testa imao je greške pri pravljenju `tmp_path`, jer Windows nije dozvolio pristup pytest podrazumevanom direktorijumu pod `%TEMP%`. Pokretanje sa jedinstvenim `--basetemp` unutar projekta zaobišlo je problem:

```powershell
$pytestTemp = Join-Path (Get-Location) ".pytest-tmp-$([guid]::NewGuid().ToString('N'))"
.\.venv\Scripts\python.exe -m pytest -q --basetemp $pytestTemp -p no:cacheprovider
```

`-p no:cacheprovider` isključuje pytest cache, a nasumično ime pravi privremeni direktorijum za taj test run. Dodat je u `.gitignore` obrazac `/\.pytest-tmp-*/` da se ti lokalni direktorijumi ne dodaju u Git.

Starter se proverava zasebno, iz njegovog direktorijuma, uz isti interpreter koji ima pytest:

```sh
python -m pytest -q -o pythonpath= --import-mode=importlib tests
```

Rezultat: **9 passed**, [sačuvani izlaz](submission/starter-tests.txt). Opcije sprečavaju da root `pytest.ini` ubaci novu aplikaciju `src` umesto starter paketa. Prvi pokušaj bez ovih opcija imao je dve import greške; to je sukob konfiguracije, ne pad testova starter logike. Istorijsko početno stanje ostaje u [Phase 1 beleškama](phase-1-baseline.md).

## Doprinos para — dopuniti naknadno

Prema dogovoru, ova sekcija ostaje prazna do potvrde stvarnih doprinosa. Predlog podele iz plana nije evidentiran kao obavljen rad.

| Član | Ime | Stvarni rad/pregled i konkretni fajlovi |
|---|---|---|
| A | | |
| B | | |

**Demo lead:**

**Napomena:** dopuniti imena, doprinose i demo lead pre predaje.

## Demo

1. Pokrenuti supported komandu iz Outcome 5; pokazati konfiguraciju, tri retrieved rezultata, odgovor i istovetni ID u References.
2. Pokrenuti unsupported komandu; pokazati skor 0.25, prag 0.5 i odsustvo citata.
3. Pokrenuti isti supported upit sa `--chunk-size 500 --overlap 80`; objasniti potpuniji kontekst, promenjeni chunk ID i ponavljanje naslova.
4. Objasniti pokrivenost termina i ograničenja refusal-a; pokazati evaluaciju i test snapshot.

Ovo je pripremljen scenario, ne tvrdnja da je demo već održan.

## Izvor korpusa i obrada

Korpus je *The Prince*, Niccolò Machiavelli, engleski prevod W. K. Marriott, Project Gutenberg eBook 1232. [Stranica izvora](https://www.gutenberg.org/ebooks/1232), [plain text](https://www.gutenberg.org/cache/epub/1232/pg1232.txt). Koristi se lokalni UTF-8 `data/book.txt`; tačan SHA-256 korišćen u eksperimentu nalazi se u [results.json](experiments/phase-8/results.json). Originalni fajl nije ručno menjan.

Loader uklanja Gutenberg zaglavlje/završnu licencu i sadržaj koristeći markere. Vraća 29 odeljaka: uvod, 26 poglavlja i dva dodatna dela. Chunking normalizuje whitespace unutar pasusa i ne prelazi granicu odeljka. Izvor i naslov poglavlja čuvaju se uz svaki chunk. [Detalji ingestion-a](phase-2-corpus.md).

## Ograničenja zaključaka

Sistem je lokalni ekstraktivni baseline. Koristi samo najbolji retrieved chunk kao odgovor, pa povećanje k samo po sebi ne poboljšava odabir citata. Skor pokrivenosti ne razume semantičku podršku: na primer, visok skor za pitanje o princu Francuske ne dokazuje da odlomak imenuje takvu osobu. Pet evaluacionih primera i terminske provere nisu dokaz opšte pouzdanosti. Pitanje o održavanju vere vraća uvodnu tvrdnju o pohvalnosti integriteta, što nije iscrpno predstavljanje kasnijeg argumenta poglavlja.

Chunk granice mogu preseći reči; ID-jevi su stabilni samo za isti korpus i parametre, bez izvornih brojeva pasusa. Za ručnu proveru treba čitati citat i širi kontekst poglavlja. Sačuvani dokazi pokazuju konkretne uspešne slučajeve i ograničenja, bez tvrdnje da sistem razume celu knjigu.
