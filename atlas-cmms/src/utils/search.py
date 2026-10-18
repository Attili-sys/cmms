"""SearchCriteria and FilterField query builder matching Spring Data JPA WrapperSpecification."""

from datetime import datetime, timezone
from enum import StrEnum
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    BigInteger,
    ColumnElement,
    Integer,
    Select,
    SmallInteger,
    Table,
    and_,
    func,
    inspect,
    or_,
    select,
)
from sqlalchemy.orm import RelationshipProperty, Session, aliased

from src.utils.pagination import as_spring_page


class EnumName(StrEnum):
    """Enums supported by Java WrapperSpecification for coercion."""

    PRIORITY = "PRIORITY"
    STATUS = "STATUS"
    JS_DATE = "JS_DATE"


class InvalidSearchFieldException(ValueError):
    """Raised when an unallowed or sensitive field path is queried."""

    def __init__(self, field: str, message: str = "Invalid search field") -> None:
        super().__init__(f"{message}: {field}")
        self.field = field
        self.client_message = message


class SearchFieldPolicy:
    """Mirrors Java SearchFieldPolicy blocklist and validation."""

    SENSITIVE_PROPERTIES = {"password", "secret", "token"}
    DISALLOWED_FIELDS: dict[str, set[str]] = {
        "User": {
            "user_settings",
            "usersettings",
            "app_stats",
            "appstats",
            "super_account_relations",
            "superaccountrelations",
            "parent_super_account",
            "parentsuperaccount",
        },
        "ApiKey": {"code"},
    }

    @classmethod
    def validate(cls, model_cls: type | None, field: str | None) -> None:
        if not field or not field.strip():
            raise InvalidSearchFieldException(field or "")
        segments = field.strip().split(".")
        for seg in segments:
            snake_seg = camel_to_snake(seg)
            if snake_seg in cls.SENSITIVE_PROPERTIES or seg.lower() in cls.SENSITIVE_PROPERTIES:
                raise InvalidSearchFieldException(field)

        if model_cls is not None:
            model_name = getattr(model_cls, "__name__", "")
            disallowed = cls.DISALLOWED_FIELDS.get(model_name, set())
            for seg in segments:
                snake_seg = camel_to_snake(seg)
                if snake_seg in disallowed or seg in disallowed:
                    raise InvalidSearchFieldException(field)


class FilterField(BaseModel):
    """A single filter condition applied to a search query."""

    field: str
    operation: str
    value: Any = None
    values: list[Any] = Field(default_factory=list)
    enum_name: EnumName | str | None = Field(default=None, alias="enumName")
    join_type: str | None = Field(default=None, alias="joinType")
    alternatives: list["FilterField"] | None = None
    value2: Any = None

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class SearchCriteria(BaseModel):
    """Search criteria for filtering, sorting, and paginating query results."""

    filter_fields: list[FilterField] = Field(default_factory=list, alias="filterFields")
    direction: str = "ASC"
    page_num: int = Field(default=0, alias="pageNum")
    page_size: int = Field(default=10, alias="pageSize")
    sort_field: str | None = Field(default=None, alias="sortField")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    def filter_company(self, company_id: int) -> None:
        self.filter_fields.append(
            FilterField(
                field="company",
                value=company_id,
                operation="eq",
                values=[],
            )
        )

    def filter_created_by(self, user_id: int) -> None:
        self.filter_fields.append(
            FilterField(
                field="createdBy",
                value=user_id,
                operation="eq",
                values=[],
            )
        )


def camel_to_snake(name: str) -> str:
    """Converts camelCase to snake_case."""
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def parse_js_date(val: Any) -> datetime | None:
    """Parses ISO date string, milliseconds epoch, or returns datetime."""
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None) if val.tzinfo else val
    if isinstance(val, (int, float)):
        ts = val / 1000.0 if val > 1e11 else float(val)
        return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)
    if isinstance(val, str):
        val = val.strip()
        if val.isdigit():
            ts = int(val)
            ts_sec = ts / 1000.0 if ts > 1e11 else float(ts)
            return datetime.fromtimestamp(ts_sec, tz=timezone.utc).replace(tzinfo=None)
        clean_val = val.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(clean_val)
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                pass
    return None


PRIORITY_MAP_INT: dict[str, int] = {
    "none": 0,
    "aucune": 0,
    "low": 1,
    "basse": 1,
    "medium": 2,
    "moyenne": 2,
    "high": 3,
    "haute": 3,
}

