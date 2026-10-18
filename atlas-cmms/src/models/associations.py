"""Association and @ElementCollection tables from Liquibase."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Table,
)

from src.models._base import Base

checklist_task_bases = Table(
    "checklist_task_bases",
    Base.metadata,
    Column("checklist_id", BigInteger, ForeignKey("checklist.id", ondelete="SET NULL"), nullable=False),
    Column("task_bases_id", BigInteger, ForeignKey("task_base.id", ondelete="SET NULL"), nullable=False),
)

comment_files = Table(
    "comment_files",
    Base.metadata,
    Column("comment_id", BigInteger, ForeignKey("comment.id", ondelete="CASCADE"), nullable=False),
    Column("files_id", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False),
)

company_custom_field_options = Table(
    "company_custom_field_options",
    Base.metadata,
    Column("field_id", BigInteger, ForeignKey("custom_field.id", ondelete="CASCADE"), nullable=False),
    Column("option_value", String(255), nullable=False),
)

own_user_preventive_maintenances = Table(
    "own_user_preventive_maintenances",
    Base.metadata,
    Column("own_user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
    Column("preventive_maintenances_id", BigInteger, ForeignKey("preventive_maintenance.id", ondelete="CASCADE"), nullable=False),
)

own_user_work_orders = Table(
    "own_user_work_orders",
    Base.metadata,
    Column("own_user_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
    Column("work_orders_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False),
)

part_preventive_maintenances = Table(
    "part_preventive_maintenances",
    Base.metadata,
    Column("part_id", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=False),
    Column("preventive_maintenances_id", BigInteger, ForeignKey("preventive_maintenance.id", ondelete="CASCADE"), nullable=False),
)

preventive_maintenance_assigned_to = Table(
    "preventive_maintenance_assigned_to",
    Base.metadata,
    Column("preventive_maintenance_id", BigInteger, ForeignKey("preventive_maintenance.id", ondelete="CASCADE"), nullable=False),
    Column("assigned_to_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
)

preventive_maintenance_customers = Table(
    "preventive_maintenance_customers",
    Base.metadata,
    Column("preventive_maintenance_id", BigInteger, ForeignKey("preventive_maintenance.id", ondelete="CASCADE"), nullable=False),
    Column("customers_id", BigInteger, ForeignKey("customer.id", ondelete="CASCADE"), nullable=False),
)

preventive_maintenance_files = Table(
    "preventive_maintenance_files",
    Base.metadata,
    Column("preventive_maintenance_id", BigInteger, ForeignKey("preventive_maintenance.id", ondelete="CASCADE"), nullable=False),
    Column("files_id", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False),
)

request_assigned_to = Table(
    "request_assigned_to",
    Base.metadata,
    Column("request_id", BigInteger, ForeignKey("request.id", ondelete="CASCADE"), nullable=False),
    Column("assigned_to_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
)

request_customers = Table(
    "request_customers",
    Base.metadata,
    Column("request_id", BigInteger, ForeignKey("request.id", ondelete="CASCADE"), nullable=False),
    Column("customers_id", BigInteger, ForeignKey("customer.id", ondelete="CASCADE"), nullable=False),
)

request_files = Table(
    "request_files",
    Base.metadata,
    Column("request_id", BigInteger, ForeignKey("request.id", ondelete="CASCADE"), nullable=False),
    Column("files_id", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False),
)

role_create_permissions = Table(
    "role_create_permissions",
    Base.metadata,
    Column("role_id", BigInteger, ForeignKey("role.id", ondelete="CASCADE"), nullable=False),
    Column("create_permissions", SmallInteger, nullable=True),
)

role_delete_other_permissions = Table(
    "role_delete_other_permissions",
    Base.metadata,
    Column("role_id", BigInteger, ForeignKey("role.id", ondelete="CASCADE"), nullable=False),
    Column("delete_other_permissions", SmallInteger, nullable=True),
)

role_edit_other_permissions = Table(
    "role_edit_other_permissions",
    Base.metadata,
    Column("role_id", BigInteger, ForeignKey("role.id", ondelete="CASCADE"), nullable=False),
    Column("edit_other_permissions", SmallInteger, nullable=True),
)

role_view_other_permissions = Table(
    "role_view_other_permissions",
    Base.metadata,
    Column("role_id", BigInteger, ForeignKey("role.id", ondelete="CASCADE"), nullable=False),
    Column("view_other_permissions", SmallInteger, nullable=True),
)

role_view_permissions = Table(
    "role_view_permissions",
    Base.metadata,
    Column("role_id", BigInteger, ForeignKey("role.id", ondelete="CASCADE"), nullable=False),
    Column("view_permissions", SmallInteger, nullable=True),
)

schedule_days_of_week = Table(
    "schedule_days_of_week",
    Base.metadata,
    Column("schedule_id", BigInteger, ForeignKey("schedule.id", ondelete="CASCADE"), nullable=False),
    Column("days_of_week", Integer, nullable=True),
)

shift_configuration_days = Table(
    "shift_configuration_days",
    Base.metadata,
    Column("shift_configuration_id", BigInteger, ForeignKey("shift_configuration.id", ondelete="CASCADE"), nullable=False),
    Column("day_of_week", String(255), nullable=False),
    Column("availability_minutes", Integer, nullable=False),
    Column("enabled", Boolean, nullable=False),
)

shift_configuration_exceptions = Table(
    "shift_configuration_exceptions",
    Base.metadata,
    Column("shift_configuration_id", BigInteger, ForeignKey("shift_configuration.id", ondelete="CASCADE"), nullable=False),
    Column("exception_date", Date, nullable=False),
    Column("availability_minutes", Integer, nullable=False),
    Column("enabled", Boolean, nullable=False),
)

subscription_plan_features = Table(
    "subscription_plan_features",
    Base.metadata,
    Column("subscription_plan_id", BigInteger, ForeignKey("subscription_plan.id", ondelete="CASCADE"), nullable=False),
    Column("features", SmallInteger, nullable=True),
)

t_asset_customer_associations = Table(
    "t_asset_customer_associations",
    Base.metadata,
    Column("id_customer", BigInteger, ForeignKey("customer.id", ondelete="CASCADE"), nullable=False),
    Column("id_asset", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False),
)

t_asset_file_associations = Table(
    "t_asset_file_associations",
    Base.metadata,
    Column("id_asset", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False),
    Column("id_file", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False),
)

t_asset_part_associations = Table(
    "t_asset_part_associations",
    Base.metadata,
    Column("id_part", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=False),
    Column("id_asset", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False),
)

t_asset_team_associations = Table(
    "t_asset_team_associations",
    Base.metadata,
    Column("id_asset", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False),
    Column("id_team", BigInteger, ForeignKey("team.id", ondelete="CASCADE"), nullable=False),
)

t_asset_user_associations = Table(
    "t_asset_user_associations",
    Base.metadata,
    Column("id_user", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
    Column("id_asset", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False),
)

t_asset_vendor_associations = Table(
    "t_asset_vendor_associations",
    Base.metadata,
    Column("id_vendor", BigInteger, ForeignKey("vendor.id", ondelete="CASCADE"), nullable=False),
    Column("id_asset", BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False),
)

t_location_customer_associations = Table(
    "t_location_customer_associations",
    Base.metadata,
    Column("id_location", BigInteger, ForeignKey("location.id", ondelete="CASCADE"), nullable=False),
    Column("id_customer", BigInteger, ForeignKey("customer.id", ondelete="CASCADE"), nullable=False),
)

t_location_file_associations = Table(
    "t_location_file_associations",
    Base.metadata,
    Column("id_location", BigInteger, ForeignKey("location.id", ondelete="CASCADE"), nullable=False),
    Column("id_file", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False),
)

t_location_team_associations = Table(
    "t_location_team_associations",
    Base.metadata,
    Column("id_location", BigInteger, ForeignKey("location.id", ondelete="CASCADE"), nullable=False),
    Column("id_team", BigInteger, ForeignKey("team.id", ondelete="CASCADE"), nullable=False),
)

t_location_user_associations = Table(
    "t_location_user_associations",
    Base.metadata,
    Column("id_location", BigInteger, ForeignKey("location.id", ondelete="CASCADE"), nullable=False),
    Column("id_user", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
)

t_location_vendor_associations = Table(
    "t_location_vendor_associations",
    Base.metadata,
    Column("id_location", BigInteger, ForeignKey("location.id", ondelete="CASCADE"), nullable=False),
    Column("id_vendor", BigInteger, ForeignKey("vendor.id", ondelete="CASCADE"), nullable=False),
)

t_meter_user_associations = Table(
    "t_meter_user_associations",
    Base.metadata,
    Column("id_meter", BigInteger, ForeignKey("meter.id", ondelete="CASCADE"), nullable=False),
    Column("id_user", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
)

t_multi_parts_part_associations = Table(
    "t_multi_parts_part_associations",
    Base.metadata,
    Column("id_part", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=False),
    Column("id_multi_parts", BigInteger, ForeignKey("multi_parts.id", ondelete="CASCADE"), nullable=False),
)

t_part_customer_associations = Table(
    "t_part_customer_associations",
    Base.metadata,
    Column("id_part", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=False),
    Column("id_customer", BigInteger, ForeignKey("customer.id", ondelete="CASCADE"), nullable=False),
)

t_part_file_associations = Table(
    "t_part_file_associations",
    Base.metadata,
    Column("id_part", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=False),
    Column("id_file", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False),
)

t_part_team_associations = Table(
    "t_part_team_associations",
    Base.metadata,
    Column("id_part", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=False),
    Column("id_team", BigInteger, ForeignKey("team.id", ondelete="CASCADE"), nullable=False),
)

t_part_user_associations = Table(
    "t_part_user_associations",
    Base.metadata,
    Column("id_part", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=False),
    Column("id_user", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
)

t_part_vendor_associations = Table(
    "t_part_vendor_associations",
    Base.metadata,
    Column("id_part", BigInteger, ForeignKey("part.id", ondelete="CASCADE"), nullable=False),
    Column("id_vendor", BigInteger, ForeignKey("vendor.id", ondelete="CASCADE"), nullable=False),
)

t_request_file_associations = Table(
    "t_request_file_associations",
    Base.metadata,
    Column("id_file", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False),
    Column("id_request", BigInteger, ForeignKey("request.id", ondelete="CASCADE"), nullable=False),
)

t_team_user_associations = Table(
    "t_team_user_associations",
    Base.metadata,
    Column("id_user", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
    Column("id_team", BigInteger, ForeignKey("team.id", ondelete="CASCADE"), nullable=False),
)

t_work_order_file_associations = Table(
    "t_work_order_file_associations",
    Base.metadata,
    Column("id_file", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False),
    Column("id_work_order", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False),
)

webhook_endpoint_asset_statuses = Table(
    "webhook_endpoint_asset_statuses",
    Base.metadata,
    Column("webhook_endpoint_id", BigInteger, ForeignKey("webhook_endpoint.id", ondelete="CASCADE"), nullable=False),
    Column("asset_statuses", String(255), nullable=False),
)

webhook_endpoint_part_fields = Table(
    "webhook_endpoint_part_fields",
    Base.metadata,
    Column("webhook_endpoint_id", BigInteger, ForeignKey("webhook_endpoint.id", ondelete="CASCADE"), nullable=False),
    Column("part_fields", String(255), nullable=False),
)

webhook_endpoint_wo_fields = Table(
    "webhook_endpoint_wo_fields",
    Base.metadata,
    Column("webhook_endpoint_id", BigInteger, ForeignKey("webhook_endpoint.id", ondelete="CASCADE"), nullable=False),
    Column("wo_fields", String(255), nullable=False),
)

webhook_endpoint_work_order_categories = Table(
    "webhook_endpoint_work_order_categories",
    Base.metadata,
    Column("webhook_endpoint_id", BigInteger, ForeignKey("webhook_endpoint.id", ondelete="CASCADE"), nullable=False),
    Column("work_order_categories_id", BigInteger, ForeignKey("work_order_category.id", ondelete="CASCADE"), nullable=False),
)

webhook_endpoint_work_order_statuses = Table(
    "webhook_endpoint_work_order_statuses",
    Base.metadata,
    Column("webhook_endpoint_id", BigInteger, ForeignKey("webhook_endpoint.id", ondelete="CASCADE"), nullable=False),
    Column("work_order_statuses", String(255), nullable=False),
)

work_order_assigned_to = Table(
    "work_order_assigned_to",
    Base.metadata,
    Column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False),
    Column("assigned_to_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
)

work_order_customers = Table(
    "work_order_customers",
    Base.metadata,
    Column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False),
    Column("customers_id", BigInteger, ForeignKey("customer.id", ondelete="CASCADE"), nullable=False),
)

work_order_files = Table(
    "work_order_files",
    Base.metadata,
    Column("work_order_id", BigInteger, ForeignKey("work_order.id", ondelete="CASCADE"), nullable=False),
    Column("files_id", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False),
)

work_order_meter_trigger_assigned_to = Table(
    "work_order_meter_trigger_assigned_to",
    Base.metadata,
    Column("work_order_meter_trigger_id", BigInteger, ForeignKey("work_order_meter_trigger.id", ondelete="CASCADE"), nullable=False),
    Column("assigned_to_id", BigInteger, ForeignKey("own_user.id", ondelete="CASCADE"), nullable=False),
)

work_order_meter_trigger_customers = Table(
    "work_order_meter_trigger_customers",
    Base.metadata,
    Column("work_order_meter_trigger_id", BigInteger, ForeignKey("work_order_meter_trigger.id", ondelete="CASCADE"), nullable=False),
    Column("customers_id", BigInteger, ForeignKey("customer.id", ondelete="CASCADE"), nullable=False),
)

work_order_meter_trigger_files = Table(
    "work_order_meter_trigger_files",
    Base.metadata,
    Column("work_order_meter_trigger_id", BigInteger, ForeignKey("work_order_meter_trigger.id", ondelete="CASCADE"), nullable=False),
    Column("files_id", BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False),
)

workflow_secondary_conditions = Table(
    "workflow_secondary_conditions",
    Base.metadata,
    Column("workflow_id", BigInteger, ForeignKey("workflow.id", ondelete="SET NULL"), nullable=False),
    Column("secondary_conditions_id", BigInteger, ForeignKey("workflow_condition.id", ondelete="SET NULL"), nullable=False),
)
