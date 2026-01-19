# 💬 MODULE 2.3: COMMUNICATION

## 📋 Mục lục
1. [Communication Channels](#1-communication-channels)
2. [Message Templates](#2-message-templates)
3. [Notification System](#3-notification-system)
4. [Communication Logs](#4-communication-logs)

---

## 1. Communication Channels

### 1.1 Channel Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      COMMUNICATION CHANNELS                                      │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📱 ZALO (Primary - Manual Copy)                                         │   │
│   │                                                                          │   │
│   │  • Customer Groups: DRT1, DRT2, SEVT, HSDN...                          │   │
│   │  • Vendor Groups: Tam Bảo, Việt Thắng...                               │   │
│   │  • Method: Copy from system → Paste to Zalo                            │   │
│   │  • Use case: Real-time communication                                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📧 EMAIL (Automated)                                                    │   │
│   │                                                                          │   │
│   │  • Formal communications                                                │   │
│   │  • Statements, Invoices                                                 │   │
│   │  • Reports                                                              │   │
│   │  • Method: SMTP automation                                              │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 🔔 IN-APP NOTIFICATIONS                                                 │   │
│   │                                                                          │   │
│   │  • Internal team notifications                                          │   │
│   │  • Status updates                                                       │   │
│   │  • Alerts and reminders                                                 │   │
│   │  • Method: WebSocket / Push                                             │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Channel Configuration

```sql
CREATE TABLE communication_channels (
    id              SERIAL PRIMARY KEY,
    channel_code    VARCHAR(20) UNIQUE NOT NULL,    -- ZALO, EMAIL, SMS, APP
    channel_name    VARCHAR(50) NOT NULL,
    
    -- Configuration
    is_automated    BOOLEAN DEFAULT FALSE,
    config          JSONB,                          -- SMTP settings, API keys
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contact preferences per customer/vendor
CREATE TABLE contact_preferences (
    id              SERIAL PRIMARY KEY,
    entity_type     VARCHAR(20) NOT NULL,           -- CUSTOMER, VENDOR
    entity_id       INTEGER NOT NULL,
    
    -- Preferred channels
    preferred_channel VARCHAR(20),                  -- ZALO, EMAIL
    zalo_room_name  VARCHAR(100),
    email_address   VARCHAR(100),
    phone_number    VARCHAR(20),
    
    -- Notification settings
    notify_booking  BOOLEAN DEFAULT TRUE,
    notify_dispatch BOOLEAN DEFAULT TRUE,
    notify_delivery BOOLEAN DEFAULT TRUE,
    notify_statement BOOLEAN DEFAULT TRUE,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Message Templates

### 2.1 Template Categories

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       MESSAGE TEMPLATES                                          │
│                                                                                  │
│   VENDOR COMMUNICATION                                                          │
│   ────────────────────                                                          │
│                                                                                  │
│   📤 VENDOR_DISPATCH_REQUEST                                                    │
│   ───────────────────────────                                                   │
│   🚛 YÊU CẦU XE - {customer_code}                                              │
│                                                                                  │
│   📅 Ngày: {booking_date}                                                       │
│   ⏰ Giờ: {pickup_time}                                                         │
│   📦 Invoice: {invoice_numbers}                                                 │
│   📋 Hàng: {cargo_type} - {package_info}                                       │
│   🚗 Loại xe: {vehicle_type}                                                   │
│   📍 Lấy: {pickup_address}                                                     │
│   📍 Giao: {delivery_address}                                                  │
│                                                                                  │
│   Vui lòng điều xe và phản hồi thông tin lái xe.                               │
│                                                                                  │
│   ─────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│   CUSTOMER COMMUNICATION                                                        │
│   ──────────────────────                                                        │
│                                                                                  │
│   📤 CUSTOMER_VEHICLE_CONFIRM                                                   │
│   ────────────────────────────                                                  │
│   {route} / {date} / {time} / Invoice: {invoices} / {cargo} / {package}        │
│   / {vehicle_type} / BKS: {license_plate} / {driver_name}                      │
│   - {driver_phone} - CCCD: {driver_id_card}                                    │
│                                                                                  │
│   ─────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│   📤 CUSTOMER_DELIVERY_CONFIRM                                                  │
│   ─────────────────────────────                                                 │
│   ✅ Đã giao hàng thành công                                                    │
│                                                                                  │
│   Job: {job_number}                                                             │
│   Thời gian: {delivery_time}                                                    │
│   Người nhận: {receiver_name}                                                   │
│                                                                                  │
│   ─────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│   INTERNAL NOTIFICATIONS                                                        │
│   ──────────────────────                                                        │
│                                                                                  │
│   📤 INTERNAL_NEW_BOOKING                                                       │
│   ────────────────────────                                                      │
│   🆕 Booking mới: {job_number}                                                  │
│   Khách: {customer_name}                                                        │
│   Ngày: {booking_date} {pickup_time}                                           │
│   Cần xử lý trước: {deadline}                                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Template Table

```sql
CREATE TABLE message_templates (
    id              SERIAL PRIMARY KEY,
    template_code   VARCHAR(50) UNIQUE NOT NULL,
    template_name   VARCHAR(100) NOT NULL,
    
    -- Content
    category        VARCHAR(20) NOT NULL,           -- VENDOR, CUSTOMER, INTERNAL
    channel         VARCHAR(20),                    -- ZALO, EMAIL, APP (null = all)
    subject         VARCHAR(200),                   -- For email
    body            TEXT NOT NULL,
    
    -- Variables
    variables       TEXT[],                         -- ['customer_code', 'booking_date', ...]
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample templates
INSERT INTO message_templates (template_code, template_name, category, body, variables) VALUES
('VENDOR_DISPATCH', 'Yêu cầu điều xe', 'VENDOR', 
'🚛 YÊU CẦU XE - {customer_code}

📅 Ngày: {booking_date}
⏰ Giờ: {pickup_time}
📦 Invoice: {invoice_numbers}
📋 Hàng: {cargo_type} - {package_info}
🚗 Loại xe: {vehicle_type}
📍 Giao: {delivery_address}

Vui lòng điều xe và phản hồi thông tin lái xe.',
ARRAY['customer_code', 'booking_date', 'pickup_time', 'invoice_numbers', 'cargo_type', 'package_info', 'vehicle_type', 'delivery_address']),

('CUSTOMER_CONFIRM', 'Xác nhận xe cho khách', 'CUSTOMER',
'{route} / {date} / {time} / Invoice: {invoices} / {cargo} / {package} / {vehicle_type} / BKS: {license_plate} / {driver_name} - {driver_phone} - CCCD: {driver_id_card}',
ARRAY['route', 'date', 'time', 'invoices', 'cargo', 'package', 'vehicle_type', 'license_plate', 'driver_name', 'driver_phone', 'driver_id_card']);
```

---

## 3. Notification System

### 3.1 Notification Types

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      NOTIFICATION TYPES                                          │
│                                                                                  │
│   Type                 │ Trigger                    │ Recipients                │
│   ─────────────────────┼────────────────────────────┼─────────────────────────  │
│   NEW_BOOKING          │ Job created                │ OPS team                  │
│   BOOKING_CONFIRMED    │ Job confirmed              │ Customer                  │
│   VEHICLE_ASSIGNED     │ Vehicle/driver assigned    │ Customer, Driver          │
│   JOB_DISPATCHED       │ Vehicle departed           │ Customer                  │
│   JOB_DELIVERED        │ Delivery completed         │ Customer, OPS             │
│   JOB_ISSUE            │ Problem reported           │ OPS, Manager              │
│   STATEMENT_READY      │ Statement generated        │ Customer/Vendor, Finance  │
│   PAYMENT_RECEIVED     │ Payment recorded           │ Finance                   │
│   RATE_EXPIRING        │ Rate near expiry           │ Finance                   │
│   DAILY_SUMMARY        │ End of day                 │ Management                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Notification Table

```sql
CREATE TABLE notifications (
    id              SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL,
    
    -- Target
    recipient_type  VARCHAR(20) NOT NULL,           -- USER, CUSTOMER, VENDOR
    recipient_id    INTEGER,
    
    -- Content
    title           VARCHAR(200) NOT NULL,
    body            TEXT,
    data            JSONB,                          -- Additional data (job_id, etc.)
    
    -- Delivery
    channel         VARCHAR(20),                    -- APP, EMAIL, SMS
    status          VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, SENT, FAILED, READ
    sent_at         TIMESTAMP,
    read_at         TIMESTAMP,
    
    -- Reference
    reference_type  VARCHAR(50),                    -- JOB, STATEMENT, etc.
    reference_id    INTEGER,
    
    -- Meta
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP
);

-- Indexes
CREATE INDEX idx_notification_recipient ON notifications(recipient_type, recipient_id);
CREATE INDEX idx_notification_status ON notifications(status);
CREATE INDEX idx_notification_type ON notifications(notification_type);
```

### 3.3 Notification Trigger

```sql
-- Auto-create notification on job status change
CREATE OR REPLACE FUNCTION notify_job_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Notify on vehicle assignment
    IF NEW.status = 'DISPATCHED' AND OLD.status != 'DISPATCHED' THEN
        INSERT INTO notifications (notification_type, recipient_type, recipient_id, title, body, reference_type, reference_id)
        VALUES (
            'VEHICLE_ASSIGNED',
            'CUSTOMER',
            NEW.customer_id,
            'Xe đã được điều',
            format('Job %s: BKS %s, Lái xe: %s', NEW.job_number, NEW.license_plate, NEW.driver_name),
            'JOB',
            NEW.id
        );
    END IF;
    
    -- Notify on delivery
    IF NEW.status = 'DELIVERED' AND OLD.status != 'DELIVERED' THEN
        INSERT INTO notifications (notification_type, recipient_type, recipient_id, title, body, reference_type, reference_id)
        VALUES (
            'JOB_DELIVERED',
            'CUSTOMER',
            NEW.customer_id,
            'Giao hàng thành công',
            format('Job %s đã giao thành công lúc %s', NEW.job_number, NEW.delivered_at),
            'JOB',
            NEW.id
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_notify_job_status
AFTER UPDATE ON jobs
FOR EACH ROW EXECUTE FUNCTION notify_job_status_change();
```

---

## 4. Communication Logs

### 4.1 Log Table

```sql
CREATE TABLE communication_logs (
    id              SERIAL PRIMARY KEY,
    
    -- Direction
    direction       VARCHAR(10) NOT NULL,           -- INBOUND, OUTBOUND
    
    -- Channel
    channel         VARCHAR(20) NOT NULL,           -- ZALO, EMAIL, SMS, APP
    channel_id      VARCHAR(100),                   -- Room name, email address
    
    -- Parties
    sender_type     VARCHAR(20),                    -- USER, CUSTOMER, VENDOR, SYSTEM
    sender_id       INTEGER,
    sender_name     VARCHAR(100),
    recipient_type  VARCHAR(20),
    recipient_id    INTEGER,
    recipient_name  VARCHAR(100),
    
    -- Content
    message_type    VARCHAR(20),                    -- TEXT, FILE, IMAGE
    subject         VARCHAR(200),
    content         TEXT,
    attachments     TEXT[],
    
    -- Template (if used)
    template_id     INTEGER REFERENCES message_templates(id),
    template_data   JSONB,
    
    -- Reference
    reference_type  VARCHAR(50),                    -- JOB, STATEMENT
    reference_id    INTEGER,
    
    -- Status
    status          VARCHAR(20) DEFAULT 'SENT',     -- SENT, DELIVERED, READ, FAILED
    error_message   TEXT,
    
    -- Timestamps
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at         TIMESTAMP,
    delivered_at    TIMESTAMP,
    read_at         TIMESTAMP
);

-- Indexes
CREATE INDEX idx_comm_log_channel ON communication_logs(channel);
CREATE INDEX idx_comm_log_reference ON communication_logs(reference_type, reference_id);
CREATE INDEX idx_comm_log_created ON communication_logs(created_at);
```

### 4.2 Communication Timeline UI

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    JOB COMMUNICATION TIMELINE                                    │
│                                                                                  │
│   Job: TRK-2601-0001                                                            │
│   Customer: DREAMTECH VIETNAM                                                    │
│   Vendor: Tam Bảo                                                               │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         TIMELINE                                        │   │
│   │                                                                          │   │
│   │  21:30 ─── 📥 INBOUND ─── Customer ────────────────────────────────────│   │
│   │            │ Channel: Zalo                                              │   │
│   │            │ From: Hà Thanh Dung (DREAMTECH)                           │   │
│   │            │ Content: [File: Phiếu book xe.xlsx]                       │   │
│   │            └────────────────────────────────────────────────────────────│   │
│   │                                                                          │   │
│   │  21:35 ─── 📤 OUTBOUND ─── Vendor ─────────────────────────────────────│   │
│   │            │ Channel: Zalo (Copy)                                       │   │
│   │            │ To: Tam Bảo                                               │   │
│   │            │ Template: VENDOR_DISPATCH_REQUEST                         │   │
│   │            │ Content: "🚛 YÊU CẦU XE - DRT1..."                        │   │
│   │            │ Status: ✓ Sent                                            │   │
│   │            └────────────────────────────────────────────────────────────│   │
│   │                                                                          │   │
│   │  21:45 ─── 📥 INBOUND ─── Vendor ──────────────────────────────────────│   │
│   │            │ Channel: Zalo                                              │   │
│   │            │ From: Tam Bảo                                             │   │
│   │            │ Content: "BKS 29H 76514 - Nguyễn Việt Đức - SĐT..."      │   │
│   │            └────────────────────────────────────────────────────────────│   │
│   │                                                                          │   │
│   │  21:50 ─── 📤 OUTBOUND ─── Customer ───────────────────────────────────│   │
│   │            │ Channel: Zalo (Copy)                                       │   │
│   │            │ To: Hà Thanh Dung (DREAMTECH)                             │   │
│   │            │ Template: CUSTOMER_VEHICLE_CONFIRM                        │   │
│   │            │ Content: "MK-DRT1 / 15.01 / 22:00 / ... / BKS: 29H..."   │   │
│   │            │ Status: ✓ Sent                                            │   │
│   │            └────────────────────────────────────────────────────────────│   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 SUMMARY

### Communication Channels
1. **Zalo** - Primary, manual copy/paste
2. **Email** - Automated for formal docs
3. **In-App** - Internal notifications

### Key Features
- Message templates with variables
- Multi-channel communication
- Real-time notifications
- Complete communication history per job

### Tables
1. `message_templates` - Reusable templates
2. `notifications` - User notifications
3. `communication_logs` - All communications

### Integration Points
- **Module 2.1**: Job status triggers notifications
- **Module 3**: Statement notifications
- **Module 4**: AI generates messages from templates
