-- KPI nhập job: MỌI mốc giờ = lúc nhân viên / Sen thao tác (Khánh chốt 10/10/2026). Không nhập tay giờ.
-- Sen nhập hộ: thời điểm = lúc nhân viên GỬI tin/file cho Sen (truyền qua header x-act-at hoặc app.act_at),
-- người = nhân viên gửi (x-actor / app.actor). Chỉ nhận x-act-at trong 72 giờ qua, không nhận giờ tương lai.
create or replace function kpi_log_event(p_job integer, p_svc integer, p_type text,
                                         p_field text, p_from text, p_to text)
returns void language plpgsql as $$
declare v_actor text; v_at text; v_ts timestamptz; h json;
begin
  begin h := nullif(current_setting('request.headers', true), '')::json; exception when others then h := null; end;
  v_actor := coalesce(nullif(current_setting('app.actor', true), ''), h->>'x-actor', 'unknown');
  v_at    := coalesce(nullif(current_setting('app.act_at', true), ''), h->>'x-act-at');
  v_ts := now();
  if v_at is not null then
    begin
      v_ts := v_at::timestamptz;
      if v_ts > now() or v_ts < now() - interval '72 hours' then v_ts := now(); end if;
    exception when others then v_ts := now();
    end;
  end if;
  insert into job_events(job_id, svc_id, event_type, field, from_value, to_value, actor, event_at)
  values (p_job, p_svc, p_type, p_field, p_from, p_to, v_actor, v_ts);
exception when others then
  raise warning 'kpi_log_event lỗi (bỏ qua): %', sqlerrm;
end $$;

-- dịch vụ: ghi lần đầu điền các ô đánh dấu tiến độ + đổi trạng thái dịch vụ + mọi lần sửa (SUA)
create or replace function trg_kpi_services() returns trigger language plpgsql as $$
declare c text; ov text; nv text; dsd jsonb;
begin
  foreach c in array array['cd_no','bl_awb_no','mbl_no','atd','driver_id','declaration_datetime','delivery_date'] loop
    execute format('select ($1).%1$I::text', c) into nv using new;
    if tg_op = 'INSERT' then ov := null; else execute format('select ($1).%1$I::text', c) into ov using old; end if;
    if nv is not null and ov is null then
      perform kpi_log_event(new.job_id, new.svc_id, 'MOC', c, null, nv);
    end if;
  end loop;
  if (new.service_details->>'vehicle_plate') is not null
     and (tg_op = 'INSERT' or (old.service_details->>'vehicle_plate') is null) then
    perform kpi_log_event(new.job_id, new.svc_id, 'MOC', 'vehicle_plate', null, new.service_details->>'vehicle_plate');
  end if;
  if tg_op = 'UPDATE' and new.status_code is distinct from old.status_code then
    perform kpi_log_event(new.job_id, new.svc_id, 'SVC_STATUS', 'status_code', old.status_code, new.status_code);
  end if;
  if tg_op = 'UPDATE' and (to_jsonb(new) - 'updated_at') is distinct from (to_jsonb(old) - 'updated_at') then
    perform kpi_log_event(new.job_id, new.svc_id, 'SUA', 'job_services', null, null);
  end if;
  return new;
end $$;
drop trigger if exists kpi_services on job_services;
create trigger kpi_services after insert or update on job_services for each row execute function trg_kpi_services();

-- giá: ghi mọi lần lưu giá (để biết lúc nhập đủ giá), không chỉ lần đầu
create or replace function trg_kpi_costs() returns trigger language plpgsql as $$
begin
  if coalesce(new.buying_amount,0) > 0 or coalesce(new.selling_amount,0) > 0
     or coalesce(new.buying_rate,0) > 0 or coalesce(new.selling_rate,0) > 0 then
    perform kpi_log_event(new.job_id, new.svc_id, 'COST', 'job_costs', null, new.cost_id::text);
  end if;
  return new;
end $$;
drop trigger if exists kpi_costs on job_costs;
create trigger kpi_costs after insert or update on job_costs for each row execute function trg_kpi_costs();

alter table job_step_done add column if not exists moc_t timestamptz, add column if not exists nguon_moc text;

alter table job_events drop constraint if exists job_events_event_type_check;
alter table job_events add constraint job_events_event_type_check
  check (event_type = any (array['STATUS','DOC','COST','MOC','SVC_STATUS','SUA']));

-- 12/10 (Khánh): kỳ thanh toán của khách — người tạo job phải nhập, thiếu = 1 lỗi KPI bước Đối chiếu
alter table job_services add column if not exists ky_thanh_toan text;
-- rollback: alter table job_services drop column if exists ky_thanh_toan;
