"""Seed phase 1 of the Corsica universe: the Ziglioli case and the Memmi war.

Scope, sourcing and the reasoning behind every modelling choice live in
`~/squiidape/research/corsica/extraction/seed-scope.md`. This script is the executable form of that
document and nothing here is invented: if a fact is not in `people.md` with a
citation, it is not seeded.

Goes through the CRUD layer rather than raw SQL so that slug generation, the
audit log, the bilateral-relationship normalisation and the incident-driven
death sync all run exactly as they would from the API.

Idempotent: every entity is looked up by (universe, natural key) first, so a
second run creates nothing and reports what already existed. Safe to re-run
after a partial failure.

Run from backend/:
  .venv/bin/python -m app.scripts.seed_corsica          # dry run, prints the plan
  .venv/bin/python -m app.scripts.seed_corsica --apply  # writes
"""

import argparse
import asyncio
import sys
import uuid

from sqlalchemy import select, text

from app.core.database import _session_factories
from app.core.enums import (
    BusinessRole,
    BusinessStatus,
    BusinessType,
    DatePrecision,
    IncidentType,
    MemberStatus,
    ParticipantOutcome,
    ParticipantRole,
    SetRelationshipType,
    SetStatus,
    SourceReliability,
)
from app.core.fuzzy_date import FuzzyDate
from app.crud.business import create_business
from app.crud.gang import create_gang
from app.crud.gang_set import create_gang_set, end_set_relationship
from app.crud.incident import create_incident
from app.crud.member import create_member, update_member
from app.crud.municipality import create_municipality
from app.crud.source import create_source
from app.models import (
    Business,
    Gang,
    GangSet,
    Incident,
    Member,
    Municipality,
    SetRelationship,
    Source,
)
from app.schemas.business import BusinessCreate, BusinessMemberIn
from app.schemas.gang import GangCreate
from app.schemas.gang_set import SetCreate
from app.schemas.incident import IncidentCreate, ParticipantCreate
from app.schemas.member import MemberCreate, MemberSetAffiliationIn, MemberUpdate
from app.schemas.municipality import MunicipalityCreate
from app.schemas.source import SourceCreate

UNIVERSE_SLUG = "corsica"


def ymd(y: int, m: int, d: int) -> FuzzyDate:
    return FuzzyDate(year=y, month=m, day=d, precision=DatePrecision.YMD)


def ym(y: int, m: int) -> FuzzyDate:
    return FuzzyDate(year=y, month=m, precision=DatePrecision.YM)


def yr(y: int, approx: bool = False) -> FuzzyDate:
    return FuzzyDate(year=y, precision=DatePrecision.Y, approx=approx)


# --------------------------------------------------------------------------
# Municipalities. Ajaccio, Bastia and Corte already exist with geometry.
# (name, parent name or None, note)
MUNICIPALITIES = [
    ("Taglio-Isolaccio", None),
    ("Cervione", None),
    ("Vescovato", None),
    ("Arena", "Vescovato"),
    ("Sorbo-Ocagnano", None),
    ("Biguglia", None),
    ("Borgo", None),
    ("Cardo", "Bastia"),
    ("La Porta", None),
]

GANGS = [
    (
        "Brise de Mer",
        ["La Brise", "Gang de la Brise de Mer"],
        "Formed in the late 1970s around the bar La Brise de Mer on the old port of "
        "Bastia, run by Antoine Castelli, which gave the group its name. Took the "
        "Haute-Corse nightclub and gaming economy by destroying the Memmi clan between "
        "1981 and 1983, then spread to mainland France, Italy, North Africa and Latin "
        "America. Fragmented into rival clans (Mariani, Guazzelli, Santucci) that fought "
        "each other through the late 2000s.",
    ),
    (
        "Clan Memmi",
        ["Bande à Memmi"],
        "The established Haute-Corse power of the 1970s, run from Corte by Louis Memmi, "
        "whom the press of the day called the 'juge de paix du milieu'. Held the gaming "
        "machines and protected the nightclub owners of Haute-Corse. Destroyed by the "
        "Brise de Mer between 1981 and 1983.",
    ),
]

# name -> (gang name, status, municipality name, bio)
SETS = {
    "Brise de Mer": (
        "Brise de Mer",
        SetStatus.ACTIVE,
        "Bastia",
        "The founding crew, before the clans split off. In 1981-85 the Brise still "
        "operated as one group out of the bar on the old port.",
    ),
    "Clan Memmi": (
        "Clan Memmi",
        SetStatus.EXTINCT,
        "Corte",
        "Louis Memmi's crew. Over twenty of its people were killed between 1980 and "
        "1983; the clan did not survive the war.",
    ),
}

