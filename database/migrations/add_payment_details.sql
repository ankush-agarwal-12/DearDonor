-- Add payment_details column to donations table
ALTER TABLE donations
ADD COLUMN IF NOT EXISTS payment_details JSONB DEFAULT '{}'::jsonb;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_payment_details
ON donations USING GIN (payment_details);

-- Add comment for documentation
COMMENT ON COLUMN donations.payment_details IS 'Stores payment method specific details like cheque number, bank name, transaction ID, etc.'; 