PRIORITY_MAP_STR: dict[str, str] = {
    "none": "NONE",
    "aucune": "NONE",
    "low": "LOW",
    "basse": "LOW",
    "medium": "MEDIUM",
    "moyenne": "MEDIUM",
    "high": "HIGH",
    "haute": "HIGH",
}

STATUS_MAP_INT: dict[str, int] = {
    "open": 0,
    "ouvert": 0,
    "in_progress": 1,
    "in progress": 1,
    "en cours": 1,
    "on_hold": 2,
    "on hold": 2,
    "en pause": 2,
    "complete": 3,
    "terminé": 3,
    "termine": 3,
}

STATUS_MAP_STR: dict[str, str] = {
    "open": "OPEN",
    "ouvert": "OPEN",
    "in_progress": "IN_PROGRESS",
    "in progress": "IN_PROGRESS",
    "en cours": "IN_PROGRESS",
    "on_hold": "ON_HOLD",
    "on hold": "ON_HOLD",
    "en pause": "ON_HOLD",
    "complete": "COMPLETE",
    "terminé": "COMPLETE",
    "termine": "COMPLETE",
}


def is_integer_column(col: ColumnElement) -> bool:
    """Checks whether a ColumnElement maps to an integer / smallinteger type."""
    col_type = getattr(col, "type", None)
    if col_type is None:
        return False
    if isinstance(col_type, (Integer, SmallInteger, BigInteger)):
        return True
    impl = getattr(col_type, "impl", None)
    return isinstance(impl, (Integer, SmallInteger, BigInteger))


def coerce_value(col: ColumnElement, val: Any, enum_name: EnumName | str | None) -> Any:
    """Coerces values based on enum_name or column type."""
    if val is None:
        return None

    if enum_name is not None:
        enum_str = str(enum_name).upper()
        if enum_str == EnumName.JS_DATE:
            return parse_js_date(val)
        if enum_str == EnumName.PRIORITY:
            key = str(val).lower()
            if is_integer_column(col):
                if isinstance(val, int):
                    return val
                return PRIORITY_MAP_INT.get(key, val)
            return PRIORITY_MAP_STR.get(key, str(val).upper())
        if enum_str == EnumName.STATUS:
            key = str(val).lower()
            if is_integer_column(col):
                if isinstance(val, int):
                    return val
                return STATUS_MAP_INT.get(key, val)
            return STATUS_MAP_STR.get(key, str(val).upper())

    # Fallback date parsing if column is datetime and val is string
    type_name = getattr(getattr(col, "type", None), "__class__", type(None)).__name__
    if type_name in ("DateTime", "Date") and isinstance(val, str):
        parsed = parse_js_date(val)
        if parsed is not None:
            return parsed

    return val


def extract_list(value: Any, values: list[Any]) -> list[Any]:
    """Extracts a flat list from value or values (handles comma-separated strings)."""
    if values and len(values) > 0:
        return list(values)
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if isinstance(value, str):
        if "," in value:
            return [v.strip() for v in value.split(",") if v.strip()]
        return [value] if value else []
    if value is not None:
        return [value]
    return []


def extract_between_bounds(
    value: Any, values: list[Any], value2: Any = None
) -> tuple[Any, Any] | None:
    """Extracts lower and upper bounds for between operations."""
    if value2 is not None and value is not None:
        return value, value2
    if values and len(values) >= 2:
        return values[0], values[1]
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return value[0], value[1]
    if isinstance(value, str) and "," in value:
        parts = [p.strip() for p in value.split(",", 1)]
        return parts[0], parts[1]
    return None


def get_model_for_table(table_name: str, model_cls: type | None = None) -> type | None:
    """Finds a mapped SQLAlchemy model class for a given table name."""
    if model_cls is not None:
        registry = getattr(model_cls, "registry", None)
        if registry is not None:
            for mapper in registry.mappers:
                if mapper.local_table.name == table_name:
                    return mapper.class_

    try:
        from src.models._base import Base

        for mapper in Base.registry.mappers:
            if mapper.local_table.name == table_name:
                return mapper.class_
    except (ImportError, AttributeError):
        return None
    return None


