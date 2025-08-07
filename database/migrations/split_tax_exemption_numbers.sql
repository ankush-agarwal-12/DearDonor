-- Migration: Split tax_exemption_number into separate 12A and 80G fields
-- Date: 2025-01-XX

-- Add new columns for separate 12A and 80G numbers
ALTER TABLE organizations ADD COLUMN tax_exemption_12a TEXT;
ALTER TABLE organizations ADD COLUMN tax_exemption_80g TEXT;

-- Note: You can manually update existing data if needed:
-- UPDATE organizations SET tax_exemption_12a = tax_exemption_number WHERE tax_exemption_number LIKE '12A%';
-- UPDATE organizations SET tax_exemption_80g = tax_exemption_number WHERE tax_exemption_number LIKE '80G%';

-- The old tax_exemption_number column is kept for backward compatibility
-- You can drop it later if needed: ALTER TABLE organizations DROP COLUMN tax_exemption_number; 