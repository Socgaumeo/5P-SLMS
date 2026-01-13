
-- Update drivers table to match import_drivers_tambao.sql
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS driver_code VARCHAR(20) UNIQUE;
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS employee_id VARCHAR(20);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS id_card_date DATE;
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS id_card_place VARCHAR(200);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS date_of_birth DATE;
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS license_plate VARCHAR(20); -- Storing directly in driver as per import source
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS vehicle_type VARCHAR(50);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update vehicles table to match import expectations (if needed)
-- The import script creates vehicles locally if not exists but tries to insert using license_plate
-- We'll ensure the column exists or is aliased. 
-- Actually, the import script uses 'license_plate' in schema definition but checks 'vehicles' table.
-- Let's check if 'license_plate' column exists in 'vehicles', if not add it (or rely on plate_number if we edit the script).
-- Current init.sql has 'plate_number'. The import script has 'license_plate'.
-- To support the import script as-is, we might need 'license_plate' column or rename 'plate_number'
-- But renaming might break other things. Let's add 'license_plate' as a column to vehicles if it doesn't exist, 
-- or better, let's just run the import for drivers first as that was the main error.
-- The verification step in import script uses 'license_plate' for vehicles too.

ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS license_plate VARCHAR(20);
-- Note: we might have dual columns 'plate_number' and 'license_plate' now. 
-- Ideally we clean this up later, but priority is getting data in.
