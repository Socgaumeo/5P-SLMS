-- Test trên DB bản sao. Tất cả trong 1 transaction rồi ROLLBACK, không để lại dữ liệu.
begin;
select set_config('app.actor', 'test', true);
with j as (insert into jobs(job_no, customer_id, description, status_code, created_by)
           select 'TEST-KPI-0001', customer_id, 'test kpi', 'PENDING', created_by from jobs limit 1 returning job_id)
select job_id as test_job from j \gset
insert into job_services(job_id, service_type_code, status_code) values (:test_job, 'TRUCKING', 'PENDING') returning svc_id \gset
update jobs set confirmed_at = now() - interval '5 hours' where job_id = :test_job;
update jobs set status_code = 'IN_PROGRESS' where job_id = :test_job;
update job_services set pickup_at = now() - interval '3 hours', delivered_at = now() - interval '2 hours' where svc_id = :svc_id;
insert into documents(job_id, doc_type, file_name) values (:test_job, 'BBGH', 'test.jpg');
update jobs set status_code = 'DELIVERED' where job_id = :test_job;
insert into job_costs(job_id, svc_id, cost_name, buying_rate, selling_rate) values (:test_job, :svc_id, 'test', 100, 120);
insert into job_costs(job_id, svc_id, cost_name, buying_rate, selling_rate) values (:test_job, :svc_id, 'test2', 50, 60);
\echo '--- job_events (mong đợi: STATUS x3, MOC confirmed_at/pickup_at/delivered_at, DOC BBGH, COST 1 lần)'
select event_type, field, from_value, to_value, actor from job_events where job_id = :test_job order by event_id;
\echo '--- KPI'
select buoc, mau, ket_qua, han_phut, phut_thuc_te from v_kpi_job_buoc where job_id = :test_job order by buoc;
\echo '--- lỗi trong trigger không chặn ghi job (đổi tên bảng sự kiện tạm thời)'
alter table job_events rename to job_events_tam;
update jobs set status_code = 'COMPLETED' where job_id = :test_job;
select status_code as van_ghi_duoc from jobs where job_id = :test_job;
alter table job_events_tam rename to job_events;
rollback;
