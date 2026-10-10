-- KPI nhập job (phương án 10/10/2026). Chạy 1 lần, trong transaction.
-- Mặc định tạm (chờ chị Hà chốt): mốc confirm = mail booking, không có thì lúc tạo job;
-- tính 24/7; KPI gán người tạo job; "Ok" = COMPLETED + có HĐ VAT + reconciled_at.
begin;

-- ===== GĐ1: lịch sử sự kiện + mốc thời gian thực tế =====
create table if not exists job_events (
  event_id   bigserial primary key,
  job_id     integer not null references jobs(job_id) on delete cascade,
  svc_id     integer references job_services(svc_id) on delete cascade,
  event_type text not null check (event_type in ('STATUS','DOC','COST','MOC')),
  field      text,
  from_value text,
  to_value   text,
  event_at   timestamptz not null default now(),
  actor      text not null default coalesce(nullif(current_setting('app.actor', true), ''), 'unknown')
);
create index if not exists job_events_job_idx  on job_events (job_id, event_at);
create index if not exists job_events_type_idx on job_events (event_type, event_at);

alter table jobs         add column if not exists confirmed_at    timestamptz,
                         add column if not exists reconciled_at   timestamptz;
alter table job_services add column if not exists pickup_at       timestamptz,
                         add column if not exists delivered_at    timestamptz,
                         add column if not exists cleared_at      timestamptz,
                         add column if not exists service_done_at timestamptz;

-- Trigger chỉ ghi bảng phụ; lỗi trong trigger KHÔNG được chặn việc ghi job.
create or replace function kpi_log_event(p_job integer, p_svc integer, p_type text,
                                         p_field text, p_from text, p_to text)
returns void language plpgsql as $$
begin
  insert into job_events(job_id, svc_id, event_type, field, from_value, to_value)
  values (p_job, p_svc, p_type, p_field, p_from, p_to);
exception when others then
  raise warning 'kpi_log_event lỗi (bỏ qua): %', sqlerrm;
end $$;

create or replace function trg_kpi_jobs() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then
    perform kpi_log_event(new.job_id, null, 'STATUS', 'status_code', null, new.status_code);
  else
    if new.status_code is distinct from old.status_code then
      perform kpi_log_event(new.job_id, null, 'STATUS', 'status_code', old.status_code, new.status_code);
    end if;
    if new.confirmed_at is distinct from old.confirmed_at and new.confirmed_at is not null then
      perform kpi_log_event(new.job_id, null, 'MOC', 'confirmed_at', null, new.confirmed_at::text);
    end if;
    if new.reconciled_at is distinct from old.reconciled_at and new.reconciled_at is not null then
      perform kpi_log_event(new.job_id, null, 'MOC', 'reconciled_at', null, new.reconciled_at::text);
    end if;
  end if;
  return new;
end $$;
drop trigger if exists kpi_jobs on jobs;
create trigger kpi_jobs after insert or update on jobs for each row execute function trg_kpi_jobs();

create or replace function trg_kpi_services() returns trigger language plpgsql as $$
declare c text; ov text; nv text;
begin
  foreach c in array array['pickup_at','delivered_at','cleared_at','service_done_at'] loop
    execute format('select ($1).%1$I::text, ($2).%1$I::text', c) into nv, ov using new, old;
    if tg_op = 'INSERT' then ov := null; end if;
    if nv is not null and nv is distinct from ov then
      perform kpi_log_event(new.job_id, new.svc_id, 'MOC', c, ov, nv);
    end if;
  end loop;
  return new;
end $$;
drop trigger if exists kpi_services on job_services;
create trigger kpi_services after insert or update on job_services for each row execute function trg_kpi_services();

create or replace function trg_kpi_documents() returns trigger language plpgsql as $$
begin
  if new.job_id is not null then
    perform kpi_log_event(new.job_id, null, 'DOC', 'doc_type', null, new.doc_type);
  end if;
  return new;
end $$;
drop trigger if exists kpi_documents on documents;
create trigger kpi_documents after insert on documents for each row execute function trg_kpi_documents();

create or replace function trg_kpi_costs() returns trigger language plpgsql as $$
declare had boolean;
begin
  if coalesce(new.buying_rate,0) > 0 or coalesce(new.selling_rate,0) > 0
     or coalesce(new.buying_amount,0) > 0 or coalesce(new.selling_amount,0) > 0 then
    select exists(select 1 from job_events where job_id = new.job_id and event_type = 'COST') into had;
    if not had then
      perform kpi_log_event(new.job_id, new.svc_id, 'COST', 'gia_dau_tien', null, new.cost_id::text);
    end if;
  end if;
  return new;
end $$;
drop trigger if exists kpi_costs on job_costs;
create trigger kpi_costs after insert or update on job_costs for each row execute function trg_kpi_costs();

-- ===== GĐ2: ô theo file V1 (đang nằm trong service_details) =====
alter table job_services add column if not exists nguoi_book       text,
                         add column if not exists intl_truck_plate text,
                         add column if not exists vehicle_kind     text,
                         add column if not exists agent_name       text,
                         add column if not exists cont_type        text,
                         add column if not exists freight_term     text check (freight_term in ('COLLECT','PREPAID')),
                         add column if not exists delivery_contact text,
                         add column if not exists cd_main_count    integer,
                         add column if not exists cd_branch_count  integer;