def find_association_table(model_cls: type, target_name: str) -> Table | None:
    """Looks up an association table linking model_cls to target_name."""
    metadata = getattr(model_cls, "metadata", None)
    if metadata is None:
        return None

    model_table = getattr(model_cls, "__tablename__", "")
    target_clean = camel_to_snake(target_name)

    # Candidate table patterns
    candidates = [
        f"{model_table}_{target_clean}",
        f"{target_clean}_{model_table}",
        f"{model_table}_{target_clean}s",
        f"own_user_{model_table}s",
        f"own_user_{model_table}",
        f"t_{model_table}_{target_clean}_associations",
        f"t_{target_clean}_{model_table}_associations",
    ]
    if target_clean in ("assigned_to", "assignedto", "user", "users"):
        candidates.extend([
            f"{model_table}_assigned_to",
            f"own_user_{model_table}s",
            f"own_user_{model_table}",
            f"t_{model_table}_user_associations",
        ])

    for cand in candidates:
        if cand in metadata.tables:
            return metadata.tables[cand]

    # Search tables containing both substrings
    for name, tbl in metadata.tables.items():
        if model_table in name and (target_clean in name or "assigned" in name):
            return tbl

    return None


def resolve_field_and_joins(
    stmt: Select,
    model_cls: type,
    field_path: str,
    joined_aliases: dict[str, Any],
) -> tuple[Select, ColumnElement]:
    """Resolves a dotted field path to a SQLAlchemy column expression, applying joins if needed."""
    SearchFieldPolicy.validate(model_cls, field_path)

    raw_segments = field_path.split(".")
    segments = [camel_to_snake(s) for s in raw_segments]

    # 1. Foreign key direct shortcut: e.g. "asset.id" -> model_cls.asset_id
    if len(segments) == 2 and segments[1] == "id":
        fk_attr = f"{segments[0]}_id"
        if hasattr(model_cls, fk_attr):
            return stmt, getattr(model_cls, fk_attr)

    # 2. Direct single attribute
    if len(segments) == 1:
        attr = segments[0]
        if hasattr(model_cls, attr):
            return stmt, getattr(model_cls, attr)
        if hasattr(model_cls, f"{attr}_id"):
            return stmt, getattr(model_cls, f"{attr}_id")
        if hasattr(model_cls, raw_segments[0]):
            return stmt, getattr(model_cls, raw_segments[0])

    # 3. Step-by-step traversal
    current_entity: Any = model_cls
    prefix = ""

    for i, raw_seg in enumerate(raw_segments):
        seg = segments[i]
        prefix = f"{prefix}.{seg}" if prefix else seg
        is_last = i == len(raw_segments) - 1

        if is_last:
            # Reached target column
            if hasattr(current_entity, seg):
                return stmt, getattr(current_entity, seg)
            if hasattr(current_entity, f"{seg}_id"):
                return stmt, getattr(current_entity, f"{seg}_id")
            if hasattr(current_entity, raw_seg):
                return stmt, getattr(current_entity, raw_seg)
            # Check table columns if current_entity is a Table
            if isinstance(current_entity, Table) and seg in current_entity.c:
                return stmt, current_entity.c[seg]

            raise InvalidSearchFieldException(field_path, f"Field '{raw_seg}' not found on entity")

        # Traversing relation
        # Check ORM relationship first
        mapper = inspect(current_entity, raiseerr=False)
        rel: RelationshipProperty | None = None
        if mapper and hasattr(mapper, "relationships"):
            rel = mapper.relationships.get(seg) or mapper.relationships.get(raw_seg)

        if rel is not None:
            target_cls = rel.mapper.class_
            if prefix not in joined_aliases:
                target_alias = aliased(target_cls, name=f"j_{prefix.replace('.', '_')}")
                stmt = stmt.outerjoin(target_alias, getattr(current_entity, rel.key))
                joined_aliases[prefix] = target_alias
            current_entity = joined_aliases[prefix]
            continue

        # Check foreign key column: e.g. location_id -> Location
        fk_col_name = f"{seg}_id" if hasattr(current_entity, f"{seg}_id") else seg
        fk_col = getattr(current_entity, fk_col_name, None)
        if fk_col is not None and hasattr(fk_col, "foreign_keys") and fk_col.foreign_keys:
            fk = next(iter(fk_col.foreign_keys))
            target_table = fk.column.table.name
            target_col = fk.column.name
            target_cls = get_model_for_table(target_table, model_cls)
            if target_cls:
                if prefix not in joined_aliases:
                    target_alias = aliased(target_cls, name=f"j_{prefix.replace('.', '_')}")
                    stmt = stmt.outerjoin(target_alias, fk_col == getattr(target_alias, target_col))
                    joined_aliases[prefix] = target_alias
                current_entity = joined_aliases[prefix]
                continue

        # Check association table (many-to-many)
        assoc_table = find_association_table(current_entity, seg)
        if assoc_table is not None:
            model_table_name = getattr(current_entity, "__tablename__", "")
            col_for_model = None
            col_for_target = None
            for c in assoc_table.columns:
                for fk in c.foreign_keys:
                    if fk.column.table.name == model_table_name:
                        col_for_model = c
                    else:
                        col_for_target = c

            if col_for_model is not None and col_for_target is not None:
                if prefix not in joined_aliases:
                    stmt = stmt.outerjoin(
                        assoc_table, current_entity.id == col_for_model
                    )
                    joined_aliases[prefix] = assoc_table

                if i == len(raw_segments) - 2 and segments[-1] == "id":
                    return stmt, col_for_target

                fk_target_table = next(iter(col_for_target.foreign_keys)).column.table.name
                target_cls = get_model_for_table(fk_target_table, model_cls)
                if target_cls:
                    target_prefix = f"{prefix}_target"
                    if target_prefix not in joined_aliases:
                        target_alias = aliased(target_cls, name=f"j_{target_prefix}")
                        stmt = stmt.outerjoin(
                            target_alias, col_for_target == target_alias.id
                        )
                        joined_aliases[target_prefix] = target_alias
                    current_entity = joined_aliases[target_prefix]
                    continue

        raise InvalidSearchFieldException(field_path, f"Cannot resolve relation '{raw_seg}'")

    raise InvalidSearchFieldException(field_path)


