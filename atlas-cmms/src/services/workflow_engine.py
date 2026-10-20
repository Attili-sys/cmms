"""Workflow evaluation and action execution engine matching Java WorkflowService."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.associations import (
    checklist_task_bases,
    workflow_secondary_conditions,
)
from src.models.enums import (
    PartAction,
    PartCondition,
    PurchaseOrderAction,
    PurchaseOrderCondition,
    RequestAction,
    RequestCondition,
    TaskAction,
    TaskCondition,
    WFMainCondition,
    WorkOrderAction,
    WorkOrderCondition,
)
from src.models.location_asset import Asset
from src.models.parts_po import Part, PartQuantity, PurchaseOrder
from src.models.requests import Request
from src.models.tasks import Task, TaskBase, TaskOption
from src.models.work_orders import WorkOrder
from src.models.workflows import Workflow, WorkflowAction, WorkflowCondition


def _enum_idx(enum_cls: type, val: Any) -> int | None:
    if val is None:
        return None
    if isinstance(val, int):
        return val
    members = list(enum_cls)
    s = str(val).strip().upper()
    for idx, m in enumerate(members):
        if m.name == s or m.value == s:
            return idx
    if s.isdigit():
        return int(s)
    return None


def _load_active_workflows(
    db: Session, company_id: int | None, main_cond: WFMainCondition
) -> list[tuple[Workflow, list[WorkflowCondition], WorkflowAction]]:
    if company_id is None:
        return []
    cond_idx = _enum_idx(WFMainCondition, main_cond)
    wfs = db.scalars(
        select(Workflow).where(
            Workflow.company_id == company_id,
            Workflow.enabled.is_(True),
            Workflow.main_condition == cond_idx,
        )
    ).all()
    results: list[tuple[Workflow, list[WorkflowCondition], WorkflowAction]] = []
    for wf in wfs:
        act = db.get(WorkflowAction, wf.action_id) if wf.action_id else None
        if act is None:
            continue
        cond_ids = db.scalars(
            select(workflow_secondary_conditions.c.secondary_conditions_id).where(
                workflow_secondary_conditions.c.workflow_id == wf.id
            )
        ).all()
        conds = (
            list(
                db.scalars(
                    select(WorkflowCondition).where(WorkflowCondition.id.in_(cond_ids))
                ).all()
            )
            if cond_ids
            else []
        )
        results.append((wf, conds, act))
    return results


def _match_wo_condition(wo: WorkOrder, cond: WorkflowCondition) -> bool:
    c_idx = _enum_idx(WorkOrderCondition, cond.work_order_condition)
    if c_idx is None:
        return True
    cond_name = list(WorkOrderCondition)[c_idx].name if 0 <= c_idx < len(WorkOrderCondition) else ""
    if cond_name == "PRIORITY_IS":
        return (wo.priority or 0) == (cond.priority or 0)
    if cond_name == "ASSET_IS":
        return wo.asset_id == cond.asset_id
    if cond_name == "LOCATION_IS":
        return wo.location_id == cond.location_id
    if cond_name == "USER_IS":
        return wo.primary_user_id == cond.user_id
    if cond_name == "TEAM_IS":
        return wo.team_id == cond.team_id
    if cond_name == "CATEGORY_IS":
        return wo.category_id == cond.work_order_category_id
    if cond_name == "STATUS_IS":
        return (wo.status or 0) == (cond.work_order_status or 0)
    if cond_name == "TITLE_CONTAINS":
        needle = (cond.label or cond.value or "").strip().lower()
        return needle in (wo.title or "").lower()
    return True


def _apply_wo_action(wo: WorkOrder, act: WorkflowAction, db: Session) -> None:
    a_idx = _enum_idx(WorkOrderAction, act.work_order_action)
    if a_idx is None:
        return
    act_name = list(WorkOrderAction)[a_idx].name if 0 <= a_idx < len(WorkOrderAction) else ""
    if act_name == "ASSIGN_PRIORITY" and act.priority is not None:
        wo.priority = act.priority
    elif act_name == "ASSIGN_ASSET" and act.asset_id is not None:
        wo.asset_id = act.asset_id
    elif act_name == "ASSIGN_LOCATION" and act.location_id is not None:
        wo.location_id = act.location_id
    elif act_name == "ASSIGN_USER" and act.user_id is not None:
        wo.primary_user_id = act.user_id
    elif act_name == "ASSIGN_TEAM" and act.team_id is not None:
        wo.team_id = act.team_id
    elif act_name == "ASSIGN_CATEGORY" and act.work_order_category_id is not None:
        wo.category_id = act.work_order_category_id
    elif act_name == "ADD_CHECKLIST" and act.checklist_id is not None and wo.id is not None:
        tb_ids = db.scalars(
            select(checklist_task_bases.c.task_bases_id).where(
                checklist_task_bases.c.checklist_id == act.checklist_id
            )
        ).all()
        for tb_id in tb_ids:
            orig_tb = db.get(TaskBase, tb_id)
            if orig_tb is None:
                continue
            cloned_tb = TaskBase(
                label=orig_tb.label,
                task_type=orig_tb.task_type,
                company_id=wo.company_id,
                asset_id=orig_tb.asset_id,
                user_id=orig_tb.user_id,
                meter_id=orig_tb.meter_id,
            )
            db.add(cloned_tb)
            db.flush()
            opts = db.scalars(
                select(TaskOption).where(TaskOption.task_base_id == orig_tb.id)
            ).all()
            for opt in opts:
                db.add(
                    TaskOption(
                        label=opt.label,
                        task_base_id=cloned_tb.id,
                        company_id=wo.company_id,
                    )
                )
            db.add(
                Task(
                    company_id=wo.company_id,
                    task_base_id=cloned_tb.id,
                    work_order_id=wo.id,
                )
            )
        db.flush()


def run_work_order_workflows(
    wo: WorkOrder, main_cond: WFMainCondition, db: Session
) -> None:
    """Evaluate and execute all enabled workflows for a WorkOrder event."""
    for _wf, conds, act in _load_active_workflows(db, wo.company_id, main_cond):
        if all(_match_wo_condition(wo, c) for c in conds):
            _apply_wo_action(wo, act, db)


def _match_request_condition(req: Request, cond: WorkflowCondition) -> bool:
    c_idx = _enum_idx(RequestCondition, cond.request_condition)
    if c_idx is None:
        return True
    cond_name = list(RequestCondition)[c_idx].name if 0 <= c_idx < len(RequestCondition) else ""
    if cond_name == "PRIORITY_IS":
        return (req.priority or 0) == (cond.priority or 0)
    if cond_name == "ASSET_IS":
        return req.asset_id == cond.asset_id
    if cond_name == "LOCATION_IS":
        return req.location_id == cond.location_id
    if cond_name == "USER_IS":
        return req.primary_user_id == cond.user_id
    if cond_name == "TEAM_IS":
        return req.team_id == cond.team_id
    if cond_name == "CATEGORY_IS":
        return req.category_id == cond.work_order_category_id
    if cond_name == "TITLE_CONTAINS":
        needle = (cond.label or cond.value or "").strip().lower()
        return needle in (req.title or "").lower()
    return True


def _apply_request_action(req: Request, act: WorkflowAction, db: Session) -> None:
    a_idx = _enum_idx(RequestAction, act.request_action)
    if a_idx is None:
        return
    act_name = list(RequestAction)[a_idx].name if 0 <= a_idx < len(RequestAction) else ""
    if act_name == "ASSIGN_PRIORITY" and act.priority is not None:
        req.priority = act.priority
    elif act_name == "ASSIGN_ASSET" and act.asset_id is not None:
        req.asset_id = act.asset_id
    elif act_name == "ASSIGN_LOCATION" and act.location_id is not None:
        req.location_id = act.location_id
    elif act_name == "ASSIGN_USER" and act.user_id is not None:
        req.primary_user_id = act.user_id
    elif act_name == "ASSIGN_TEAM" and act.team_id is not None:
        req.team_id = act.team_id
    elif act_name == "ASSIGN_CATEGORY" and act.work_order_category_id is not None:
        req.category_id = act.work_order_category_id
    elif act_name == "APPROVE" and req.work_order_id is None:
        wo = WorkOrder(
            title=req.title,
            description=req.description,
            priority=req.priority or 0,
            status=0,
            company_id=req.company_id,
            location_id=req.location_id,
            asset_id=req.asset_id,
            category_id=req.category_id,
            team_id=req.team_id,
            primary_user_id=req.primary_user_id,
            image_id=req.image_id,
            due_date=req.due_date,
            estimated_duration=req.estimated_duration or 0.0,
            required_signature=bool(req.required_signature),
            archived=False,
            is_demo=False,
            created_by=req.created_by,
        )
        db.add(wo)
        db.flush()
        wo.custom_id = f"WO{wo.id:06d}"
        req.work_order_id = wo.id


def run_request_workflows(
    req: Request, main_cond: WFMainCondition, db: Session
) -> None:
    """Evaluate and execute all enabled workflows for a Request event."""
    for _wf, conds, act in _load_active_workflows(db, req.company_id, main_cond):
        if all(_match_request_condition(req, c) for c in conds):
            _apply_request_action(req, act, db)


def _match_po_condition(po: PurchaseOrder, cond: WorkflowCondition) -> bool:
    c_idx = _enum_idx(PurchaseOrderCondition, cond.purchase_order_condition)
    if c_idx is None:
        return True
    cond_name = (
        list(PurchaseOrderCondition)[c_idx].name
        if 0 <= c_idx < len(PurchaseOrderCondition)
        else ""
    )
    if cond_name == "VENDOR_IS":
        return po.vendor_id == cond.vendor_id
    if cond_name == "CATEGORY_IS":
        return po.category_id == cond.purchase_order_category_id
    if cond_name == "STATUS_IS":
        return (po.status if po.status is not None else 2) == (cond.purchase_order_status or 0)
    return True


def _apply_po_action(po: PurchaseOrder, act: WorkflowAction, db: Session) -> None:
    a_idx = _enum_idx(PurchaseOrderAction, act.purchase_order_action)
    if a_idx is None:
        return
    act_name = (
        list(PurchaseOrderAction)[a_idx].name
        if 0 <= a_idx < len(PurchaseOrderAction)
        else ""
    )
    if act_name == "ASSIGN_VENDOR" and act.vendor_id is not None:
        po.vendor_id = act.vendor_id
    elif act_name == "ASSIGN_CATEGORY" and act.purchase_order_category_id is not None:
        po.category_id = act.purchase_order_category_id
    elif act_name == "APPROVE":
        po.status = 0
    elif act_name == "REJECT":
        po.status = 1


def run_purchase_order_workflows(
    po: PurchaseOrder, main_cond: WFMainCondition, db: Session
) -> None:
    """Evaluate and execute all enabled workflows for a PurchaseOrder event."""
    for _wf, conds, act in _load_active_workflows(db, po.company_id, main_cond):
        if all(_match_po_condition(po, c) for c in conds):
            _apply_po_action(po, act, db)


def _match_part_condition(part: Part, cond: WorkflowCondition) -> bool:
    c_idx = _enum_idx(PartCondition, cond.part_condition)
    if c_idx is None:
        return True
    cond_name = list(PartCondition)[c_idx].name if 0 <= c_idx < len(PartCondition) else ""
    if cond_name == "PART_IS":
        return part.id == cond.part_id
    if cond_name == "QUANTITY_INFERIOR":
        return float(part.quantity or 0.0) < float(cond.number_value or 0.0)
    return True


def _apply_part_action(part: Part, act: WorkflowAction, db: Session) -> None:
    a_idx = _enum_idx(PartAction, act.part_action)
    if a_idx is None:
        return
    act_name = list(PartAction)[a_idx].name if 0 <= a_idx < len(PartAction) else ""
    if act_name == "CREATE_PURCHASE_ORDER":
        po = PurchaseOrder(
            name=f"Auto PO - {part.name}",
            status=2,  # PENDING
            company_id=part.company_id,
            vendor_id=act.vendor_id,
            category_id=act.purchase_order_category_id,
        )
        db.add(po)
        db.flush()
        db.add(
            PartQuantity(
                part_id=part.id,
                purchase_order_id=po.id,
                quantity=float(act.number_value or 1.0),
            )
        )
        db.flush()


def run_part_workflows(part: Part, db: Session) -> None:
    """Evaluate and execute all enabled workflows for a Part update event."""
    for _wf, conds, act in _load_active_workflows(db, part.company_id, WFMainCondition.PART_UPDATED):
        if all(_match_part_condition(part, c) for c in conds):
            _apply_part_action(part, act, db)


def _match_task_condition(task: Task, cond: WorkflowCondition, db: Session) -> bool:
    c_idx = _enum_idx(TaskCondition, cond.task_condition)
    if c_idx is None:
        return True
    cond_name = list(TaskCondition)[c_idx].name if 0 <= c_idx < len(TaskCondition) else ""
    tb = db.get(TaskBase, task.task_base_id) if task.task_base_id else None
    tb_label = (tb.label if tb else "") or ""
    t_val = str(task.value or "")
    target_str = (cond.value or cond.label or "").strip()

    if cond_name == "NAME_IS":
        return tb_label.strip().lower() == (cond.label or cond.value or "").strip().lower()
    if cond_name == "NAME_CONTAINS":
        return (cond.label or cond.value or "").strip().lower() in tb_label.lower()
    if cond_name == "VALUE_IS":
        return t_val.strip().lower() == target_str.lower()
    if cond_name == "VALUE_CONTAINS":
        return target_str.lower() in t_val.lower()
    if cond_name == "NUMBER_VALUE_SUPERIOR":
        try:
            return float(t_val) > float(cond.number_value or 0.0)
        except ValueError:
            return False
    if cond_name == "NUMBER_VALUE_INFERIOR":
        try:
            return float(t_val) < float(cond.number_value or 0.0)
        except ValueError:
            return False
    return True


def _apply_task_action(task: Task, act: WorkflowAction, db: Session) -> None:
    a_idx = _enum_idx(TaskAction, act.task_action)
    if a_idx is None:
        return
    act_name = list(TaskAction)[a_idx].name if 0 <= a_idx < len(TaskAction) else ""
    tb = db.get(TaskBase, task.task_base_id) if task.task_base_id else None
    parent_wo = db.get(WorkOrder, task.work_order_id) if task.work_order_id else None
    asset_id = act.asset_id or (tb.asset_id if tb else None) or (parent_wo.asset_id if parent_wo else None)
    location_id = act.location_id or (parent_wo.location_id if parent_wo else None)
    title = act.value or (tb.label if tb else None) or "Workflow Triggered Item"

    if act_name == "CREATE_REQUEST":
        req = Request(
            title=title,
            priority=act.priority or 0,
            company_id=task.company_id,
            asset_id=asset_id,
            location_id=location_id,
            category_id=act.work_order_category_id,
            team_id=act.team_id,
            primary_user_id=act.user_id,
            cancelled=False,
            is_demo=False,
            required_signature=False,
            estimated_duration=0.0,
        )
        db.add(req)
        db.flush()
        req.custom_id = f"R{req.id:06d}"
    elif act_name == "CREATE_WORK_ORDER":
        wo = WorkOrder(
            title=title,
            priority=act.priority or 0,
            status=0,
            company_id=task.company_id,
            asset_id=asset_id,
            location_id=location_id,
            category_id=act.work_order_category_id,
            team_id=act.team_id,
            primary_user_id=act.user_id,
            archived=False,
            is_demo=False,
            required_signature=False,
            estimated_duration=0.0,
        )
        db.add(wo)
        db.flush()
        wo.custom_id = f"WO{wo.id:06d}"
    elif act_name == "SET_ASSET_STATUS" and asset_id is not None and act.asset_status is not None:
        asset = db.get(Asset, asset_id)
        if asset is not None and asset.company_id == task.company_id:
            asset.status = act.asset_status


def run_task_workflows(task: Task, db: Session) -> None:
    """Evaluate and execute all enabled workflows for a Task update event."""
    for _wf, conds, act in _load_active_workflows(db, task.company_id, WFMainCondition.TASK_UPDATED):
        if all(_match_task_condition(task, c, db) for c in conds):
            _apply_task_action(task, act, db)