# legal_name -> dict
# Bilateral family links, applied after every member exists because `family` holds
# member UUIDs. Only one side of each pair is listed: _sync_bilateral_family writes
# the inverse. Relatives who are not members (Me Jean-Louis Seatelli, Robert
# Moracchini junior) cannot go here at all, so they stay in the biographies.
FAMILY = [
    ("Daniel Ziglioli", "brother", "Gérard Ziglioli"),
    ("Pierre-Marie Santucci", "brother", "François-Marie Santucci"),
    ("Louis Memmi", "brother", "Pierre-Jean Memmi"),
    ("Daniel Ziglioli", "cousin", "Christian Leoni"),
]

# legal_name -> dict
MEMBERS = {
    "Daniel Ziglioli": dict(
        status=MemberStatus.DEAD,
        dob=yr(1950, approx=True),
        date_of_death=ymd(1982, 9, 14),
        gang=None,
        set=None,
        biography=(
            "Ran a family wholesale drinks business at Cervione and owned the Le Castel "
            "discothèque at Taglio-Isolaccio. Close to the Memmi clan without belonging "
            "to it. Shot eight times with large-calibre rounds as he left his warehouse "
            "at 18:00 on 14 September 1982, aged 32, and died in the ambulance. The "
            "Brise wanted Le Castel: two of its members had been thrown out of the club "
            "by force, and an affront over a deception is said to have been grafted onto "
            "the dispute. The only killing of the Memmi war that ever produced a trial."
        ),
    ),
    "Gérard Ziglioli": dict(
        status=MemberStatus.DEAD,
        date_of_death=ymd(1983, 4, 14),
        gang=None,
        set=None,
        biography=(
            "Daniel Ziglioli's brother. Came back from the mainland to carry out the "
            "vendetta for Daniel's murder and was killed in April 1983 before he could."
        ),
    ),
    "Robert Moracchini": dict(
        status=MemberStatus.DEAD,
        dob=ymd(1959, 6, 6),
        date_of_death=ymd(2025, 3, 29),
        gang="Brise de Mer",
        set="Brise de Mer",
        from_date=yr(1978, approx=True),
        biography=(
            "Co-founder of the Brise de Mer, born at La Porta. Managed a bar on the "
            "place Saint-Nicolas in Bastia and later ran Le Continental; inseparable "
            "from François-Marie 'Francis' Santucci. Principal accused at the 1985 "
            "Dijon trial for the Ziglioli murder, and acquitted.\n\n"
            "In October 1986 a fifty-officer task force went after the Brise's "
            "finances, backed by prefect François Garsi, who had sworn to 'get them the "
            "way the Americans got Al Capone'. Moracchini was taken into custody at 27, "
            "driving a Porsche bought in the name of his bar, of which his mother was "
            "the official manager. Double books were found at the Palais des Glaces, "
            "understating profit by roughly a million francs. He took 20 months (12 "
            "suspended) in 1987 for abus de biens sociaux.\n\n"
            "From the 2000s he stepped back from crime and ran a bistro and a tabac in "
            "Bastia. He summited Everest in May 2023, aged 63. On 29 March 2025 he was "
            "shot several times with a 9mm in the street near his home on the rue du "
            "Commandant Luce-de-Casabianca, in central Bastia, at about 08:00. By then "
            "he was one of the last of the Brise's founding generation still alive."
        ),
    ),
    "Pierre-Marie Santucci": dict(
        status=MemberStatus.DEAD,
        dob=yr(1957, approx=True),
        date_of_death=ymd(2009, 2, 10),
        gang="Brise de Mer",
        set="Brise de Mer",
        from_date=yr(1978, approx=True),
        biography=(
            "Founding member of the Brise de Mer and later head of one of its clans. "
            "Younger brother of François-Marie 'Francis' Santucci; where Francis was the "
            "calm strategist, Pierre-Marie was impulsive and violent, and became the "
            "group's gâchette. At the 1985 Dijon trial he gave his profession as waiter "
            "at La Brise de Mer and told off the presiding judge when a question "
            "displeased him. He was acquitted.\n\n"
            "Arrested at Sartène with Francis Mariani and Maurice Costa on 5 July 2000. "
            "On 31 May 2001 the three walked out of Borgo prison in sandals on the "
            "strength of a forged fax purporting to come from the Ajaccio tribunal, "
            "correctly signed and naming the right juge des libertés, actually sent from "
            "a hotel in Aix-en-Provence.\n\n"
            "By 2009 he had grown quiet and rarely went out except for his near-nightly "
            "card game at Chez Fanfan in Arena, Vescovato. Leaving the bar after dark on "
            "10 February 2009, lit by a streetlamp on the near-empty car park, he was "
            "killed by a single sniper round through the heart, fired from about eighty "
            "metres across the road. No one was ever charged."
        ),
    ),
    "Georges Seatelli": dict(
        status=MemberStatus.DEAD,
        date_of_death=ymd(1998, 8, 21),
        gang="Brise de Mer",
        set="Brise de Mer",
        from_date=yr(1982, approx=True),
        aliases=["le Gris"],
        biography=(
            "Founding member of the Brise de Mer, known as 'le Gris'. The odd one out "
            "socially: the son and grandson of a notary, a brilliant student who never "
            "finished his law degree at Aix-en-Provence, leaving the faculty for good in "
            "December 1982 to join the clan. His brother did finish: Me Jean-Louis "
            "Seatelli is a leading criminal barrister at the Bastia courthouse.\n\n"
            "Charged with complicity in the Ziglioli murder and acquitted at Dijon in "
            "1985. His family house at Cardo, above Bastia, had been destroyed on 28 "
            "December 1982 with two gas bottles and several kilos of dynamite. A "
            "childhood friend of Augustin-Dominique 'Mimi' Viola, later named in a 1999 "
            "prefecture note as the Brise's intermediary close to the president of the "
            "Haute-Corse conseil général.\n\n"
            "Shot dead in August 1998 while having lunch on the terrace of a beach "
            "restaurant south of Bastia, hit several times in the back by two "
            "unidentified gunmen. His son was killed at 18, shot by a shopkeeper he was "
            "trying to rob."
        ),
    ),
    "François-Marie Santucci": dict(
        status=MemberStatus.DEAD,
        date_of_death=ym(1992, 7),
        gang="Brise de Mer",
        set="Brise de Mer",
        from_date=yr(1978, approx=True),
        aliases=["Francis"],
        biography=(
            "Founding member of the Brise de Mer and its most charismatic figure: "
            "intelligent, calm, a strategist with the bearing of an executive, the man "
            "the group listened to. Inseparable from Robert Moracchini. It was Francis "
            "who went up to Corte to tell Louis Memmi that the nightclubs now belonged "
            "to the young men; Memmi laughed it off, and the war followed. Died of "
            "cancer in July 1992."
        ),
    ),
    "Louis Memmi": dict(
        status=MemberStatus.DEAD,
        dob=yr(1931, approx=True),
        date_of_death=ymd(1981, 9, 10),
        gang="Clan Memmi",
        set="Clan Memmi",
        biography=(
            "Head of the Haute-Corse milieu from Corte, in his fifties by 1981, whom the "
            "press of the day half-affectionately called the 'juge de paix du milieu'. "
            "Made his money on gaming and slot machines and protected the nightclub "
            "owners of Haute-Corse. Two convictions and one murder acquittal on his "
            "record. He had eliminated his own rivals in his time.\n\n"
            "Shot dead at 04:40 on 10 September 1981 under the century-old olive tree in "
            "his garden at Corte, after a night playing cards at the Niolu fair, by two "
            "gunmen hidden in the scrub. Fifty thousand francs were found in his pocket. "
            "Over two thousand people attended the funeral. He had left instructions: "
            "'ni fleurs ni couronnes'. The killing was never judicially solved and it "
            "opened the Brise de Mer's war."
        ),
    ),
    "Pierre-Jean Memmi": dict(
        status=MemberStatus.DEAD,
        date_of_death=yr(1982, approx=True),
        gang="Clan Memmi",
        set="Clan Memmi",
        biography=(
            "Louis Memmi's brother, who swore to punish his killers. Shot dead on the "
            "cours Paoli, the main street of Corte, in the autumn of 1982."
        ),
    ),
    "Christian Leoni": dict(
        status=MemberStatus.UNKNOWN,
        gang="Brise de Mer",
        set="Brise de Mer",
        from_date=yr(1985, approx=True),
        biography=(
            "Daniel Ziglioli's own cousin. At the 1985 Dijon trial he appeared for the "
            "defence, testifying that Robert Moracchini had been with him at the Casone "
            "stadium in Borgo on the evening of the murder. He had never mentioned this "
            "before and had never been interviewed during the investigation. The Ziglioli "
            "family shouted betrayal in open court. He went on to become the Brise de "
            "Mer's banker, distributing the proceeds among the members and placing them "
            "in the legal economy."
        ),
    ),
}

