# Faza 3 - chunking sa strukturom i metapodacima

## Dogovorene odluke

Plan vec odredjuje jedinice i osnovno ponasanje, pa nije bilo blokirajucih pitanja za ovu fazu:

- `chunk_size` i `overlap` su broj Python znakova, ne tokena.
- Podrazumevane vrednosti su `140` i `30`; u planu predlozena alternativa je `500` i `80`.
- Chunker normalizuje prelomljene redove unutar pasusa, a granice pasusa cuva kao razmak izmedju pasusa.
- Kada moze, kraj chunka pomera se na kraj pasusa koji staje u dozvoljenu velicinu.
- Dugi pasus se sece po karakterima; sledeci chunk preuzima zadati broj znakova overlap-a.
- Svaki Gutenberg odeljak se deli zasebno, tako da chunk nikada ne prelazi granicu odeljka/poglavlja.

## Implementacija

`src/chunking.py` sada sadrzi:

- `Chunk` sa `chunk_id`, `doc_id`, `chapter_id`, `chapter_title`, `chunk_index`, `text` i `source`.
- `split_text_with_overlap(text, chunk_size=140, overlap=30)` sa validacijom argumenata, praznog teksta, praznih pasusa, Windows/Unix prelomnih redova i Unicode teksta.
- `build_chunks(documents, chunk_size=140, overlap=30)` koji pravi stabilne ID-jeve po odeljku, npr. `prince-section-003-chunk-000`, i prenosi naslov i izvor.

`Chunk.title` je alias za `chapter_title`, tako da prikaz izvora moze da koristi jednostavno ime polja.

## Provera nad stvarnom knjigom

| Konfiguracija (znakovi) | Broj chunk-ova | Najveca duzina | Prazni chunk-ovi | Odeljaka sa chunk-ovima |
|---|---:|---:|---:|---:|
| `140 / 30` | 2,703 | 140 | 0 | 29 |
| `500 / 80` | 804 | 500 | 0 | 29 |

Ovo su osnovne velicine korpusa za proveru implementacije, ne zakljucak o retrieval kvalitetu. Poredjenje kvaliteta sa istim upitom pripada eksperimentalnoj fazi plana.

## Testovi

Dodato je `tests/test_chunking.py` sa pokrivanjem:

- granica pasusa i overlap-a;
- fallback-a za dugi pasus;
- praznog i kratkog teksta;
- neispravnih velicina/overlap-a;
- Windows CRLF i Unicode teksta;
- stabilnih ID-jeva i prenosa metapodataka;
- praznih dokumenata i odvajanja poglavlja.

Pokretanje iz root-a:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Rezultat: `16 passed` (testovi korpusa i chunking-a).
