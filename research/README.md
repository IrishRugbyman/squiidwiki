# Research

Source material for the wiki. **Nothing in here is wiki data** - it is what wiki data gets
made out of, and it stays here after seeding so a claim can always be walked back to the
document it came from.

Two kinds of directory sit at this level, and the distinction is the thing to hold on to:

| | what it is |
|---|---|
| `detroit/`, `corsica/` | **one per universe**, holding everything gathered for it |
| `privedatabase/` | **one harvested source**, cutting across universes (Detroit, Chicago and others in one site) |

Anything that only concerns one city belongs in that city's directory. `privedatabase/`
stays separate because a single harvest of one website covers several universes at once,
and splitting it would destroy the provenance.

## The per-universe layout

`detroit/` is the fully worked example; `corsica/` uses the same names for the parts it has.

```
sources/      Citations, ready to become Source rows. Bookmark exports, link lists,
              MDOC lookups. Books and PDFs live here too.
raw/          Unprocessed dumps - copy-paste, harvested page text. Needs triage.
extraction/   Curated notes, ready or nearly ready to seed. This is where research
              turns into something a seed script can read.
documents/    Complete primary records, one directory per case.
tools/        Seed scripts that write to the database, one per body of work.
```

The pipeline runs left to right: `sources/` and `raw/` in, `extraction/` in the middle,
`tools/` writing out. See `detroit/README.md` for what each file in that universe holds.

## Where to start

- **Detroit** - `detroit/README.md`. The largest body of work by far.
  - `detroit/extraction/leads.md` is the queue: fragments that name something real but do
    not resolve to a row yet. Read it before starting a new round.
- **Corsica** - `corsica/extraction/seed-scope.md` defines phase one.
- **privedatabase** - `privedatabase/README.md`, and read its reliability note before
  trusting anything in it.

## Conventions worth knowing before you add to this

- **Seed scripts are idempotent and dry-run by default.** Every one of them checks for an
  existing row before creating, and only writes when passed `--go`. Follow that shape.
- **A tools/ directory holds scripts.** Data the scripts read goes beside it, not in it -
  see `privedatabase/data/` and `privedatabase/batches/`.
- **Say where a fact came from.** Every extraction doc names its source and rates it, and
  records what was searched and *not* found, so nobody repeats a dead end.
- **The hard rules in the root `CLAUDE.md` apply to what leaves here**: never name the
  French source in wiki prose, never hedge in it, and never write into a biography
  something a column already holds.