# (name, type, municipality, status, description, [(member, role)])
BUSINESSES = [
    (
        "Le Castel",
        BusinessType.NIGHTLIFE,
        "Taglio-Isolaccio",
        BusinessStatus.CLOSED,
        "Daniel Ziglioli's discothèque, and the reason he was killed: the Brise wanted "
        "it, and two of its members had been thrown out of the club by force.",
        [("Daniel Ziglioli", BusinessRole.OWNER)],
    ),
    (
        "Ziglioli (wholesale drinks)",
        BusinessType.RETAIL,
        "Cervione",
        BusinessStatus.CLOSED,
        "The Ziglioli family's wholesale drinks business. Daniel was shot leaving its "
        "warehouse on 14 September 1982.",
        [("Daniel Ziglioli", BusinessRole.OWNER)],
    ),
    (
        "La Brise de Mer",
        BusinessType.HOSPITALITY,
        "Bastia",
        BusinessStatus.ACTIVE,
        "The bar on the old port of Bastia, run by Antoine Castelli, where the group "
        "formed and from which it took its name. Bombed on 28 November 1982.",
        [],
    ),
    (
        "Le Continental",
        BusinessType.NIGHTLIFE,
        "Bastia",
        BusinessStatus.ACTIVE,
        "Robert Moracchini's bar. His mother was the official manager, and the Porsche "
        "he drove was bought in the bar's name. His 1987 conviction for abus de biens "
        "sociaux concerned his stake in it.",
        [("Robert Moracchini", BusinessRole.OWNER)],
    ),
    (
        "Palais des Glaces",
        BusinessType.NIGHTLIFE,
        "Bastia",
        BusinessStatus.ACTIVE,
        "Searched in the October 1986 crackdown, where investigators found a double set "
        "of books understating profit by roughly one million francs.",
        [("Robert Moracchini", BusinessRole.BENEFICIARY)],
    ),
    (
        "Le Saint-Nicolas",
        BusinessType.NIGHTLIFE,
        "Bastia",
        BusinessStatus.ACTIVE,
        "Searched alongside Le Continental and the Palais des Glaces in October 1986.",
        [("Robert Moracchini", BusinessRole.BENEFICIARY)],
    ),
    (
        "L'Apocalypse",
        BusinessType.NIGHTLIFE,
        None,
        BusinessStatus.ACTIVE,
        "The star nightclub of the island, also targeted in the October 1986 crackdown. "
        "Its manager Gilbert Voillemier was taken into custody.",
        [],
    ),
    (
        "Chez Fanfan",
        BusinessType.HOSPITALITY,
        "Arena",
        BusinessStatus.ACTIVE,
        "The bar on the route nationale at Arena where Pierre-Marie Santucci played "
        "cards almost every night. He was shot dead on its car park on 10 February 2009.",
        [],
    ),
]

