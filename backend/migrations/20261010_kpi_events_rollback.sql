begin;
drop view if exists v_kpi_job_buoc;
drop table if exists kpi_rules;
drop trigger if exists kpi_costs on job_costs;          drop function if exists trg_kpi_costs();
drop trigger if exists kpi_documents on documents;      drop function if exists trg_kpi_documents();
drop trigger if exists kpi_services on job_services;    drop function if exists trg_kpi_services();
drop trigger if exists kpi_jobs on jobs;                drop function if exists trg_kpi_jobs();
drop function if exists kpi_log_event(integer, integer, text, text, text, text);
drop table if exists job_events;
alter table job_services drop column if exists pickup_at, drop column if exists delivered_at,
  drop column if exists cleared_at, drop column if exists service_done_at,
  drop column if exists nguoi_book, drop column if exists intl_truck_plate, drop column if exists vehicle_kind,
  drop column if exists agent_name, drop column if exists cont_type, drop column if exists freight_term,
  drop column if exists delivery_contact, drop column if exists cd_main_count, drop column if exists cd_branch_count;
alter table jobs drop column if exists confirmed_at, drop column if exists reconciled_at;
commit;

-- hoàn tác loại chứng từ (chỉ chạy khi chưa có chứng từ loại mới)
alter table documents drop constraint if exists documents_doc_type_check;
alter table documents add constraint documents_doc_type_check check (doc_type = any (array[
  'AN','DEBIT','DO','CD','CO','INVOICE','AWB','BL','PACKING_LIST','BBGH','OTHER']));
