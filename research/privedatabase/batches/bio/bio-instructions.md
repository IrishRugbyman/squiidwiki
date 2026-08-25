# Write a member biography from one French source sentence

Input: a JSON list of objects with `ref`, `name`, `sentence` (French) and
`already_in_fields`.

For each object, write a short English biography of the person named in `name`,
drawn ONLY from `sentence`.

## The one rule that matters

**Never write anything the database already stores in its own column.**
`already_in_fields` tells you what those are for this member:

- `sets` — his set or sets. Never write "member of the 600", "of O'Block".
- `gang` — his nation. Never write "a Black Disciple", "a Gangster Disciple".
- `status` — DEAD / LOCKED / FREE. Never write "he is incarcerated", "he is
  deceased", "he was killed" as a bare fact. A *circumstance* is fine and useful
  ("shot outside a nightclub", "serving 33 years for a shooting") because the
  column holds only the state.
- `family` — his relatives. Never write "brother of X", "cousin of Y" for anyone
  listed there.

Dates of birth and death, aliases and incarceration terms also have their own
columns. Leave them out.

## What DOES belong

Everything else the sentence says and no column can hold. Typically:

- music and reputation ("name-checked in a Chief Keef track", "a rapper")
- standing on the street ("one of the men running O'Block", "an OG of Brick City")
- associations that are not family ("was close to Odee", "fell out with X")
- history ("started with the MOB before joining the 600", "switched from the
  Black P. Stones")
- the circumstances of a killing or an arrest, as distinct from the bare fact

## How to write it

- English, plain past or present tense, one to three sentences.
- No invention whatsoever. **Every proper name you write must appear in the
  sentence**, spelled the same way.
- No hedging, no "reportedly", no "according to the source".
- If nothing is left once the columns are removed, return an empty string. That
  is a correct answer and happens often - say so rather than padding.

## Output

A JSON list, one element per ref: `{"ref": "<ref>", "bio": "<text or empty>"}`.
Include every ref.
