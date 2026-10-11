# Faza 2 — Gutenberg korpus

## Provera izvora

- Lokalni izvor je `data/book.txt`, plain text eBook 1232.
- Proveren je direktan plain-text izvor na [Project Gutenberg](https://www.gutenberg.org/cache/epub/1232/pg1232.txt). Zaglavlje izvora navodi *The Prince*, Niccolò Machiavelli, prevod W. K. Marriott; izdanje je objavljeno 11. februara 2006, poslednji put ažurirano 24. jula 2026.
- Lokalni fajl je validan UTF-8, ima tačno po jedan START i END marker, veličine je 308,019 bajtova. SHA-256: `33496a305f7a4b933784fb5aec95f920fbc3d4687794817e4cc444aa6578d2e4`.
- `Niccolò` sadrži U+00F2 (`ò`); znak nije pokvaren. PowerShell terminal ga je ranije pogrešno prikazao. U samom naslovnom delu tela Gutenberg namerno koristi transliteraciju `Nicolo`.
- Nema potrebe za ponovnim preuzimanjem ili dupliranjem fajla. Fajl ostaje `data/book.txt`, kako je prikazano u root strukturi.

## Urađeno

- Napravljen je `src/corpus.py` sa `Document`, `CorpusFormatError` i `load_book(path)`.
- Loader čita UTF-8/UTF-8 BOM, proverava Gutenbergove granice, uklanja licencu i završni boilerplate i izuzima tabelu sadržaja.
- Tekst se deli na stabilno numerisane odeljke: uvod, 26 poglavlja i dva dodatna dela iz Gutenberg fajla. ID formata je `prince-section-001`; svaki odeljak čuva naslov i Gutenberg izvor.
- Pasusi i prelomi redova ostaju sačuvani unutar odeljaka. Loader ne menja izvorni fajl.
- Dodati su testovi za osnovno parsiranje, UTF-8, stabilnost ID-ja, nedostajući fajl, nedostajuće/neispravne markere i stvarni lokalni korpus.
- `requirements.txt` navodi `pytest>=8.3`; `pytest.ini` ograni?ava automatsko otkrivanje testova na root `tests/`, a `.gitignore` ignori?e Python/pytest cache i virtualenv.

## Rezultat obrade

Loader trenutno vraća 29 odeljaka, ukupno 49,458 reči i 279,309 znakova odeljaka (uključujući njihove unutrašnje prelome pasusa). Ostaju naslov poglavlja i izvor kao metapodaci. Gutenbergova licenca, naslovno zaglavlje i tabela sadržaja nisu deo indeksiranog teksta.

## Provera

`pytest` je instaliran kao `9.1.1` u privremeni virtualenv izvan repozitorijuma. Za ponavljanje lokalno iz root-a aktivirati ili direktno koristiti Python iz virtualenv-a:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Provera tokom ove faze: `7 passed`.

Ne pokretati `pytest` iz root-a bez putanje `tests`, jer bi pytest pronašao i stare testove u pomoćnom starter direktorijumu; starter import-i se sudaraju sa root paketom `src`. Starter nije menjan.

## Napomena za rad u paru

Root `.gitignore` ignoriše `data/`, ali Git trenutno već prati `data/book.txt`; trenutni fajl zato ostaje dostupan u repozitorijumu. Ne menjati to pravilo bez dogovora ako se korpus kasnije zameni ili doda nova putanja.
