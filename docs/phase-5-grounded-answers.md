# Phase 5 — grounded odgovor, citati i odbijanje

## Implementacija

`src/rag.py` dodaje `build_grounded_answer(question, chunks, top_k=3, min_score=0.5)`. Rezultat sadrzi odgovor, retrieval rezultate, reference i oznaku da li je sistem odbio odgovor. Metoda ne poziva LLM: podrzan odgovor je tacan tekst iz najbolje rangiranog chunk-a, eksplicitno oznacen kao dokazni odlomak. Reference navode isti chunk ID, naslov poglavlja, izvor i tekst koji moze da se proveri.

Ako nema pogodaka, sistem odbija bez referenci. Ako je najbolji skor ispod praga, odbija, objasnjava skor i prag, a pronađene rezultate ostavlja dostupnim za debug. `render()` prikazuje odvojene `Answer` i `References` sekcije; refusal prikazuje da nema citata.

## Izbor praga i provera na korpusu

Podrazumevani prag je `0.5` na pokrivenosti jedinstvenih upitnih termina. Na korpusu sa podrazumevanim chunking-om `140/30`:

- Podrzani upit: “When is it safer to be feared than loved?” daje najbolji skor `1.00`, u `CHAPTER XVII.` (chunk `prince-section-018-chunk-022`). Odgovor se prikazuje kao citirani odlomak, bez parafraze.
- Nepodrzani upit: “Who won the World Cup in 1958?” daje najbolji skor `0.25`; prag ga odbija i ne izdaje citat.

Prag razdvaja ova dva proverena primera. Leksički skor nije semantički dokaz: eksperimentom je upit “Who is the prince of France?” dobio skor `1.00` zbog termina koji se pojavljuju u istom odlomku, iako to ne dokazuje odgovor na pitanje. Zato sistem vraća samo doslovni odlomak i ne tvrdi da je generisao parafrazu ili proverio semantičku implikaciju. Ručna evaluacija relevantnosti ostaje potrebna; semantički verifier nije deo ove faze.

## Testovi

`tests/test_rag.py` proverava tačnost citata prema retrieved chunk-u, prikaz odvojenih sekcija, odbijanje bez rezultata i sa niskim skorom, validaciju praga i par primera nad stvarnim Gutenberg korpusom.
