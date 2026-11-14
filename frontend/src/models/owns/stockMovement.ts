export type MovementType =
  | 'OPENING'
  | 'RECEIPT'
  | 'PO_RECEIPT'
  | 'PO_REVERSAL'
  | 'ISSUE'
  | 'WO_CONSUMPTION'
  | 'WO_RETURN'
  | 'COUNT_GAIN'
  | 'COUNT_LOSS'
  | 'ADJUSTMENT';

export interface StockMovement {
  id: number;
  createdAt: string;
  movementType: MovementType;
  change: number;
  balanceAfter: number | null;
  quantity: number;
  reason: string | null;
  unitCost: number | null;
  createdBy: { id: number; firstName: string; lastName: string } | null;
  workOrder: { id: number; title: string; customId: string } | null;
  purchaseOrder: { id: number; name: string } | null;
}

export interface StockMovementPage {
  content: StockMovement[];
  totalElements: number;
  page: number;
  size: number;
}
