-- Stock ledger: every quantity change on a part is a part_transaction row with its type,
-- signed change, running balance and reason. Additive only — the previous build keeps running.
-- purchase_order_id carries no FK: Canvas refuses new constraints on existing tables.
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS movement_type VARCHAR(32);
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS change DOUBLE PRECISION;
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS balance_after DOUBLE PRECISION;
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS reason TEXT;
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS purchase_order_id BIGINT;
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS unit_cost DOUBLE PRECISION;

CREATE INDEX IF NOT EXISTS ix_part_transaction_part_created ON part_transaction (part_id, created_at);

-- Type the rows written before the ledger existed. Their balance is unknown and stays NULL.
UPDATE part_transaction
SET movement_type = CASE description
        WHEN 'PART_RESTOCK' THEN 'RECEIPT'
        WHEN 'PART_RECEPTION' THEN 'PO_RECEIPT'
        ELSE 'WO_CONSUMPTION'
    END,
    change = CASE description
        WHEN 'PART_RESTOCK' THEN quantity
        WHEN 'PART_RECEPTION' THEN quantity
        ELSE -quantity
    END
WHERE movement_type IS NULL;

-- One baseline per stocked part, so every ledger starts from today's balance.
INSERT INTO part_transaction (
    id, created_at, updated_at, quantity, change, balance_after,
    movement_type, reason, description, company_id, part_id
)
SELECT nextval('part_transaction_seq'), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
       ABS(p.quantity), p.quantity, p.quantity,
       'OPENING', 'Ledger start', 'LEDGER_START', p.company_id, p.id
FROM part p
WHERE p.non_stock = FALSE
  AND NOT EXISTS (
      SELECT 1 FROM part_transaction t
      WHERE t.part_id = p.id AND t.description = 'LEDGER_START'
  );
