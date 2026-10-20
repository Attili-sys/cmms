-- Normalize blank/whitespace strings to NULL so blank values do not collide
UPDATE asset SET custom_id = NULL WHERE TRIM(COALESCE(custom_id, '')) = '';
UPDATE asset SET bar_code = NULL WHERE TRIM(COALESCE(bar_code, '')) = '';
UPDATE asset SET nfc_id = NULL WHERE TRIM(COALESCE(nfc_id, '')) = '';

-- Deduplicate existing rows within the same company by appending -{id} to later duplicates
UPDATE asset
SET custom_id = custom_id || '-' || CAST(id AS VARCHAR)
WHERE custom_id IS NOT NULL
  AND id NOT IN (
      SELECT MIN(id)
      FROM asset
      WHERE custom_id IS NOT NULL
      GROUP BY company_id, custom_id
  );

UPDATE asset
SET bar_code = bar_code || '-' || CAST(id AS VARCHAR)
WHERE bar_code IS NOT NULL
  AND id NOT IN (
      SELECT MIN(id)
      FROM asset
      WHERE bar_code IS NOT NULL
      GROUP BY company_id, bar_code
  );

UPDATE asset
SET nfc_id = nfc_id || '-' || CAST(id AS VARCHAR)
WHERE nfc_id IS NOT NULL
  AND id NOT IN (
      SELECT MIN(id)
      FROM asset
      WHERE nfc_id IS NOT NULL
      GROUP BY company_id, nfc_id
  );

-- Create tenant-scoped partial unique indexes
CREATE UNIQUE INDEX IF NOT EXISTS uq_asset_company_custom_id
    ON asset (company_id, custom_id)
    WHERE custom_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_asset_company_bar_code
    ON asset (company_id, bar_code)
    WHERE bar_code IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_asset_company_nfc_id
    ON asset (company_id, nfc_id)
    WHERE nfc_id IS NOT NULL;
