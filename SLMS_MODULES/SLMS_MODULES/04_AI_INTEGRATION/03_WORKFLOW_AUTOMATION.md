# ⚙️ MODULE 4.3: WORKFLOW AUTOMATION

## 📋 Mục lục
1. [Automation Overview](#1-automation-overview)
2. [n8n Integration](#2-n8n-integration)
3. [Zalo Bot Automation](#3-zalo-bot-automation)
4. [Scheduled Tasks](#4-scheduled-tasks)

---

## 1. Automation Overview

### 1.1 Automation Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      AUTOMATION ARCHITECTURE                                     │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         TRIGGERS                                        │   │
│   │                                                                          │   │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
│   │  │   Zalo     │  │   Email    │  │  Webhook   │  │  Schedule  │        │   │
│   │  │  Message   │  │  Received  │  │   Event    │  │   (Cron)   │        │   │
│   │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        │   │
│   │        │               │               │               │                │   │
│   └────────┼───────────────┼───────────────┼───────────────┼────────────────┘   │
│            │               │               │               │                    │
│            └───────────────┴───────────────┴───────────────┘                    │
│                                    │                                            │
│                                    ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                      n8n WORKFLOW ENGINE                                │   │
│   │                                                                          │   │
│   │  ┌──────────────────────────────────────────────────────────────────┐   │   │
│   │  │                    WORKFLOW: Process Booking                     │   │   │
│   │  │                                                                   │   │   │
│   │  │  [Zalo] → [AI Parse] → [Create Job] → [Notify Vendor] → [Log]   │   │   │
│   │  │                                                                   │   │   │
│   │  └──────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │  ┌──────────────────────────────────────────────────────────────────┐   │   │
│   │  │                    WORKFLOW: Assign Vehicle                      │   │   │
│   │  │                                                                   │   │   │
│   │  │  [Zalo] → [AI Extract] → [Update Job] → [Notify Customer]       │   │   │
│   │  │                                                                   │   │   │
│   │  └──────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │  ┌──────────────────────────────────────────────────────────────────┐   │   │
│   │  │                    WORKFLOW: Daily Report                        │   │   │
│   │  │                                                                   │   │   │
│   │  │  [Schedule] → [Query DB] → [Generate Report] → [Send Email]     │   │   │
│   │  │                                                                   │   │   │
│   │  └──────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                          ACTIONS                                        │   │
│   │                                                                          │   │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
│   │  │  Database  │  │    AI      │  │   Email    │  │   Zalo     │        │   │
│   │  │   CRUD     │  │  Service   │  │   Send     │  │  Message   │        │   │
│   │  └────────────┘  └────────────┘  └────────────┘  └────────────┘        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Workflows

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          KEY WORKFLOWS                                           │
│                                                                                  │
│   #  │ Workflow              │ Trigger          │ Action                        │
│   ───┼───────────────────────┼──────────────────┼──────────────────────────────│
│   1  │ Process Booking       │ Zalo file/text   │ Parse → Create Job → Notify  │
│   2  │ Assign Vehicle        │ Zalo vendor msg  │ Extract → Update → Confirm   │
│   3  │ Complete Job          │ Zalo/Manual      │ Update status → Calculate    │
│   4  │ Generate Statement    │ Manual/Schedule  │ Query → Generate → Send      │
│   5  │ Daily Report          │ Schedule 18:00   │ Query → Format → Email       │
│   6  │ Rate Expiry Alert     │ Schedule 08:00   │ Check → Alert finance team   │
│   7  │ AR Aging Alert        │ Schedule weekly  │ Check → Alert if overdue     │
│   8  │ MISA Sync             │ Statement confirm│ Map → API call → Update      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. n8n Integration

### 2.1 n8n Setup

```yaml
# docker-compose.yml for n8n
version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=slms2026
      - N8N_HOST=n8n.yourdomain.com
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.yourdomain.com/
      - GENERIC_TIMEZONE=Asia/Ho_Chi_Minh
    volumes:
      - n8n_data:/home/node/.n8n
    restart: unless-stopped

volumes:
  n8n_data:
```

### 2.2 Workflow: Process Booking

```json
{
  "name": "SLMS - Process Booking",
  "nodes": [
    {
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "slms/booking",
        "httpMethod": "POST"
      }
    },
    {
      "name": "AI Parse",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://slms-api:8000/api/ai/process",
        "method": "POST",
        "body": {
          "source": "={{$json.source}}",
          "content_type": "={{$json.content_type}}",
          "content": "={{$json.content}}"
        }
      }
    },
    {
      "name": "Check Intent",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json.intent}}",
              "value2": "create_job"
            }
          ]
        }
      }
    },
    {
      "name": "Create Job",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://slms-api:8000/api/jobs",
        "method": "POST",
        "body": "={{$json.entities}}"
      }
    },
    {
      "name": "Generate Vendor Message",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://slms-api:8000/api/messages/generate",
        "method": "POST",
        "body": {
          "template": "VENDOR_DISPATCH",
          "data": "={{$json}}"
        }
      }
    },
    {
      "name": "Log to Database",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "workflow_logs",
        "columns": "workflow_name, trigger_data, result, created_at"
      }
    }
  ]
}
```

### 2.3 Workflow: Assign Vehicle

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW: ASSIGN VEHICLE                                      │
│                                                                                  │
│   ┌─────────────┐                                                               │
│   │   Webhook   │  POST /slms/vehicle-assign                                    │
│   │   Trigger   │  Body: { source: "zalo", room: "Tam Bảo", content: "..." }   │
│   └──────┬──────┘                                                               │
│          │                                                                       │
│          ▼                                                                       │
│   ┌─────────────┐                                                               │
│   │  AI Extract │  Extract: license_plate, driver_name, phone, cccd            │
│   │   Vehicle   │  Match to pending job by context (quote/invoice/date)        │
│   └──────┬──────┘                                                               │
│          │                                                                       │
│          ▼                                                                       │
│   ┌─────────────┐                                                               │
│   │ Find Job    │  Query jobs where:                                            │
│   │             │  - status = 'PENDING' or 'CONFIRMED'                          │
│   │             │  - matches invoice_numbers or booking_date                    │
│   └──────┬──────┘                                                               │
│          │                                                                       │
│          ▼                                                                       │
│   ┌─────────────┐                                                               │
│   │ Update Job  │  UPDATE jobs SET                                              │
│   │             │    license_plate, driver_name, driver_phone,                 │
│   │             │    status = 'DISPATCHED', dispatched_at = NOW()              │
│   └──────┬──────┘                                                               │
│          │                                                                       │
│          ▼                                                                       │
│   ┌─────────────┐                                                               │
│   │  Generate   │  Template: CUSTOMER_VEHICLE_CONFIRM                           │
│   │  Customer   │  "MK-DRT1 / 15.01 / 22:00 / ... / BKS: 29H 76514 / ..."     │
│   │  Message    │                                                               │
│   └──────┬──────┘                                                               │
│          │                                                                       │
│          ▼                                                                       │
│   ┌─────────────┐                                                               │
│   │   Return    │  { success: true, job_number: "TRK-2601-0001",               │
│   │   Response  │    message_to_customer: "..." }                               │
│   └─────────────┘                                                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Zalo Bot Automation

### 3.1 Zalo Message Handler

```python
# zalo_handler.py

from typing import Dict, Any
import asyncio

class ZaloMessageHandler:
    """Handle incoming Zalo messages and route to workflows"""
    
    def __init__(self, n8n_webhook_url: str, ai_service):
        self.n8n_url = n8n_webhook_url
        self.ai_service = ai_service
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming Zalo message
        
        message = {
            "room_name": "Tam Bảo",
            "room_type": "vendor",  # vendor, customer
            "sender_name": "Thủy Tam Bảo",
            "content": "BKS: 29H 76514...",
            "content_type": "text",  # text, file, image
            "file_path": None,
            "quote_content": "MK-DRT1 / 15.01..."  # quoted message
        }
        """
        
        # Determine message context
        context = self._build_context(message)
        
        # Route based on room type
        if message['room_type'] == 'vendor':
            return await self._handle_vendor_message(message, context)
        elif message['room_type'] == 'customer':
            return await self._handle_customer_message(message, context)
        else:
            return await self._handle_internal_message(message, context)
    
    async def _handle_vendor_message(self, message: Dict, context: Dict) -> Dict:
        """Handle message from vendor (usually vehicle assignment)"""
        
        # Check if this is a vehicle info response
        if self._looks_like_vehicle_info(message['content']):
            # Trigger vehicle assignment workflow
            return await self._trigger_workflow('vehicle-assign', {
                'source': 'zalo',
                'room': message['room_name'],
                'content': message['content'],
                'quote': message.get('quote_content'),
                'context': context
            })
        
        # Otherwise, process normally
        return await self._process_with_ai(message, context)
    
    async def _handle_customer_message(self, message: Dict, context: Dict) -> Dict:
        """Handle message from customer (usually booking request)"""
        
        # Check for file attachment
        if message['content_type'] == 'file' and message.get('file_path'):
            return await self._trigger_workflow('process-booking-file', {
                'source': 'zalo',
                'room': message['room_name'],
                'file_path': message['file_path'],
                'context': context
            })
        
        # Text message - could be booking or query
        return await self._process_with_ai(message, context)
    
    async def _process_with_ai(self, message: Dict, context: Dict) -> Dict:
        """Process message through AI service"""
        
        ai_response = await self.ai_service.process({
            'source': 'ZALO',
            'source_id': message['room_name'],
            'content_type': message['content_type'].upper(),
            'content': message['content'],
            'context': context
        })
        
        # Route based on detected intent
        intent_handlers = {
            'create_job': 'process-booking',
            'assign_vehicle': 'vehicle-assign',
            'query_status': 'job-status',
            'generate_statement': 'generate-statement',
        }
        
        workflow = intent_handlers.get(ai_response.intent.value)
        
        if workflow:
            return await self._trigger_workflow(workflow, {
                'ai_response': ai_response.__dict__,
                'original_message': message,
                'context': context
            })
        
        # No specific workflow - return AI response directly
        return {
            'success': True,
            'intent': ai_response.intent.value,
            'message': ai_response.message,
            'action': 'none'
        }
    
    async def _trigger_workflow(self, workflow: str, data: Dict) -> Dict:
        """Trigger n8n workflow via webhook"""
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.n8n_url}/slms/{workflow}",
                json=data
            ) as response:
                return await response.json()
    
    def _looks_like_vehicle_info(self, content: str) -> bool:
        """Check if content looks like vehicle assignment info"""
        import re
        
        patterns = [
            r'\d{2}[A-Z]\s*\d{4,5}',  # License plate
            r'0\d{9,10}',              # Phone number
            r'CCCD|CMND',              # ID card mention
        ]
        
        matches = sum(1 for p in patterns if re.search(p, content, re.I))
        return matches >= 2
    
    def _build_context(self, message: Dict) -> Dict:
        """Build context from message and history"""
        
        context = {
            'room_name': message['room_name'],
            'room_type': message['room_type'],
        }
        
        # If there's a quoted message, extract job reference
        if message.get('quote_content'):
            context['quote'] = message['quote_content']
            # Try to extract job reference from quote
            import re
            job_match = re.search(r'(TRK-\d{4}-\d{4})', message['quote_content'])
            if job_match:
                context['job_reference'] = job_match.group(1)
        
        return context
```

---

## 4. Scheduled Tasks

### 4.1 Task Configuration

```sql
CREATE TABLE scheduled_tasks (
    id              SERIAL PRIMARY KEY,
    task_code       VARCHAR(50) UNIQUE NOT NULL,
    task_name       VARCHAR(100) NOT NULL,
    
    -- Schedule
    cron_expression VARCHAR(50) NOT NULL,           -- "0 18 * * *" = daily 6pm
    timezone        VARCHAR(50) DEFAULT 'Asia/Ho_Chi_Minh',
    
    -- Task details
    workflow_name   VARCHAR(100),                   -- n8n workflow to trigger
    parameters      JSONB,
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    last_run        TIMESTAMP,
    next_run        TIMESTAMP,
    last_status     VARCHAR(20),
    last_error      TEXT,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO scheduled_tasks (task_code, task_name, cron_expression, workflow_name, parameters) VALUES
('DAILY_REPORT', 'Daily Operations Report', '0 18 * * *', 'daily-report', '{"recipients": ["manager@company.com"]}'),
('RATE_EXPIRY', 'Rate Expiry Check', '0 8 * * *', 'rate-expiry-alert', '{"days_ahead": 30}'),
('AR_AGING', 'AR Aging Alert', '0 9 * * 1', 'ar-aging-alert', '{"overdue_days": 30}'),
('MISA_SYNC', 'MISA Balance Sync', '0 6 * * *', 'misa-balance-sync', '{}'),
('BACKUP_REMINDER', 'Backup Status Check', '0 7 * * *', 'backup-check', '{}');
```

### 4.2 Task Scheduler

```python
# scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

class TaskScheduler:
    """Manage scheduled tasks"""
    
    def __init__(self, db, n8n_client):
        self.db = db
        self.n8n = n8n_client
        self.scheduler = AsyncIOScheduler(timezone='Asia/Ho_Chi_Minh')
    
    async def load_tasks(self):
        """Load and schedule all active tasks"""
        
        tasks = await self.db.fetch("""
            SELECT * FROM scheduled_tasks WHERE is_active = TRUE
        """)
        
        for task in tasks:
            self._schedule_task(task)
        
        self.scheduler.start()
    
    def _schedule_task(self, task: dict):
        """Schedule a single task"""
        
        trigger = CronTrigger.from_crontab(
            task['cron_expression'],
            timezone=task['timezone']
        )
        
        self.scheduler.add_job(
            self._run_task,
            trigger=trigger,
            args=[task['task_code']],
            id=task['task_code'],
            replace_existing=True
        )
    
    async def _run_task(self, task_code: str):
        """Execute a scheduled task"""
        
        task = await self.db.fetchrow(
            "SELECT * FROM scheduled_tasks WHERE task_code = $1",
            task_code
        )
        
        try:
            # Update last_run
            await self.db.execute(
                "UPDATE scheduled_tasks SET last_run = NOW() WHERE task_code = $1",
                task_code
            )
            
            # Trigger n8n workflow
            result = await self.n8n.trigger_workflow(
                task['workflow_name'],
                task['parameters'] or {}
            )
            
            # Update status
            await self.db.execute("""
                UPDATE scheduled_tasks SET 
                    last_status = 'SUCCESS',
                    last_error = NULL,
                    next_run = (
                        SELECT next_fire_time FROM information_schema...
                    )
                WHERE task_code = $1
            """, task_code)
            
        except Exception as e:
            await self.db.execute("""
                UPDATE scheduled_tasks SET 
                    last_status = 'FAILED',
                    last_error = $2
                WHERE task_code = $1
            """, task_code, str(e))
            
            # Log error
            print(f"Task {task_code} failed: {e}")
```

### 4.3 Task Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       SCHEDULED TASKS DASHBOARD                                  │
│                                                                                  │
│   Task              │ Schedule      │ Last Run    │ Status  │ Next Run          │
│   ──────────────────┼───────────────┼─────────────┼─────────┼────────────────── │
│   Daily Report      │ 18:00 daily   │ 15/01 18:00 │ ✅ OK   │ 16/01 18:00       │
│   Rate Expiry       │ 08:00 daily   │ 16/01 08:00 │ ✅ OK   │ 17/01 08:00       │
│   AR Aging Alert    │ 09:00 Monday  │ 13/01 09:00 │ ✅ OK   │ 20/01 09:00       │
│   MISA Sync         │ 06:00 daily   │ 16/01 06:00 │ ✅ OK   │ 17/01 06:00       │
│   Backup Check      │ 07:00 daily   │ 16/01 07:00 │ ⚠️ WARN │ 17/01 07:00       │
│                                                                                  │
│   [▶ Run Now] [⏸ Pause] [📝 Edit] [🗑 Delete]                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 SUMMARY

### Automation Components
1. **n8n** - Workflow engine
2. **Zalo Handler** - Message routing
3. **Scheduler** - Cron-based tasks

### Key Workflows
- Process Booking (Zalo → AI → Create Job)
- Assign Vehicle (Vendor → Update → Notify)
- Daily Report (Schedule → Generate → Email)
- MISA Sync (Statement → API → Update)

### Scheduled Tasks
- Daily Operations Report (18:00)
- Rate Expiry Check (08:00)
- AR Aging Alert (Monday 09:00)
- MISA Balance Sync (06:00)

### Integration
- Webhooks for real-time triggers
- API calls to SLMS backend
- Database operations
- External services (MISA, Email)
