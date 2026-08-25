# Primary documents

Full court records and official paperwork, one directory per case. Unlike `sources/`
(citations) and `raw/` (unprocessed dumps), everything here is a complete primary
document held locally, because the issuing sites are unreliable to re-fetch:
`mdocweb.state.mi.us` and Justia both 403 this server, and Michigan appellate PDFs
move when the courts reorganise their site.

Each case directory is named `<surname>-<lower court case number>` and each file is
`YYYY-MM-DD-<court>-<docket>.<ext>`, so the directory sorts chronologically. Keep the
`.pdf` as retrieved and a `.txt` extraction alongside it, since the PDFs are scanned
layouts that grep badly.

Not everything here is a court filing. Material that belongs to a case but has no docket -
a prisoner's own manuscript, correspondence, a photographed exhibit - goes in the same case
directory under a descriptive name plus its own page or item number, and `INDEX.md` says
why the dated naming does not apply. `herbert-07-011024` is the example.

The PDFs, their `.txt` extractions and any scans are **not committed** - `.gitignore`
excludes `research/**/*.pdf`, `research/**/*.txt` and `research/**/*.{jpg,jpeg,png,webp}`
because this repo is public. Only `INDEX.md` is tracked, so it has to carry enough detail
to stand alone: what each document establishes and where to re-fetch it.

Add a matching row to `sources/legal-sources.txt` when a document becomes a
`Source` row in the wiki.
