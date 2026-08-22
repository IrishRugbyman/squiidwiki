"""Record what the r/Chiraqology "1 Eye (NLMB) x G Farro (NLMB)" thread says.

The thread (2021) is the only source for three things the database did not have:
1Eye's legal name (Michael Smith), the month he died (September 2015, with the
thread itself split on the exact day), and the existence of G Farro, an NLMB
member who appears nowhere in the privedatabase corpus.

Reddit is unreachable from this box (403), so the thread text was pasted in by
hand and the photo pulled from its preview.redd.it URL. The source row is
UNVERIFIED: a search for press coverage of a Michael Smith found dead in Chicago
in September 2015 turned up nothing, and the thread's own author says the
article they once had has since disappeared.

Idempotent: re-running finds the existing source/member by url/nickname.
"""

import subprocess
import sys

from wikiapi import CHICAGO, Api, q

PHOTO = (
    "/tmp/claude-1000/-home-lbzgiu-squiidwiki/"
    "6fb6ab57-fa1f-4c5c-938b-7deccb30a3e2/scratchpad/farro.jpg"
)
THREAD = "https://www.reddit.com/r/Chiraqology/comments/pzbx9c/1_eye_nlmb_x_g_farro_nlmb/"
ACCESSED = "2026-08-22"

ONE_EYE = "6197baaa-0062-4c46-8473-f6abbf901382"
NLMB_SET = "b2ca28cb-db68-4c0d-935f-5ebc5ad64502"

ONE_EYE_BIO = (
    "Named as Michael Smith in a 2021 r/Chiraqology thread, where the poster says "
    "he went missing on 7 September 2015 and his body was found on 11 September. "
    "A second contributor gives 10 September 2015 as the date of death; an earlier "
    "claim in the same thread that BLACKMOBB killed him in 2012 was contradicted by "
    "two others and is not carried here. The killer is not identified. The "
    "privedatabase Chicago pages list him only as a body attributed to BLACKMOBB, "
    "credited to ShawtyHitt. No press coverage of the death has been found, and the "
    "thread's author says the article they once had can no longer be located, so "
    "everything above rests on one anonymous forum thread."
)

G_FARRO_BIO = (
    "NLMB. Known from a single throwback photo posted to r/Chiraqology in 2021, "
    'captioned "1 Eye (NLMB) x G Farro (NLMB)", in which he sits with 1 Eye '
    "(Michael Smith, d. September 2015). Which of the two men in the frame he is "
    "was not stated. Nothing else about him appears in the thread or anywhere in "
    "the privedatabase corpus."
)


def main():
    """Create the source, update 1Eye, create G Farro, attach the photo to both."""
    api = Api()

    mode = api.call("GET", "admin/db-mode")
    if mode.get("mode") != "prod":
        sys.exit(f"backend is in {mode.get('mode')!r} mode, refusing to write")

    # --- source -------------------------------------------------------------
    rows = q(f"SELECT id FROM source WHERE url = '{THREAD}'")
    if rows:
        source_id = rows[0]["id"]
        print(f"source exists  {source_id}")
    else:
        src = api.call(
            "POST",
            "sources/",
            {
                "universe_id": CHICAGO,
                "url": THREAD,
                "title": "1 Eye (NLMB) \U0001f54a️ x G Farro (NLMB)",
                "publication": "Reddit - r/Chiraqology",
                "published_at": {"year": 2021, "precision": "Y", "approx": True},
                "accessed_at": ACCESSED,
                "reliability": "UNVERIFIED",
                "notes": (
                    "Throwback photo post by u/dream-tha-menace9. In the comments the "
                    "poster gives 1 Eye's name as Michael Smith, missing 7 September "
                    "2015, body found 11 September; u/M040win gives 10 September 2015; "
                    "u/051kfala's claim of a 2012 BLACKMOBB killing is contradicted by "
                    "u/AlexRD19 and u/M040win. A deleted comment says 1 Eye's son is "
                    "NoLimit. No article was ever produced in the thread."
                ),
            },
        )
        if "_error" in src:
            sys.exit(f"source create failed: {src}")
        source_id = src["id"]
        print(f"source created {source_id}")

    # --- 1Eye ---------------------------------------------------------------
    cur = api.call("GET", f"members/{ONE_EYE}?universe_id={CHICAGO}")
    src_ids = sorted(set(cur.get("source_ids", [])) | {source_id})
    upd = api.call(
        "PATCH",
        f"members/{ONE_EYE}?universe_id={CHICAGO}",
        {
            "legal_name": "Michael Smith",
            "status": "DEAD",
            # The thread agrees on September 2015 and disagrees on the day, so the
            # day is left out rather than picked. Detail is in the biography.
            "date_of_death": {"year": 2015, "month": 9, "precision": "YM"},
            "biography": ONE_EYE_BIO,
            "source_ids": src_ids,
        },
    )
    if "_error" in upd:
        sys.exit(f"1Eye update failed: {upd}")
    print(f"1Eye updated   {upd['display_name']} / {upd['legal_name']} / {upd['date_of_death']}")

    # --- G Farro ------------------------------------------------------------
    rows = q(f"SELECT id FROM member WHERE nickname = 'G Farro' AND universe_id = '{CHICAGO}'")
    if rows:
        farro_id = rows[0]["id"]
        print(f"G Farro exists {farro_id}")
    else:
        new = api.call(
            "POST",
            "members/",
            {
                "universe_id": CHICAGO,
                "nickname": "G Farro",
                "status": "UNKNOWN",
                "biography": G_FARRO_BIO,
                "affiliations": [{"set_id": NLMB_SET, "is_primary": True}],
                "source_ids": [source_id],
            },
        )
        if "_error" in new:
            sys.exit(f"G Farro create failed: {new}")
        farro_id = new["id"]
        print(f"G Farro created {farro_id}")

    # --- photo, one copy per member ----------------------------------------
    caption = "Throwback photo of 1 Eye and G Farro, posted to r/Chiraqology in 2021"
    for member_id, who in ((ONE_EYE, "1Eye"), (farro_id, "G Farro")):
        existing = q(
            f"SELECT id FROM media WHERE member_id = '{member_id}' AND caption = '{caption}'"
        )
        if existing:
            print(f"photo exists   {who} {existing[0]['id']}")
            continue
        r = subprocess.run(
            [
                "curl",
                "-sS",
                "-X",
                "POST",
                "http://localhost:8001/api/v1/media/",
                "-H",
                f"Authorization: Bearer {api.token}",
                "-F",
                f"file=@{PHOTO};type=image/jpeg",
                "-F",
                f"universe_id={CHICAGO}",
                "-F",
                f"member_id={member_id}",
                "-F",
                f"caption={caption}",
            ],
            capture_output=True,
            text=True,
        )
        print(f"photo {who}: {r.stdout[:200]}{r.stderr[:200]}")


if __name__ == "__main__":
    main()
