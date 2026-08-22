"""Backfill member.is_rapper, and strip the claim out of the prose it duplicated.

Two passes. EDITS covers the members whose own biography stated the claim; NAMED
covers rappers the bool applies to whose bio never said so.

The bool now holds "is a rapper", so the prose must not repeat it. Only the
rapper claim is removed; every other fact in the bio is left exactly as it was.
Members whose bio names *someone else* as a rapper (Dre Savage on Polo G,
Poo Poo on Lil Jojo, Lil Duke on Young Pappy, Lil Jeff on Lil Jay, Blood Money
on Shy Glizzy) are deliberately not flagged.
"""

from wikiapi import Api, q  # noqa: E402

# member_id -> new biography (None = leave the bio untouched, only set the flag)
EDITS = {
    # bio was nothing but the rapper claim
    "5ea9ff1c-e516-4c18-8374-4cf6b1b551fe": "",  # Dre
    "b6845e66-1452-4b9a-93f8-078de491f30e": "",  # Pooh Bear
    "532f5b68-50ac-49e4-ba21-954c822dca33": "",  # Royal Baybee
    # rapper claim removed, rest kept verbatim
    "780550c4-9af4-4971-b854-8e5f226bd3d0": (  # Famous Dex
        "Started as an affiliate of the Fly Boy Gang and spent time with STL/EBT. "
        "He was present when BossTop of O'Block was robbed."
    ),
    "c52ed067-243c-4730-9c5c-af302d8441d1": "Close to Scrapp.",  # FTO BigGuy
    "54fbe3c0-774b-49ac-a126-53ffa93563e8": (  # Gino Marley
        "Close to Fredo Santana and Blood Money."
    ),
    "60270dde-3b3b-49bb-bd04-b00275d56542": "Close to Prince Dre of O'Block.",  # Kenny Mac
    "14f57129-edf1-4506-b194-d163bf22e51e": (  # Reggie Baybee
        "Now a comedian. Didn't hesitate to diss his dead enemies. "
        "Had personal beef with Lil John of Lowelife. Fought with Lil John."
    ),
    "e1b069f2-dbd1-490a-9ba8-d30c41ac2b21": "Close to Mexico.",  # T3
    "fbb1a335-dd48-428f-92a3-a92a028fcb5f": (  # Von
        "Released Kill To Survive, Street Life, No Love and Killa Ward on YouTube and SoundCloud."
    ),
    "baf31cbe-ea23-491c-977d-aa5a58b6a616": (  # Sonny (Detroit)
        "Called the leader of the Seven Mile Bloods by prosecutors and its second in command "
        "by street sourcing; younger brother of Smoke. Convicted on 27 August 2018 of six "
        "crimes including racketeering conspiracy, murder in aid of racketeering for the death "
        'of Djuan "Neff" Page, and three counts of attempted murder; acquitted of two weapons '
        "charges. Sentenced in October 2019 to two life terms plus three ten-year terms, all "
        "concurrent, aged 31.  Acquitted of first-degree murder in 2010. In 2013, while running "
        "the gang, he took part in Detroit's Stop the Violence programme, speaking in area high "
        "schools against gang life. Jailed since July 2014, when officers found him with a "
        "loaded semi-automatic and he drew 55 months on a federal gun charge."
    ),
    # flag only: the sentence carries a fact the bool does not hold
    "9b79976a-fe31-4420-a5d3-c3366fe401c3": None,  # King Von, worked with Chief Keef
    "6a92b323-5159-4e2c-ae72-b2936f04c02b": None,  # Shoota Shellz, 'Death of 150'
    "64e5c2c3-753c-47f4-9e4b-37433f69a49b": None,  # YK, diss track vs Tyga/The Game
}

# Known rappers whose bio never made the claim, so there is nothing to strip.
NAMED = [
    "72629aa8-fbde-48c7-b4a5-a5b0655b1e5f",  # Chief Keef
    "0053b6be-439f-4466-9c13-74e0721c95c0",  # Tadoe
    "f0ad662f-d0d8-4c77-8432-1065acb6f9f9",  # Blood Money
    "231b8166-4443-4e12-938a-987b941867be",  # Fredo Santana
    "d85a3159-21b3-4e0f-b121-e5b78269e220",  # Doowop
    # "Capo" is the Front$treet/Glo Gang one; the Killaward 078 Capo is someone else.
    "f86800e9-5953-4c89-87bd-3ae987ceaea7",  # GBE Capo
    "ceb83ea3-b4d0-4061-8937-e52acab7e88b",  # L'A Capone
    "31eb495d-59ee-4e7a-a386-7e26b4fcf9fe",  # FBG Duck
    "d4459f34-93e9-412e-ab5a-4e23ad737d96",  # Lil Durk
    # Lil Reese of Lamron, not any of the nine other members nicknamed Reese.
    "bc941543-49aa-467e-b528-edce801784aa",  # Lil Reese
    "e3929c20-3a13-491b-9ce4-77294765a8e3",  # G Herbo, a/k/a Lil Herb
    "2fd22235-a481-4847-9305-cc9ed78c45fa",  # Lil Bibby
    "d2f98427-3456-42a5-a21d-859888830b50",  # Tay600
    "ec63bb88-0610-4d12-95c2-22c15b1ce29e",  # JB Bin Laden
    "ce535086-e777-4533-8615-384aa8c07fc0",  # Rooga
    "0d70ff0b-d66f-433c-8628-bde63abe19ee",  # King Yella
    "9fa38dfe-bdcf-4d82-ae5f-499e0efa7a6a",  # Memo600
    "9b47c79e-8f87-42c9-b88b-78e3c95bad20",  # Edai
    "20503eab-8b91-4a9a-87a9-59c35f540252",  # Billionaire Black
    # King Lil Jay of STL/EBT, not the four other members nicknamed Lil Jay.
    "b16f6d13-6f5c-4e92-bb10-0687fe42ab50",  # King Lil Jay
    # Lil Jojo of Brick$quad 069. J-Macc carries "Lil Jojo" as an alias, which
    # his own bio contradicts, so he is left alone.
    "a9eed9b0-a3ab-4577-ae1e-9deb1f5bf1c2",  # Lil Jojo
]


def universe_of(mid):
    """Return the member's universe id, or None if the member is gone."""
    rows = q(f"SELECT universe_id::text FROM member WHERE id = '{mid}'")
    return rows[0]["universe_id"] if rows else None


def main():
    """Apply every flag and bio rewrite through the admin API."""
    api = Api()
    for mid, new_bio in list(EDITS.items()) + [(m, None) for m in NAMED]:
        uid = universe_of(mid)
        if uid is None:
            print(f"MISSING {mid}")
            continue
        payload = {"is_rapper": True}
        if new_bio is not None:
            payload["biography"] = new_bio
        res = api.call("PATCH", f"members/{mid}?universe_id={uid}", payload)
        if isinstance(res, dict) and "_error" in res:
            print(f"FAIL {mid}: {res}")
        else:
            print(
                f"ok   {res['display_name']:<15} is_rapper={res['is_rapper']} bio={res['biography']!r}"
            )


main()
