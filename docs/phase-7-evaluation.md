# Phase 7 — evaluacion i verifikacija

## Skup i reprodukcija

`data/evaluation.json` sadrzi pet unapred definisanih pitanja: tri podrzana sa ocekivanim poglavljem i terminima dokaza, i dva nepodrzana. Pokretanje:

```sh
python -m src.evaluation
python -m pytest -q
```

Evaluacioni skript proverava da li podrzano pitanje nije odbijeno i da li **citirani odlomak** sadrzi ocekivano poglavlje i dokazne termine. Za nepodrzano pitanje proverava refusal i odsustvo referenci. Izlaz prikazuje najbolji retrieved chunk, skor i ID citata.

## Rezultati nad Gutenberg eBook 1232

Konfiguracija: `chunk_size=140`, `overlap=30` karaktera, `top_k=3`, `min_score=0.50`.

| ID | Tip | Najbolji retrieval | Skor | Ishod | Rucna provera |
|---|---|---|---:|---|---|
| `supported-feared-or-loved` | Podrzano | `prince-section-018-chunk-022`, CHAPTER XVII. | 1.00 | Odgovor/citat | Odlomak doslovno kaze da je sigurnije biti feared than loved. |
| `supported-keeping-faith` | Podrzano | `prince-section-019-chunk-003`, CHAPTER XVIII.[1] | 1.00 | Odgovor/citat | Odlomak pocinje tvrdnjom da je pohvalno da princ odrzi veru i zivi sa integritetom. |
| `supported-fox-and-lion` | Podrzano | `prince-section-020-chunk-120`, CHAPTER XIX. | 0.75 | Odgovor/citat | Citirani odlomak izricito imenuje fox i lion kao prirode koje princ treba da imitira. |
| `unsupported-world-cup` | Nepodrzano | `prince-section-001-chunk-083`, INTRODUCTION | 0.25 | Refusal, bez citata | Slab leksicki pogodak dolazi od reci “won” i “world”; odlomak ne govori o prvenstvu 1958. |
| `unsupported-current-population` | Nepodrzano | `prince-section-001-chunk-059`, INTRODUCTION | 0.33 | Refusal, bez citata | Pominjanje Rima u istorijskom kontekstu ne daje trenutnu populaciju. |

Rezultat komande `python -m src.evaluation`: **5/5 passed**. U ovoj fazi rezultat testova `python -m pytest -q` bio je **37 passed**. Podrzana pitanja imaju eksplicitan dokaz u samom citatu; nepodrzani slucajevi odbijaju se ispod praga. Ovo je mali, rucno odabran skup, ne statisticka procena kvaliteta celog sistema.

Nakon Milanove dopune 11 automatizovanih testnih slucajeva, provera od 2026-10-13 daje **48 passed**; evaluacija ostaje **5/5 passed**. Dopuna obuhvata granicu praga, prazna pitanja, CLI greske i proveru da ocekivani dokaz mora biti u citiranom odlomku. [Opis doprinosa i zavrsni rezultati](evidence.md), [aktuelni izlaz testova](submission/tests.txt).

## Ogranicenja

Leksički skor moze da pronadje reci iz pitanja bez odgovora na njegovo znacenje. Evaluacioni skup zato proverava citirani tekst prema unapred poznatom poglavlju/dokaznim terminima, a ne samo uspeh retrieval-a. Rezultat 5/5 vazi samo za ovih pet konkretnih primera. Dodati varijante formulacije, parafraze, pitanja sa vise potrebnih odlomaka i negativne primere sa visokim leksickim preklapanjem pre nego sto se donosi siri zakljucak o refusal pouzdanosti.
