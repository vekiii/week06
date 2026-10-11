# Phase 6 — CLI i konfiguracija

## Interfejs

CLI se pokrece iz root-a projekta komandom `python -m src.cli`. Profil `the-prince` koristi podrazumevani lokalni fajl `data/book.txt`; `--corpus-path` omogucava izbor druge putanje. Podrazumevane vrednosti su chunk size `140`, overlap `30` karaktera, `top-k=3` i prag `0.5`.

`--show-context` prikazuje sve retrieved chunk-ove, a `--show-scores` prikazuje i leksicke skorove. Konfiguracija se ispisuje uz svaki odgovor radi ponovljivosti. Ne postoji dodatni corpus profil u ovoj implementaciji; jedini izbor je `the-prince`.

## Primeri

```sh
python -m src.cli --question "When is it safer to be feared than loved?"
python -m src.cli --question "When is it safer to be feared than loved?" --chunk-size 500 --overlap 80 --top-k 5 --show-scores
python -m src.cli --question "Who won the World Cup in 1958?" --show-context
```

Provera `python -m src.cli --question "When is it safer to be feared than loved?" --top-k 5 --show-scores` nad `data/book.txt` prikazala je konfiguraciju `chunk_size=140 chars, overlap=30 chars, top_k=5, min_score=0.50`, odgovor sa citatom `prince-section-018-chunk-022` iz `CHAPTER XVII.`, i pet retrieved rezultata sa skorovima. Komanda `python -m src.cli --help` prikazuje sve opcije i jedini korpus profil.

## Testovi

`tests/test_cli.py` proverava help/options, pokretanje podrzanog pitanja nad lokalnom knjigom, prikaz konfiguracije i retrieval konteksta, kao i prijavu neispravnog ulaznog korpusa. Kompletna provera: `python -m pytest -q` -> `36 passed`.