def build_predicate(
    col: ColumnElement,
    op: str,
    value: Any,
    values: list[Any],
    enum_name: EnumName | str | None,
    value2: Any = None,
) -> ColumnElement | None:
    """Builds a SQLAlchemy comparison predicate for a single column and operation."""
    op_clean = op.strip().lower()

    if op_clean == "eq":
        val = coerce_value(col, value, enum_name)
        return col == val

    if op_clean == "ne":
        val = coerce_value(col, value, enum_name)
        return col != val

    if op_clean == "gt":
        val = coerce_value(col, value, enum_name)
        return col > val

    if op_clean in ("ge", "goe", "gte"):
        val = coerce_value(col, value, enum_name)
        return col >= val

    if op_clean == "lt":
        val = coerce_value(col, value, enum_name)
        return col < val

    if op_clean in ("le", "loe", "lte"):
        val = coerce_value(col, value, enum_name)
        return col <= val

    if op_clean in ("cn", "contains", "like"):
        val_str = str(value) if value is not None else ""
        return col.ilike(f"%{val_str}%")

    if op_clean in ("nc", "does_not_contain"):
        val_str = str(value) if value is not None else ""
        return ~col.ilike(f"%{val_str}%")

    if op_clean in ("inn", "nu", "isnull"):
        return col.is_(None)

    if op_clean in ("nn", "isnotnull"):
        return col.is_not(None)

    if op_clean == "inm":
        # Support both 'is not None' and IN_MANY_TO_MANY
        items = extract_list(value, values)
        if items:
            coerced = [coerce_value(col, v, enum_name) for v in items]
            return col.in_(coerced)
        return col.is_not(None)

    if op_clean == "in":
        items = extract_list(value, values)
        coerced = [coerce_value(col, v, enum_name) for v in items]
        return col.in_(coerced)

    if op_clean in ("nin", "not_in"):
        items = extract_list(value, values)
        coerced = [coerce_value(col, v, enum_name) for v in items]
        return ~col.in_(coerced)

    if op_clean in ("bw", "between", "begins_with"):
        bounds = extract_between_bounds(value, values, value2)
        if bounds is not None:
            low = coerce_value(col, bounds[0], enum_name)
            high = coerce_value(col, bounds[1], enum_name)
            return col.between(low, high)
        val_str = str(value) if value is not None else ""
        return col.ilike(f"{val_str}%")

    if op_clean in ("bn", "does_not_begin_with"):
        val_str = str(value) if value is not None else ""
        return ~col.ilike(f"{val_str}%")

    if op_clean in ("ew", "ends_with"):
        val_str = str(value) if value is not None else ""
        return col.ilike(f"%{val_str}")

    if op_clean in ("en", "does_not_end_with"):
        val_str = str(value) if value is not None else ""
        return ~col.ilike(f"%{val_str}")

    raise InvalidSearchFieldException(op, f"Unsupported operation: {op}")


