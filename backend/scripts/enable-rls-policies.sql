-- =============================================================================
-- ENABLE RLS (Row Level Security) for 5P-SLMS
-- Run this in Supabase SQL Editor
-- =============================================================================

-- Enable RLS on all critical tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE drivers ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_services ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_costs ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- POLICIES: Allow service_role full access (backend uses this)
-- =============================================================================

-- Users table
CREATE POLICY "service_role_all_users" ON users
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Customers table
CREATE POLICY "service_role_all_customers" ON customers
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Vendors table
CREATE POLICY "service_role_all_vendors" ON vendors
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Drivers table
CREATE POLICY "service_role_all_drivers" ON drivers
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Vehicles table
CREATE POLICY "service_role_all_vehicles" ON vehicles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Jobs table
CREATE POLICY "service_role_all_jobs" ON jobs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Job Services table
CREATE POLICY "service_role_all_job_services" ON job_services
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Job Costs table
CREATE POLICY "service_role_all_job_costs" ON job_costs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Vendor Rates table
CREATE POLICY "service_role_all_vendor_rates" ON vendor_rates
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Customer Rates table
CREATE POLICY "service_role_all_customer_rates" ON customer_rates
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Activity Logs table
CREATE POLICY "service_role_all_activity_logs" ON activity_logs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- =============================================================================
-- POLICIES: Block anon role from sensitive tables
-- =============================================================================

-- Master data tables can be read by anon (for dropdowns)
ALTER TABLE master_statuses ENABLE ROW LEVEL SECURITY;
ALTER TABLE master_service_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE master_vehicle_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE master_routes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_read_master_statuses" ON master_statuses
    FOR SELECT TO anon USING (true);

CREATE POLICY "anon_read_master_service_types" ON master_service_types
    FOR SELECT TO anon USING (true);

CREATE POLICY "anon_read_master_vehicle_types" ON master_vehicle_types
    FOR SELECT TO anon USING (true);

CREATE POLICY "anon_read_master_routes" ON master_routes
    FOR SELECT TO anon USING (true);

-- Service role full access to master tables
CREATE POLICY "service_role_all_master_statuses" ON master_statuses
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_master_service_types" ON master_service_types
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_master_vehicle_types" ON master_vehicle_types
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_master_routes" ON master_routes
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- =============================================================================
-- VERIFICATION: Check RLS is enabled
-- =============================================================================
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public';
