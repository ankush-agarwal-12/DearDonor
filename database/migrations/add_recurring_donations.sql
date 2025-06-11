-- Add recurring donation fields to donations table
ALTER TABLE donations
ADD COLUMN IF NOT EXISTS is_recurring BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS recurring_frequency TEXT CHECK (recurring_frequency IN ('Monthly', 'Quarterly', 'Yearly')),
ADD COLUMN IF NOT EXISTS start_date DATE,
ADD COLUMN IF NOT EXISTS next_due_date DATE,
ADD COLUMN IF NOT EXISTS recurring_status TEXT DEFAULT 'Active' CHECK (recurring_status IN ('Active', 'Paused', 'Cancelled'));

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_recurring_donations 
ON donations (is_recurring, recurring_status, next_due_date)
WHERE is_recurring = TRUE; 