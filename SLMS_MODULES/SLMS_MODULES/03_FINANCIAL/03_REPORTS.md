# 📊 MODULE 3.3: REPORTS (Báo cáo)

## 📋 Mục lục
1. [Report Overview](#1-report-overview)
2. [Operational Reports](#2-operational-reports)
3. [Financial Reports](#3-financial-reports)
4. [Performance Reports](#4-performance-reports)

---

## 1. Report Overview

### 1.1 Report Categories

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         REPORT CATEGORIES                                        │
│                                                                                  │
│   📊 OPERATIONAL REPORTS                                                        │
│   ──────────────────────                                                        │
│   • Daily Job Summary                                                           │
│   • Weekly Operations Report                                                    │
│   • Job Status Report                                                           │
│   • Vehicle Utilization                                                         │
│                                                                                  │
│   💰 FINANCIAL REPORTS                                                          │
│   ─────────────────────                                                         │
│   • Revenue Report                                                              │
│   • Cost Analysis                                                               │
│   • Profit & Loss                                                               │
│   • Accounts Receivable Aging                                                   │
│   • Accounts Payable Summary                                                    │
│                                                                                  │
│   📈 PERFORMANCE REPORTS                                                        │
│   ──────────────────────                                                        │
│   • Customer Performance                                                        │
│   • Vendor Performance                                                          │
│   • Route Performance                                                           │
│   • KPI Dashboard                                                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Report Configuration

```sql
CREATE TABLE report_definitions (
    id              SERIAL PRIMARY KEY,
    report_code     VARCHAR(50) UNIQUE NOT NULL,
    report_name     VARCHAR(100) NOT NULL,
    category        VARCHAR(20) NOT NULL,           -- OPERATIONAL, FINANCIAL, PERFORMANCE
    
    -- Query
    base_query      TEXT,
    parameters      JSONB,                          -- Available parameters
    
    -- Output
    output_format   VARCHAR(20) DEFAULT 'TABLE',    -- TABLE, CHART, DASHBOARD
    columns         JSONB,                          -- Column definitions
    
    -- Schedule
    schedule_cron   VARCHAR(50),                    -- Cron expression
    recipients      TEXT[],                         -- Email recipients
    
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE report_runs (
    id              SERIAL PRIMARY KEY,
    report_id       INTEGER REFERENCES report_definitions(id),
    
    -- Parameters used
    parameters      JSONB,
    
    -- Results
    row_count       INTEGER,
    execution_time_ms INTEGER,
    output_file     VARCHAR(255),
    
    -- Status
    status          VARCHAR(20),                    -- RUNNING, COMPLETED, FAILED
    error_message   TEXT,
    
    -- Meta
    run_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_by          INTEGER REFERENCES users(id)
);
```

---

## 2. Operational Reports

### 2.1 Daily Job Summary

```sql
-- Daily Job Summary View
CREATE OR REPLACE VIEW v_daily_job_summary AS
SELECT 
    booking_date as report_date,
    
    -- Job counts
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE status = 'COMPLETED') as completed,
    COUNT(*) FILTER (WHERE status IN ('DISPATCHED', 'IN_TRANSIT')) as in_progress,
    COUNT(*) FILTER (WHERE status = 'PENDING') as pending,
    COUNT(*) FILTER (WHERE status = 'CANCELLED') as cancelled,
    
    -- Revenue
    SUM(revenue_amount) FILTER (WHERE status = 'COMPLETED') as total_revenue,
    SUM(cost_amount) FILTER (WHERE status = 'COMPLETED') as total_cost,
    SUM(revenue_amount - cost_amount) FILTER (WHERE status = 'COMPLETED') as total_profit,
    
    -- Breakdown by customer (top 5)
    jsonb_object_agg(
        customer_code, 
        job_count
    ) FILTER (WHERE customer_rank <= 5) as top_customers
    
FROM (
    SELECT 
        j.*,
        c.customer_code,
        COUNT(*) OVER (PARTITION BY booking_date, customer_id) as job_count,
        ROW_NUMBER() OVER (PARTITION BY booking_date ORDER BY COUNT(*) OVER (PARTITION BY booking_date, customer_id) DESC) as customer_rank
    FROM jobs j
    JOIN customers c ON j.customer_id = c.id
) sub
GROUP BY booking_date
ORDER BY booking_date DESC;
```

### 2.2 Daily Report Format

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      DAILY OPERATIONS REPORT                                     │
│                      Date: 15/01/2026                                            │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ JOB SUMMARY                                                             │   │
│   │                                                                          │   │
│   │   Total Jobs:     25                                                    │   │
│   │   ✅ Completed:   20                                                    │   │
│   │   🚚 In Progress:  3                                                    │   │
│   │   ⏳ Pending:      2                                                    │   │
│   │   ❌ Cancelled:    0                                                    │   │
│   │                                                                          │   │
│   │   Completion Rate: 80%                                                  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ FINANCIAL SUMMARY                                                       │   │
│   │                                                                          │   │
│   │   Revenue:        25,500,000 VND                                        │   │
│   │   Cost:           20,300,000 VND                                        │   │
│   │   Gross Profit:    5,200,000 VND                                        │   │
│   │   Margin:          25.6%                                                │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ TOP CUSTOMERS                                                           │   │
│   │                                                                          │   │
│   │   1. DREAMTECH:    8 jobs (32%)                                         │   │
│   │   2. HOSIDEN:      5 jobs (20%)                                         │   │
│   │   3. SAMSUNG:      4 jobs (16%)                                         │   │
│   │   4. KKF:          3 jobs (12%)                                         │   │
│   │   5. Others:       5 jobs (20%)                                         │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ TOP VENDORS                                                             │   │
│   │                                                                          │   │
│   │   1. Tam Bảo:     15 jobs (60%)                                         │   │
│   │   2. Việt Thắng:   6 jobs (24%)                                         │   │
│   │   3. Nam Bình:     4 jobs (16%)                                         │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Financial Reports

### 3.1 Monthly P&L Report

```sql
-- Monthly P&L View
CREATE OR REPLACE VIEW v_monthly_pnl AS
SELECT 
    DATE_TRUNC('month', booking_date) as month,
    
    -- Revenue
    SUM(revenue_amount) as gross_revenue,
    
    -- Cost breakdown
    SUM(cost_amount) as direct_cost,
    
    -- Margins
    SUM(revenue_amount) - SUM(cost_amount) as gross_profit,
    ROUND(((SUM(revenue_amount) - SUM(cost_amount)) / NULLIF(SUM(revenue_amount), 0)) * 100, 2) as gross_margin_pct,
    
    -- Counts
    COUNT(*) as total_jobs,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT vendor_id) as unique_vendors,
    
    -- Averages
    ROUND(AVG(revenue_amount), 0) as avg_revenue_per_job,
    ROUND(AVG(cost_amount), 0) as avg_cost_per_job,
    ROUND(AVG(revenue_amount - cost_amount), 0) as avg_profit_per_job

FROM jobs
WHERE status = 'COMPLETED'
GROUP BY DATE_TRUNC('month', booking_date)
ORDER BY month DESC;
```

### 3.2 Accounts Receivable Aging

```sql
-- AR Aging View
CREATE OR REPLACE VIEW v_ar_aging AS
SELECT 
    c.customer_code,
    c.customer_name,
    
    -- Current (0-30 days)
    SUM(s.total_amount) FILTER (
        WHERE s.payment_due_date >= CURRENT_DATE - INTERVAL '30 days'
          AND s.status NOT IN ('PAID')
    ) as current_0_30,
    
    -- 31-60 days
    SUM(s.total_amount) FILTER (
        WHERE s.payment_due_date < CURRENT_DATE - INTERVAL '30 days'
          AND s.payment_due_date >= CURRENT_DATE - INTERVAL '60 days'
          AND s.status NOT IN ('PAID')
    ) as days_31_60,
    
    -- 61-90 days
    SUM(s.total_amount) FILTER (
        WHERE s.payment_due_date < CURRENT_DATE - INTERVAL '60 days'
          AND s.payment_due_date >= CURRENT_DATE - INTERVAL '90 days'
          AND s.status NOT IN ('PAID')
    ) as days_61_90,
    
    -- Over 90 days
    SUM(s.total_amount) FILTER (
        WHERE s.payment_due_date < CURRENT_DATE - INTERVAL '90 days'
          AND s.status NOT IN ('PAID')
    ) as over_90,
    
    -- Total
    SUM(s.total_amount) FILTER (WHERE s.status NOT IN ('PAID')) as total_outstanding

FROM statements s
JOIN customers c ON s.customer_id = c.id
WHERE s.statement_type = 'CUSTOMER'
GROUP BY c.customer_code, c.customer_name
HAVING SUM(s.total_amount) FILTER (WHERE s.status NOT IN ('PAID')) > 0
ORDER BY total_outstanding DESC;
```

### 3.3 AR Aging Report Format

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ACCOUNTS RECEIVABLE AGING REPORT                              │
│                    As of: 16/01/2026                                             │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ Customer     │ Current   │ 31-60     │ 61-90     │ >90 Days  │ Total    │   │
│   ├──────────────┼───────────┼───────────┼───────────┼───────────┼──────────┤   │
│   │ DREAMTECH    │ 23.4M     │ 15.2M     │ 0         │ 0         │ 38.6M    │   │
│   │ HOSIDEN      │ 18.5M     │ 0         │ 0         │ 0         │ 18.5M    │   │
│   │ SAMSUNG      │ 45.0M     │ 32.0M     │ 0         │ 0         │ 77.0M    │   │
│   │ KKF          │ 8.2M      │ 5.5M      │ 2.1M      │ 0         │ 15.8M    │   │
│   ├──────────────┼───────────┼───────────┼───────────┼───────────┼──────────┤   │
│   │ TOTAL        │ 95.1M     │ 52.7M     │ 2.1M      │ 0         │ 149.9M   │   │
│   └──────────────┴───────────┴───────────┴───────────┴───────────┴──────────┘   │
│                                                                                  │
│   Summary:                                                                       │
│   • Current (0-30): 63.4% ✅                                                     │
│   • 31-60 days: 35.2% ⚠️                                                        │
│   • 61-90 days: 1.4% 🔴                                                         │
│   • Over 90: 0%                                                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Performance Reports

### 4.1 KPI Dashboard

```sql
-- KPI Summary View
CREATE OR REPLACE VIEW v_kpi_dashboard AS
WITH period_data AS (
    SELECT 
        DATE_TRUNC('month', booking_date) as period,
        COUNT(*) as total_jobs,
        COUNT(*) FILTER (WHERE status = 'COMPLETED') as completed_jobs,
        COUNT(*) FILTER (WHERE status = 'CANCELLED') as cancelled_jobs,
        SUM(revenue_amount) FILTER (WHERE status = 'COMPLETED') as revenue,
        SUM(cost_amount) FILTER (WHERE status = 'COMPLETED') as cost,
        AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) 
            FILTER (WHERE status = 'COMPLETED') as avg_completion_hours
    FROM jobs
    GROUP BY DATE_TRUNC('month', booking_date)
)
SELECT 
    period,
    total_jobs,
    completed_jobs,
    cancelled_jobs,
    
    -- KPIs
    ROUND((completed_jobs::DECIMAL / NULLIF(total_jobs, 0)) * 100, 1) as completion_rate,
    ROUND((cancelled_jobs::DECIMAL / NULLIF(total_jobs, 0)) * 100, 1) as cancellation_rate,
    revenue,
    cost,
    revenue - cost as profit,
    ROUND(((revenue - cost) / NULLIF(revenue, 0)) * 100, 1) as profit_margin,
    ROUND(avg_completion_hours, 1) as avg_completion_hours,
    ROUND(revenue / NULLIF(total_jobs, 0), 0) as revenue_per_job

FROM period_data
ORDER BY period DESC;
```

### 4.2 Vendor Performance

```sql
-- Vendor Performance View
CREATE OR REPLACE VIEW v_vendor_performance AS
SELECT 
    v.vendor_code,
    v.vendor_name,
    
    -- Volume
    COUNT(j.id) as total_jobs,
    SUM(j.cost_amount) as total_value,
    
    -- Quality
    AVG(sr.overall_rating) as avg_rating,
    
    -- Timeliness
    COUNT(*) FILTER (WHERE j.delivered_at <= j.delivery_date + j.delivery_time) as on_time_count,
    ROUND(
        COUNT(*) FILTER (WHERE j.delivered_at <= j.delivery_date + j.delivery_time)::DECIMAL 
        / NULLIF(COUNT(*), 0) * 100, 1
    ) as on_time_rate,
    
    -- Issues
    COUNT(*) FILTER (WHERE j.status = 'CANCELLED') as cancelled_count,
    COUNT(*) FILTER (WHERE EXISTS (
        SELECT 1 FROM statement_items si 
        WHERE si.job_id = j.id AND si.is_disputed = TRUE
    )) as disputed_count

FROM vendors v
LEFT JOIN jobs j ON v.id = j.vendor_id AND j.booking_date >= CURRENT_DATE - INTERVAL '90 days'
LEFT JOIN service_ratings sr ON j.id = sr.job_id
GROUP BY v.vendor_code, v.vendor_name
ORDER BY total_jobs DESC;
```

### 4.3 KPI Dashboard Format

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         KPI DASHBOARD                                            │
│                         January 2026                                             │
│                                                                                  │
│   ┌──────────────────────────────────────┬──────────────────────────────────┐   │
│   │ 📊 OPERATIONS                        │ 💰 FINANCIAL                     │   │
│   │                                      │                                   │   │
│   │ Total Jobs:        125               │ Revenue:       89.5M VND         │   │
│   │ Completed:         118 (94.4%)       │ Cost:          71.2M VND         │   │
│   │ In Progress:         5 (4.0%)        │ Gross Profit:  18.3M VND         │   │
│   │ Cancelled:           2 (1.6%)        │ Margin:        20.4%             │   │
│   │                                      │                                   │   │
│   │ Avg Jobs/Day:      4.2               │ Revenue/Job:   715K VND          │   │
│   │ On-Time Rate:      92.3%             │ Profit/Job:    146K VND          │   │
│   │                                      │                                   │   │
│   └──────────────────────────────────────┴──────────────────────────────────┘   │
│                                                                                  │
│   ┌──────────────────────────────────────┬──────────────────────────────────┐   │
│   │ 👥 TOP CUSTOMERS (by Revenue)        │ 🚚 TOP VENDORS (by Volume)       │   │
│   │                                      │                                   │   │
│   │ 1. DREAMTECH: 45.8M (51.2%)         │ 1. Tam Bảo: 78 jobs (62.4%)      │   │
│   │ 2. HOSIDEN: 28.5M (31.8%)           │ 2. Việt Thắng: 32 jobs (25.6%)   │   │
│   │ 3. DS-BN: 15.2M (17.0%)             │ 3. Nam Bình: 15 jobs (12.0%)     │   │
│   │                                      │                                   │   │
│   └──────────────────────────────────────┴──────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📈 TREND (Last 6 Months)                                                │   │
│   │                                                                          │   │
│   │   Month   │ Jobs  │ Revenue  │ Margin │ On-Time                        │   │
│   │   ────────┼───────┼──────────┼────────┼────────                        │   │
│   │   Aug 25  │  98   │ 72.3M    │ 19.2%  │ 89.5%                          │   │
│   │   Sep 25  │ 105   │ 78.5M    │ 20.1%  │ 90.2%                          │   │
│   │   Oct 25  │ 112   │ 82.1M    │ 19.8%  │ 91.5%                          │   │
│   │   Nov 25  │ 108   │ 79.8M    │ 20.5%  │ 91.0%                          │   │
│   │   Dec 25  │ 120   │ 88.2M    │ 21.2%  │ 92.1%                          │   │
│   │   Jan 26  │ 125   │ 89.5M    │ 20.4%  │ 92.3%                          │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 SUMMARY

### Report Categories
1. **Operational** - Daily/weekly job tracking
2. **Financial** - P&L, AR/AP, margins
3. **Performance** - KPIs, vendor scores

### Key Reports
- Daily Job Summary
- Monthly P&L
- Accounts Receivable Aging
- KPI Dashboard
- Vendor Performance

### Generation Methods
- Scheduled auto-generation
- Manual request via UI
- AI natural language request

### Output Formats
- Screen dashboard
- Excel export
- PDF export
- Email delivery
