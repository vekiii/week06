# Week 6 RAG — The Prince

Lokalni, ekstraktivni RAG primer nad Gutenberg tekstom knjige *The Prince*. Retrieval koristi leksičku pokrivenost termina; odgovor je doslovni odlomak iz pronađenog chunk-a ili refusal ako nema rezultata/dovoljnog skora.

## Pokretanje

Iz root-a projekta:

```powershell
python -m src.cli --question "When is it safer to be feared than loved?"
```

```sh
python -m src.cli --question "When is it safer to be feared than loved?" --chunk-size 500 --overlap 80 --top-k 5
```

`--help` prikazuje sve opcije. Podrazumevani profil je `the-prince`, a korpus je `data/book.txt`. Za drugu putanju koristi `--corpus-path`. Chunk veličina i overlap su u karakterima.

Primer sa retrieval dokazima i skorovima:

```sh
python -m src.cli --question "When is it safer to be feared than loved?" --show-scores
```

`--show-context` ispisuje pronađene chunk-ove; `--show-scores` prikazuje i skorove. Izlaz uključuje konfiguraciju radi ponovljivosti.

Testovi se pokreću komandom `python -m pytest -q`.
