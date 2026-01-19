# 🔧 MODULE 1.1: SYSTEM INFRASTRUCTURE

## 📋 Mục lục
1. [Users & Authentication](#1-users--authentication)
2. [Roles & Permissions](#2-roles--permissions)
3. [Audit Logging](#3-audit-logging)
4. [Backup & Recovery](#4-backup--recovery)

---

## 1. Users & Authentication

### 1.1 User Table Schema

```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    user_code       VARCHAR(20) UNIQUE NOT NULL,    -- VD: USR001, OPS001
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(100) UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    phone           VARCHAR(20),
    
    -- Role & Status
    role_id         INTEGER REFERENCES roles(id),
    department      VARCHAR(50),                     -- CS, OPS, FINANCE, ADMIN
    is_active       BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login      TIMESTAMP,
    
    -- Profile
    avatar_url      VARCHAR(255),
    preferences     JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_active ON users(is_active);
```

### 1.2 User Departments

| Department | Code | Mô tả |
|------------|------|-------|
| Customer Service | CS | Nhận booking, tương tác khách hàng |
| Operations | OPS | Điều xe, theo dõi vận chuyển |
| Finance | FIN | Bảng kê, công nợ, báo cáo |
| Admin | ADM | Quản trị hệ thống |
| Driver | DRV | Lái xe (mobile app) |

### 1.3 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          AUTHENTICATION FLOW                                     │
│                                                                                  │
│   ┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌────────────────┐  │
│   │  Login   │───>│  Validate    │───>│  Generate     │───>│  Return Token  │  │
│   │  Request │    │  Credentials │    │  JWT Token    │    │  + User Info   │  │
│   └──────────┘    └──────────────┘    └───────────────┘    └────────────────┘  │
│                                                                                  │
│   Token Contents:                                                                │
│   {                                                                              │
│     "user_id": 1,                                                               │
│     "user_code": "OPS001",                                                      │
│     "role": "operations",                                                       │
│     "permissions": ["job.view", "job.edit", "vehicle.assign"],                 │
│     "exp": 1735689600                                                           │
│   }                                                                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Roles & Permissions

### 2.1 Roles Table Schema

```sql
CREATE TABLE roles (
    id              SERIAL PRIMARY KEY,
    role_code       VARCHAR(20) UNIQUE NOT NULL,    -- ADMIN, CS, OPS, FIN, DRV
    role_name       VARCHAR(50) NOT NULL,
    description     TEXT,
    permissions     JSONB NOT NULL DEFAULT '[]',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default roles
INSERT INTO roles (role_code, role_name, permissions) VALUES
('ADMIN', 'Administrator', '["*"]'),
('CS', 'Customer Service', '["customer.*", "job.create", "job.view"]'),
('OPS', 'Operations', '["job.*", "vehicle.*", "driver.*"]'),
('FIN', 'Finance', '["statement.*", "report.*", "job.view"]'),
('DRV', 'Driver', '["job.view_assigned", "job.update_status"]');
```

### 2.2 Permission Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PERMISSION MATRIX                                      │
│                                                                                  │
│   Module          │ Admin │  CS   │  OPS  │  FIN  │ Driver                      │
│   ────────────────┼───────┼───────┼───────┼───────┼────────                      │
│   Users           │ CRUD  │   -   │   -   │   -   │   -                          │
│   Customers       │ CRUD  │ CRUD  │  R    │  R    │   -                          │
│   Vendors         │ CRUD  │  R    │  RU   │  R    │   -                          │
│   Drivers         │ CRUD  │  R    │ CRUD  │  R    │   -                          │
│   Vehicles        │ CRUD  │  R    │ CRUD  │  R    │   -                          │
│   ────────────────┼───────┼───────┼───────┼───────┼────────                      │
│   Jobs - Create   │  ✓    │  ✓    │  ✓    │   -   │   -                          │
│   Jobs - View     │  ✓    │  ✓    │  ✓    │  ✓    │ Own only                     │
│   Jobs - Edit     │  ✓    │  ✓    │  ✓    │   -   │ Status                       │
│   Jobs - Delete   │  ✓    │   -   │   -   │   -   │   -                          │
│   Jobs - Assign   │  ✓    │   -   │  ✓    │   -   │   -                          │
│   ────────────────┼───────┼───────┼───────┼───────┼────────                      │
│   Rates - View    │  ✓    │  ✓    │  ✓    │  ✓    │   -                          │
│   Rates - Edit    │  ✓    │   -   │   -   │  ✓    │   -                          │
│   ────────────────┼───────┼───────┼───────┼───────┼────────                      │
│   Statements      │  ✓    │   -   │   -   │ CRUD  │   -                          │
│   Reports         │  ✓    │  R    │  R    │ CRUD  │   -                          │
│   ────────────────┼───────┼───────┼───────┼───────┼────────                      │
│   AI Logs         │  R    │   -   │   -   │   -   │   -                          │
│   System Config   │ CRUD  │   -   │   -   │   -   │   -                          │
│                                                                                  │
│   Legend: C=Create, R=Read, U=Update, D=Delete                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Permission Check Function

```sql
-- Function to check permission
CREATE OR REPLACE FUNCTION check_permission(
    p_user_id INTEGER,
    p_permission VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_permissions JSONB;
BEGIN
    SELECT r.permissions INTO v_permissions
    FROM users u
    JOIN roles r ON u.role_id = r.id
    WHERE u.id = p_user_id AND u.is_active = TRUE;
    
    -- Admin has all permissions
    IF v_permissions @> '["*"]' THEN
        RETURN TRUE;
    END IF;
    
    -- Check specific permission
    IF v_permissions @> to_jsonb(p_permission) THEN
        RETURN TRUE;
    END IF;
    
    -- Check wildcard (e.g., "job.*" matches "job.create")
    IF v_permissions @> to_jsonb(split_part(p_permission, '.', 1) || '.*') THEN
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;
```

---

## 3. Audit Logging

### 3.1 Audit Log Table

```sql
CREATE TABLE audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    
    -- Who
    user_id         INTEGER REFERENCES users(id),
    user_code       VARCHAR(20),
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    
    -- What
    action          VARCHAR(50) NOT NULL,           -- CREATE, UPDATE, DELETE, VIEW, LOGIN
    entity_type     VARCHAR(50) NOT NULL,           -- job, customer, statement, etc.
    entity_id       INTEGER,
    entity_code     VARCHAR(50),
    
    -- Details
    old_values      JSONB,                          -- Before state
    new_values      JSONB,                          -- After state
    changes         JSONB,                          -- Diff only
    
    -- Context
    request_id      UUID,                           -- For tracing
    session_id      VARCHAR(100),
    
    -- Timestamp
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
```

### 3.2 Audit Trigger Function

```sql
-- Generic audit trigger
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_user_id INTEGER;
    v_old_data JSONB;
    v_new_data JSONB;
    v_changes JSONB;
BEGIN
    -- Get current user from session
    v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER;
    
    IF TG_OP = 'INSERT' THEN
        v_new_data := to_jsonb(NEW);
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, new_values)
        VALUES (v_user_id, 'CREATE', TG_TABLE_NAME, NEW.id, v_new_data);
        RETURN NEW;
        
    ELSIF TG_OP = 'UPDATE' THEN
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
        v_changes := jsonb_diff(v_old_data, v_new_data);  -- Custom diff function
        
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_values, new_values, changes)
        VALUES (v_user_id, 'UPDATE', TG_TABLE_NAME, NEW.id, v_old_data, v_new_data, v_changes);
        RETURN NEW;
        
    ELSIF TG_OP = 'DELETE' THEN
        v_old_data := to_jsonb(OLD);
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_values)
        VALUES (v_user_id, 'DELETE', TG_TABLE_NAME, OLD.id, v_old_data);
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables
CREATE TRIGGER audit_jobs AFTER INSERT OR UPDATE OR DELETE ON jobs
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_customers AFTER INSERT OR UPDATE OR DELETE ON customers
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

### 3.3 Audit Log UI

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            AUDIT LOG VIEWER                                      │
│                                                                                  │
│  Filters: [User: All ▼] [Entity: jobs ▼] [Action: All ▼] [Date: Last 7 days ▼] │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │ Time          │ User    │ Action │ Entity        │ Changes                │  │
│  ├───────────────┼─────────┼────────┼───────────────┼────────────────────────┤  │
│  │ 15:30:25      │ OPS001  │ UPDATE │ job/TRK-001   │ status: PENDING → DISP │  │
│  │ 15:28:10      │ OPS001  │ UPDATE │ job/TRK-001   │ vehicle_id: null → 5   │  │
│  │ 15:25:00      │ CS001   │ CREATE │ job/TRK-001   │ New job created        │  │
│  │ 15:20:15      │ FIN001  │ UPDATE │ rate/RT-012   │ price: 850K → 900K     │  │
│  │ 15:15:30      │ ADMIN   │ CREATE │ user/USR005   │ New user: Nguyen Van A │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  [◀ Prev] Page 1 of 50 [Next ▶]                    Total: 1,234 records        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Backup & Recovery

### 4.1 Backup Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BACKUP STRATEGY                                        │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    BACKUP SCHEDULE                                      │   │
│   │                                                                          │   │
│   │   Type            Frequency       Retention       Storage               │   │
│   │   ──────────────  ──────────────  ──────────────  ────────────────     │   │
│   │   Full Backup     Weekly (Sun)    4 weeks         Google Cloud Storage  │   │
│   │   Incremental     Daily (2 AM)    14 days         Google Cloud Storage  │   │
│   │   Transaction     Real-time       7 days          WAL Archive           │   │
│   │   Point-in-time   Continuous      72 hours        WAL Archive           │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    BACKUP LOCATIONS                                     │   │
│   │                                                                          │   │
│   │   Primary:    gs://slms-backup/production/                              │   │
│   │   Secondary:  gs://slms-backup-dr/production/    (Different region)     │   │
│   │   Local:      /var/backups/slms/                 (7 days retention)     │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Backup Scripts

```bash
#!/bin/bash
# backup_daily.sh - Daily incremental backup

DATE=$(date +%Y%m%d)
BACKUP_DIR="/var/backups/slms"
GCS_BUCKET="gs://slms-backup/production"

# PostgreSQL backup
pg_dump -Fc slms_db > "${BACKUP_DIR}/slms_${DATE}.dump"

# Upload to GCS
gsutil cp "${BACKUP_DIR}/slms_${DATE}.dump" "${GCS_BUCKET}/daily/"

# Cleanup old local backups (keep 7 days)
find ${BACKUP_DIR} -name "*.dump" -mtime +7 -delete

# Log backup status
echo "$(date): Daily backup completed - slms_${DATE}.dump" >> /var/log/slms_backup.log
```

### 4.3 Recovery Procedures

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         RECOVERY PROCEDURES                                      │
│                                                                                  │
│   SCENARIO 1: Accidental Data Deletion                                          │
│   ─────────────────────────────────────                                         │
│   1. Identify deletion time from audit_logs                                     │
│   2. Use point-in-time recovery to time before deletion                         │
│   3. Export affected records                                                    │
│   4. Restore records to production                                              │
│                                                                                  │
│   SCENARIO 2: Database Corruption                                               │
│   ────────────────────────────────                                              │
│   1. Stop application servers                                                   │
│   2. Restore from latest full backup                                            │
│   3. Apply incremental backups                                                  │
│   4. Replay WAL logs to point-in-time                                           │
│   5. Verify data integrity                                                      │
│   6. Restart application servers                                                │
│                                                                                  │
│   SCENARIO 3: Complete System Failure                                           │
│   ──────────────────────────────────                                            │
│   1. Provision new database server                                              │
│   2. Restore from GCS backup (secondary region if needed)                       │
│   3. Update DNS/connection strings                                              │
│   4. Verify all integrations                                                    │
│   5. Resume operations                                                          │
│                                                                                  │
│   RTO (Recovery Time Objective): 4 hours                                        │
│   RPO (Recovery Point Objective): 1 hour                                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 SUMMARY

### Tables in this module
1. `users` - User accounts
2. `roles` - Role definitions with permissions
3. `audit_logs` - All system changes

### Key Features
- JWT-based authentication
- Role-based access control (RBAC)
- Comprehensive audit logging
- Automated backup with GCS

### Integration Points
- All other modules use `users` for authentication
- All modules write to `audit_logs`
- Backup covers all database tables