# (title, url, publication, published_at, reliability, notes)
SOURCES = [
    (
        "Vendetta",
        "https://isbnsearch.org/isbn/9782259277525",
        "Plon",
        yr(2020),
        SourceReliability.HIGH,
        "Violette Lazard & Marion Galland, Plon, 2020, ISBN 9782259277525. The primary "
        "source for this universe: an investigative account sourced to court files, "
        "police records, named interviews and dated press. NB the URL is an ISBN lookup "
        "because Source.url is NOT NULL and this is a printed book.",
    ),
    (
        "Assassinat de Louis Memmi",
        "https://www.corsematin.com/",
        "Corse-Matin",
        ymd(1981, 9, 11),
        SourceReliability.MEDIUM,
        "Cited in Vendetta. Contemporary report of the Memmi killing and the Niolu fair "
        "card game. Not consulted directly; retrieve from the Corse-Matin archive.",
    ),
    (
        "Assassinat de Daniel Ziglioli",
        "https://www.corsematin.com/",
        "Le Provençal-Corse",
        ymd(1982, 9, 16),
        SourceReliability.MEDIUM,
        "Cited in Vendetta. Source of the 'époux modèle / travailleur assidu / père "
        "admirable' description. Not consulted directly.",
    ),
    (
        "Procès Ziglioli, cour d'assises de Dijon",
        "https://www.corsematin.com/",
        "Corse-Matin",
        ymd(1985, 5, 31),
        SourceReliability.MEDIUM,
        "Cited in Vendetta. Contains the Ziglioli family's reaction to Christian Leoni's "
        "alibi testimony. Not consulted directly.",
    ),
    (
        "Le procès de la Brise de Mer",
        "https://www.lecanardenchaine.fr/",
        "Le Canard enchaîné",
        ym(1985, 6),
        SourceReliability.MEDIUM,
        "Louis-Marie Horeau's account of the Dijon trial, cited in Vendetta. Not "
        "consulted directly.",
    ),
    (
        "Liste de personnes assassinées en Corse",
        "https://fr.wikipedia.org/wiki/Liste_de_personnes_assassin%C3%A9es_en_Corse",
        "Wikipédia",
        None,
        SourceReliability.MEDIUM,
        "Consulted 2026-08-20.",
    ),
    (
        "Robert Moracchini",
        "https://fr.wikipedia.org/wiki/Robert_Moracchini",
        "Wikipédia",
        None,
        SourceReliability.MEDIUM,
        "Consulted 2026-08-20. Source of the birth date and place, the Everest ascent "
        "and the 1987 conviction.",
    ),
    (
        "Gang de la Brise de Mer",
        "https://en.wikipedia.org/wiki/Gang_de_la_Brise_de_Mer",
        "Wikipedia",
        None,
        SourceReliability.MEDIUM,
        "Consulted 2026-08-20.",
    ),
    (
        "Pierre-Marie Santucci, figure du banditisme corse, abattu",
        "https://www.france24.com/fr/20090210-pierre-marie-santucci-figure-banditisme-corse-abattu-",
        "France 24",
        ymd(2009, 2, 10),
        SourceReliability.HIGH,
        "Consulted 2026-08-20. 403s non-browser clients; open in a browser.",
    ),
    (
        "Corse: un fondateur présumé du gang de la Brise de Mer assassiné",
        "https://www.20min.ch/fr/story/corse-un-fondateur-presume-du-gang-de-la-brise-de-mer-assassine-103313826",
        "20 minutes",
        ymd(2025, 3, 29),
        SourceReliability.MEDIUM,
        "Consulted 2026-08-20. Reports the Moracchini killing.",
    ),
]


