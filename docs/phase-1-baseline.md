# Faza 1 — početno stanje i interfejsi

## Da li je ova faza potrebna?

Kratak odgovor: **delimično**. Za obavezne ishode iz PDF-a nije potrebno prvo unapređivati ili predavati starter primer. Ipak, korisno je jednom zabeležiti njegovo početno ponašanje, jer zadatak traži poređenje retrieval-a, a ovo daje referentnu tačku i upozorava na ograničenja pre nego što knjiga postane korpus. Ne treba trošiti vreme na popravljanje startera; primenjujemo naučene koncepte u novoj aplikaciji u root-u.

## Okruženje i način pokretanja

Starteri u `rag-week-6-homework-starter/.venv` nisu upotrebljivi na Windows-u: virtualenv ima `bin/` strukturu i Unix entry-point skripte, ne Windows `Scripts/` i izvršni Python. Sistemski Python 3.14 dostupan je, ali `pytest` nije instaliran (`python -m pytest -q` javlja `No module named pytest`). Zbog toga **test suite nije pokrenut**. Instalacija zavisnosti nije urađena; za kasniju proveru treba napraviti novi lokalni Windows virtualenv u starteru ili koristiti okruženje koje starter podržava.

CLI je pokrenut sistemskim Pythonom iz direktorijuma startera sa podrazumevanim profilom `default`. Komande i başlangıç izlazi su sačuvani ispod. CLI je determinističan uz iste ulaze i kod, ali je izlaz baseline-a prikazan tačno onako kako ga je starter odštampao.

## Početni CLI rezultati

Komanda A:

```powershell
python -m src.cli --question "What is retrieval augmented generation?"
```

Izlaz:

```text
Question:
What is retrieval augmented generation?

Answer:
Grounded response based on retrieved context:
[doc-1-chunk-0] Retrieval augmented generation combines retrieval with text generation. The model should answer using retrieved evidence rather than unsuppo
[doc-2-chunk-0] Chunking splits documents into smaller parts. Good chunk size and overlap improve retrieval quality. Metadata helps filtering and source tra

Corpus profile: default

Refused: False
Citations: doc-1-chunk-0, doc-2-chunk-0
```

Napomena: starter CLI odseca chunk tekst na prikazu, bez oznake da je skraćen.

Komanda B:

```powershell
python -m src.cli --question "Who won the world cup in 1958?"
```

Izlaz:

```text
Question:
Who won the world cup in 1958?

Answer:
Grounded response based on retrieved context:
[doc-1-chunk-0] Retrieval augmented generation combines retrieval with text generation. The model should answer using retrieved evidence rather than unsuppo
[doc-3-chunk-0] If retrieved context does not support a claim, the system should refuse and ask for better evidence. This reduces hallucinations and increas

Corpus profile: default

Refused: False
Citations: doc-1-chunk-0, doc-3-chunk-0
```

Ovaj navodno nepodržani upit **nije odbijen**. Leksički retrieval dobija pogodak od reči poput `the`, `in` i `who`, a prag i odgovor ne proveravaju da li je pronađeni sadržaj semantički dokaz za tvrdnju.

## Trenutna ograničenja startera

