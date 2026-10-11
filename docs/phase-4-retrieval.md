# Faza 4 - top-k leksicki retrieval

## Metoda

`src/retrieval.py` koristi jednostavan, deterministicki lexical coverage skor:

`score = broj jedinstvenih query termina pronadjenih u chunk-u / broj jedinstvenih query termina`

Pre racunanja skora tekst se normalizuje Unicode NFKC i casefold-om, tokenizuje po Unicode slovima/ciframa, a cesta engleska stop-reci se uklanjaju. Isti termin doprinosi najvise jednom i u upitu i u chunk-u. Time ponavljanje reci ne uvecava rezultat.

Rezultat je izmedju 0 i 1. Funkcija `retrieve_top_k(query, chunks, k=3, min_score=0.0)` izbacuje rezultate sa skorom 0, primenjuje opcioni prag (ukljucujuci granicu), sortira prvo po opadajucem skoru, pa pri izjednacenju po rastucem `chunk_id`. Isti ulazi zato daju isti redosled bez obzira na ulazni redosled chunk-ova. `k` mora biti pozitivan; prag mora biti konacan broj u opsegu `[0, 1]`.

## Trade-off

Ovo je razumljiv baseline koji je pogodan za poredjenje chunking strategija. Ne razume sinonime, morfologiju, redosled reci, fraze ni vaznost retkih reci. Stop-word lista je kratka i engleska jer je korpus na engleskom. Skor oznacava leksicko poklapanje, ne dokaz da odlomak podrzava odgovor. TF-IDF/BM25 ostaju moguce unapredjenje posle baseline merenja.

## Isti upit sa `top_k=2` i `top_k=3`

Upit: `Is it better for a prince to be loved or feared?`

Koriscena konfiguracija: `chunk_size=140`, `overlap=30`; `k` menja samo broj rezultata.

Top 2:

```text
prince-section-018-chunk-001  score=1.000  CHAPTER XVII.
BETTER TO BE LOVED THAN FEARED

Coming now to the other qualities mentioned above, I say that every prince ought to desire to be considered

prince-section-018-chunk-000  score=0.750  CHAPTER XVII.
CONCERNING CRUELTY AND CLEMENCY, AND WHETHER IT IS BETTER TO BE LOVED THAN FEARED
```

Top 3 dodaje:

```text
prince-section-018-chunk-020  score=0.750  CHAPTER XVII.
my shores.

Christopher Pitt.

Upon this a question arises: whether it be better to be loved than feared or feared than loved? It may be an
```

Tokeni posle uklanjanja stop-reci su `better`, `prince`, `loved`, `feared`. Prvi chunk poklapa sva cetiri; drugi i treci po tri. Trece mesto donosi konkretnu recenicu koja je dobar dokaz za temu, dok prva dva rezultata pretezno daju naslov i kontekst. Primer pokazuje da veci `k` moze dodati korisniji dokaz cak i kada mu je skor nizi. Ne pokazuje da je lexical coverage semanticki ispravan uopste.

## Testovi

`tests/test_retrieval.py` pokriva Unicode/stop-word tokenizaciju, neosetljivost na ponavljanje, opadajuce rangiranje, top-k 2/3, stabilno razresavanje izjednacenja, prazan rezultat, prag i neispravne argumente.

Provera iz root-a: `python -m pytest -q` -> `28 passed`.

## Sledeci korak

Prag je dostupan kroz retrieval API. Njegovo ponasanje u RAG refusal logici i prikaz punih retrieval detalja u CLI-ju dolaze u narednim fazama.


## Prosireno poredjenje za `k=5`, `k=7` i `k=10`

Zadrzan je isti upit i konfiguracija (`140/30`). Svako vece `k` vraca isti rangirani prefiks i dodaje naredne rezultate:

| Rang | Chunk ID | Skor | Poglavlje |
|---:|---|---:|---|
| 1 | `prince-section-018-chunk-001` | 1.000 | XVII |
| 2 | `prince-section-018-chunk-000` | 0.750 | XVII |
| 3 | `prince-section-018-chunk-020` | 0.750 | XVII |
| 4 | `prince-section-001-chunk-042` | 0.500 | Introduction |
| 5 | `prince-section-003-chunk-011` | 0.500 | II |
| 6 | `prince-section-008-chunk-037` | 0.500 | VII |
| 7 | `prince-section-018-chunk-022` | 0.500 | XVII |
| 8 | `prince-section-018-chunk-057` | 0.500 | XVII |
| 9 | `prince-section-020-chunk-085` | 0.500 | XIX |
| 10 | `prince-section-027-chunk-055` | 0.500 | XXVI |

`k=5` vraca prva pet rezultata, `k=7` prvih sedam, a `k=10` svih deset prikazanih. Od cetvrtog rezultata skor je 0.500, ali neki pogoci su samo delimicna leksicka poklapanja ili dolaze iz drugog konteksta. Povecan `k` daje veci izbor dokaza, uz vise nebitnog konteksta; naredna RAG faza treba da odabere i citira samo ono sto stvarno podrzava odgovor.

Konkretno, rezultati 4-5 sadrze reci `better`/`loved` u uvodu i poglavlju II, ali ne odgovaraju direktno na pitanje o izboru izmedju ljubavi i straha. Rezultat 6 pominje `better` i `prince` u drugoj temi. Rezultat 7 je ponovo iz XVII poglavlja i daje direktnu tvrdnju da je sigurnije biti feared than loved. Rezultat 8 nastavlja istu raspravu o ljubavi i strahu. Rezultati 9-10 su delimicni pogodci u poglavljima XIX i XXVI, bez odgovarajuceg fokusa na pitanje.

Zato je u ovom primeru `k=3` vec dohvatio najdirektniji odlomak, dok `k=5` ukljucuje dva slabija pogotka; `k=7` dodaje jos jedan relevantan odlomak iz istog poglavlja, a `k=10` siri kontekst sa nekoliko slabih pogodaka. Ovo je primer zasto broj rezultata sam po sebi ne garantuje kvalitet evidence.

Testirana je podrska za `k` vrednosti `2`, `3`, `5`, `7` i `10`, kao i da su rezultati stabilan prefiks bez obzira na broj trazenih rezultata.
