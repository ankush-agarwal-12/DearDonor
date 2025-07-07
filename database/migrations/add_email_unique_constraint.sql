-- Add unique constraint for email per organization
-- This ensures donors within the same organization cannot have duplicate emails

-- Check for existing duplicates first (run this query to see if any exist)
-- SELECT email, organization_id, COUNT(*) as duplicate_count
-- FROM donors 
-- WHERE email IS NOT NULL AND email != ''
-- GROUP BY email, organization_id
-- HAVING COUNT(*) > 1;

-- Add the unique constraint (will fail if duplicates exist)
ALTER TABLE donors 
ADD CONSTRAINT donors_email_organization_unique 
UNIQUE (email, organization_id);

-- Update the index to be unique  
DROP INDEX IF EXISTS idx_donors_email;
CREATE UNIQUE INDEX idx_donors_email_org ON donors(email, organization_id) 
WHERE email IS NOT NULL AND email != ''; 