- Korpus je ručno ugrađena lista od tri kratka dokumenta (`default`) ili četiri dokumenta (`training-rag`); nema učitavanja lokalne knjige ili fajla.
- Chunking koristi fiksne brojeve **karaktera** (podrazumevano `140`, overlap `30`), spljoštava whitespace i može da preseče rečenicu/usred reči. Ne čuva poglavlje, pasus ili izvorni raspon.
- Tokenizer prepoznaje samo ASCII slova i cifre (`[a-zA-Z0-9]+`), bez stop-word uklanjanja, lematizacije ili obrade interpunkcije specifične za jezik.
- Leksički skor je broj ponovljenih query-token pojava u chunk-u podeljen brojem svih chunk-tokena. Ponavljanje query termina može naduvati skor; česte reči mogu dati lažno relevantan rezultat.
- Rezultati se sortiraju samo po skoru, bez stabilnog tie-break-a; prag `min_score=0.01` je fiksni default argument.
- RAG vraća retrieved chunk tekst kao „answer“, a ne sintetizovan odgovor; nema provere da li kontekst stvarno podržava pitanje. Nizak prag refusal-a (`best.score < 0.02`) nije pouzdan dokaz podrške.
- Podržani odgovor citira chunk ID-jeve, ali ne daje naslov poglavlja, izvor niti citatni odlomak kao odvojenu referencu.
- CLI prima pitanje, veličinu/overlap, top-k i dva hard-coded corpus profile-a. Ne prikazuje score ni pune retrieved rezultate.
- Početno testiranje je blokirano nekompatibilnim preuzetim virtualenv-ом i nedostajućim `pytest`-ом; to je stanje okruženja, ne dokaz da testovi prolaze ili padaju.

## Predloženi interfejsi nove aplikacije

Ovo je dogovoreni početni nacrt za aplikaciju u root-u; možemo ga usvojiti pre implementacije. Ne mora kopirati starterove funkcije ako se tokom uvida u konkretan Gutenberg fajl pojavi bolji, jednostavniji oblik.

### `src/corpus.py`

```python
@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    text: str
    source: str
    chapter_id: str | None = None


def load_book(path: str | Path) -> list[Document]: ...
```

`load_book` učita UTF-8 plain text, validira Gutenberg markere, uklanja boilerplate i vraća poglavlja kao dokumente. Izvorni fajl ostaje netaknut.

### `src/chunking.py`

```python
@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str
    source: str
    chapter_id: str | None = None


def split_text_with_overlap(text: str, chunk_size: int, overlap: int) -> list[str]: ...
def build_chunks(documents: Sequence[Document], chunk_size: int, overlap: int) -> list[Chunk]: ...
```

Chunking ne prelazi granicu dokumenta/poglavlja; `chunk_size`/`overlap` za prvu iteraciju su karakteri, što CLI i dokumentacija moraju jasno reći.

### `src/retrieval.py`

```python
@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    score: float


def retrieve_top_k(
    query: str,
    chunks: Sequence[Chunk],
    k: int = 3,
    min_score: float = 0.0,
) -> list[RetrievalResult]: ...
```

Rezultati su po skoru opadajuće sortirani, deterministički pri izjednačenju; skor i njegova ograničenja moraju biti objašnjivi.

### `src/rag.py`

```python
@dataclass(frozen=True)
class RagAnswer:
    answer: str
    citations: list[str]
    refused: bool
    retrieved: list[RetrievalResult]


def build_grounded_answer(
    question: str,
    chunks: Sequence[Chunk],
    top_k: int = 3,
) -> RagAnswer: ...
```

Retrieval izlaz se vraća zajedno sa odgovorom da CLI/evidence mogu pokazati puno opravdanje. Podržani odgovor mora vezati svaki citat za vraćeni chunk; nepodržan odgovor vraća `refused=True` i prazne citate.

### `src/cli.py`

Predloženi ulaz: `--question` (obavezan), `--corpus` (podrazumevano `the-prince`), `--corpus-path` (podrazumevano root `data/book.txt`), `--chunk-size`, `--overlap`, `--top-k` i `--show-context`. CLI prikazuje konfiguraciju, retrieval chunk ID/poglavlje/skor/tekst, odgovor i citate. Tačne opcije potvrditi kad implementiramo parser i evidence komande.

## Sledeći korak

Pre nego što pređemo na ingestion, treba srediti zavisnost za testove u novom root projektu (minimalno `pytest`, ili standard-library `unittest` ako ne želimo zavisnost) i proveriti encoding/markere `data/book.txt`. Faza 1 je inače dovoljna za donošenje implementacionih odluka; starter ne treba dalje menjati.