def _incidents(mem: dict, muni: dict) -> list[tuple]:
    """(key, IncidentCreate kwargs); key is the idempotency handle."""
    return [
        (
            "memmi-1981",
            dict(
                type=IncidentType.MURDER,
                date=ymd(1981, 9, 10),
                municipality_id=muni.get("Corte"),
                location_text="His garden, Corte",
                narrative=(
                    "Louis Memmi was shot dead at 04:40 under the century-old olive tree "
                    "in his garden at Corte, after a night playing cards at the Niolu "
                    "fair. Two gunmen were hidden in the scrub; he did not reach the "
                    "third step. His wife was asleep in the flat above the restaurant "
                    "the couple ran. Fifty thousand francs were found in his pocket. The "
                    "next day's papers wondered about a gambling dispute; nobody yet "
                    "suspected a rival clan had emerged. Never judicially solved. This "
                    "killing opened the Brise de Mer's war."
                ),
                participants=[
                    ("Louis Memmi", ParticipantRole.VICTIM, ParticipantOutcome.KILLED, False, None)
                ],
            ),
        ),
        (
            "ziglioli-1982",
            dict(
                type=IncidentType.MURDER,
                date=ymd(1982, 9, 14),
                municipality_id=muni.get("Cervione"),
                location_text="Outside his warehouse, Cervione",
                narrative=(
                    "Daniel Ziglioli, 32, left his family's wholesale drinks warehouse at "
                    "18:00 and was hit eight times with large-calibre rounds. He died in "
                    "the ambulance. He also owned the Le Castel discothèque, which the "
                    "Brise wanted; two of its members had been thrown out of the club by "
                    "force, and an affront over a deception is said to have been grafted "
                    "onto that dispute.\n\n"
                    "This was the only killing of the Memmi war that produced a trial, "
                    "and the only case where police gathered enough to identify the "
                    "shooters. A witness saw two figures reach a car after the shots. "
                    "Minutes later an off-duty border-police officer driving home passed "
                    "the car and saw a passenger throw a large package into the Golo. He "
                    "thought he recognised Robert Moracchini, doubted himself because "
                    "Moracchini should have been in prison, checked the files, and found "
                    "he had been released days earlier. The river was dredged at the road "
                    "bridge and the package held the murder weapon. Moracchini went "
                    "straight back to prison; Seatelli and Santucci fled and were caught "
                    "on 2 December 1982 in an old house at Sorbo-Ocagnano with a shotgun, "
                    "an Italian military rifle, large-calibre weapons, wigs and gloves. "
                    "Seatelli was charged with complicity, Santucci with assassinat.\n\n"
                    "The trial opened at Dijon on 28 May 1985, moved off the island to "
                    "avoid pressure. It collapsed. The police witness retracted, saying "
                    "he no longer remembered seeing Moracchini and on reflection thought "
                    "he had not. Other witnesses sent medical certificates and stayed "
                    "away. Nine Sporting Club de Bastia players flew to Dijon to support "
                    "the alibi. Daniel Ziglioli's own cousin, Christian Leoni, testified "
                    "that Moracchini had been with him at the Casone stadium in Borgo. "
                    "Men in black sat in the front row throughout, watching the jurors. "
                    "The avocat général asked for fifteen years against Moracchini and "
                    "Santucci and eight to ten against Seatelli. On 1 June 1985 the court "
                    "acquitted all three; the jury had forty questions to answer and "
                    "deliberated for thirty minutes. No investigation into possible juror "
                    "corruption was ever opened."
                ),
                participants=[
                    (
                        "Daniel Ziglioli",
                        ParticipantRole.VICTIM,
                        ParticipantOutcome.KILLED,
                        False,
                        None,
                    ),
                    (
                        "Robert Moracchini",
                        ParticipantRole.SHOOTER,
                        ParticipantOutcome.UNHARMED,
                        True,
                        "Identified by a border-police officer who saw him dispose of the "
                        "murder weapon in the Golo, where it was recovered. Acquitted at "
                        "Dijon on 1 June 1985 after that officer retracted and the "
                        "victim's cousin provided an alibi. No investigation into "
                        "possible juror corruption was ever opened.",
                    ),
                    (
                        "Pierre-Marie Santucci",
                        ParticipantRole.SHOOTER,
                        ParticipantOutcome.UNHARMED,
                        True,
                        "Charged with assassinat; fled and was caught on 2 December 1982 "
                        "at Sorbo-Ocagnano armed and equipped with wigs and gloves. "
                        "Acquitted at Dijon on 1 June 1985.",
                    ),
                    (
                        "Georges Seatelli",
                        ParticipantRole.ASSISTED,
                        ParticipantOutcome.UNHARMED,
                        True,
                        "Charged with complicity; caught with Santucci on 2 December 1982 "
                        "at Sorbo-Ocagnano. Told the court the gloves found in the house "
                        "were for slaughtering pigs. Acquitted at Dijon on 1 June 1985.",
                    ),
                ],
            ),
        ),
        (
            "pj-memmi-1982",
            dict(
                type=IncidentType.MURDER,
                date=yr(1982, approx=True),
                municipality_id=muni.get("Corte"),
                location_text="Cours Paoli, Corte",
                narrative=(
                    "Pierre-Jean Memmi, Louis's brother, who had sworn to punish his "
                    "killers, was shot dead on the cours Paoli in the autumn of 1982. The "
                    "sources give the season but not the day."
                ),
                participants=[
                    (
                        "Pierre-Jean Memmi",
                        ParticipantRole.VICTIM,
                        ParticipantOutcome.KILLED,
                        False,
                        None,
                    )
                ],
            ),
        ),
        (
            "brise-bar-bombing-1982",
            dict(
                type=IncidentType.BOMBING,
                date=ymd(1982, 11, 28),
                municipality_id=muni.get("Bastia"),
                location_text="La Brise de Mer bar, old port, Bastia",
                narrative=(
                    "Five people were talking in the back room of the La Brise de Mer bar "
                    "when the door opened and a charge of about two hundred grams went "
                    "off. Doors, windows, tables and the counter were wrecked and the "
                    "front room was left strewn with debris, but nobody was seriously "
                    "hurt. A retaliatory strike against the gang's own headquarters."
                ),
                participants=[],
            ),
        ),
        (
            "seatelli-house-bombing-1982",
            dict(
                type=IncidentType.BOMBING,
                date=ymd(1982, 12, 28),
                municipality_id=muni.get("Cardo"),
                location_text="The Seatelli family house, Cardo, above Bastia",
                narrative=(
                    "Two gas bottles and several kilos of dynamite were placed to wipe "
                    "the house off the map, and it was blown up in the middle of the "
                    "afternoon. Georges Seatelli was not inside."
                ),
                participants=[
                    (
                        "Georges Seatelli",
                        ParticipantRole.VICTIM,
                        ParticipantOutcome.UNHARMED,
                        False,
                        None,
                    )
                ],
            ),
        ),
        (
            "gerard-ziglioli-1983",
            dict(
                type=IncidentType.MURDER,
                date=ymd(1983, 4, 14),
                municipality_id=None,
                location_text=None,
                narrative=(
                    "Gérard Ziglioli, Daniel's brother, had come back from the mainland "
                    "to carry out the vendetta for him. He was killed first. The sources "
                    "give the date but not the place."
                ),
                participants=[
                    (
                        "Gérard Ziglioli",
                        ParticipantRole.VICTIM,
                        ParticipantOutcome.KILLED,
                        False,
                        None,
                    )
                ],
            ),
        ),
        (
            "seatelli-1998",
            dict(
                type=IncidentType.MURDER,
                date=ymd(1998, 8, 21),
                municipality_id=muni.get("Biguglia"),
                location_text="Terrace of a beach restaurant, Biguglia",
                narrative=(
                    "Georges Seatelli was having lunch on the terrace of a beach "
                    "restaurant south of Bastia when two unidentified men shot him "
                    "several times in the back, with 9mm and 11.43mm pistols. Reporting "
                    "at the time linked the killing to the fight for control of nightlife "
                    "venues, the same racket behind the Ziglioli murders. Vendetta gives "
                    "only 'August 1998'; the day comes from press reporting and should be "
                    "confirmed against the Corse-Matin archive."
                ),
                participants=[
                    (
                        "Georges Seatelli",
                        ParticipantRole.VICTIM,
                        ParticipantOutcome.KILLED,
                        False,
                        None,
                    )
                ],
            ),
        ),
        (
            "santucci-2009",
            dict(
                type=IncidentType.MURDER,
                date=ymd(2009, 2, 10),
                municipality_id=muni.get("Arena"),
                location_text="Car park of Chez Fanfan, Arena, Vescovato",
                narrative=(
                    "Pierre-Marie Santucci had grown quiet with age and rarely went out "
                    "except for his card game at Chez Fanfan, almost every night, at the "
                    "same bar on the route nationale. Habit is a professional error in "
                    "the milieu. It was not late when he left on 10 February 2009 but it "
                    "was already dark, and a powerful streetlamp made him a clear target "
                    "on the near-empty car park. A sniper posted across the road, about "
                    "eighty metres away, fired a single round through his heart. No one "
                    "was ever charged. The killing belongs to the Brise's second, "
                    "internal war, which also took Richard Casanova in 2008 and Francis "
                    "Mariani and Francis Guazzelli in 2009."
                ),
                participants=[
                    (
                        "Pierre-Marie Santucci",
                        ParticipantRole.VICTIM,
                        ParticipantOutcome.KILLED,
                        False,
                        None,
                    )
                ],
            ),
        ),
        (
            "moracchini-2025",
            dict(
                type=IncidentType.MURDER,
                date=ymd(2025, 3, 29),
                municipality_id=muni.get("Bastia"),
                location_text="Rue du Commandant Luce-de-Casabianca, Bastia",
                narrative=(
                    "Robert Moracchini, 65, was shot several times with a 9mm in the "
                    "street near his home in central Bastia at about 08:00 on a Saturday "
                    "morning. The Bastia prosecutor opened an investigation for murder by "
                    "an organised gang, entrusted to the Haute-Corse judicial police. He "
                    "had left crime behind in the 2000s for a bistro and a tabac, and had "
                    "summited Everest less than two years earlier. Unsolved."
                ),
                participants=[
                    (
                        "Robert Moracchini",
                        ParticipantRole.VICTIM,
                        ParticipantOutcome.KILLED,
                        False,
                        None,
                    )
                ],
            ),
        ),
    ]


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write to the database")
    args = ap.parse_args()
    dry = not args.apply

    created: list[str] = []
    skipped: list[str] = []

    async with _session_factories["prod"]() as s:
        row = (
            await s.execute(
                text("SELECT id FROM universe WHERE slug = :slug"), {"slug": UNIVERSE_SLUG}
            )
        ).first()
        if row is None:
            print(f"Universe '{UNIVERSE_SLUG}' not found", file=sys.stderr)
            return 1
        uni: uuid.UUID = row[0]

        actor_row = (
            await s.execute(
                text(
                    "SELECT id, email FROM users WHERE global_role = 'ADMIN' ORDER BY created_at LIMIT 1"
                )
            )
        ).first()
        if actor_row is None:
            print("No ADMIN user to attribute the seed to", file=sys.stderr)
            return 1
        actor: uuid.UUID = actor_row[0]
        print(f"universe={uni}  actor={actor_row[1]}  mode={'DRY RUN' if dry else 'APPLY'}\n")

        async def existing(model, **where):
            stmt = select(model).where(model.universe_id == uni)
            for k, v in where.items():
                stmt = stmt.where(getattr(model, k) == v)
            return (await s.execute(stmt)).scalars().first()

        # --- municipalities -------------------------------------------------
        muni: dict[str, uuid.UUID] = {}
        for m in (
            await s.execute(select(Municipality).where(Municipality.universe_id == uni))
        ).scalars():
            muni[m.name] = m.id
        for name, parent in MUNICIPALITIES:
            if name in muni:
                skipped.append(f"municipality {name}")
                continue
            created.append(f"municipality {name}")
            if dry:
                muni[name] = uuid.uuid4()
                continue
            obj = await create_municipality(
                s,
                MunicipalityCreate(
                    universe_id=uni, name=name, parent_id=muni.get(parent) if parent else None
                ),
                actor,
            )
            muni[name] = obj.id

        # --- gangs ----------------------------------------------------------
        gangs: dict[str, uuid.UUID] = {}
        for name, aliases, desc in GANGS:
            found = await existing(Gang, name=name)
            if found:
                gangs[name] = found.id
                skipped.append(f"gang {name}")
                continue
            created.append(f"gang {name}")
            if dry:
                gangs[name] = uuid.uuid4()
                continue
            obj = await create_gang(
                s, GangCreate(universe_id=uni, name=name, aliases=aliases, description=desc), actor
            )
            gangs[name] = obj.id

        # --- sets -----------------------------------------------------------
        sets: dict[str, uuid.UUID] = {}
        for name, (gang, status, muni_name, bio) in SETS.items():
            found = await existing(GangSet, name=name)
            if found:
                sets[name] = found.id
                skipped.append(f"set {name}")
                continue
            created.append(f"set {name}")
            if dry:
                sets[name] = uuid.uuid4()
                continue
            obj = await create_gang_set(
                s,
                SetCreate(
                    universe_id=uni,
                    name=name,
                    bio=bio,
                    status=status,
                    gang_id=gangs[gang],
                    municipality_id=muni.get(muni_name),
                ),
                actor,
            )
            sets[name] = obj.id

        # --- the one set relationship, opened 1981 and closed 1983 ----------
        a, b = sorted([sets["Brise de Mer"], sets["Clan Memmi"]])
        rel = (
            (
                await s.execute(
                    select(SetRelationship).where(
                        SetRelationship.set_a_id == a, SetRelationship.set_b_id == b
                    )
                )
            )
            .scalars()
            .first()
        )
        if rel is not None:
            skipped.append("set relationship Brise de Mer <-> Clan Memmi")
        else:
            created.append("set relationship Brise de Mer <-> Clan Memmi (ENEMY, 1981-1983)")
            rel = SetRelationship(
                set_a_id=a,
                set_b_id=b,
                relationship_type=SetRelationshipType.ENEMY,
                from_date=yr(1981).model_dump(mode="json"),
            )
            if not dry:
                s.add(rel)
                await s.commit()
                await s.refresh(rel)
                # The war ended because one side ceased to exist.
                await end_set_relationship(
                    s, sets["Brise de Mer"], rel.id, yr(1983).model_dump(mode="json")
                )

        # --- members --------------------------------------------------------
        mem: dict[str, uuid.UUID] = {}
        for legal_name, d in MEMBERS.items():
            found = await existing(Member, legal_name=legal_name)
            if found:
                mem[legal_name] = found.id
                skipped.append(f"member {legal_name}")
                continue
            created.append(f"member {legal_name}")
            if dry:
                mem[legal_name] = uuid.uuid4()
                continue
            affiliations = []
            if d.get("set"):
                affiliations = [
                    MemberSetAffiliationIn(
                        set_id=sets[d["set"]], is_primary=True, from_date=d.get("from_date")
                    )
                ]
            obj = await create_member(
                s,
                MemberCreate(
                    universe_id=uni,
                    legal_name=legal_name,
                    aliases=d.get("aliases"),
                    biography=d.get("biography", ""),
                    status=d.get("status", MemberStatus.UNKNOWN),
                    dob=d.get("dob"),
                    date_of_death=d.get("date_of_death"),
                    gang_id=gangs[d["gang"]] if d.get("gang") else None,
                    affiliations=affiliations,
                ),
                actor,
            )
            mem[legal_name] = obj.id

        # --- family links, now that every id exists -------------------------
        for who, rel, other in FAMILY:
            if who not in mem or other not in mem:
                continue
            current = await existing(Member, legal_name=who)
            fam = dict(current.family or {}) if current else {}
            ids = set(fam.get(rel) or [])
            if str(mem[other]) in ids:
                skipped.append(f"family {who} {rel} {other}")
                continue
            created.append(f"family {who} {rel} {other}")
            if dry:
                continue
            ids.add(str(mem[other]))
            fam[rel] = sorted(ids)
            await update_member(s, mem[who], uni, MemberUpdate(family=fam))

        # --- businesses -----------------------------------------------------
        for name, btype, muni_name, status, desc, members in BUSINESSES:
            if await existing(Business, name=name):
                skipped.append(f"business {name}")
                continue
            created.append(f"business {name}")
            if dry:
                continue
            await create_business(
                s,
                BusinessCreate(
                    universe_id=uni,
                    name=name,
                    business_type=btype,
                    description=desc,
                    status=status,
                    municipality_id=muni.get(muni_name) if muni_name else None,
                    members=[
                        BusinessMemberIn(member_id=mem[mn], role=r)
                        for mn, r in members
                        if mn in mem
                    ],
                ),
                actor,
            )

        # --- sources --------------------------------------------------------
        for title, url, pub, published, rel_rating, notes in SOURCES:
            if await existing(Source, title=title):
                skipped.append(f"source {title}")
                continue
            created.append(f"source {title}")
            if dry:
                continue
            await create_source(
                s,
                SourceCreate(
                    universe_id=uni,
                    url=url,
                    title=title,
                    publication=pub,
                    published_at=published,
                    reliability=rel_rating,
                    notes=notes,
                ),
                actor,
            )

        # --- incidents last, so death sync has members to update ------------
        for key, spec in _incidents(mem, muni):
            # Keyed on (type, sortable_date): distinct across all nine, and unlike
            # location_text it is never NULL, which the old check read as "not found"
            # so that a second --apply would have duplicated that incident.
            sortable = spec["date"].to_sortable_date() if spec["date"] else None
            if await existing(Incident, type=spec["type"], sortable_date=sortable):
                skipped.append(f"incident {key}")
                continue
            created.append(f"incident {key}")
            if dry:
                continue
            await create_incident(
                s,
                IncidentCreate(
                    universe_id=uni,
                    type=spec["type"],
                    date=spec["date"],
                    municipality_id=spec["municipality_id"],
                    location_text=spec["location_text"],
                    narrative=spec["narrative"],
                    participants=[
                        ParticipantCreate(
                            member_id=mem[n], role=r, outcome=o, acquitted=acq, notes=note
                        )
                        for n, r, o, acq, note in spec["participants"]
                        if n in mem
                    ],
                ),
                actor,
            )

    print(f"created ({len(created)}):")
    for c in created:
        print(f"  + {c}")
    if skipped:
        print(f"\nalready present ({len(skipped)}):")
        for k in skipped:
            print(f"  = {k}")
    if dry:
        print("\nDRY RUN, nothing written. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
