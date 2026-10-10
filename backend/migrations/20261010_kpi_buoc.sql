-- KPI nhập job theo bước (file V1 chị Hà 08/10): ghi LẦN ĐẦU mỗi bước của mỗi dịch vụ được nhập ĐỦ ô + chứng từ.
create table if not exists job_step_done (
  id         bigserial primary key,
  job_id     integer not null references jobs(job_id) on delete cascade,
  svc_id     integer references job_services(svc_id) on delete cascade,
  svc_type   text not null,
  buoc       integer not null,
  ten_buoc   text,
  trang_thai text,
  kpi        text,
  done_at    timestamptz not null default now(),
  actor      text default 'unknown',
  unique (svc_id, buoc)
);
create index if not exists job_step_done_job on job_step_done(job_id);
-- rollback: drop table job_step_done;
