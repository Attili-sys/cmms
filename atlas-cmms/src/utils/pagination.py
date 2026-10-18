"""Pagination utilities matching Spring Data Page<T> JSON envelope."""

from typing import Any, Generic, TypeVar
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from src.schemas._base import CamelModel

T = TypeVar("T")


class SortDetails(CamelModel):
    """Sort details matching Spring Page sort property."""

    empty: bool = True
    sorted: bool = False
    unsorted: bool = True


class Page(CamelModel, Generic[T]):
    """Generic pagination response matching Spring Data Page<T>."""

    content: list[T]
    total_elements: int
    total_pages: int
    size: int
    number: int
    first: bool
    last: bool
    number_of_elements: int
    empty: bool
    sort: SortDetails


def as_spring_page(
    items: list[T],
    total_elements: int,
    page_num: int = 0,
    page_size: int = 20,
    sort_field: str | None = None,
    direction: str = "ASC",
) -> Page[T]:
    """Convert items list and counts into a Spring Page[T] object."""
    page_num = max(0, page_num)
    page_size = max(1, min(1000, page_size))
    total_pages = (total_elements + page_size - 1) // page_size if total_elements > 0 else 0
    is_first = page_num == 0
    is_last = (page_num >= total_pages - 1) if total_pages > 0 else True
    is_empty = len(items) == 0

    has_sort = bool(sort_field)
    sort_obj = SortDetails(
        empty=not has_sort,
        sorted=has_sort,
        unsorted=not has_sort,
    )

    return Page[T](
        content=items,
        total_elements=total_elements,
        total_pages=total_pages,
        size=page_size,
        number=page_num,
        first=is_first,
        last=is_last,
        number_of_elements=len(items),
        empty=is_empty,
        sort=sort_obj,
    )


def paginate(
    stmt: Select,
    db: Session,
    page_num: int = 0,
    page_size: int = 20,
    sort_field: str | None = None,
    direction: str = "ASC",
) -> Page[Any]:
    """Execute paginated select statement and return Spring Page envelope."""
    page_num = max(0, page_num)
    page_size = max(1, min(1000, page_size))

    # Calculate total elements count
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total_elements = db.scalar(count_stmt) or 0

    # Apply sorting if specified
    if sort_field:
        is_desc = direction.upper() in ("DSC", "DESC")
        # Try to resolve sort_field on the principal entity
        entity = None
        for col in stmt.column_descriptions:
            if col.get("entity") is not None:
                entity = col["entity"]
                break

        if entity and hasattr(entity, sort_field):
            col_attr = getattr(entity, sort_field)
            stmt = stmt.order_by(col_attr.desc() if is_desc else col_attr.asc())

    # Apply limit and offset
    offset = page_num * page_size
    paged_stmt = stmt.offset(offset).limit(page_size)
    items = list(db.scalars(paged_stmt).all())

    return as_spring_page(
        items=items,
        total_elements=total_elements,
        page_num=page_num,
        page_size=page_size,
        sort_field=sort_field,
        direction=direction,
    )
