-- Backup existing recurring donation data before removal
-- Run this BEFORE executing remove_recurring_donations.sql

-- Create a backup table for recurring donations data
CREATE TABLE IF NOT EXISTS recurring_donations_backup AS
SELECT 
    id,
    organization_id,
    donor_id,
    amount,
    date,
    purpose,
    payment_mode,
    is_recurring,
    recurring_frequency,
    start_date,
    next_due_date,
    recurring_status,
    last_paid_date,
    linked_to_recurring,
    recurring_id,
    is_scheduled_payment,
    created_at
FROM donations 
WHERE is_recurring = true OR linked_to_recurring = true;

-- Add a comment to the backup table
COMMENT ON TABLE recurring_donations_backup IS 'Backup of all recurring donation data before feature removal';

-- Show summary of backed up data
SELECT 
    'Recurring Plans' as type,
    COUNT(*) as count
FROM recurring_donations_backup 
WHERE is_recurring = true AND linked_to_recurring = false
UNION ALL
SELECT 
    'Linked Payments' as type,
    COUNT(*) as count
FROM recurring_donations_backup 
WHERE linked_to_recurring = true
UNION ALL
SELECT 
    'Total Records' as type,
    COUNT(*) as count
FROM recurring_donations_backup; 