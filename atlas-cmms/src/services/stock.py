"""Stock ledger: the only code that changes a part's quantity.

Every change is one ``part_transaction`` row carrying its movement type, the signed change, the
balance after it and a reason, so a part's history always explains its quantity. Callers own the
transaction: nothing here commits.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.enums import MovementType
from src.models.parts_po import Part, PartTransaction
from src.schemas.errors import CustomException

INBOUND = frozenset(
    {
        MovementType.OPENING,
        MovementType.RECEIPT,
        MovementType.PO_RECEIPT,
        MovementType.WO_RETURN,
        MovementType.COUNT_GAIN,
    }
)
OUTBOUND = frozenset(
    {
        MovementType.ISSUE,
        MovementType.WO_CONSUMPTION,
        MovementType.PO_REVERSAL,
        MovementType.COUNT_LOSS,
    }
)

# Written to `description` as well, so readers of the pre-ledger column keep working.
LEGACY_DESCRIPTION = {
    MovementType.RECEIPT: "PART_RESTOCK",
    MovementType.PO_RECEIPT: "PART_RECEPTION",
    MovementType.WO_CONSUMPTION: "PART_CONSUMPTION",
}


def lock_part(db: Session, part_id: int) -> Part:
    """Load a part with a row lock (Postgres) so concurrent stock changes serialise."""
    part = db.scalar(select(Part).where(Part.id == part_id).with_for_update())
    if part is None:
        raise CustomException(status_code=404, message=f"Part {part_id} not found")
    return part


def record_movement(
    db: Session,
    part: Part,
    movement_type: MovementType,
    quantity: float,
    *,
    user_id: int | None,
    work_order_id: int | None = None,
    purchase_order_id: int | None = None,
    reason: str | None = None,
    unit_cost: float | None = None,
    allow_negative: bool = False,
    run_workflows: bool = True,
) -> PartTransaction:
    """Apply one movement to ``part`` and write its ledger row.

    ``quantity`` is the magnitude. Its direction comes from ``movement_type``, except
    ``ADJUSTMENT``, whose sign is the sign of ``quantity``. ``part`` should come from
    :func:`lock_part` when the caller has not loaded it under a lock already.
    """
    quantity = float(quantity)
    if movement_type == MovementType.ADJUSTMENT:
        if quantity == 0:
            raise CustomException(status_code=406, message="Adjustment must change the quantity")
        change = quantity
    else:
        if quantity <= 0:
            raise CustomException(status_code=406, message="Quantity must be positive")
        change = quantity if movement_type in INBOUND else -quantity

    balance_after: float | None = None
    if not part.non_stock:
        current = float(part.quantity or 0.0)
        new_balance = current + change
        if new_balance < 0 and not allow_negative:
            raise CustomException(
                status_code=406, message=f"Insufficient stock for part {part.name}"
            )
        part.quantity = new_balance
        balance_after = new_balance

    tx = PartTransaction(
        part_id=part.id,
        company_id=part.company_id,
        quantity=abs(quantity),
        change=change,
        balance_after=balance_after,
        movement_type=movement_type.value,
        reason=(reason or "").strip() or None,
        work_order_id=work_order_id,
        purchase_order_id=purchase_order_id,
        unit_cost=float(part.cost or 0.0) if unit_cost is None else float(unit_cost),
        description=LEGACY_DESCRIPTION.get(movement_type, movement_type.value),
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(tx)
    if run_workflows:
        # Imported here: workflow_engine records PO receipts through this module.
        from src.services.workflow_engine import run_part_workflows

        run_part_workflows(part, db)
    return tx


def count_stock(
    db: Session,
    part: Part,
    counted: float,
    *,
    user_id: int | None,
    reason: str | None,
) -> tuple[PartTransaction | None, float]:
    """Set the book quantity to a physical count. Returns the ledger row (None when no variance) and the variance."""
    counted = float(counted)
    if counted < 0:
        raise CustomException(status_code=406, message="Counted quantity cannot be negative")
    variance = counted - float(part.quantity or 0.0)
    if variance == 0:
        return None, 0.0
    if not (reason or "").strip():
        raise CustomException(status_code=406, message="A reason is required when the count differs")
    movement = MovementType.COUNT_GAIN if variance > 0 else MovementType.COUNT_LOSS
    tx = record_movement(db, part, movement, abs(variance), user_id=user_id, reason=reason)
    return tx, variance
