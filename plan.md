# Week 6 RAG projekat — plan implementacije

## Cilj

U paru napraviti proširenu RAG aplikaciju nad knjigom *The Prince* (Niccolò Machiavelli, prevod W. K. Marriott) sa Project Gutenberg-a. Sistem treba da pripremi tekstualni korpus, podeli ga u preklapajuće chunk-ove, pronađe relevantne odlomke, odgovara samo na osnovu pronađenog teksta i navede proverljive citate. Za pitanja bez dovoljne podrške treba jasno da odbije odgovor.

Plan prvenstveno prati obavezne ishode, zadatke i ta?an evidence template iz `Week 6 RAG Homework Starter.pdf`. Starter projekat slu?i samo kao primer organizacije i po?etnih interfejsa; nova aplikacija i svi projektni fajlovi bi?e napravljeni u root-u repozitorijuma.

## Opseg i pretpostavke

- Korpus: engleski tekst iz [Project Gutenberg, eBook 1232](https://www.gutenberg.org/ebooks/1232), sačuvan kao UTF-8 plain text.
- Projekat se nalazi u root-u repozitorijuma. `rag-week-6-homework-starter/` moze se pregledati kao referenca, ali nije radni direktorijum niti deo implementacije.
- Starter projekat i njegove testove ne menjati; napraviti novu aplikaciju, testove i `docs/` u root-u.
- U root-u postoji `data/book.txt`; prvo proveriti encoding, izvor i izdanje. Po?etni pregled ukazuje na mogu?i encoding problem (`Niccol?`), pa proveriti bajtove pre ingestion-a.
- Prva verzija koristi postojeći lokalni leksički retrieval bez spoljnog LLM-a. To čini rezultat reproduktivnim i izvodljivim bez API ključeva. Odgovor se sastavlja iz retrieved odlomaka; ako se kasnije dodaje LLM, mora dobiti samo retrieved kontekst i zadržati iste citate i refusal pravila.
- Ne uključivati Gutenbergovu licencu i početni/završni boilerplate u pretraživ tekst; zabeležiti izvor i izdanje u metapodacima projekta.

## Struktura koju ciljamo

```text
week06/                         # root Git repozitorijuma
  data/
    book.txt                    # Gutenberg plain text korpus
  src/
    corpus.py                   # u?itavanje i ?i??enje knjige
    chunking.py                 # chunk-ovi sa granicama poglavlja
    retrieval.py                # leksi?ko rangiranje top-k
    rag.py                      # grounded odgovor, citati i refusal
    cli.py                      # parametri i pokretanje pipeline-a
  tests/
    test_corpus.py
    test_chunking.py
    test_retrieval.py
    test_rag.py
  docs/
    evidence.md                 # ta?an evidence template iz PDF-a
  plan.md
  README.md
  requirements.txt
```

Postoje?i `rag-week-6-homework-starter/` ostaje samo pomo?ni primer; nova aplikacija je u root-u.

Ako se postojeći raspored razlikuje, zadržati trenutne putanje i dodati samo nedostajuće fajlove.

## Faze implementacije

### 1. Razumeti zadatak i uspostaviti po?etno stanje

1. Koristiti PDF kao glavni izvor zahteva. Zabele?iti pet ishoda i prepisati ta?an evidence template u novi `docs/evidence.md`.
2. Po ?elji pregledati starter README, checklist-u i kod kao primere za corpus, chunking, retrieval, citate i refusal; nova aplikacija ne zavisi od startera.
3. Zabele?iti po?etno Git stanje i proveriti postoje?e `data/book.txt`, `.gitignore` i root direktorijume.
4. Dogovoriti module i funkcijske interfejse za novu aplikaciju pre podele rada.
5. Pokrenuti starter CLI i testove ako je okru?enje kompatibilno, a rezultate i ograni?enja sa?uvati u `docs/phase-1-baseline.md`. Ne popravljati starter radi samog baseline-a.

**Izlaz:** po?etno pona?anje i ograni?enja startera su zabele?eni radi pore?enja; dogovorena je struktura i API nove root aplikacije.

### 2. Preuzeti i pripremiti Gutenberg korpus

1. Koristiti vec postojeci `data/book.txt` ako provera izvora i UTF-8 prodje; zadrzati to ime iz postojece strukture umesto da se pravi duplikat. Ponovo preuzeti plain text eBook 1232 samo ako fajl ne prodje proveru.
2. Sacuvati izvorni fajl neizmenjenim. Obradu raditi u loader-u, ne rucnim prepisivanjem knjige.
3. Dodati loader koji:
   - proverava da je fajl dostupan i prijavljuje korisnu grešku ako nije;
   - čita UTF-8 (po potrebi podržava BOM);
   - uklanja Project Gutenberg zaglavlje/licencu i završni boilerplate koristeći poznate markere, uz bezbedno ponašanje i jasnu grešku/upozorenje ako markeri nedostaju;
   - prepoznaje naslov i poglavlja kao metapodatke;
   - čuva tekst odlomaka i njihove granice dovoljno dobro da se mogu citirati.
4. Predstaviti sadržaj kao dokumente ili odeljke sa stabilnim ID-ovima, npr. `prince-chapter-01`; naslov poglavlja sačuvati uz svaki kasniji chunk.
5. Prikazati osnovnu statistiku pri učitavanju/debug-u: broj poglavlja, broj znakova/reči i da li su Gutenberg markeri uklonjeni.

**Kriterijum prihvatanja:** knjiga se učita lokalno, boilerplate nije u korpusu, a poglavlja ostaju prepoznatljiva za citate.

### 3. Chunking sa strukturom i proverljivim metapodacima

1. Proširiti `Document`/`Chunk` po potrebi da nose `chapter_id`, `chapter_title`, redni broj chunk-a i izvor.
2. Ne praviti chunk preko granice poglavlja. Unutar poglavlja koristiti granice pasusa kad je moguće; fallback na postojeći preklapajući karakter-based splitter.
3. Sačuvati `chunk_size` i `overlap` kao podesive parametre. Prvo koristiti trenutne podrazumevane vrednosti kao baseline; isprobati i alternativu primerenu dužini teksta, npr. `chunk_size=500, overlap=80` znakova. Zabeležiti jedinice (znakovi, ne tokeni).
4. Osigurati validaciju `chunk_size > 0`, `0 <= overlap < chunk_size`, bez praznih chunk-ova; testirati kratak tekst, prazan tekst, pasuse i Unicode.
5. ID chunk-a mora biti stabilan kroz ponovljena učitavanja iste knjige i konfiguracije, npr. `prince-ch03-chunk-004`.

**Kriterijum prihvatanja:** chunk vraća ID, poglavlje i tekst; citat može navesti tačno mesto u knjizi.

### 4. Retrieval top-k

1. Sačuvati jednostavan leksički pristup kao razumljiv baseline, ali ispraviti bodovanje da ne nagrađuje ponavljanje istih reči u jednom chunk-u bez granice; porediti query tokene sa normalizovanim tekstom.
2. Dokumentovati scoring pristup i ograničenja. Kao fakultativno unapređenje razmotriti TF-IDF/BM25 tek pošto baseline radi i meri se; izabrati jednu metodu i objasniti trade-off.
3. Vratiti rezultate sortirane opadajuće po skoru, ograničene na `k`; pri izjednačenju koristiti stabilan redosled po ID-u ili izvornom redosledu.
4. Ne vraćati chunk-ove sa nultim/nepostojećim relevantnim signalom. Prag mora biti konfigurabilan ili opravdan primerima; ne pretpostavljati da svaki upit ima odgovor u knjizi.
5. CLI treba jasno da prikaže upit, ID, poglavlje, skor i tekst svakog pronađenog chunk-a, bar u režimu evidence/debug.
6. Ispitati top-k za `k=2` i `k=3` na istom upitu i objasniti šta se menja.

**Kriterijum prihvatanja:** rangiranje i top-k ponašanje su proverljivi, ponovljivi i imaju testove.

### 5. Grounded odgovor, citati i odbijanje

1. `build_grounded_answer` koristi samo retrieved rezultate; ne dopunjava činjenice iz opšteg znanja.
2. Odgovor ima jasno odvojene sekcije `Answer` i `References`.
3. Svaki navedeni citat mora odgovarati chunk ID-u iz retrieval izlaza i uključiti naslov poglavlja; po mogućnosti dodati kratak direktan citat/odlomak radi provere.
4. U baseline režimu formirati sažet odgovor ekstraktivno iz relevantnih rečenica/odlomaka, ili jasno označiti da je prikazani odgovor sastavljen od evidence odlomaka. Ne predstavljati sirovi kontekst kao parafrazu modela.
5. Odbiti odgovor kada nema rezultata ili podrška ispod opravdanog praga. Poruka treba da kaže da korpus nema dovoljno dokaza; opcionalno prikaži zašto (nema rezultata / nizak skor).
6. Obezbediti da refusal nema citate koji bi sugerisali podršku, a svaki podržani odgovor ima citate.

**Kriterijum prihvatanja:** podržan odgovor se može proveriti u knizi preko citation ID/poglavlja; nepodržan upit završava se refusal-om.

### 6. CLI i konfiguracija

1. Dodati korpus `the-prince` uz postojeće profile; izbore prikazati u `--help`.
2. Dodati putanju ka korpusu ili jasno dogovorenu podrazumevanu lokaciju (`data/the_prince.txt`). Ne ugrađivati apsolutnu putanju lokalnog računara.
3. Omogućiti `--question`, `--chunk-size`, `--overlap`, `--top-k`; po potrebi `--show-context`/`--show-scores` za dokazni izlaz.
4. Prikazati konfiguraciju u rezultatu kako bi se eksperimenti mogli ponoviti.
5. Primeri komandi treba da rade iz direktorijuma projekta na Windows-u i macOS/Linux-u (poziv `python -m src.cli ...`).

### 7. Testovi i evaluacija

Dodati ili dopuniti testove za sledeće slučajeve:

- učitavanje stvarnog fajla, uklanjanje Gutenberg markera, poglavlja i greška za nedostajući fajl;
- stabilni ID-ovi, granice poglavlja, overlap, validacija i Unicode;
- tokenizer i scoring za relevantne/nerelavantne i ponovljene termine;
- sortiranje, `top_k=2`, `top_k=3`, tie-break i prazan rezultat;
- supported pitanje: citati postoje i odgovaraju vraćenim chunk-ovima;
- unsupported pitanje: refusal, bez citata;
- postojeći starter testovi i profil ponašaju se kako je očekivano.

Ručno napraviti mali skup evaluacionih pitanja iz različitih poglavlja:
- najmanje 3 podržana pitanja čiji odgovor je eksplicitno nađen u tekstu;
- najmanje 2 nepodržana pitanja (npr. savremeni događaji koji knjiga ne pokriva);
- za svako pitanje unapred zapisati očekivano poglavlje/ključni dokaz i proveriti retrieval rezultat.

Ne ocenjujemo samo da se kod izvršava: ručno proveriti da li vraćeni odlomci zaista podržavaju tvrdnju i da li sistem odbija pitanja izvan izvora.

### 8. Eksperiment: uticaj chunking-a

1. Izabrati najmanje jedan podržan upit sa konkretnim pojmom i pokrenuti ga sa dve konfiguracije, na primer baseline `140/30` i alternativnom `500/80`.
2. Sačuvati identičan upit, top-k i retrieval rezultate za oba slučaja.
3. Uporediti: da li relevantan kontekst pronađen, da li je odlomak dovoljno potpun, da li citat precizno locira pasus, broj/preklapanje duplikatnih chunk-ova.
4. Napisati kratak zaključak sa stvarnim opažanjima; ne tvrditi da je jedna konfiguracija bolja bez dokaza.

**Kriterijum prihvatanja:** evidence uključuje komande, izlaz za obe konfiguracije i objašnjenje razlike.

### 9. Dokazni materijal i parna predaja

Napraviti `docs/evidence.md` po ta?noj strukturi iz PDF-a (pet Outcome sekcija i pripadaju?e podstavke). Dodatne napomene o testovima, izvoru korpusa, doprinosu para i demo-u dodati posle obaveznog template-a:

1. Outcome 1 — konfiguracije, isti upit, rezultati i poređenje.
2. Outcome 2 — upit, top-k 2 i top-k 3, skorovi i objašnjenje rangiranja.
3. Outcome 3 — podržano pitanje, odgovor, citati i retrieved ID-jevi.
4. Outcome 4 — nepodržano pitanje, retrieved kontekst/skorovi i refusal.
5. Outcome 5 — reproduktivne CLI komande i kompletan supported/unsupported par.
6. Test/komanda za reprodukciju i kratki rezultat.
7. Doprinos oba člana para i ko vodi demo; navesti konkretne fajlove/zadatke svakog člana.
8. Izvor korpusa, izdanje/URL i sve promene čišćenja.

Ne izmišljati rezultate unapred: evidence popuniti nakon izvršavanja implementacije.

## Podela rada u paru

Predlog podele sa zajedničkim pregledom:

- **Član A:** Gutenberg loader, parsiranje poglavlja, metapodaci i chunking.
- **Član B:** retrieval scoring, top-k, grounded odgovor, citati, refusal i CLI.
- **Zajedno:** dogovor API-ja pre rada, integracija, testovi, chunking eksperiment, evidence i demo.

Oboje treba da mogu da objasne ingestion, ranking i refusal; pred predaju zameniti uloge u code review-u i pregledati izmene drugog člana.

## Redosled isporuke i Definition of Done

1. Starter radi i početno ponašanje je zabeleženo.
2. Gutenberg tekst se učitava i deli po poglavljima.
3. Chunk-ovi nose stabilne ID-jeve i metapodatke.
4. Top-k retrieval rangira smisleno i daje vidljive skorove.
5. Odgovor ima proverljive citate ili odbija bez dovoljne podrške.
6. CLI podržava knjigu i eksperimentalne parametre.
7. Testovi pokrivaju pipeline i postojeći starter.
8. Evidentiran je stvarni A/B chunking eksperiment.
9. `evidence.md` pokriva ishode 1–5, komande, rezultate i parni doprinos.
10. Demo može uživo pokazati jedno podržano i jedno nepodržano pitanje.

## Rizici i odluke za praćenje

- **Poglavlja nisu čisto obeležena u plain text-u:** prvo pregledati konkretne markere; parser treba da bude testiran na ovom izdanju i da ne prihvati tiho neispravan korpus.
- **Leksičko rangiranje promašuje parafraze:** zadržati ga kao baseline, probati BM25/TF-IDF samo kao dokumentovano unapređenje; ne menjati metod bez poređenja.
- **Prag refusal-a:** kalibrisati ga nad podržanim i nepodržanim pitanjima; skor sam po sebi nije dokaz semantičke podrške.
- **Preveliki kontekst ili previše duplikata:** porediti veličinu/overlap i eventualno deduplikovati susedne rezultate.
- **Izvorni tekst/encoding:** ostaviti originalni tekst u `data/`, zabeležiti tačan Gutenberg URL i validirati parser na UTF-8.

## Van opsega za prvu predaju

- Hosting aplikacije ili izrada vektorske baze.
- Plaćeni embedding/LLM API kao preduslov.
- Tvrdnja da sistem razume celu knjigu ili da retrieval skor garantuje istinitost.
- Semantički evaluator/LLM-as-a-judge pre nego što postoje osnovni ponovljivi primeri.
