# Phase 8 — uticaj chunking-a

## Izabrani upit i uslovi

**Upit: `When is it safer to be feared than loved?`**

Upit je izabran zato što XVII poglavlje eksplicitno kaže da je sigurnije biti predmet straha nego ljubavi kada se jedno od ta dva mora žrtvovati. Očekujemo taj dokaz u citiranom odgovoru. Upit je sačuvan i u [results.json](experiments/phase-8/results.json), zajedno sa SHA-256 izvornog korpusa, parametrima, komandama, skorovima i punim tekstom pronađenih chunk-ova.

U oba pokretanja koristimo isti `data/book.txt`, isti upit, leksički retrieval, `top_k=3` i `min_score=0.5`. Menjamo zajedno veličinu chunk-a i overlap: `140/30` prema `500/80`, u karakterima. Zato ovaj eksperiment poredi dve konfiguracije; ne izoluje zasebni uticaj veličine i overlap-a.

## Komande i sačuvani izlazi

Pokrenuti iz root-a projekta:

```sh
python -m src.cli --corpus the-prince --corpus-path data/book.txt --question "When is it safer to be feared than loved?" --chunk-size 140 --overlap 30 --top-k 3 --min-score 0.5 --show-scores
python -m src.cli --corpus the-prince --corpus-path data/book.txt --question "When is it safer to be feared than loved?" --chunk-size 500 --overlap 80 --top-k 3 --min-score 0.5 --show-scores
```

Obe komande su izvršene uspešno. Kompletni UTF-8 CLI izlazi, uključujući Answer, References i sve retrieved odlomke, sačuvani su u [140-30.txt](experiments/phase-8/140-30.txt) i [500-80.txt](experiments/phase-8/500-80.txt).

## Izmereni rezultati

| Svojstvo | 140/30 | 500/80 |
|---|---:|---:|
| Ukupan broj chunk-ova u knjizi | 2703 | 804 |
| Broj vraćenih rezultata | 3 | 3 |
| Karakteri u vraćenim tekstovima, sa ponavljanjem | 359 | 1081 |
| Skor najbolje rangiranog odlomka | 1.000 | 1.000 |
| Dužina citiranog odlomka | 139 | 500 |
| Potpuno identični duplikati u top-3 | 0 | 0 |
| Zajednički sufiks/prefiks rezultata na mestima 2 i 3 | 30 karaktera | 80 karaktera |
| Refusal | Ne | Ne |

Svi vraćeni rezultati pripadaju `CHAPTER XVII.`:

| Konfiguracija | Rang | Chunk ID | Skor |
|---|---:|---|---:|
| 140/30 | 1 | `prince-section-018-chunk-022` | 1.000 |
| 140/30 | 2 | `prince-section-018-chunk-000` | 0.667 |
| 140/30 | 3 | `prince-section-018-chunk-001` | 0.667 |
| 500/80 | 1 | `prince-section-018-chunk-007` | 1.000 |
| 500/80 | 2 | `prince-section-018-chunk-000` | 0.667 |
| 500/80 | 3 | `prince-section-018-chunk-001` | 0.667 |

## Poređenje sadržaja i citata

**Relevantnost:** oba prva rezultata sadrže direktnu tvrdnju „it is much safer to be feared than loved“ i uslov „either must be dispensed with“. Sistem citira upravo taj rezultat, pa je odgovor proverljiv u XVII poglavlju. Skor 1.0 ovde odgovara pronalasku dokaza; to nije opšta garancija semantičke podrške.

**Potpunost:** odlomak 140/30 počinje sa `em in one person` i završava se sa `Because this is to be asserted`. Ključna tvrdnja i uslov su prisutni, ali uvodni deo rečenice nedostaje. Odlomak 500/80 uključuje celo postavljeno pitanje, želju da vladar bude i voljen i zastrašujuć, teškoću spajanja ta dva i navedeni zaključak. Ipak, uključuje i kraj prethodnog stiha i potpis prevodioca, počinje sa `ith all my pow’rs` i završava sa `and as lon`. Veći chunk daje više korisnog konteksta, ali ne garantuje granice rečenice ili reči.

**Ponavljanje:** nema potpuno identičnih chunk-ova, ali rezultati 2 i 3 delimično ponavljaju naslov. Kod 140/30 zajednički tekst je `BETTER TO BE LOVED THAN FEARED` (30 karaktera). Kod 500/80 treći rezultat ponavlja 80 od 81 karaktera drugog rezultata. Veći overlap ovde povećava redundantnost. Ta dva rezultata daju naslov i uvod u temu, a prvi rezultat nosi direktan odgovor.

**Lokacija citata:** svaki odgovor navodi chunk ID, naslov poglavlja i Gutenberg izvor. ID je ponovljiv za isti korpus i iste parametre, ali nije trajni broj pasusa u knjizi. Isti ključni dokaz menja ID sa `chunk-022` na `chunk-007` kada se promeni konfiguracija. Čak i isti ID `chunk-001` označava tekst različite dužine u dve konfiguracije. Za proveru citata potrebno je sačuvati i konfiguraciju; to je urađeno u izlazima i JSON-u. Trenutni chunk metapodaci nemaju broj izvornog pasusa ni karakterne ofsete.

## Zaključak

Za ovaj upit `500/80` daje razumljiviji kontekst uz istu osnovnu tvrdnju i isti najbolji skor. Cena je više prikazanog teksta i veće ponavljanje naslova. `140/30` uspešno nalazi kratak dokaz, uz slabije granice odlomka. Jedan primer nije dovoljan za promenu podrazumevanih parametara ili tvrdnju da veći chunk uvek daje bolji odgovor. Rezultati su dokaz A/B eksperimenta za Phase 8 i mogu se uključiti u završni evidence dokument u Phase 9.
