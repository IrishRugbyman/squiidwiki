"""`app.scripts.dedupe_incarcerations.plan`: which duplicate spells are extras.

Built in memory, no database: the rule is about rows and their write times.
Every value is invented.
"""

import datetime
import uuid

from app.models.member import MemberIncarceration
from app.scripts.dedupe_incarcerations import plan

T0 = datetime.datetime(2099, 1, 1, 12, 0, 0)
FROM = {"year": 2099, "month": 3, "day": 1, "precision": "YMD", "approx": False, "circa_text": None}


def _spell(member, offense: str, seconds: float, **kw) -> MemberIncarceration:
    return MemberIncarceration(
        id=uuid.uuid4(),
        member_id=member,
        case_id=kw.pop("case_id", "2099-000001-FC"),
        notes=kw.pop("notes", f"Offense: {offense}\nCounty: Testcounty"),
        from_date=FROM,
        created_at=T0 + datetime.timedelta(seconds=seconds),
        **kw,
    )


def test_a_reimport_is_removed_and_the_oldest_copy_kept():
    m = uuid.uuid4()
    first = [_spell(m, "Assault", 0), _spell(m, "Felony Firearms", 1)]
    again = [_spell(m, "Assault", 900), _spell(m, "Felony Firearms", 901)]
    deletions, multi, differing = plan(first + again, gap=120, keep_one=False)
    assert {e.id for e, _ in deletions} == {s.id for s in again}
    assert {k.id for _, k in deletions} == {s.id for s in first}
    assert multi == [] and differing == []


def test_identical_counts_in_one_import_are_kept_and_reported():
    m = uuid.uuid4()
    one_import = [_spell(m, "Felony Firearms", 0), _spell(m, "Felony Firearms", 1)]
    deletions, multi, _ = plan(one_import, gap=120, keep_one=False)
    assert deletions == []
    assert [(g["rows"], g["keep"]) for g in multi] == [(2, 2)]


def test_two_counts_imported_four_times_keeps_two():
    m = uuid.uuid4()
    rows = [_spell(m, "Felony Firearms", i * 600 + j) for i in range(4) for j in range(2)]
    deletions, multi, _ = plan(rows, gap=120, keep_one=False)
    assert len(deletions) == 6
    assert {k.id for _, k in deletions} == {rows[0].id}
    assert [(g["rows"], g["keep"]) for g in multi] == [(8, 2)]


def test_keep_one_collapses_every_group():
    m = uuid.uuid4()
    rows = [_spell(m, "Felony Firearms", 0), _spell(m, "Felony Firearms", 1)]
    deletions, multi, _ = plan(rows, gap=120, keep_one=True)
    assert [e.id for e, _ in deletions] == [rows[1].id]
    assert multi == []


def test_copies_that_differ_are_left_alone():
    m = uuid.uuid4()
    rows = [
        _spell(m, "Assault", 0, facility="Test Facility A"),
        _spell(m, "Assault", 900, facility="Test Facility B"),
    ]
    deletions, _, differing = plan(rows, gap=120, keep_one=False)
    assert deletions == []
    assert differing[0]["differs_in"] == ["facility"]


def test_different_members_and_offenses_are_not_duplicates():
    a, b = uuid.uuid4(), uuid.uuid4()
    rows = [_spell(a, "Assault", 0), _spell(b, "Assault", 900), _spell(a, "Robbery", 900)]
    assert plan(rows, gap=120, keep_one=False) == ([], [], [])
