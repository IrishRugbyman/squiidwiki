# Corsica research

Source material for the Corsica universe (`6f9b8d0a-0d3a-4086-bfc1-2a4e9025c1ae`). Same
layout as `../detroit/`, with the parts that exist so far.

```
sources/      The two books the extraction rests on
extraction/   Curated notes, ready to seed
```

## sources/

- `vendetta-lazard-galland-2020.epub` - *Vendetta*, Violette Lazard and Marion Galland
  (Plon, 2020). The main narrative source.
- `ca-dezingue-en-corse-3-blog-a-part.pdf` - "Ça dézingue en Corse 3", Blog à part.

Both were renamed on 2026-08-25 from the filenames they were downloaded with, which
carried archive hashes and ISBNs and sorted badly.

## extraction/

- `people.md` - curated people, ready to seed as `Member` / `Incident` / `Source`. Read its
  scope note first: the four names it began with are one case, not four leads.
- `seed-scope.md` - what phase one creates, scoped to exactly what `people.md` sources: the
  Ziglioli case, the war behind it, and the deaths of the four men in it. About 40 primary
  records. Checked against the live models rather than against `CLAUDE.md`.

The executable form of `seed-scope.md` is `backend/app/scripts/seed_corsica.py`.

## Note on the gang table

Migration `33ac22d53ce8` backfilled five Chicago nations into every universe that existed
at the time, which is wrong for Corsica. That was **cleared for this universe on
2026-08-20**. Check `gang` before seeding if a new universe is added.
