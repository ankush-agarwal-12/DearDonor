-- Add PAN and donor_type columns to donors table
ALTER TABLE donors
ADD COLUMN IF NOT EXISTS pan TEXT,
ADD COLUMN IF NOT EXISTS donor_type TEXT DEFAULT 'Individual';

-- Update existing rows to have 'Individual' as donor_type if it's NULL
UPDATE donors 
SET donor_type = 'Individual' 
WHERE donor_type IS NULL; 