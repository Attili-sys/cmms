"""Comprehensive unit tests for SearchCriteria, FilterField, and execute_search."""

from datetime import datetime
import pytest
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    SmallInteger,
    String,
    Table,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from src.models.work_orders import WorkOrder
from src.utils.search import (
    EnumName,
    FilterField,
    InvalidSearchFieldException,
    SearchCriteria,
    SearchFieldPolicy,
    apply_search_criteria,
    execute_search,
)


class TestBase(DeclarativeBase):
    __test__ = False


class TestCompany(TestBase):
    __tablename__ = "test_company"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))


class TestLocation(TestBase):
    __tablename__ = "test_location"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)


class TestAsset(TestBase):
    __tablename__ = "test_asset"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    location_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("test_location.id"), nullable=True
    )


class TestUser(TestBase):
    __tablename__ = "test_user"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))


test_work_order_assigned_to = Table(
    "test_work_order_assigned_to",
    TestBase.metadata,
    Column("work_order_id", BigInteger, ForeignKey("test_work_order.id"), primary_key=True),
    Column("assigned_to_id", BigInteger, ForeignKey("test_user.id"), primary_key=True),
)


class TestWorkOrder(TestBase):
    __tablename__ = "test_work_order"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("test_company.id"), nullable=False
    )
    asset_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("test_asset.id"), nullable=True
    )
    location_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("test_location.id"), nullable=True
    )
    primary_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("test_user.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    estimated_duration: Mapped[float] = mapped_column(Float, default=0.0)


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    TestBase.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    # Seed test data
    c1 = TestCompany(id=1, name="Acme Corp")
    c2 = TestCompany(id=2, name="Other Corp")
    session.add_all([c1, c2])

    loc1 = TestLocation(id=10, name="Building North", code="BN-01")
    loc2 = TestLocation(id=20, name="Building South", code="BS-02")
    session.add_all([loc1, loc2])

    asset1 = TestAsset(id=100, name="Centrifugal Pump", location_id=10)
    asset2 = TestAsset(id=200, name="Diesel Generator", location_id=20)
    session.add_all([asset1, asset2])

    u1 = TestUser(id=1000, first_name="Alice", email="alice@test.com")
    u2 = TestUser(id=2000, first_name="Bob", email="bob@test.com")
    session.add_all([u1, u2])

    wo1 = TestWorkOrder(
        id=1,
        title="Repair Centrifugal Pump",
        description="Vibrating heavily during startup",
        priority=3,  # HIGH
        status=0,  # OPEN
        company_id=1,
        asset_id=100,
        location_id=10,
        primary_user_id=1000,
        created_at=datetime(2025, 1, 10, 8, 0, 0),
        due_date=datetime(2025, 1, 15, 17, 0, 0),
        estimated_duration=4.5,
    )
    wo2 = TestWorkOrder(
        id=2,
        title="Inspect Generator Backup",
        description="Routine monthly inspection",
        priority=1,  # LOW
        status=1,  # IN_PROGRESS
        company_id=1,
        asset_id=200,
        location_id=20,
        primary_user_id=2000,
        created_at=datetime(2025, 1, 12, 9, 0, 0),
        due_date=datetime(2025, 1, 14, 12, 0, 0),
        estimated_duration=2.0,
    )
    wo3 = TestWorkOrder(
        id=3,
        title="Calibrate Pressure Valve",
        description=None,
        priority=2,  # MEDIUM
        status=3,  # COMPLETE
        company_id=1,
        asset_id=100,
        location_id=10,
        primary_user_id=1000,
        created_at=datetime(2025, 1, 14, 10, 0, 0),
        due_date=datetime(2025, 1, 20, 18, 0, 0),
        estimated_duration=1.0,
    )
    wo4 = TestWorkOrder(
        id=4,
        title="Other Company Task",
        description="Belongs to company 2",
        priority=0,  # NONE
        status=0,  # OPEN
        company_id=2,
        asset_id=None,
        location_id=None,
        primary_user_id=None,
        created_at=datetime(2025, 1, 15, 11, 0, 0),
        due_date=None,
        estimated_duration=5.0,
    )
    session.add_all([wo1, wo2, wo3, wo4])
    session.commit()

    # Seed association table
    session.execute(
        test_work_order_assigned_to.insert().values([
            {"work_order_id": 1, "assigned_to_id": 1000},
            {"work_order_id": 1, "assigned_to_id": 2000},
            {"work_order_id": 2, "assigned_to_id": 2000},
        ])
    )
    session.commit()

    yield session
    session.close()


def test_operator_eq(db_session: Session) -> None:
    criteria = SearchCriteria(
        filter_fields=[FilterField(field="title", operation="eq", value="Repair Centrifugal Pump")]
    )
    page = execute_search(db_session, TestWorkOrder, criteria)
    assert page["totalElements"] == 1
    assert page["content"][0].id == 1


def test_operator_ne(db_session: Session) -> None:
    criteria = SearchCriteria(
        filter_fields=[FilterField(field="priority", operation="ne", value=3)]
    )
    page = execute_search(db_session, TestWorkOrder, criteria)
    assert page["totalElements"] == 3
    assert all(wo.priority != 3 for wo in page["content"])


def test_operator_gt_ge_lt_le(db_session: Session) -> None:
    # gt
    criteria_gt = SearchCriteria(
        filter_fields=[FilterField(field="estimated_duration", operation="gt", value=2.0)]
    )
    page_gt = execute_search(db_session, TestWorkOrder, criteria_gt)
    assert page_gt["totalElements"] == 2  # 4.5 and 5.0

    # ge / goe
    criteria_ge = SearchCriteria(
        filter_fields=[FilterField(field="estimated_duration", operation="ge", value=2.0)]
    )
    page_ge = execute_search(db_session, TestWorkOrder, criteria_ge)
    assert page_ge["totalElements"] == 3  # 2.0, 4.5, 5.0

    criteria_goe = SearchCriteria(
        filter_fields=[FilterField(field="estimated_duration", operation="goe", value=2.0)]
    )
    page_goe = execute_search(db_session, TestWorkOrder, criteria_goe)
    assert page_goe["totalElements"] == 3

    # lt
    criteria_lt = SearchCriteria(
        filter_fields=[FilterField(field="estimated_duration", operation="lt", value=2.0)]
    )
    page_lt = execute_search(db_session, TestWorkOrder, criteria_lt)
    assert page_lt["totalElements"] == 1  # 1.0

    # le / loe
    criteria_le = SearchCriteria(
        filter_fields=[FilterField(field="estimated_duration", operation="le", value=2.0)]
    )
    page_le = execute_search(db_session, TestWorkOrder, criteria_le)
    assert page_le["totalElements"] == 2  # 1.0, 2.0

    criteria_loe = SearchCriteria(
        filter_fields=[FilterField(field="estimated_duration", operation="loe", value=2.0)]
    )
    page_loe = execute_search(db_session, TestWorkOrder, criteria_loe)
    assert page_loe["totalElements"] == 2


def test_operator_cn_and_nc(db_session: Session) -> None:
    # cn: case-insensitive contains
    criteria_cn = SearchCriteria(
        filter_fields=[FilterField(field="title", operation="cn", value="pump")]
    )
    page_cn = execute_search(db_session, TestWorkOrder, criteria_cn)
    assert page_cn["totalElements"] == 1
    assert page_cn["content"][0].id == 1

    # nc: does not contain
    criteria_nc = SearchCriteria(
        filter_fields=[FilterField(field="title", operation="nc", value="pump")]
    )
    page_nc = execute_search(db_session, TestWorkOrder, criteria_nc)
    assert page_nc["totalElements"] == 3


def test_operator_in_and_nin(db_session: Session) -> None:
    # in with list
    criteria_in = SearchCriteria(
        filter_fields=[FilterField(field="id", operation="in", values=[1, 3])]
    )
    page_in = execute_search(db_session, TestWorkOrder, criteria_in)
    assert page_in["totalElements"] == 2
    assert {wo.id for wo in page_in["content"]} == {1, 3}

    # in with comma-separated string
    criteria_str = SearchCriteria(
        filter_fields=[FilterField(field="id", operation="in", value="1, 3")]
    )
    page_str = execute_search(db_session, TestWorkOrder, criteria_str)
    assert page_str["totalElements"] == 2

    # nin (not in)
    criteria_nin = SearchCriteria(
        filter_fields=[FilterField(field="id", operation="nin", values=[1, 2])]
    )
    page_nin = execute_search(db_session, TestWorkOrder, criteria_nin)
    assert page_nin["totalElements"] == 2
    assert {wo.id for wo in page_nin["content"]} == {3, 4}


def test_operator_inn_and_inm(db_session: Session) -> None:
    # inn: is None
    criteria_inn = SearchCriteria(
        filter_fields=[FilterField(field="description", operation="inn")]
    )
    page_inn = execute_search(db_session, TestWorkOrder, criteria_inn)
    assert page_inn["totalElements"] == 1
    assert page_inn["content"][0].id == 3

    # inm: is not None
    criteria_inm = SearchCriteria(
        filter_fields=[FilterField(field="description", operation="inm")]
    )
    page_inm = execute_search(db_session, TestWorkOrder, criteria_inm)
    assert page_inm["totalElements"] == 3


def test_operator_bw_between_and_begins_with(db_session: Session) -> None:
    # bw with values list: between
    criteria_bw = SearchCriteria(
        filter_fields=[FilterField(field="estimated_duration", operation="bw", values=[1.5, 4.8])]
    )
    page_bw = execute_search(db_session, TestWorkOrder, criteria_bw)
    assert page_bw["totalElements"] == 2  # 2.0 and 4.5
    assert {wo.id for wo in page_bw["content"]} == {1, 2}

    # bw with value list
    criteria_bw2 = SearchCriteria(
        filter_fields=[FilterField(field="estimated_duration", operation="bw", value=[1.5, 4.8])]
    )
    page_bw2 = execute_search(db_session, TestWorkOrder, criteria_bw2)
    assert page_bw2["totalElements"] == 2

    # bw with single string: begins with
    criteria_bw_str = SearchCriteria(
        filter_fields=[FilterField(field="title", operation="bw", value="Repair")]
    )
    page_bw_str = execute_search(db_session, TestWorkOrder, criteria_bw_str)
    assert page_bw_str["totalElements"] == 1
    assert page_bw_str["content"][0].id == 1


def test_operator_bn_ew_en(db_session: Session) -> None:
    # bn: does not begin with
    criteria_bn = SearchCriteria(
        filter_fields=[FilterField(field="title", operation="bn", value="Repair")]
    )
    page_bn = execute_search(db_session, TestWorkOrder, criteria_bn)
    assert page_bn["totalElements"] == 3

    # ew: ends with
    criteria_ew = SearchCriteria(
        filter_fields=[FilterField(field="title", operation="ew", value="Backup")]
    )
    page_ew = execute_search(db_session, TestWorkOrder, criteria_ew)
    assert page_ew["totalElements"] == 1
    assert page_ew["content"][0].id == 2

    # en: does not end with
    criteria_en = SearchCriteria(
        filter_fields=[FilterField(field="title", operation="en", value="Backup")]
    )
    page_en = execute_search(db_session, TestWorkOrder, criteria_en)
    assert page_en["totalElements"] == 3


def test_dotted_field_paths_and_joins(db_session: Session) -> None:
    # 1. Foreign key shortcut: asset.id -> asset_id
    criteria_asset = SearchCriteria(
        filter_fields=[FilterField(field="asset.id", operation="eq", value=100)]
    )
    page_asset = execute_search(db_session, TestWorkOrder, criteria_asset)
    assert page_asset["totalElements"] == 2
    assert {wo.id for wo in page_asset["content"]} == {1, 3}

    # 2. camelCase-to-snake_case column: primaryUser.id -> primary_user_id
    criteria_user = SearchCriteria(
        filter_fields=[FilterField(field="primaryUser.id", operation="eq", value=2000)]
    )
    page_user = execute_search(db_session, TestWorkOrder, criteria_user)
    assert page_user["totalElements"] == 1
    assert page_user["content"][0].id == 2

    # 3. Foreign key join: location.name -> join TestLocation and match name
    criteria_loc = SearchCriteria(
        filter_fields=[FilterField(field="location.name", operation="eq", value="Building South")]
    )
    page_loc = execute_search(db_session, TestWorkOrder, criteria_loc)
    assert page_loc["totalElements"] == 1
    assert page_loc["content"][0].id == 2

    # 4. Association table many-to-many: assignedTo.id
    criteria_assigned = SearchCriteria(
        filter_fields=[FilterField(field="assignedTo.id", operation="eq", value=1000)]
    )
    page_assigned = execute_search(db_session, TestWorkOrder, criteria_assigned)
    assert page_assigned["totalElements"] == 1
    assert page_assigned["content"][0].id == 1


def test_alternatives_or_clause(db_session: Session) -> None:
    # status == 3 (COMPLETE) OR priority == 3 (HIGH)
    criteria = SearchCriteria(
        filter_fields=[
            FilterField(
                field="status",
                operation="eq",
                value=3,
                alternatives=[FilterField(field="priority", operation="eq", value=3)],
            )
        ]
    )
    page = execute_search(db_session, TestWorkOrder, criteria)
    assert page["totalElements"] == 2
    assert {wo.id for wo in page["content"]} == {1, 3}


def test_enum_name_coercion(db_session: Session) -> None:
    # Priority: "HIGH" -> 3
    criteria_pri = SearchCriteria(
        filter_fields=[
            FilterField(
                field="priority",
                operation="eq",
                value="HIGH",
                enum_name=EnumName.PRIORITY,
            )
        ]
    )
    page_pri = execute_search(db_session, TestWorkOrder, criteria_pri)
    assert page_pri["totalElements"] == 1
    assert page_pri["content"][0].id == 1

    # Priority French: "Moyenne" -> 2
    criteria_pri_fr = SearchCriteria(
        filter_fields=[
            FilterField(
                field="priority",
                operation="eq",
                value="Moyenne",
                enum_name=EnumName.PRIORITY,
            )
        ]
    )
    page_pri_fr = execute_search(db_session, TestWorkOrder, criteria_pri_fr)
    assert page_pri_fr["totalElements"] == 1
    assert page_pri_fr["content"][0].id == 3

    # Status: "IN_PROGRESS" -> 1
    criteria_stat = SearchCriteria(
        filter_fields=[
            FilterField(
                field="status",
                operation="eq",
                value="IN_PROGRESS",
                enum_name=EnumName.STATUS,
            )
        ]
    )
    page_stat = execute_search(db_session, TestWorkOrder, criteria_stat)
    assert page_stat["totalElements"] == 1
    assert page_stat["content"][0].id == 2

    # JS_DATE: ISO 8601 string
    criteria_date = SearchCriteria(
        filter_fields=[
            FilterField(
                field="due_date",
                operation="ge",
                value="2025-01-16T00:00:00.000Z",
                enum_name=EnumName.JS_DATE,
            )
        ]
    )
    page_date = execute_search(db_session, TestWorkOrder, criteria_date)
    assert page_date["totalElements"] == 1
    assert page_date["content"][0].id == 3


def test_sorting(db_session: Session) -> None:
    # ASC sorting by estimated_duration
    crit_asc = SearchCriteria(sort_field="estimated_duration", direction="ASC")
    page_asc = execute_search(db_session, TestWorkOrder, crit_asc)
    durations = [wo.estimated_duration for wo in page_asc["content"]]
    assert durations == sorted(durations)

    # DESC sorting
    crit_desc = SearchCriteria(sort_field="estimated_duration", direction="DESC")
    page_desc = execute_search(db_session, TestWorkOrder, crit_desc)
    durations_desc = [wo.estimated_duration for wo in page_desc["content"]]
    assert durations_desc == sorted(durations, reverse=True)

    # Three-letter Java DSC quirk
    crit_dsc = SearchCriteria(sort_field="estimated_duration", direction="DSC")
    page_dsc = execute_search(db_session, TestWorkOrder, crit_dsc)
    assert [wo.id for wo in page_dsc["content"]] == [wo.id for wo in page_desc["content"]]

    # Nested sort: location.name
    crit_nested = SearchCriteria(sort_field="location.name", direction="ASC")
    page_nested = execute_search(db_session, TestWorkOrder, crit_nested)
    assert len(page_nested["content"]) == 4

    # Default sort by created_at desc
    crit_default = SearchCriteria()
    page_default = execute_search(db_session, TestWorkOrder, crit_default)
    dates = [wo.created_at for wo in page_default["content"]]
    assert dates == sorted(dates, reverse=True)


def test_pagination(db_session: Session) -> None:
    # Page 0 with size 2
    crit_p0 = SearchCriteria(
        page_num=0,
        page_size=2,
        sort_field="id",
        direction="ASC",
    )
    page0 = execute_search(db_session, TestWorkOrder, crit_p0)
    assert page0["totalElements"] == 4
    assert page0["totalPages"] == 2
    assert page0["number"] == 0
    assert page0["size"] == 2
    assert page0["numberOfElements"] == 2
    assert page0["first"] is True
    assert page0["last"] is False
    assert page0["empty"] is False
    assert [wo.id for wo in page0["content"]] == [1, 2]

    # Page 1 with size 2
    crit_p1 = SearchCriteria(
        page_num=1,
        page_size=2,
        sort_field="id",
        direction="ASC",
    )
    page1 = execute_search(db_session, TestWorkOrder, crit_p1)
    assert page1["number"] == 1
    assert page1["first"] is False
    assert page1["last"] is True
    assert [wo.id for wo in page1["content"]] == [3, 4]


def test_company_id_isolation(db_session: Session) -> None:
    criteria = SearchCriteria()
    # Company 1
    page1 = execute_search(db_session, TestWorkOrder, criteria, company_id=1)
    assert page1["totalElements"] == 3
    assert all(wo.company_id == 1 for wo in page1["content"])

    # Company 2
    page2 = execute_search(db_session, TestWorkOrder, criteria, company_id=2)
    assert page2["totalElements"] == 1
    assert page2["content"][0].id == 4


def test_serializer_support(db_session: Session) -> None:
    def serialize_wo(wo: TestWorkOrder) -> dict:
        return {"id": wo.id, "title": wo.title}

    criteria = SearchCriteria(page_size=2)
    page = execute_search(
        db_session,
        TestWorkOrder,
        criteria,
        serializer=serialize_wo,
    )
    assert len(page["content"]) == 2
    assert isinstance(page["content"][0], dict)
    assert "title" in page["content"][0]


def test_security_field_policy() -> None:
    with pytest.raises(InvalidSearchFieldException):
        SearchFieldPolicy.validate(TestWorkOrder, "password")

    with pytest.raises(InvalidSearchFieldException):
        SearchFieldPolicy.validate(TestWorkOrder, "user.secret")

    with pytest.raises(InvalidSearchFieldException):
        SearchFieldPolicy.validate(TestWorkOrder, "token")


def test_real_model_query_building() -> None:
    # Verifies that apply_search_criteria builds valid SQL queries on the actual project models
    criteria = SearchCriteria(
        filter_fields=[
            FilterField(field="asset.id", operation="eq", value=5),
            FilterField(field="primaryUser.id", operation="eq", value=10),
            FilterField(field="category.id", operation="in", values=[1, 2]),
            FilterField(field="location.name", operation="cn", value="Plant"),
            FilterField(
                field="priority",
                operation="eq",
                value="HIGH",
                enum_name=EnumName.PRIORITY,
            ),
        ],
        sort_field="location.name",
        direction="DESC",
    )
    stmt = apply_search_criteria(select(WorkOrder), WorkOrder, criteria, company_id=1)
    sql = str(stmt.compile())
    assert "work_order.asset_id" in sql
    assert "work_order.primary_user_id" in sql
    assert "work_order.category_id" in sql
    assert "work_order.company_id" in sql
