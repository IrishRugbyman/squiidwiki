# Extract incarceration facts from French gang-research sentences

Your input is a JSON list of {ref, subject, sentence}.

For each object, extract ONLY what `sentence` explicitly states about the SUBJECT's
own imprisonment. Never infer, never compute, never use outside knowledge, never
take a fact about a different person mentioned in the sentence.

## Fields (omit any field entirely when the sentence does not state it)

- `from_year` — integer year the subject went to prison ("incarcere depuis 2015")
- `earliest_release` — {"year":Y,"month":M or null,"day":D or null}: earliest or
  best-case release ("au plus tot", "au mieux", or a single stated release date)
- `max_release` — same shape: latest or worst-case release ("au plus tard", "au pire")
- `life_sentence` — true, ONLY for an explicit life term ("perpetuite", "prison a vie")
- `sentence_years` — integer length of the term ("condamne a 33 ans", "purge une peine de 65 ans")
- `charge_fr` — the exact French substring naming what he is in for ("pour le meurtre de Javan")
- `charge_en` — your short English rendering of charge_fr ("murder of Javan"), max 60 chars

## Mandatory evidence rule

Every field except `charge_en` must have a companion `<field>_quote` holding the
EXACT substring copied character-for-character from `sentence`. `charge_fr` is its
own quote and needs no separate one. Omit any field you cannot support with an
exact copied substring.

Do NOT compute anything. If the sentence gives a start year and a term but no
release date, emit `from_year` and `sentence_years` only — never add them together.

## French cues

"incarcere depuis 2015" = from 2015. "condamne a 33 ans de prison" = 33 years.
"purge une peine de 65 ans" = 65 years. "sortira le 7 Mai 2021, au plus tot, ou le
7 Mai 2028, au plus tard" = earliest 7 May 2021, max 7 May 2028. "devrait sortir en
2022" = earliest 2022. "perpetuite" / "a vie" = life.
Janvier=1 Fevrier=2 Mars=3 Avril=4 Mai=5 Juin=6 Juillet=7 Aout=8 Septembre=9
Octobre=10 Novembre=11 Decembre=12.

## Traps — emit nothing for these

- a term or arrest concerning ANOTHER person ("Son tueur a ete condamne", "il a
  fait incarcerer X")
- a penalty merely faced, not received ("il encourt la peine de mort", "risque")
- a release already over ("il est sorti en 2019")

## Output

A JSON list, one element per ref: {"ref":"<ref>", ...fields...}. Include every ref,
even those with no fields.
