-- Remove recurring donation features from donations table
-- This migration removes all recurring donation functionality

-- First, drop the indexes related to recurring donations
DROP INDEX IF EXISTS idx_recurring_donations;
DROP INDEX IF EXISTS idx_recurring_links;

-- Remove foreign key constraint for recurring_id if it exists
ALTER TABLE donations DROP CONSTRAINT IF EXISTS donations_recurring_id_fkey;
ALTER TABLE donations DROP CONSTRAINT IF EXISTS donations_recurring_id_fkey1;
ALTER TABLE donations DROP CONSTRAINT IF EXISTS donations_recurring_id_fkey2;

-- Drop all recurring-related columns from donations table
ALTER TABLE donations DROP COLUMN IF EXISTS is_recurring;
ALTER TABLE donations DROP COLUMN IF EXISTS recurring_frequency;
ALTER TABLE donations DROP COLUMN IF EXISTS start_date;
ALTER TABLE donations DROP COLUMN IF EXISTS next_due_date;
ALTER TABLE donations DROP COLUMN IF EXISTS recurring_status;
ALTER TABLE donations DROP COLUMN IF EXISTS last_paid_date;
ALTER TABLE donations DROP COLUMN IF EXISTS linked_to_recurring;
ALTER TABLE donations DROP COLUMN IF EXISTS recurring_id;
ALTER TABLE donations DROP COLUMN IF EXISTS is_scheduled_payment;

-- Note: This migration will permanently remove all recurring donation data
-- Make sure to backup any important recurring donation information before running this migration 