-- Chép dữ liệu cũ (chỉ khoá rõ nghĩa; vehicle_type cũ là trọng tải xe nên KHÔNG chép sang vehicle_kind).
update job_services set
  nguoi_book       = coalesce(nguoi_book,       nullif(service_details->>'nguoi_book',''), nullif(service_details->>'nguoi_booking','')),
  intl_truck_plate = coalesce(intl_truck_plate, nullif(service_details->>'china_truck_plate','')),
  agent_name       = coalesce(agent_name,       nullif(service_details->>'agent','')),
  cont_type        = coalesce(cont_type,        nullif(service_details->>'cont_type',''))
where service_details ?| array['nguoi_book','nguoi_booking','china_truck_plate','agent','cont_type'];
-- doc_type là text tự do (không CHECK): loại mới BOOKING, WEIGHT_SLIP, PHOTO_PICKUP, PHOTO_DELIVERY,
-- SERVICE_CONFIRM, QUOTATION chỉ cần thêm vào danh sách hợp lệ ở backend + script Sen.

-- ===== GĐ3: luật KPI + view =====
create table if not exists kpi_rules (
  mau          text not null,   -- trucking | cbt | sea_air | handling | cd
  buoc         text not null,   -- START | DELIVERED | FINISH
  han_phut     integer not null,
  mo_ta        text,
  primary key (mau, buoc)
);
insert into kpi_rules values
  ('trucking','START',240,'Tạo job ≤ T+4h từ khi khách confirm'),
  ('cbt','START',240,'Tạo job ≤ T+4h'),
  ('sea_air','START',240,'Tạo job ≤ T+4h'),
  ('handling','START',240,'Tạo job ≤ T+4h'),
  ('cd','START',240,'Tạo job ≤ T+4h'),
  ('trucking','DELIVERED',240,'Có BBGH ≤ T+4h sau giao'),
  ('cbt','DELIVERED',240,'Có BBGH ≤ T+4h sau giao'),
  ('sea_air','DELIVERED',240,'Có BBGH ≤ T+4h sau giao'),
  ('trucking','FINISH',1440,'Có giá mua/bán ≤ D+1 sau giao'),
  ('cbt','FINISH',1440,'Có giá ≤ D+1'),
  ('sea_air','FINISH',7200,'Có giá ≤ T+5 ngày'),
  ('handling','FINISH',2880,'Có giá ≤ T+2 ngày sau xong dịch vụ'),
  ('cd','FINISH',2880,'Có giá ≤ T+2 ngày sau thông quan')
on conflict (mau, buoc) do update set han_phut = excluded.han_phut, mo_ta = excluded.mo_ta;

create or replace view v_kpi_job_buoc as
with mau as (
  select j.job_id, j.job_no, j.created_by, j.status_code,
         (j.created_at at time zone 'UTC') as tao_luc, j.confirmed_at,
         case
           when bool_or(s.service_type_code like 'BORDER\_%') then 'cbt'
           when bool_or(s.service_type_code like 'SEA\_%' or s.service_type_code like 'AIR\_%') then 'sea_air'
           when bool_or(s.service_type_code like 'WHS\_%') then 'handling'
           when bool_or(s.service_type_code = 'TRUCKING') then 'trucking'
           when bool_or(s.service_type_code like 'CUS\_%') then 'cd'
         end as mau,
         max(s.delivered_at) as delivered_at,
         max(coalesce(s.service_done_at, s.cleared_at)) as xong_dv_at
  from jobs j left join job_services s on s.job_id = j.job_id
  group by j.job_id
), ev as (
  select job_id,
         min(event_at) filter (where event_type = 'DOC' and to_value = 'BBGH') as bbgh_at,
         min(event_at) filter (where event_type = 'COST') as gia_at
  from job_events group by job_id
), buoc as (
  select m.job_id, m.job_no, m.created_by, m.mau, 'START' as buoc,
         m.confirmed_at as moc_t, m.tao_luc as xong_luc from mau m
  union all
  select m.job_id, m.job_no, m.created_by, m.mau, 'DELIVERED', m.delivered_at, e.bbgh_at
  from mau m left join ev e using (job_id)
  union all
  select m.job_id, m.job_no, m.created_by, m.mau, 'FINISH',
         case when m.mau in ('handling','cd') then m.xong_dv_at else m.delivered_at end, e.gia_at
  from mau m left join ev e using (job_id)
)
select b.*, r.han_phut,
       b.moc_t + make_interval(mins => r.han_phut) as han_luc,
       case
         when b.moc_t is null then 'CHUA_CO_MOC'
         when b.xong_luc is null and now() > b.moc_t + make_interval(mins => r.han_phut) then 'TRE_CHUA_LAM'
         when b.xong_luc is null then 'DANG_TRONG_HAN'
         when b.xong_luc <= b.moc_t + make_interval(mins => r.han_phut) then 'DAT'
         else 'TRE'
       end as ket_qua,
       round(extract(epoch from (coalesce(b.xong_luc, now()) - b.moc_t)) / 60) as phut_thuc_te
from buoc b join kpi_rules r on r.mau = b.mau and r.buoc = b.buoc;

commit;
