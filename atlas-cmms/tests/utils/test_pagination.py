"""Tests for dates formatting/parsing and Spring-compatible pagination."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session

from src.utils.dates import (
    format_iso_utc_ms,
    parse_iso_datetime,
    to_epoch_ms,
)
from src.utils.pagination import as_spring_page, paginate


class PaginationTestBase(DeclarativeBase):
    pass


class DummyItem(PaginationTestBase):
    __tablename__ = "dummy_item"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)


def test_date_formatting_iso_utc_ms():
    dt = datetime(2026, 10, 18, 12, 34, 56, 789123, tzinfo=timezone.utc)
    formatted = format_iso_utc_ms(dt)
    assert formatted == "2026-10-18T12:34:56.789+00:00"

    # Naive datetime assumed UTC
    dt_naive = datetime(2026, 10, 18, 12, 34, 56, 789000)
    assert format_iso_utc_ms(dt_naive) == "2026-10-18T12:34:56.789+00:00"


def test_date_parsing_iso_and_timestamps():
    # ISO with +00:00
    dt1 = parse_iso_datetime("2026-10-18T12:34:56.789+00:00")
    assert dt1.year == 2026
    assert dt1.month == 10
    assert dt1.day == 18
    assert dt1.hour == 12
    assert dt1.microsecond == 789000

    # ISO with Z
    dt2 = parse_iso_datetime("2026-10-18T12:34:56.789Z")
    assert dt2 == dt1

    # Millisecond epoch timestamp
    ms = to_epoch_ms(dt1)
    dt3 = parse_iso_datetime(ms)
    assert abs((dt3 - dt1).total_seconds()) < 0.002

    # Second epoch timestamp
    dt4 = parse_iso_datetime(1700000000)
    assert dt4.tzinfo == timezone.utc


def test_as_spring_page_structure():
    items = ["a", "b", "c"]
    page = as_spring_page(
        items=items,
        total_elements=10,
        page_num=0,
        page_size=3,
        sort_field="name",
        direction="ASC",
    )
    dump = page.model_dump(by_alias=True)

    assert dump["content"] == ["a", "b", "c"]
    assert dump["totalElements"] == 10
    assert dump["totalPages"] == 4
    assert dump["size"] == 3
    assert dump["number"] == 0
    assert dump["first"] is True
    assert dump["last"] is False
    assert dump["numberOfElements"] == 3
    assert dump["empty"] is False
    assert dump["sort"] == {"empty": False, "sorted": True, "unsorted": False}


def test_as_spring_page_last_page_and_empty():
    # Last page
    page_last = as_spring_page(items=["x"], total_elements=10, page_num=3, page_size=3)
    assert page_last.first is False
    assert page_last.last is True

    # Empty page
    page_empty = as_spring_page(items=[], total_elements=0, page_num=0, page_size=10)
    assert page_empty.total_pages == 0
    assert page_empty.empty is True
    assert page_empty.first is True
    assert page_empty.last is True


def test_paginate_with_sqlite_db():
    engine = create_engine("sqlite:///:memory:")
    PaginationTestBase.metadata.create_all(engine)

    with Session(engine) as db:
        for i in range(25):
            db.add(DummyItem(id=i + 1, name=f"Item {i:02d}"))
        db.commit()

        # Page 0 (items 0..9)
        stmt = select(DummyItem)
        p0 = paginate(stmt, db, page_num=0, page_size=10, sort_field="name", direction="ASC")
        assert len(p0.content) == 10
        assert p0.total_elements == 25
        assert p0.total_pages == 3
        assert p0.number == 0
        assert p0.first is True
        assert p0.last is False
        assert p0.content[0].name == "Item 00"
        assert p0.content[-1].name == "Item 09"

        # Page 2 (last page, items 20..24)
        p2 = paginate(stmt, db, page_num=2, page_size=10, sort_field="name", direction="ASC")
        assert len(p2.content) == 5
        assert p2.number == 2
        assert p2.first is False
        assert p2.last is True
        assert p2.content[0].name == "Item 20"
        assert p2.content[-1].name == "Item 24"

        # Descending sort
        p_desc = paginate(stmt, db, page_num=0, page_size=5, sort_field="name", direction="DSC")
        assert p_desc.content[0].name == "Item 24"
