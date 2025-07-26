-- Add fields for linking donations to recurring schedules
ALTER TABLE donations
ADD COLUMN IF NOT EXISTS linked_to_recurring BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS recurring_id UUID REFERENCES donations(id),
ADD COLUMN IF NOT EXISTS is_scheduled_payment BOOLEAN DEFAULT FALSE;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_recurring_links
ON donations (linked_to_recurring, recurring_id)
WHERE linked_to_recurring = TRUE;

-- Add last_paid_date to track recurring donation status
ALTER TABLE donations
ADD COLUMN IF NOT EXISTS last_paid_date DATE; 