def process_single_filter(
    stmt: Select,
    model_cls: type,
    filter_field: FilterField,
    joined_aliases: dict[str, Any],
) -> tuple[Select, ColumnElement | None]:
    """Processes a single FilterField and its alternatives."""
    stmt, col = resolve_field_and_joins(stmt, model_cls, filter_field.field, joined_aliases)
    main_pred = build_predicate(
        col,
        filter_field.operation,
        filter_field.value,
        filter_field.values,
        filter_field.enum_name,
        filter_field.value2,
    )

    if not filter_field.alternatives:
        return stmt, main_pred

    alt_preds = []
    for alt in filter_field.alternatives:
        stmt, alt_pred = process_single_filter(stmt, model_cls, alt, joined_aliases)
        if alt_pred is not None:
            alt_preds.append(alt_pred)

    if main_pred is not None and alt_preds:
        return stmt, or_(main_pred, *alt_preds)
    if main_pred is not None:
        return stmt, main_pred
    if alt_preds:
        return stmt, or_(*alt_preds)
    return stmt, None


def apply_search_criteria(
    stmt: Select,
    model_cls: type,
    criteria: SearchCriteria,
    company_id: int | None = None,
    paginate: bool = False,
) -> Select:
    """Applies SearchCriteria filters, joins, company_id, and sorting to a SQLAlchemy Select statement."""
    joined_aliases: dict[str, Any] = {}
    predicates: list[ColumnElement] = []

    # Apply company_id multi-tenant isolation
    if company_id is not None and hasattr(model_cls, "company_id"):
        predicates.append(model_cls.company_id == company_id)

    # Process filter fields
    for ff in criteria.filter_fields:
        stmt, pred = process_single_filter(stmt, model_cls, ff, joined_aliases)
        if pred is not None:
            predicates.append(pred)

    if predicates:
        stmt = stmt.where(and_(*predicates))

    # Apply sorting
    sort_field = criteria.sort_field
    if sort_field:
        stmt, sort_col = resolve_field_and_joins(stmt, model_cls, sort_field, joined_aliases)
        direction = (criteria.direction or "ASC").upper()
        if direction in ("DESC", "DSC"):
            stmt = stmt.order_by(sort_col.desc())
        else:
            stmt = stmt.order_by(sort_col.asc())
    else:
        # Default sorting
        if hasattr(model_cls, "created_at"):
            stmt = stmt.order_by(model_cls.created_at.desc())
        elif hasattr(model_cls, "id"):
            stmt = stmt.order_by(model_cls.id.desc())

    # Apply pagination if requested
    if paginate:
        page_num = max(0, criteria.page_num)
        page_size = min(max(1, criteria.page_size), 1000)
        stmt = stmt.offset(page_num * page_size).limit(page_size)

    return stmt


def execute_search(
    db: Session,
    model_cls: type,
    criteria: SearchCriteria,
    company_id: int | None = None,
    base_stmt: Select | None = None,
    serializer: Any = None,
) -> dict[str, Any]:
    """Executes a paginated search query and returns the Spring Page<T> envelope."""
    if base_stmt is None:
        base_stmt = select(model_cls)

    # 1. Apply filters, joins, company_id, sorting without pagination
    filtered_stmt = apply_search_criteria(
        base_stmt,
        model_cls,
        criteria,
        company_id=company_id,
        paginate=False,
    )

    # 2. Count total elements
    count_subq = filtered_stmt.order_by(None).subquery()
    count_stmt = select(func.count()).select_from(count_subq)
    total_elements = db.scalar(count_stmt) or 0

    # 3. Apply pagination
    page_num = max(0, criteria.page_num)
    page_size = min(max(1, criteria.page_size), 1000)
    paged_stmt = filtered_stmt.offset(page_num * page_size).limit(page_size)

    # 4. Fetch results
    rows = db.scalars(paged_stmt).all()
    if serializer is not None:
        content = [serializer(row) for row in rows]
    else:
        content = list(rows)

    page_obj = as_spring_page(
        items=content,
        total_elements=total_elements,
        page_num=page_num,
        page_size=page_size,
        sort_field=criteria.sort_field,
        direction=criteria.direction or "ASC",
    )
    return page_obj.model_dump(by_alias=True)
