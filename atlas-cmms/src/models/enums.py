"""All 44 Java enums ported to Python StrEnum with OrdinalEnum / StringEnum SQLAlchemy types."""

from enum import StrEnum
from typing import Any

from sqlalchemy import SmallInteger, String, TypeDecorator


class OrdinalEnum(TypeDecorator):
    """Stores Java ordinal (0-based declaration index) as SMALLINT in Postgres, exposes StrEnum in Python."""

    impl = SmallInteger
    cache_ok = True

    def __init__(self, enum_cls: type[StrEnum], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.enum_cls = enum_cls
        self._members = list(enum_cls)
        self._by_name = {m.value: idx for idx, m in enumerate(self._members)}

    def process_bind_param(self, value: Any, dialect: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, StrEnum):
            return self._by_name[value.value]
        if isinstance(value, str):
            if value in self._by_name:
                return self._by_name[value]
            if value.isdigit():
                return int(value)
        raise ValueError(f"Invalid {self.enum_cls.__name__} value: {value!r}")

    def process_result_value(self, value: Any, dialect: Any) -> StrEnum | None:
        if value is None:
            return None
        if isinstance(value, int) and 0 <= value < len(self._members):
            return self._members[value]
        if isinstance(value, str) and value in self._by_name:
            return self.enum_cls(value)
        return value


class StringEnum(TypeDecorator):
    """Stores enum name as VARCHAR in Postgres, exposes StrEnum in Python."""

    impl = String
    cache_ok = True

    def __init__(self, enum_cls: type[StrEnum], length: int | None = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.enum_cls = enum_cls
        self.impl = String(length) if length else String()
        self._members = list(enum_cls)

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, StrEnum):
            return value.value
        if isinstance(value, int) and 0 <= value < len(self._members):
            return self._members[value].value
        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> StrEnum | None:
        if value is None:
            return None
        try:
            return self.enum_cls(str(value))
        except ValueError:
            return value


class ApprovalStatus(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class AssetStatus(StrEnum):
    OPERATIONAL = "OPERATIONAL"
    DOWN = "DOWN"
    MODERNIZATION = "MODERNIZATION"
    STANDBY = "STANDBY"
    INSPECTION_SCHEDULED = "INSPECTION_SCHEDULED"
    COMMISSIONING = "COMMISSIONING"
    EMERGENCY_SHUTDOWN = "EMERGENCY_SHUTDOWN"


class BasicPermission(StrEnum):
    CREATE_EDIT_PEOPLE_AND_TEAMS = "CREATE_EDIT_PEOPLE_AND_TEAMS"
    CREATE_EDIT_CATEGORIES = "CREATE_EDIT_CATEGORIES"
    DELETE_WORK_ORDERS = "DELETE_WORK_ORDERS"
    DELETE_PREVENTIVE_MAINTENANCE_TRIGGERS = "DELETE_PREVENTIVE_MAINTENANCE_TRIGGERS"
    DELETE_ASSETS = "DELETE_ASSETS"
    DELETE_PARTS_AND_MULTI_PARTS = "DELETE_PARTS_AND_MULTI_PARTS"
    DELETE_PURCHASE_ORDERS = "DELETE_PURCHASE_ORDERS"
    DELETE_METERS = "DELETE_METERS"
    DELETE_VENDORS_AND_CUSTOMERS = "DELETE_VENDORS_AND_CUSTOMERS"
    DELETE_CATEGORIES = "DELETE_CATEGORIES"
    DELETE_FILES = "DELETE_FILES"
    DELETE_PEOPLE_AND_TEAMS = "DELETE_PEOPLE_AND_TEAMS"
    ACCESS_SETTINGS = "ACCESS_SETTINGS"
    DELETE_LOCATIONS = "DELETE_LOCATIONS"


class BusinessType(StrEnum):
    BUILDING_MANAGEMENT = "BUILDING_MANAGEMENT"
    CHURCH_MANAGEMENT = "CHURCH_MANAGEMENT"
    CITY_MAINTENANCE = "CITY_MAINTENANCE"
    EQUIPMENT_MANAGEMENT = "EQUIPMENT_MANAGEMENT"
    FACILITY_MANAGEMENT = "FACILITY_MANAGEMENT"
    FARMING_MAINTENANCE = "FARMING_MAINTENANCE"
    FLEET_MANAGEMENT = "FLEET_MANAGEMENT"
    GENERAL_ASSET_MANAGEMENT = "GENERAL_ASSET_MANAGEMENT"
    GYM_FITNESS_MAINTENANCE = "GYM_FITNESS_MAINTENANCE"
    HOSPITALITY = "HOSPITALITY"
    MANUFACTURING_MANAGEMENT = "MANUFACTURING_MANAGEMENT"
    PHYSICAL_ASSET_MANAGEMENT = "PHYSICAL_ASSET_MANAGEMENT"
    PROPERTY_MANAGEMENT = "PROPERTY_MANAGEMENT"
    RESTAURANT_MANAGEMENT = "RESTAURANT_MANAGEMENT"
    SCHOOL_MAINTENANCE = "SCHOOL_MAINTENANCE"


class CustomFieldEntityType(StrEnum):
    WORK_ORDER = "WORK_ORDER"
    ASSET = "ASSET"
    LOCATION = "LOCATION"
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    PART = "PART"
    PURCHASE_REQUEST = "PURCHASE_REQUEST"
    METER = "METER"


class CustomFieldType(StrEnum):
    SHORT_TEXT = "SHORT_TEXT"
    LONG_TEXT = "LONG_TEXT"
    NUMBER = "NUMBER"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    DATE = "DATE"
    DATE_TIME = "DATE_TIME"
    LINK = "LINK"


class DateFormat(StrEnum):
    MMDDYY = "MMDDYY"
    DDMMYY = "DDMMYY"


class EnumName(StrEnum):
    PRIORITY = "PRIORITY"
    STATUS = "STATUS"
    JS_DATE = "JS_DATE"


class FieldType(StrEnum):
    OPTIONAL = "OPTIONAL"
    REQUIRED = "REQUIRED"
    HIDDEN = "HIDDEN"


class FileType(StrEnum):
    IMAGE = "IMAGE"
    OTHER = "OTHER"


class ImportEntity(StrEnum):
    WORK_ORDER = "WORK_ORDER"
    ASSET = "ASSET"
    LOCATION = "LOCATION"
    PART = "PART"
    METER = "METER"
    PREVENTIVE_MAINTENANCE = "PREVENTIVE_MAINTENANCE"


class Language(StrEnum):
    EN = "EN"
    FR = "FR"
    TR = "TR"
    ES = "ES"
    PT_BR = "PT_BR"
    PL = "PL"
    DE = "DE"
    AR = "AR"
    IT = "IT"
    SV = "SV"
    RU = "RU"
    PT = "PT"
    HU = "HU"
    NL = "NL"
    ZH_CN = "ZH_CN"
    ZH = "ZH"
    BA = "BA"
    JA = "JA"


class MailType(StrEnum):
    SMTP = "SMTP"
    SENDGRID = "SENDGRID"


class NotificationType(StrEnum):
    INFO = "INFO"
    ASSET = "ASSET"
    WORK_ORDER = "WORK_ORDER"
    PART = "PART"
    METER = "METER"
    LOCATION = "LOCATION"
    TEAM = "TEAM"
    REQUEST = "REQUEST"
    PURCHASE_ORDER = "PURCHASE_ORDER"


class PermissionEntity(StrEnum):
    PEOPLE_AND_TEAMS = "PEOPLE_AND_TEAMS"
    CATEGORIES = "CATEGORIES"
    CATEGORIES_WEB = "CATEGORIES_WEB"
    WORK_ORDERS = "WORK_ORDERS"
    PREVENTIVE_MAINTENANCES = "PREVENTIVE_MAINTENANCES"
    ASSETS = "ASSETS"
    PARTS_AND_MULTIPARTS = "PARTS_AND_MULTIPARTS"
    PURCHASE_ORDERS = "PURCHASE_ORDERS"
    METERS = "METERS"
    VENDORS_AND_CUSTOMERS = "VENDORS_AND_CUSTOMERS"
    FILES = "FILES"
    LOCATIONS = "LOCATIONS"
    SETTINGS = "SETTINGS"
    REQUESTS = "REQUESTS"
    ANALYTICS = "ANALYTICS"


class PlanFeatures(StrEnum):
    PREVENTIVE_MAINTENANCE = "PREVENTIVE_MAINTENANCE"
    CHECKLIST = "CHECKLIST"
    FILE = "FILE"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    METER = "METER"
    REQUEST_CONFIGURATION = "REQUEST_CONFIGURATION"
    ADDITIONAL_TIME = "ADDITIONAL_TIME"
    ADDITIONAL_COST = "ADDITIONAL_COST"
    ANALYTICS = "ANALYTICS"
    REQUEST_PORTAL = "REQUEST_PORTAL"
    SIGNATURE = "SIGNATURE"
    ROLE = "ROLE"
    WORKFLOW = "WORKFLOW"
    API_ACCESS = "API_ACCESS"
    WEBHOOK = "WEBHOOK"
    IMPORT_CSV = "IMPORT_CSV"
    RESOURCE_PLANNING = "RESOURCE_PLANNING"


class PortalFieldType(StrEnum):
    ASSET = "ASSET"
    LOCATION = "LOCATION"
    DESCRIPTION = "DESCRIPTION"
    CONTACT = "CONTACT"
    IMAGE = "IMAGE"
    FILES = "FILES"


class Priority(StrEnum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RecurrenceBasedOn(StrEnum):
    SCHEDULED_DATE = "SCHEDULED_DATE"
    COMPLETED_DATE = "COMPLETED_DATE"


class RecurrenceType(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class RelationType(StrEnum):
    DUPLICATE_OF = "DUPLICATE_OF"
    DUPLICATED_BY = "DUPLICATED_BY"
    RELATED_TO = "RELATED_TO"
    SPLIT_TO = "SPLIT_TO"
    SPLIT_FROM = "SPLIT_FROM"
    BLOCKED_BY = "BLOCKED_BY"
    BLOCKS = "BLOCKS"


class RelationTypeInternal(StrEnum):
    DUPLICATE_OF = "DUPLICATE_OF"
    RELATED_TO = "RELATED_TO"
    SPLIT_FROM = "SPLIT_FROM"
    BLOCKS = "BLOCKS"


class RoleCode(StrEnum):
    ADMIN = "ADMIN"
    LIMITED_ADMIN = "LIMITED_ADMIN"
    TECHNICIAN = "TECHNICIAN"
    LIMITED_TECHNICIAN = "LIMITED_TECHNICIAN"
    VIEW_ONLY = "VIEW_ONLY"
    REQUESTER = "REQUESTER"
    USER_CREATED = "USER_CREATED"


class RoleType(StrEnum):
    ROLE_SUPER_ADMIN = "ROLE_SUPER_ADMIN"
    ROLE_CLIENT = "ROLE_CLIENT"


class Status(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETE = "COMPLETE"


class StorageType(StrEnum):
    GCP = "GCP"
    MINIO = "MINIO"


class SubscriptionScheduledChangeType(StrEnum):
    RESET_TO_FREE = "RESET_TO_FREE"


class TaskType(StrEnum):
    SUBTASK = "SUBTASK"
    NUMBER = "NUMBER"
    TEXT = "TEXT"
    INSPECTION = "INSPECTION"
    MULTIPLE = "MULTIPLE"
    METER = "METER"


class TimeStatus(StrEnum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"


class WorkOrderMeterTriggerCondition(StrEnum):
    LESS_THAN = "LESS_THAN"
    MORE_THAN = "MORE_THAN"


class PartField(StrEnum):
    NAME = "NAME"
    COST = "COST"
    ASSIGNED_TO = "ASSIGNED_TO"
    BARCODE = "BARCODE"
    DESCRIPTION = "DESCRIPTION"
    CATEGORY = "CATEGORY"
    QUANTITY = "QUANTITY"
    AREA = "AREA"
    ADDITIONAL_INFOS = "ADDITIONAL_INFOS"
    NON_STOCK = "NON_STOCK"
    CUSTOMERS = "CUSTOMERS"
    VENDORS = "VENDORS"
    MIN_QUANTITY = "MIN_QUANTITY"
    TEAMS = "TEAMS"
    ASSETS = "ASSETS"
    MULTI_PARTS = "MULTI_PARTS"
    UNIT = "UNIT"


class WOField(StrEnum):
    ASSET = "ASSET"
    ASSIGNEES = "ASSIGNEES"
    CATEGORY = "CATEGORY"
    DESCRIPTION = "DESCRIPTION"
    DUE_DATE = "DUE_DATE"
    ESTIMATED_DURATION = "ESTIMATED_DURATION"
    LOCATION = "LOCATION"
    PARTS = "PARTS"
    PRIORITY = "PRIORITY"
    STATUS = "STATUS"
    TITLE = "TITLE"
    TEAM = "TEAM"
    CUSTOMERS = "CUSTOMERS"


class WebhookEvent(StrEnum):
    ASSET_STATUS_CHANGE = "ASSET_STATUS_CHANGE"
    METER_TRIGGER_STATUS_CHANGE = "METER_TRIGGER_STATUS_CHANGE"
    NEW_ASSET = "NEW_ASSET"
    NEW_CATEGORY_ON_WORK_ORDER = "NEW_CATEGORY_ON_WORK_ORDER"
    NEW_COMMENT_ON_WORK_ORDER = "NEW_COMMENT_ON_WORK_ORDER"
    NEW_LOCATION = "NEW_LOCATION"
    NEW_PART = "NEW_PART"
    NEW_PURCHASE_ORDER = "NEW_PURCHASE_ORDER"
    NEW_VENDOR = "NEW_VENDOR"
    NEW_WORK_ORDER = "NEW_WORK_ORDER"
    NEW_REQUEST = "NEW_REQUEST"
    PART_CHANGE = "PART_CHANGE"
    PART_DELETE = "PART_DELETE"
    PART_QUANTITY_CHANGED = "PART_QUANTITY_CHANGED"
    PURCHASE_ORDER_CHANGE = "PURCHASE_ORDER_CHANGE"
    PURCHASE_ORDER_STATUS_CHANGE = "PURCHASE_ORDER_STATUS_CHANGE"
    WORK_ORDER_CHANGE = "WORK_ORDER_CHANGE"
    WORK_ORDER_DELETE = "WORK_ORDER_DELETE"
    WORK_ORDER_OVERDUE = "WORK_ORDER_OVERDUE"
    WORK_ORDER_STATUS_CHANGE = "WORK_ORDER_STATUS_CHANGE"
    WORK_REQUEST_STATUS_CHANGE = "WORK_REQUEST_STATUS_CHANGE"


class PartAction(StrEnum):
    CREATE_PURCHASE_ORDER = "CREATE_PURCHASE_ORDER"


class PartCondition(StrEnum):
    PART_IS = "PART_IS"
    QUANTITY_INFERIOR = "QUANTITY_INFERIOR"


class PurchaseOrderAction(StrEnum):
    ASSIGN_VENDOR = "ASSIGN_VENDOR"
    ASSIGN_CATEGORY = "ASSIGN_CATEGORY"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    SEND_REMINDER_EMAIL = "SEND_REMINDER_EMAIL"


class PurchaseOrderCondition(StrEnum):
    VENDOR_IS = "VENDOR_IS"
    CATEGORY_IS = "CATEGORY_IS"
    STATUS_IS = "STATUS_IS"
    DUE_DATE_BETWEEN = "DUE_DATE_BETWEEN"
    DUE_DATE_AFTER = "DUE_DATE_AFTER"


class RequestAction(StrEnum):
    ASSIGN_PRIORITY = "ASSIGN_PRIORITY"
    ASSIGN_ASSET = "ASSIGN_ASSET"
    ASSIGN_LOCATION = "ASSIGN_LOCATION"
    ASSIGN_USER = "ASSIGN_USER"
    ASSIGN_TEAM = "ASSIGN_TEAM"
    ASSIGN_CATEGORY = "ASSIGN_CATEGORY"
    ADD_CHECKLIST = "ADD_CHECKLIST"
    APPROVE = "APPROVE"
    SEND_REMINDER_EMAIL = "SEND_REMINDER_EMAIL"


class RequestCondition(StrEnum):
    PRIORITY_IS = "PRIORITY_IS"
    ASSET_IS = "ASSET_IS"
    LOCATION_IS = "LOCATION_IS"
    USER_IS = "USER_IS"
    TEAM_IS = "TEAM_IS"
    CATEGORY_IS = "CATEGORY_IS"
    CREATED_AT_BETWEEN = "CREATED_AT_BETWEEN"
    DUE_DATE_BETWEEN = "DUE_DATE_BETWEEN"
    DUE_DATE_AFTER = "DUE_DATE_AFTER"
    TITLE_CONTAINS = "TITLE_CONTAINS"


class TaskAction(StrEnum):
    CREATE_REQUEST = "CREATE_REQUEST"
    CREATE_WORK_ORDER = "CREATE_WORK_ORDER"
    SET_ASSET_STATUS = "SET_ASSET_STATUS"


class TaskCondition(StrEnum):
    NAME_IS = "NAME_IS"
    NAME_CONTAINS = "NAME_CONTAINS"
    VALUE_IS = "VALUE_IS"
    VALUE_CONTAINS = "VALUE_CONTAINS"
    NUMBER_VALUE_SUPERIOR = "NUMBER_VALUE_SUPERIOR"
    NUMBER_VALUE_INFERIOR = "NUMBER_VALUE_INFERIOR"


class WFMainCondition(StrEnum):
    WORK_ORDER_CREATED = "WORK_ORDER_CREATED"
    WORK_ORDER_CLOSED = "WORK_ORDER_CLOSED"
    WORK_ORDER_ARCHIVED = "WORK_ORDER_ARCHIVED"
    REQUEST_CREATED = "REQUEST_CREATED"
    REQUEST_APPROVED = "REQUEST_APPROVED"
    REQUEST_REJECTED = "REQUEST_REJECTED"
    PURCHASE_ORDER_CREATED = "PURCHASE_ORDER_CREATED"
    PURCHASE_ORDER_UPDATED = "PURCHASE_ORDER_UPDATED"
    TASK_UPDATED = "TASK_UPDATED"
    PART_UPDATED = "PART_UPDATED"


class WorkOrderAction(StrEnum):
    ASSIGN_PRIORITY = "ASSIGN_PRIORITY"
    ASSIGN_ASSET = "ASSIGN_ASSET"
    ASSIGN_LOCATION = "ASSIGN_LOCATION"
    ASSIGN_USER = "ASSIGN_USER"
    ASSIGN_TEAM = "ASSIGN_TEAM"
    ASSIGN_CATEGORY = "ASSIGN_CATEGORY"
    ADD_CHECKLIST = "ADD_CHECKLIST"
    SEND_REMINDER_EMAIL = "SEND_REMINDER_EMAIL"


class WorkOrderCondition(StrEnum):
    PRIORITY_IS = "PRIORITY_IS"
    ASSET_IS = "ASSET_IS"
    LOCATION_IS = "LOCATION_IS"
    USER_IS = "USER_IS"
    TEAM_IS = "TEAM_IS"
    CATEGORY_IS = "CATEGORY_IS"
    CREATED_AT_BETWEEN = "CREATED_AT_BETWEEN"
    DUE_DATE_BETWEEN = "DUE_DATE_BETWEEN"
    DUE_DATE_AFTER = "DUE_DATE_AFTER"
    STATUS_IS = "STATUS_IS"
    TITLE_CONTAINS = "TITLE_CONTAINS"
