# 🧠 GIẢI PHÁP 3: CONVERSATION MEMORY

## Mục lục

1. [Tổng quan vấn đề](#1-tổng-quan-vấn-đề)
2. [Kiến trúc giải pháp](#2-kiến-trúc-giải-pháp)
3. [Chi tiết Implementation](#3-chi-tiết-implementation)
4. [Files cần tạo](#4-files-cần-tạo)
5. [Hướng dẫn từng bước](#5-hướng-dẫn-từng-bước)
6. [Test cases](#6-test-cases)
7. [Integration với hệ thống hiện tại](#7-integration-với-hệ-thống-hiện-tại)

---

## 1. TỔNG QUAN VẤN ĐỀ

### 1.1 Vấn đề với Stateless Chat

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    STATELESS CHAT PROBLEM                                        │
│                                                                                  │
│   User: "Đặt xe cho DRT1 ngày mai đi Hải Phòng"                                │
│   Bot:  "Đã tạo booking. Bạn cần loại xe gì?"                                  │
│                                                                                  │
│   User: "Xe 5 tấn"                                                              │
│   Bot:  ❌ "Tôi không hiểu. Vui lòng cung cấp đầy đủ thông tin booking."       │
│         ❌ Bot quên mất context trước đó!                                       │
│                                                                                  │
│   ─────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│   EXPECTED BEHAVIOR:                                                            │
│                                                                                  │
│   User: "Đặt xe cho DRT1 ngày mai đi Hải Phòng"                                │
│   Bot:  "Đã nhận booking cho DRT1, ngày mai, đi Hải Phòng.                     │
│          Bạn cần loại xe gì?"                                                   │
│                                                                                  │
│   User: "Xe 5 tấn"                                                              │
│   Bot:  ✅ "Đã cập nhật: xe 5 tấn. Giờ lấy hàng là mấy giờ?"                   │
│                                                                                  │
│   User: "22h"                                                                   │
│   Bot:  ✅ "Hoàn tất booking:                                                   │
│          - KH: DRT1                                                             │
│          - Ngày: 18/01/2026                                                     │
│          - Xe: 5 tấn                                                            │
│          - Giờ: 22:00                                                           │
│          - Đến: Hải Phòng                                                       │
│          Xác nhận tạo job?"                                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Các scenario cần xử lý

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    CONVERSATION SCENARIOS                                        │
│                                                                                  │
│   SCENARIO 1: Multi-turn Booking (Bổ sung thông tin qua nhiều turn)            │
│   ────────────────────────────────────────────────────────────────              │
│   Turn 1: "Đặt xe cho DRT1"           → Thiếu: date, destination, vehicle      │
│   Turn 2: "Ngày mai đi HP"            → Thiếu: vehicle                         │
│   Turn 3: "Xe 5 tấn"                  → Đủ thông tin → Confirm                 │
│                                                                                  │
│   SCENARIO 2: Correction (Sửa thông tin đã nhập)                               │
│   ────────────────────────────────────────────────                              │
│   Turn 1: "Đặt xe 5T cho DRT1 ngày mai đi HP"                                  │
│   Turn 2: "Sửa lại, đi Quảng Ninh không phải HP"  → Update destination         │
│   Turn 3: "Confirm"                   → Tạo job với destination = QN           │
│                                                                                  │
│   SCENARIO 3: Context Switch (Chuyển sang task mới)                            │
│   ────────────────────────────────────────────────                              │
│   Turn 1: "Đặt xe cho DRT1 ngày mai đi HP"                                     │
│   Turn 2: "Thôi bỏ đi, check job 2501001 giúp tôi"  → Clear context, new task │
│                                                                                  │
│   SCENARIO 4: Reference Previous (Tham chiếu job/booking trước)                │
│   ─────────────────────────────────────────────────────────────                 │
│   Turn 1: "Đặt xe giống job hôm qua cho DRT1"  → Load template from history   │
│   Turn 2: "Nhưng đổi điểm đến sang QN"         → Modify template               │
│                                                                                  │
│   SCENARIO 5: Batch with Memory (Tạo nhiều jobs liên tiếp)                     │
│   ────────────────────────────────────────────────────────                      │
│   Turn 1: "Đặt xe 5T cho DRT1 ngày mai đi HP lúc 8h"  → Job 1 created         │
│   Turn 2: "Thêm 1 chuyến nữa lúc 14h"                 → Job 2, same context   │
│   Turn 3: "Và 1 chuyến đi QN lúc 20h"                 → Job 3, partial context│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Memory Types

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MEMORY TYPES                                                  │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │ SHORT-TERM MEMORY (Session Context)                                      │  │
│   │ ───────────────────────────────────                                      │  │
│   │ • Lifetime: Current conversation session                                 │  │
│   │ • Storage: In-memory (Redis optional)                                   │  │
│   │ • Content:                                                               │  │
│   │   - Current intent & entities being built                               │  │
│   │   - Pending confirmation items                                          │  │
│   │   - Last N messages for context                                         │  │
│   │   - Temporary state (editing, correcting)                               │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │ WORKING MEMORY (Active Task)                                             │  │
│   │ ────────────────────────────                                             │  │
│   │ • Lifetime: Until task completion or cancellation                       │  │
│   │ • Storage: Session state                                                 │  │
│   │ • Content:                                                               │  │
│   │   - Accumulated entities for current task                               │  │
│   │   - Missing required fields                                             │  │
│   │   - Validation state                                                    │  │
│   │   - Confirmation status                                                 │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │ LONG-TERM MEMORY (User Preferences) - Optional Phase 2                  │  │
│   │ ──────────────────────────────────────────────────────                  │  │
│   │ • Lifetime: Persistent across sessions                                  │  │
│   │ • Storage: Database                                                      │  │
│   │ • Content:                                                               │  │
│   │   - Frequently used customers                                           │  │
│   │   - Common routes                                                       │  │
│   │   - Preferred vehicle types                                             │  │
│   │   - Input patterns/shortcuts                                            │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. KIẾN TRÚC GIẢI PHÁP

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    CONVERSATION MEMORY ARCHITECTURE                              │
│                                                                                  │
│   User Message                                                                   │
│       │                                                                          │
│       ▼                                                                          │
│   ┌─────────────────┐                                                           │
│   │ ConversationMgr │ ─── Manages sessions, routes messages                     │
│   └────────┬────────┘                                                           │
│            │                                                                     │
│            ▼                                                                     │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│   │ SessionStore    │◄──►│ ConversationSt. │◄──►│ EntityAccum.    │            │
│   │                 │    │                 │    │                 │            │
│   │ • Get/Create    │    │ • Intent state  │    │ • Merge entities│            │
│   │ • TTL manage    │    │ • Message hist. │    │ • Track missing │            │
│   │ • Cleanup       │    │ • Task state    │    │ • Validate      │            │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│            │                      │                      │                      │
│            └──────────────────────┼──────────────────────┘                      │
│                                   │                                             │
│                                   ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                      ContinuationDetector                                │  │
│   │ ─────────────────────────────────────────────────────────────────────── │  │
│   │ • Is this a continuation of previous task?                              │  │
│   │ • Is this a correction/modification?                                    │  │
│   │ • Is this a new task (context switch)?                                  │  │
│   │ • Is this a reference to past job/booking?                              │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                   │                                             │
│                                   ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                      ResponseGenerator                                   │  │
│   │ ─────────────────────────────────────────────────────────────────────── │  │
│   │ • Generate contextual response                                          │  │
│   │ • Ask for missing fields                                                │  │
│   │ • Confirm accumulated data                                              │  │
│   │ • Handle corrections                                                    │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 State Machine

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    CONVERSATION STATE MACHINE                                    │
│                                                                                  │
│                         ┌──────────────┐                                        │
│                         │    IDLE      │                                        │
│                         │  (No task)   │                                        │
│                         └──────┬───────┘                                        │
│                                │                                                │
│                    New intent detected                                          │
│                                │                                                │
│                                ▼                                                │
│                         ┌──────────────┐                                        │
│                         │  COLLECTING  │◄─────────────────┐                    │
│                         │  (Building)  │                  │                    │
│                         └──────┬───────┘                  │                    │
│                                │                          │                    │
│               ┌────────────────┼────────────────┐         │                    │
│               │                │                │         │                    │
│               ▼                ▼                ▼         │                    │
│        ┌───────────┐    ┌───────────┐    ┌───────────┐   │                    │
│        │ Missing   │    │ Complete  │    │ Correction│   │                    │
│        │ fields    │    │ data      │    │ requested │   │                    │
│        └─────┬─────┘    └─────┬─────┘    └─────┬─────┘   │                    │
│              │                │                │         │                    │
│              │                ▼                │         │                    │
│              │         ┌──────────────┐        │         │                    │
│              │         │  CONFIRMING  │        │         │                    │
│              │         │  (Pending)   │        │         │                    │
│              │         └──────┬───────┘        │         │                    │
│              │                │                │         │                    │
│              │    ┌───────────┼───────────┐    │         │                    │
│              │    │           │           │    │         │                    │
│              │    ▼           ▼           ▼    │         │                    │
│              │  ┌─────┐   ┌───────┐   ┌──────┐ │         │                    │
│              │  │Confirm│  │Reject │   │ Edit │─┼─────────┘                    │
│              │  └───┬───┘  └───┬───┘   └──────┘                               │
│              │      │          │                                               │
│              │      ▼          │                                               │
│              │ ┌──────────┐    │                                               │
│              │ │ EXECUTED │    │                                               │
│              │ │ (Done)   │    │                                               │
│              │ └────┬─────┘    │                                               │
│              │      │          │                                               │
│              └──────┼──────────┘                                               │
│                     │                                                          │
│                     ▼                                                          │
│              ┌──────────────┐                                                  │
│              │    IDLE      │                                                  │
│              │  (Ready)     │                                                  │
│              └──────────────┘                                                  │
│                                                                                  │
│   TRANSITIONS:                                                                  │
│   • IDLE → COLLECTING: New intent detected                                     │
│   • COLLECTING → COLLECTING: More entities added                               │
│   • COLLECTING → CONFIRMING: All required fields present                       │
│   • CONFIRMING → EXECUTED: User confirms                                       │
│   • CONFIRMING → COLLECTING: User edits/corrects                               │
│   • ANY → IDLE: User cancels or timeout                                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MESSAGE PROCESSING FLOW                                       │
│                                                                                  │
│   1. User sends message                                                         │
│      │                                                                          │
│      ▼                                                                          │
│   2. ConversationManager.process(session_id, message)                          │
│      │                                                                          │
│      ├─► Load/Create session                                                   │
│      │   • SessionStore.get_or_create(session_id)                              │
│      │   • Returns: ConversationState                                          │
│      │                                                                          │
│      ├─► Detect continuation type                                              │
│      │   • ContinuationDetector.detect(state, message)                         │
│      │   • Returns: NEW_TASK | CONTINUATION | CORRECTION | REFERENCE           │
│      │                                                                          │
│      ├─► Process based on type                                                 │
│      │   │                                                                      │
│      │   ├─► NEW_TASK:                                                         │
│      │   │   • Clear working memory                                            │
│      │   │   • Extract new intent + entities                                   │
│      │   │   • Initialize task state                                           │
│      │   │                                                                      │
│      │   ├─► CONTINUATION:                                                     │
│      │   │   • Extract new entities from message                               │
│      │   │   • Merge with existing entities                                    │
│      │   │   • Update task state                                               │
│      │   │                                                                      │
│      │   ├─► CORRECTION:                                                       │
│      │   │   • Identify field to correct                                       │
│      │   │   • Update specific entity                                          │
│      │   │   • Keep other entities                                             │
│      │   │                                                                      │
│      │   └─► REFERENCE:                                                        │
│      │       • Load referenced job/booking                                     │
│      │       • Use as template                                                 │
│      │       • Apply modifications                                             │
│      │                                                                          │
│      ├─► Check completeness                                                    │
│      │   • EntityAccumulator.check_required()                                  │
│      │   • Returns: missing_fields[]                                           │
│      │                                                                          │
│      ├─► Generate response                                                     │
│      │   │                                                                      │
│      │   ├─► If missing fields:                                                │
│      │   │   • Ask for specific missing info                                   │
│      │   │   • Show current accumulated data                                   │
│      │   │                                                                      │
│      │   └─► If complete:                                                      │
│      │       • Show confirmation summary                                       │
│      │       • Wait for user confirm/edit                                      │
│      │                                                                          │
│      └─► Save state                                                            │
│          • SessionStore.save(session_id, state)                                │
│          • Add message to history                                              │
│                                                                                  │
│   3. Return response to user                                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. CHI TIẾT IMPLEMENTATION

### 3.1 File: `conversation_state.py`

```python
# backend/app/ai/memory/conversation_state.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid


class TaskState(Enum):
    """Trạng thái của task hiện tại"""
    IDLE = "idle"                    # Không có task
    COLLECTING = "collecting"        # Đang thu thập thông tin
    CONFIRMING = "confirming"        # Chờ xác nhận
    EXECUTED = "executed"            # Đã thực hiện
    CANCELLED = "cancelled"          # Đã hủy


class ContinuationType(Enum):
    """Loại continuation của message"""
    NEW_TASK = "new_task"            # Task mới hoàn toàn
    CONTINUATION = "continuation"    # Tiếp tục task hiện tại
    CORRECTION = "correction"        # Sửa thông tin
    CONFIRMATION = "confirmation"    # Xác nhận
    CANCELLATION = "cancellation"    # Hủy task
    REFERENCE = "reference"          # Tham chiếu job/booking cũ


@dataclass
class Message:
    """Một message trong conversation"""
    id: str
    role: str                        # "user" | "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def user(cls, content: str, **metadata) -> "Message":
        return cls(
            id=str(uuid.uuid4()),
            role="user",
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
    
    @classmethod
    def assistant(cls, content: str, **metadata) -> "Message":
        return cls(
            id=str(uuid.uuid4()),
            role="assistant",
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )


@dataclass
class TaskContext:
    """Context của task đang thực hiện"""
    intent: Optional[str] = None     # Intent hiện tại (create_booking, update_job, etc.)
    entities: Dict[str, Any] = field(default_factory=dict)  # Accumulated entities
    missing_fields: List[str] = field(default_factory=list)  # Fields còn thiếu
    validation_errors: List[str] = field(default_factory=list)  # Lỗi validation
    state: TaskState = TaskState.IDLE
    started_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    confirmation_data: Optional[Dict] = None  # Data chờ confirm
    
    def reset(self):
        """Reset task context"""
        self.intent = None
        self.entities = {}
        self.missing_fields = []
        self.validation_errors = []
        self.state = TaskState.IDLE
        self.started_at = None
        self.last_updated = None
        self.confirmation_data = None
    
    def start_task(self, intent: str, entities: Dict[str, Any] = None):
        """Bắt đầu task mới"""
        self.intent = intent
        self.entities = entities or {}
        self.missing_fields = []
        self.validation_errors = []
        self.state = TaskState.COLLECTING
        self.started_at = datetime.now()
        self.last_updated = datetime.now()
    
    def add_entities(self, new_entities: Dict[str, Any]):
        """Thêm entities vào accumulated"""
        for key, value in new_entities.items():
            if value is not None:
                self.entities[key] = value
        self.last_updated = datetime.now()
    
    def update_entity(self, key: str, value: Any):
        """Update một entity cụ thể"""
        self.entities[key] = value
        self.last_updated = datetime.now()
    
    def is_active(self) -> bool:
        """Check xem có task đang active không"""
        return self.state in [TaskState.COLLECTING, TaskState.CONFIRMING]
    
    def is_complete(self, required_fields: List[str]) -> bool:
        """Check xem đã đủ required fields chưa"""
        for field in required_fields:
            if field not in self.entities or self.entities[field] is None:
                return False
        return True


@dataclass
class ConversationState:
    """
    State của một conversation session
    """
    session_id: str
    user_id: Optional[str] = None
    
    # Message history
    messages: List[Message] = field(default_factory=list)
    max_history: int = 20            # Giữ tối đa N messages
    
    # Current task context
    task: TaskContext = field(default_factory=TaskContext)
    
    # Session metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    ttl_minutes: int = 30            # Session timeout
    
    # Additional context
    context: Dict[str, Any] = field(default_factory=dict)  # Custom context data
    
    def add_message(self, message: Message):
        """Thêm message vào history"""
        self.messages.append(message)
        self.last_activity = datetime.now()
        
        # Trim history if needed
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_recent_messages(self, n: int = 5) -> List[Message]:
        """Lấy N messages gần nhất"""
        return self.messages[-n:] if self.messages else []
    
    def get_conversation_text(self, n: int = 5) -> str:
        """Lấy text của N messages gần nhất để đưa vào prompt"""
        recent = self.get_recent_messages(n)
        lines = []
        for msg in recent:
            role = "User" if msg.role == "user" else "Assistant"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)
    
    def is_expired(self) -> bool:
        """Check xem session đã hết hạn chưa"""
        expiry = self.last_activity + timedelta(minutes=self.ttl_minutes)
        return datetime.now() > expiry
    
    def reset_task(self):
        """Reset current task, giữ lại history"""
        self.task.reset()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": m.metadata
                }
                for m in self.messages
            ],
            "task": {
                "intent": self.task.intent,
                "entities": self.task.entities,
                "missing_fields": self.task.missing_fields,
                "state": self.task.state.value,
                "started_at": self.task.started_at.isoformat() if self.task.started_at else None,
            },
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        """Deserialize from dictionary"""
        state = cls(
            session_id=data["session_id"],
            user_id=data.get("user_id")
        )
        
        # Restore messages
        for m in data.get("messages", []):
            state.messages.append(Message(
                id=m["id"],
                role=m["role"],
                content=m["content"],
                timestamp=datetime.fromisoformat(m["timestamp"]),
                metadata=m.get("metadata", {})
            ))
        
        # Restore task
        task_data = data.get("task", {})
        state.task.intent = task_data.get("intent")
        state.task.entities = task_data.get("entities", {})
        state.task.missing_fields = task_data.get("missing_fields", [])
        state.task.state = TaskState(task_data.get("state", "idle"))
        if task_data.get("started_at"):
            state.task.started_at = datetime.fromisoformat(task_data["started_at"])
        
        # Restore timestamps
        state.created_at = datetime.fromisoformat(data["created_at"])
        state.last_activity = datetime.fromisoformat(data["last_activity"])
        state.context = data.get("context", {})
        
        return state
```

### 3.2 File: `session_store.py`

```python
# backend/app/ai/memory/session_store.py

from typing import Dict, Optional
from datetime import datetime, timedelta
import json
import asyncio
from abc import ABC, abstractmethod

from .conversation_state import ConversationState


class SessionStore(ABC):
    """Abstract base class cho session storage"""
    
    @abstractmethod
    async def get(self, session_id: str) -> Optional[ConversationState]:
        """Lấy session state"""
        pass
    
    @abstractmethod
    async def save(self, state: ConversationState):
        """Lưu session state"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str):
        """Xóa session"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self):
        """Cleanup các session hết hạn"""
        pass
    
    async def get_or_create(
        self, 
        session_id: str, 
        user_id: Optional[str] = None
    ) -> ConversationState:
        """Lấy session hoặc tạo mới nếu chưa có"""
        state = await self.get(session_id)
        
        if state is None or state.is_expired():
            state = ConversationState(
                session_id=session_id,
                user_id=user_id
            )
            await self.save(state)
        
        return state


class InMemorySessionStore(SessionStore):
    """
    In-memory session store (cho development/testing)
    Production nên dùng Redis
    """
    
    def __init__(self, cleanup_interval: int = 300):
        self._sessions: Dict[str, ConversationState] = {}
        self._cleanup_interval = cleanup_interval
        self._cleanup_task = None
    
    async def start(self):
        """Start cleanup task"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            await asyncio.sleep(self._cleanup_interval)
            await self.cleanup_expired()
    
    async def get(self, session_id: str) -> Optional[ConversationState]:
        return self._sessions.get(session_id)
    
    async def save(self, state: ConversationState):
        self._sessions[state.session_id] = state
    
    async def delete(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    async def cleanup_expired(self):
        """Remove expired sessions"""
        expired = [
            sid for sid, state in self._sessions.items()
            if state.is_expired()
        ]
        for sid in expired:
            del self._sessions[sid]
        
        if expired:
            print(f"Cleaned up {len(expired)} expired sessions")
    
    def get_stats(self) -> Dict:
        """Get store statistics"""
        return {
            "total_sessions": len(self._sessions),
            "active_sessions": len([
                s for s in self._sessions.values()
                if not s.is_expired()
            ])
        }


class RedisSessionStore(SessionStore):
    """
    Redis-based session store (cho production)
    """
    
    def __init__(self, redis_client, key_prefix: str = "chat_session:"):
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    def _key(self, session_id: str) -> str:
        return f"{self.key_prefix}{session_id}"
    
    async def get(self, session_id: str) -> Optional[ConversationState]:
        data = await self.redis.get(self._key(session_id))
        if data:
            return ConversationState.from_dict(json.loads(data))
        return None
    
    async def save(self, state: ConversationState):
        key = self._key(state.session_id)
        data = json.dumps(state.to_dict())
        # Set with TTL
        ttl = state.ttl_minutes * 60
        await self.redis.setex(key, ttl, data)
    
    async def delete(self, session_id: str):
        await self.redis.delete(self._key(session_id))
    
    async def cleanup_expired(self):
        # Redis handles TTL automatically
        pass
```

### 3.3 File: `continuation_detector.py`

```python
# backend/app/ai/memory/continuation_detector.py

from typing import Optional, Tuple
import re

from .conversation_state import ConversationState, ContinuationType, TaskState
from app.ai.clients import AIClientManager


class ContinuationDetector:
    """
    Detect loại continuation của message
    """
    
    # Keywords cho cancellation
    CANCEL_KEYWORDS = [
        "hủy", "bỏ", "cancel", "thôi", "không cần", "dừng",
        "bỏ qua", "skip", "quên đi", "forget"
    ]
    
    # Keywords cho confirmation
    CONFIRM_KEYWORDS = [
        "ok", "được", "confirm", "xác nhận", "đồng ý", "yes",
        "đúng rồi", "chính xác", "tạo đi", "tạo luôn", "làm đi"
    ]
    
    # Keywords cho correction
    CORRECTION_KEYWORDS = [
        "sửa", "đổi", "thay", "không phải", "nhầm", "fix",
        "correct", "change", "update", "sai rồi", "sửa lại"
    ]
    
    # Keywords cho reference
    REFERENCE_KEYWORDS = [
        "giống", "như", "tương tự", "copy", "theo",
        "job", "booking", "hôm qua", "lần trước"
    ]
    
    # Intent keywords (để detect new task)
    INTENT_KEYWORDS = {
        "create_booking": ["đặt xe", "book", "booking", "tạo job", "cần xe", "lấy hàng"],
        "update_job": ["cập nhật", "update", "sửa job", "thay đổi"],
        "check_status": ["check", "kiểm tra", "status", "tình trạng", "đang ở đâu"],
        "assign_vehicle": ["gán xe", "assign", "phân xe", "điều xe"],
        "cancel_job": ["hủy job", "cancel job", "bỏ job"],
    }
    
    def __init__(self, ai_client: Optional[AIClientManager] = None):
        self.ai = ai_client
    
    def detect(
        self, 
        state: ConversationState, 
        message: str
    ) -> Tuple[ContinuationType, Optional[str]]:
        """
        Detect continuation type
        
        Args:
            state: Current conversation state
            message: New user message
        
        Returns:
            Tuple of (ContinuationType, detected_intent or None)
        """
        message_lower = message.lower().strip()
        
        # 1. Check cancellation
        if self._is_cancellation(message_lower):
            return ContinuationType.CANCELLATION, None
        
        # 2. Check confirmation (only if in CONFIRMING state)
        if state.task.state == TaskState.CONFIRMING:
            if self._is_confirmation(message_lower):
                return ContinuationType.CONFIRMATION, state.task.intent
        
        # 3. Check correction
        correction_field = self._is_correction(message_lower, state)
        if correction_field:
            return ContinuationType.CORRECTION, correction_field
        
        # 4. Check reference to past job
        if self._is_reference(message_lower):
            return ContinuationType.REFERENCE, None
        
        # 5. Check if new task (has clear intent keywords)
        new_intent = self._detect_intent(message_lower)
        if new_intent:
            # New task only if no active task or different intent
            if not state.task.is_active() or new_intent != state.task.intent:
                return ContinuationType.NEW_TASK, new_intent
        
        # 6. Default: continuation if there's active task
        if state.task.is_active():
            return ContinuationType.CONTINUATION, state.task.intent
        
        # 7. If no active task and no clear intent, treat as new task
        # (will need to classify intent in next step)
        return ContinuationType.NEW_TASK, None
    
    def _is_cancellation(self, message: str) -> bool:
        """Check if message is cancellation"""
        for keyword in self.CANCEL_KEYWORDS:
            if keyword in message:
                # Make sure it's not "cancel job" (which is a task)
                if "job" not in message or keyword not in ["hủy", "cancel"]:
                    return True
        return False
    
    def _is_confirmation(self, message: str) -> bool:
        """Check if message is confirmation"""
        # Short messages with confirm keywords
        if len(message.split()) <= 5:
            for keyword in self.CONFIRM_KEYWORDS:
                if keyword in message:
                    return True
        return False
    
    def _is_correction(
        self, 
        message: str, 
        state: ConversationState
    ) -> Optional[str]:
        """
        Check if message is correction
        Returns the field being corrected if detected
        """
        # Check correction keywords
        has_correction_keyword = any(kw in message for kw in self.CORRECTION_KEYWORDS)
        
        if not has_correction_keyword:
            return None
        
        # Try to identify which field is being corrected
        field_patterns = {
            "customer_code": ["khách", "kh", "customer"],
            "date": ["ngày", "date", "hôm"],
            "time": ["giờ", "time", "lúc"],
            "vehicle_type": ["xe", "vehicle", "tải"],
            "destination": ["đến", "destination", "giao"],
            "origin": ["lấy", "origin", "pickup"],
        }
        
        for field, patterns in field_patterns.items():
            for pattern in patterns:
                if pattern in message:
                    return field
        
        # Generic correction - will need context to determine field
        return "unknown"
    
    def _is_reference(self, message: str) -> bool:
        """Check if message references past job/booking"""
        for keyword in self.REFERENCE_KEYWORDS:
            if keyword in message:
                return True
        return False
    
    def _detect_intent(self, message: str) -> Optional[str]:
        """Detect intent from message"""
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message:
                    return intent
        return None
    
    async def detect_with_ai(
        self, 
        state: ConversationState, 
        message: str
    ) -> Tuple[ContinuationType, Optional[str]]:
        """
        Use AI for more accurate detection (when rule-based is uncertain)
        """
        if not self.ai:
            return self.detect(state, message)
        
        # Build context
        conversation_text = state.get_conversation_text(n=3)
        task_context = ""
        if state.task.is_active():
            task_context = f"""
Current task: {state.task.intent}
Collected data: {state.task.entities}
Missing fields: {state.task.missing_fields}
"""
        
        prompt = f"""Analyze this message in the context of a logistics chat system.

CONVERSATION HISTORY:
{conversation_text}

{task_context}

NEW MESSAGE: "{message}"

Determine the type of this message:
1. NEW_TASK - User wants to start a completely new task
2. CONTINUATION - User is providing more info for current task
3. CORRECTION - User wants to fix/change something they said
4. CONFIRMATION - User is confirming the pending action
5. CANCELLATION - User wants to cancel current task
6. REFERENCE - User is referencing a past job/booking

Also identify the intent if it's a NEW_TASK:
- create_booking: Create new booking/job
- update_job: Update existing job
- check_status: Check job status
- assign_vehicle: Assign vehicle to job

Respond in JSON format:
{{
    "continuation_type": "NEW_TASK|CONTINUATION|CORRECTION|CONFIRMATION|CANCELLATION|REFERENCE",
    "intent": "intent_name or null",
    "confidence": 0.95,
    "reasoning": "brief explanation"
}}
"""
        
        try:
            response = await self.ai.generate(
                prompt=prompt,
                system_prompt="You are analyzing conversation flow in a logistics system.",
                temperature=0.1
            )
            
            # Parse response
            import json
            result = json.loads(response)
            
            cont_type = ContinuationType(result["continuation_type"].lower())
            intent = result.get("intent")
            
            return cont_type, intent
            
        except Exception as e:
            print(f"AI detection failed, falling back to rules: {e}")
            return self.detect(state, message)
```

### 3.4 File: `entity_accumulator.py`

```python
# backend/app/ai/memory/entity_accumulator.py

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .conversation_state import ConversationState, TaskContext


@dataclass
class AccumulationResult:
    """Kết quả accumulation"""
    entities: Dict[str, Any]
    missing_fields: List[str]
    is_complete: bool
    changes: List[str]  # Fields that changed
    warnings: List[str]


class EntityAccumulator:
    """
    Accumulate và merge entities qua nhiều turns
    """
    
    # Required fields for each intent
    REQUIRED_FIELDS = {
        "create_booking": ["customer_code", "date", "destination"],
        "update_job": ["job_id"],
        "check_status": ["job_id"],
        "assign_vehicle": ["job_id", "license_plate"],
        "cancel_job": ["job_id"],
    }
    
    # Optional but useful fields
    OPTIONAL_FIELDS = {
        "create_booking": ["time", "vehicle_type", "origin", "cargo", "quantity", "notes"],
        "update_job": ["status", "driver", "vehicle", "notes"],
        "assign_vehicle": ["driver_name", "driver_phone"],
    }
    
    # Default values for some fields
    FIELD_DEFAULTS = {
        "origin": "Từ kho",  # Default pickup location
    }
    
    def __init__(self):
        pass
    
    def accumulate(
        self,
        task: TaskContext,
        new_entities: Dict[str, Any],
        intent: Optional[str] = None
    ) -> AccumulationResult:
        """
        Accumulate new entities into task context
        
        Args:
            task: Current task context
            new_entities: Newly extracted entities
            intent: Intent (use task.intent if None)
        
        Returns:
            AccumulationResult with merged entities and status
        """
        intent = intent or task.intent
        changes = []
        warnings = []
        
        # Start with existing entities
        merged = dict(task.entities)
        
        # Merge new entities
        for key, value in new_entities.items():
            if value is None:
                continue
            
            old_value = merged.get(key)
            
            # Check for conflict
            if old_value is not None and old_value != value:
                # New value overrides old
                warnings.append(f"'{key}' changed: {old_value} → {value}")
            
            if old_value != value:
                changes.append(key)
            
            merged[key] = value
        
        # Apply defaults for missing optional fields
        for field, default in self.FIELD_DEFAULTS.items():
            if field not in merged:
                merged[field] = default
        
        # Check required fields
        required = self.REQUIRED_FIELDS.get(intent, [])
        missing = []
        for field in required:
            if field not in merged or merged[field] is None:
                missing.append(field)
        
        return AccumulationResult(
            entities=merged,
            missing_fields=missing,
            is_complete=len(missing) == 0,
            changes=changes,
            warnings=warnings
        )
    
    def correct_entity(
        self,
        task: TaskContext,
        field: str,
        new_value: Any
    ) -> AccumulationResult:
        """
        Correct a specific entity
        """
        merged = dict(task.entities)
        old_value = merged.get(field)
        
        changes = []
        warnings = []
        
        if old_value != new_value:
            changes.append(field)
            if old_value is not None:
                warnings.append(f"Corrected '{field}': {old_value} → {new_value}")
        
        merged[field] = new_value
        
        # Recalculate missing
        required = self.REQUIRED_FIELDS.get(task.intent, [])
        missing = [f for f in required if f not in merged or merged[f] is None]
        
        return AccumulationResult(
            entities=merged,
            missing_fields=missing,
            is_complete=len(missing) == 0,
            changes=changes,
            warnings=warnings
        )
    
    def get_missing_fields_message(
        self, 
        intent: str, 
        missing: List[str]
    ) -> str:
        """
        Generate human-readable message about missing fields
        """
        if not missing:
            return ""
        
        field_names = {
            "customer_code": "khách hàng",
            "date": "ngày lấy hàng",
            "time": "giờ lấy hàng",
            "destination": "điểm giao hàng",
            "origin": "điểm lấy hàng",
            "vehicle_type": "loại xe",
            "job_id": "mã job",
            "license_plate": "biển số xe",
            "driver_name": "tên tài xế",
            "driver_phone": "số điện thoại tài xế",
        }
        
        missing_names = [field_names.get(f, f) for f in missing]
        
        if len(missing_names) == 1:
            return f"Xin cho biết {missing_names[0]}?"
        else:
            return f"Xin bổ sung: {', '.join(missing_names)}"
    
    def get_summary(self, task: TaskContext) -> str:
        """
        Generate summary of accumulated entities
        """
        if not task.entities:
            return "Chưa có thông tin nào."
        
        field_labels = {
            "customer_code": "Khách hàng",
            "date": "Ngày",
            "time": "Giờ",
            "destination": "Giao tại",
            "origin": "Lấy tại",
            "vehicle_type": "Loại xe",
            "cargo": "Hàng hóa",
            "quantity": "Số lượng",
            "notes": "Ghi chú",
            "job_id": "Job",
        }
        
        lines = []
        for key, value in task.entities.items():
            if value is not None:
                label = field_labels.get(key, key)
                lines.append(f"• {label}: {value}")
        
        return "\n".join(lines)
    
    def validate_entities(
        self, 
        intent: str, 
        entities: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate entities beyond just presence
        Returns (is_valid, error_messages)
        """
        errors = []
        
        # Date validation
        if "date" in entities:
            date_val = entities["date"]
            # Check if date is not in the past
            # (actual validation would be more complex)
            pass
        
        # Customer validation
        if "customer_code" in entities:
            customer = entities["customer_code"]
            # Could check if customer exists in DB
            pass
        
        # Job ID validation
        if "job_id" in entities:
            job_id = entities["job_id"]
            # Check format
            if not str(job_id).isdigit() and not str(job_id).startswith("JOB"):
                errors.append(f"Mã job không hợp lệ: {job_id}")
        
        return len(errors) == 0, errors
```

### 3.5 File: `conversation_manager.py`

```python
# backend/app/ai/memory/conversation_manager.py

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .conversation_state import (
    ConversationState, 
    Message, 
    TaskState, 
    ContinuationType
)
from .session_store import SessionStore, InMemorySessionStore
from .continuation_detector import ContinuationDetector
from .entity_accumulator import EntityAccumulator, AccumulationResult

from app.ai.clients import AIClientManager
from app.ai.pipeline.intent_classifier import IntentClassifier
from app.ai.pipeline.entity_extractor import EntityExtractor


@dataclass
class ProcessResult:
    """Kết quả xử lý message"""
    response: str
    state: ConversationState
    action: Optional[Dict[str, Any]] = None  # Action to execute
    needs_confirmation: bool = False
    confirmation_data: Optional[Dict] = None


class ConversationManager:
    """
    Main manager cho conversation với memory
    """
    
    def __init__(
        self,
        ai_client: AIClientManager,
        session_store: Optional[SessionStore] = None,
        db_session = None
    ):
        self.ai = ai_client
        self.store = session_store or InMemorySessionStore()
        self.db = db_session
        
        # Initialize components
        self.detector = ContinuationDetector(ai_client)
        self.accumulator = EntityAccumulator()
        self.intent_classifier = IntentClassifier(ai_client)
        self.entity_extractor = EntityExtractor(ai_client, db_session)
    
    async def process(
        self,
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> ProcessResult:
        """
        Process a user message
        
        Args:
            session_id: Session identifier
            message: User message
            user_id: Optional user ID
            context: Additional context (e.g., from frontend)
        
        Returns:
            ProcessResult
        """
        # 1. Get or create session
        state = await self.store.get_or_create(session_id, user_id)
        
        # 2. Add user message to history
        state.add_message(Message.user(message))
        
        # 3. Detect continuation type
        cont_type, detected_intent = self.detector.detect(state, message)
        
        # 4. Process based on continuation type
        if cont_type == ContinuationType.CANCELLATION:
            result = await self._handle_cancellation(state)
        
        elif cont_type == ContinuationType.CONFIRMATION:
            result = await self._handle_confirmation(state)
        
        elif cont_type == ContinuationType.CORRECTION:
            result = await self._handle_correction(state, message, detected_intent)
        
        elif cont_type == ContinuationType.REFERENCE:
            result = await self._handle_reference(state, message)
        
        elif cont_type == ContinuationType.NEW_TASK:
            result = await self._handle_new_task(state, message, detected_intent, context)
        
        else:  # CONTINUATION
            result = await self._handle_continuation(state, message, context)
        
        # 5. Add assistant response to history
        state.add_message(Message.assistant(result.response))
        
        # 6. Save state
        await self.store.save(state)
        
        return result
    
    async def _handle_cancellation(self, state: ConversationState) -> ProcessResult:
        """Handle task cancellation"""
        had_task = state.task.is_active()
        state.reset_task()
        
        if had_task:
            response = "Đã hủy. Bạn cần gì khác không?"
        else:
            response = "Không có gì để hủy. Bạn cần giúp gì?"
        
        return ProcessResult(response=response, state=state)
    
    async def _handle_confirmation(self, state: ConversationState) -> ProcessResult:
        """Handle task confirmation"""
        if state.task.state != TaskState.CONFIRMING:
            return ProcessResult(
                response="Không có gì để xác nhận.",
                state=state
            )
        
        # Execute the action
        action = {
            "type": state.task.intent,
            "data": state.task.entities,
            "confirmation_data": state.task.confirmation_data
        }
        
        # Mark as executed
        state.task.state = TaskState.EXECUTED
        
        # Generate response
        response = self._generate_execution_response(state.task.intent, state.task.entities)
        
        # Reset for next task
        state.reset_task()
        
        return ProcessResult(
            response=response,
            state=state,
            action=action
        )
    
    async def _handle_correction(
        self, 
        state: ConversationState, 
        message: str,
        field: Optional[str]
    ) -> ProcessResult:
        """Handle correction of existing data"""
        if not state.task.is_active():
            return ProcessResult(
                response="Không có thông tin nào để sửa. Bạn muốn bắt đầu task mới?",
                state=state
            )
        
        # Extract the correction from message
        # Use entity extractor focused on the specific field
        extracted = await self.entity_extractor.extract(
            message=message,
            intent=state.task.intent,
            context={"focus_field": field}
        )
        
        if not extracted.entities:
            return ProcessResult(
                response="Tôi không hiểu bạn muốn sửa gì. Vui lòng nói rõ hơn.",
                state=state
            )
        
        # Apply correction
        result = self.accumulator.accumulate(state.task, extracted.entities)
        
        # Update task
        state.task.entities = result.entities
        state.task.missing_fields = result.missing_fields
        
        # Generate response
        if result.is_complete:
            state.task.state = TaskState.CONFIRMING
            state.task.confirmation_data = result.entities
            response = self._generate_confirmation_request(state.task)
        else:
            response = f"Đã cập nhật.\n\n"
            response += self.accumulator.get_summary(state.task)
            if result.missing_fields:
                response += f"\n\n{self.accumulator.get_missing_fields_message(state.task.intent, result.missing_fields)}"
        
        return ProcessResult(
            response=response,
            state=state,
            needs_confirmation=result.is_complete,
            confirmation_data=result.entities if result.is_complete else None
        )
    
    async def _handle_reference(
        self, 
        state: ConversationState, 
        message: str
    ) -> ProcessResult:
        """Handle reference to past job/booking"""
        # Extract job reference
        # Could be: "giống job hôm qua", "như booking 2501001", etc.
        
        # For now, simple implementation
        # TODO: Load referenced job and use as template
        
        return ProcessResult(
            response="Tính năng tham chiếu job cũ đang được phát triển. Vui lòng nhập thông tin booking mới.",
            state=state
        )
    
    async def _handle_new_task(
        self,
        state: ConversationState,
        message: str,
        detected_intent: Optional[str],
        context: Optional[Dict]
    ) -> ProcessResult:
        """Handle new task"""
        # Reset any previous task
        state.reset_task()
        
        # Classify intent if not detected
        if not detected_intent:
            intent_result = await self.intent_classifier.classify(message, context)
            detected_intent = intent_result.intent
        
        # Extract entities
        extracted = await self.entity_extractor.extract(
            message=message,
            intent=detected_intent,
            context=context
        )
        
        # Start new task
        state.task.start_task(detected_intent, extracted.entities)
        
        # Accumulate and check completeness
        result = self.accumulator.accumulate(state.task, {})  # Already have entities
        state.task.missing_fields = result.missing_fields
        
        # Generate response
        if result.is_complete:
            state.task.state = TaskState.CONFIRMING
            state.task.confirmation_data = state.task.entities
            response = self._generate_confirmation_request(state.task)
            needs_confirmation = True
        else:
            response = f"Đã nhận thông tin:\n\n"
            response += self.accumulator.get_summary(state.task)
            response += f"\n\n{self.accumulator.get_missing_fields_message(state.task.intent, result.missing_fields)}"
            needs_confirmation = False
        
        return ProcessResult(
            response=response,
            state=state,
            needs_confirmation=needs_confirmation,
            confirmation_data=state.task.entities if needs_confirmation else None
        )
    
    async def _handle_continuation(
        self,
        state: ConversationState,
        message: str,
        context: Optional[Dict]
    ) -> ProcessResult:
        """Handle continuation of current task"""
        if not state.task.is_active():
            # No active task, treat as new
            return await self._handle_new_task(state, message, None, context)
        
        # Extract new entities
        extracted = await self.entity_extractor.extract(
            message=message,
            intent=state.task.intent,
            context=context
        )
        
        # Accumulate
        result = self.accumulator.accumulate(state.task, extracted.entities)
        
        # Update task
        state.task.entities = result.entities
        state.task.missing_fields = result.missing_fields
        
        # Generate response
        if result.is_complete:
            state.task.state = TaskState.CONFIRMING
            state.task.confirmation_data = result.entities
            response = self._generate_confirmation_request(state.task)
            needs_confirmation = True
        else:
            # Acknowledge changes
            if result.changes:
                response = "Đã cập nhật: " + ", ".join(result.changes) + "\n\n"
            else:
                response = ""
            
            response += self.accumulator.get_summary(state.task)
            
            if result.missing_fields:
                response += f"\n\n{self.accumulator.get_missing_fields_message(state.task.intent, result.missing_fields)}"
            
            needs_confirmation = False
        
        return ProcessResult(
            response=response,
            state=state,
            needs_confirmation=needs_confirmation,
            confirmation_data=result.entities if needs_confirmation else None
        )
    
    def _generate_confirmation_request(self, task: TaskContext) -> str:
        """Generate confirmation request message"""
        summary = self.accumulator.get_summary(task)
        
        intent_names = {
            "create_booking": "tạo booking",
            "update_job": "cập nhật job",
            "assign_vehicle": "gán xe",
            "cancel_job": "hủy job",
        }
        
        action = intent_names.get(task.intent, task.intent)
        
        return f"""✅ Đã đủ thông tin để {action}:

{summary}

Xác nhận thực hiện? (Gõ "ok" để xác nhận hoặc sửa thông tin)"""
    
    def _generate_execution_response(
        self, 
        intent: str, 
        entities: Dict[str, Any]
    ) -> str:
        """Generate response after execution"""
        if intent == "create_booking":
            return f"""🎉 Đã tạo booking thành công!

• Khách hàng: {entities.get('customer_code')}
• Ngày: {entities.get('date')}
• Giờ: {entities.get('time', 'Chưa xác định')}
• Giao tại: {entities.get('destination')}
• Loại xe: {entities.get('vehicle_type', 'Chưa xác định')}

Bạn cần gì khác không?"""
        
        elif intent == "assign_vehicle":
            return f"""✅ Đã gán xe thành công!

• Job: {entities.get('job_id')}
• Biển số: {entities.get('license_plate')}
• Tài xế: {entities.get('driver_name', 'Chưa có')}

Bạn cần gì khác không?"""
        
        else:
            return f"✅ Đã thực hiện {intent} thành công!"
    
    async def get_session_stats(self) -> Dict:
        """Get session statistics"""
        if hasattr(self.store, 'get_stats'):
            return self.store.get_stats()
        return {}
```

### 3.6 File: `__init__.py`

```python
# backend/app/ai/memory/__init__.py

from .conversation_state import (
    ConversationState,
    TaskContext,
    TaskState,
    ContinuationType,
    Message
)
from .session_store import (
    SessionStore,
    InMemorySessionStore,
    RedisSessionStore
)
from .continuation_detector import ContinuationDetector
from .entity_accumulator import EntityAccumulator, AccumulationResult
from .conversation_manager import ConversationManager, ProcessResult

__all__ = [
    # State
    'ConversationState',
    'TaskContext',
    'TaskState',
    'ContinuationType',
    'Message',
    
    # Storage
    'SessionStore',
    'InMemorySessionStore',
    'RedisSessionStore',
    
    # Detection
    'ContinuationDetector',
    
    # Accumulation
    'EntityAccumulator',
    'AccumulationResult',
    
    # Manager
    'ConversationManager',
    'ProcessResult',
]
```

---

## 4. FILES CẦN TẠO

### 4.1 Directory Structure

```
backend/app/ai/memory/
├── __init__.py
├── conversation_state.py     # State models (ConversationState, TaskContext, Message)
├── session_store.py          # Session storage (InMemory, Redis)
├── continuation_detector.py  # Detect continuation type
├── entity_accumulator.py     # Accumulate entities across turns
└── conversation_manager.py   # Main manager orchestrating everything

backend/app/api/v1/endpoints/
└── chat.py                   # Updated chat endpoint with session support

frontend/src/
├── contexts/
│   └── ChatSessionContext.tsx    # React context for session management
├── hooks/
│   └── useChatSession.ts         # Hook for chat with memory
└── components/
    └── chat/
        ├── ChatWindow.tsx        # Updated with session support
        └── ConfirmationCard.tsx  # UI for confirmations
```

### 4.2 Summary of Files

| # | File | Lines | Chức năng |
|---|------|-------|-----------|
| 1 | `conversation_state.py` | ~250 | State models, serialization |
| 2 | `session_store.py` | ~150 | InMemory + Redis storage |
| 3 | `continuation_detector.py` | ~200 | Detect message type (new/continue/correct/confirm) |
| 4 | `entity_accumulator.py` | ~200 | Merge entities, track missing fields |
| 5 | `conversation_manager.py` | ~350 | Main orchestrator |
| 6 | `__init__.py` | ~40 | Exports |

---

## 5. HƯỚNG DẪN TỪNG BƯỚC

### 5.1 Task List

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION TASKS                                          │
│                                                                                  │
│   ☐ Task 3.1: Tạo directory structure và __init__.py                           │
│                                                                                  │
│   ☐ Task 3.2: Implement conversation_state.py                                  │
│      • ConversationState class                                                  │
│      • TaskContext class                                                        │
│      • Message class                                                            │
│      • Serialization (to_dict, from_dict)                                      │
│                                                                                  │
│   ☐ Task 3.3: Implement session_store.py                                       │
│      • InMemorySessionStore                                                     │
│      • RedisSessionStore (optional)                                             │
│      • TTL management                                                           │
│                                                                                  │
│   ☐ Task 3.4: Implement continuation_detector.py                               │
│      • Rule-based detection                                                     │
│      • AI-based detection (optional enhancement)                                │
│      • Handle all continuation types                                            │
│                                                                                  │
│   ☐ Task 3.5: Implement entity_accumulator.py                                  │
│      • Merge entities                                                           │
│      • Track missing fields                                                     │
│      • Generate messages for missing fields                                     │
│      • Validation                                                               │
│                                                                                  │
│   ☐ Task 3.6: Implement conversation_manager.py                                │
│      • Main process() method                                                    │
│      • Handle all continuation types                                            │
│      • Generate contextual responses                                            │
│      • Integration with IntentClassifier, EntityExtractor                      │
│                                                                                  │
│   ☐ Task 3.7: Update chat API endpoint                                         │
│      • Add session_id parameter                                                 │
│      • Return session info                                                      │
│      • Handle confirmation actions                                              │
│                                                                                  │
│   ☐ Task 3.8: Update frontend                                                  │
│      • Session management                                                       │
│      • Confirmation UI                                                          │
│      • State indicators                                                         │
│                                                                                  │
│   ☐ Task 3.9: Integration testing                                              │
│      • Multi-turn scenarios                                                     │
│      • Correction scenarios                                                     │
│      • Timeout/cleanup                                                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Step-by-Step Guide

#### Step 1: Setup Directory

```bash
mkdir -p backend/app/ai/memory
touch backend/app/ai/memory/__init__.py
```

#### Step 2: Implement theo thứ tự

1. `conversation_state.py` - Không dependency
2. `session_store.py` - Cần conversation_state
3. `continuation_detector.py` - Cần conversation_state
4. `entity_accumulator.py` - Cần conversation_state
5. `conversation_manager.py` - Cần tất cả + pipeline components

#### Step 3: Integration với existing pipeline

```python
# Update app/ai/pipeline/__init__.py

from app.ai.memory import ConversationManager

# ConversationManager wraps the entire pipeline
```

---

## 6. TEST CASES

### 6.1 Unit Tests

```python
# tests/test_conversation_memory.py

import pytest
from datetime import datetime
from app.ai.memory import (
    ConversationState,
    TaskContext,
    TaskState,
    ContinuationType,
    ContinuationDetector,
    EntityAccumulator
)


class TestConversationState:
    """Test conversation state management"""
    
    def test_create_state(self):
        state = ConversationState(session_id="test-123")
        assert state.session_id == "test-123"
        assert state.task.state == TaskState.IDLE
    
    def test_add_message(self):
        state = ConversationState(session_id="test-123")
        state.add_message(Message.user("Hello"))
        state.add_message(Message.assistant("Hi!"))
        
        assert len(state.messages) == 2
        assert state.messages[0].role == "user"
        assert state.messages[1].role == "assistant"
    
    def test_message_history_limit(self):
        state = ConversationState(session_id="test-123", max_history=5)
        
        for i in range(10):
            state.add_message(Message.user(f"Message {i}"))
        
        assert len(state.messages) == 5
        assert "Message 5" in state.messages[0].content
    
    def test_serialization(self):
        state = ConversationState(session_id="test-123")
        state.task.start_task("create_booking", {"customer_code": "DRT1"})
        
        data = state.to_dict()
        restored = ConversationState.from_dict(data)
        
        assert restored.session_id == state.session_id
        assert restored.task.intent == state.task.intent
        assert restored.task.entities == state.task.entities


class TestContinuationDetector:
    """Test continuation detection"""
    
    def setup_method(self):
        self.detector = ContinuationDetector()
    
    def test_detect_new_task(self):
        state = ConversationState(session_id="test")
        cont_type, intent = self.detector.detect(state, "Đặt xe cho DRT1 ngày mai")
        
        assert cont_type == ContinuationType.NEW_TASK
        assert intent == "create_booking"
    
    def test_detect_continuation(self):
        state = ConversationState(session_id="test")
        state.task.start_task("create_booking", {"customer_code": "DRT1"})
        
        cont_type, _ = self.detector.detect(state, "Xe 5 tấn")
        
        assert cont_type == ContinuationType.CONTINUATION
    
    def test_detect_cancellation(self):
        state = ConversationState(session_id="test")
        state.task.start_task("create_booking", {})
        
        cont_type, _ = self.detector.detect(state, "Thôi hủy đi")
        
        assert cont_type == ContinuationType.CANCELLATION
    
    def test_detect_confirmation(self):
        state = ConversationState(session_id="test")
        state.task.start_task("create_booking", {})
        state.task.state = TaskState.CONFIRMING
        
        cont_type, _ = self.detector.detect(state, "Ok")
        
        assert cont_type == ContinuationType.CONFIRMATION
    
    def test_detect_correction(self):
        state = ConversationState(session_id="test")
        state.task.start_task("create_booking", {"destination": "HP"})
        
        cont_type, field = self.detector.detect(state, "Sửa lại đi Quảng Ninh")
        
        assert cont_type == ContinuationType.CORRECTION


class TestEntityAccumulator:
    """Test entity accumulation"""
    
    def setup_method(self):
        self.accumulator = EntityAccumulator()
    
    def test_accumulate_entities(self):
        task = TaskContext()
        task.start_task("create_booking", {"customer_code": "DRT1"})
        
        result = self.accumulator.accumulate(
            task,
            {"date": "2026-01-18", "destination": "HP"}
        )
        
        assert "customer_code" in result.entities
        assert "date" in result.entities
        assert "destination" in result.entities
        assert result.is_complete
    
    def test_missing_fields(self):
        task = TaskContext()
        task.start_task("create_booking", {"customer_code": "DRT1"})
        
        result = self.accumulator.accumulate(task, {})
        
        assert "date" in result.missing_fields
        assert "destination" in result.missing_fields
        assert not result.is_complete
    
    def test_correction(self):
        task = TaskContext()
        task.start_task("create_booking", {
            "customer_code": "DRT1",
            "date": "2026-01-18",
            "destination": "HP"
        })
        
        result = self.accumulator.correct_entity(task, "destination", "QN")
        
        assert result.entities["destination"] == "QN"
        assert "destination" in result.changes
```

### 6.2 Integration Tests

```python
# tests/test_conversation_integration.py

import pytest
from app.ai.memory import ConversationManager


class TestConversationFlow:
    """Integration tests for full conversation flow"""
    
    @pytest.fixture
    def manager(self, ai_client, db_session):
        return ConversationManager(ai_client, db_session=db_session)
    
    @pytest.mark.asyncio
    async def test_multi_turn_booking(self, manager):
        """Test multi-turn booking creation"""
        session_id = "test-multi-turn"
        
        # Turn 1: Start booking
        result1 = await manager.process(session_id, "Đặt xe cho DRT1")
        assert "DRT1" in result1.response
        assert result1.needs_confirmation is False
        
        # Turn 2: Add date
        result2 = await manager.process(session_id, "Ngày mai đi Hải Phòng")
        assert "ngày" in result2.response.lower() or "Hải Phòng" in result2.response
        
        # Turn 3: Should be complete and ask for confirmation
        # (if vehicle_type is optional)
        # or ask for vehicle_type
    
    @pytest.mark.asyncio
    async def test_correction_flow(self, manager):
        """Test correction during conversation"""
        session_id = "test-correction"
        
        # Turn 1: Start with destination
        result1 = await manager.process(
            session_id, 
            "Đặt xe cho DRT1 ngày mai đi Hải Phòng"
        )
        
        # Turn 2: Correct destination
        result2 = await manager.process(
            session_id,
            "Sửa lại, đi Quảng Ninh không phải Hải Phòng"
        )
        
        assert "Quảng Ninh" in result2.response or "QN" in result2.response
    
    @pytest.mark.asyncio
    async def test_cancellation(self, manager):
        """Test task cancellation"""
        session_id = "test-cancel"
        
        # Start a task
        await manager.process(session_id, "Đặt xe cho DRT1")
        
        # Cancel it
        result = await manager.process(session_id, "Thôi bỏ đi")
        
        assert "hủy" in result.response.lower()
        
        # State should be reset
        state = await manager.store.get(session_id)
        assert state.task.state == TaskState.IDLE
    
    @pytest.mark.asyncio
    async def test_session_expiry(self, manager):
        """Test session timeout"""
        session_id = "test-expiry"
        
        # Create session
        state = await manager.store.get_or_create(session_id)
        
        # Manually expire it
        from datetime import timedelta
        state.last_activity = datetime.now() - timedelta(hours=1)
        await manager.store.save(state)
        
        # Should create new session
        new_state = await manager.store.get_or_create(session_id)
        assert new_state.created_at > state.created_at
```

---

## 7. INTEGRATION VỚI HỆ THỐNG HIỆN TẠI

### 7.1 Updated Chat API

```python
# backend/app/api/v1/endpoints/chat.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.ai.clients import get_ai_client
from app.ai.memory import ConversationManager, ProcessResult
from app.core.auth import get_current_user
from app.models import User


router = APIRouter(prefix="/chat", tags=["Chat"])

# Global manager instance (or use dependency injection)
_manager: Optional[ConversationManager] = None


def get_conversation_manager(db: Session = Depends(get_db)):
    global _manager
    if _manager is None:
        _manager = ConversationManager(
            ai_client=get_ai_client(),
            db_session=db
        )
    return _manager


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    needs_confirmation: bool = False
    confirmation_data: Optional[dict] = None
    task_state: Optional[str] = None
    accumulated_entities: Optional[dict] = None


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Send a chat message with conversation memory
    """
    # Generate session_id if not provided
    session_id = request.session_id or f"session-{current_user.id}-{uuid.uuid4().hex[:8]}"
    
    try:
        result = await manager.process(
            session_id=session_id,
            message=request.message,
            user_id=str(current_user.id)
        )
        
        return ChatResponse(
            response=result.response,
            session_id=session_id,
            needs_confirmation=result.needs_confirmation,
            confirmation_data=result.confirmation_data,
            task_state=result.state.task.state.value,
            accumulated_entities=result.state.task.entities if result.state.task.is_active() else None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm/{session_id}")
async def confirm_action(
    session_id: str,
    current_user: User = Depends(get_current_user),
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Confirm pending action in a session
    """
    result = await manager.process(
        session_id=session_id,
        message="ok",  # Confirmation trigger
        user_id=str(current_user.id)
    )
    
    return {
        "response": result.response,
        "action_executed": result.action is not None,
        "action": result.action
    }


@router.post("/cancel/{session_id}")
async def cancel_task(
    session_id: str,
    current_user: User = Depends(get_current_user),
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Cancel current task in a session
    """
    result = await manager.process(
        session_id=session_id,
        message="hủy",  # Cancellation trigger
        user_id=str(current_user.id)
    )
    
    return {
        "response": result.response,
        "cancelled": True
    }


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    current_user: User = Depends(get_current_user),
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Get current session state
    """
    state = await manager.store.get(session_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "task_state": state.task.state.value,
        "intent": state.task.intent,
        "entities": state.task.entities,
        "missing_fields": state.task.missing_fields,
        "message_count": len(state.messages),
        "created_at": state.created_at.isoformat(),
        "last_activity": state.last_activity.isoformat()
    }
```

### 7.2 Frontend Integration

```typescript
// frontend/src/hooks/useChatSession.ts

import { useState, useCallback, useRef } from 'react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface TaskState {
  state: string;
  intent: string | null;
  entities: Record<string, any>;
  missingFields: string[];
}

interface UseChatSessionReturn {
  messages: ChatMessage[];
  taskState: TaskState | null;
  needsConfirmation: boolean;
  confirmationData: Record<string, any> | null;
  isLoading: boolean;
  sendMessage: (message: string) => Promise<void>;
  confirmAction: () => Promise<void>;
  cancelTask: () => Promise<void>;
  resetSession: () => void;
}

export function useChatSession(): UseChatSessionReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [taskState, setTaskState] = useState<TaskState | null>(null);
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [confirmationData, setConfirmationData] = useState<Record<string, any> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const sessionIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(async (message: string) => {
    setIsLoading(true);
    
    // Add user message immediately
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    
    try {
      const response = await fetch('/api/v1/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: sessionIdRef.current
        })
      });
      
      const data = await response.json();
      
      // Save session ID
      sessionIdRef.current = data.session_id;
      
      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
      
      // Update state
      setNeedsConfirmation(data.needs_confirmation);
      setConfirmationData(data.confirmation_data);
      
      if (data.task_state) {
        setTaskState({
          state: data.task_state,
          intent: data.accumulated_entities ? 'active' : null,
          entities: data.accumulated_entities || {},
          missingFields: []
        });
      }
      
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const confirmAction = useCallback(async () => {
    if (!sessionIdRef.current) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/chat/confirm/${sessionIdRef.current}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      // Add confirmation response
      const message: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, message]);
      
      // Reset confirmation state
      setNeedsConfirmation(false);
      setConfirmationData(null);
      setTaskState(null);
      
    } catch (error) {
      console.error('Confirm error:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const cancelTask = useCallback(async () => {
    if (!sessionIdRef.current) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/chat/cancel/${sessionIdRef.current}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      // Add cancellation response
      const message: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, message]);
      
      // Reset state
      setNeedsConfirmation(false);
      setConfirmationData(null);
      setTaskState(null);
      
    } catch (error) {
      console.error('Cancel error:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const resetSession = useCallback(() => {
    sessionIdRef.current = null;
    setMessages([]);
    setTaskState(null);
    setNeedsConfirmation(false);
    setConfirmationData(null);
  }, []);

  return {
    messages,
    taskState,
    needsConfirmation,
    confirmationData,
    isLoading,
    sendMessage,
    confirmAction,
    cancelTask,
    resetSession
  };
}
```

### 7.3 Confirmation UI Component

```tsx
// frontend/src/components/chat/ConfirmationCard.tsx

import React from 'react';
import { Check, X, Edit } from 'lucide-react';

interface ConfirmationCardProps {
  data: Record<string, any>;
  onConfirm: () => void;
  onCancel: () => void;
  onEdit?: (field: string) => void;
}

const FIELD_LABELS: Record<string, string> = {
  customer_code: 'Khách hàng',
  date: 'Ngày',
  time: 'Giờ',
  destination: 'Giao tại',
  origin: 'Lấy tại',
  vehicle_type: 'Loại xe',
  cargo: 'Hàng hóa',
  quantity: 'Số lượng',
  notes: 'Ghi chú'
};

export const ConfirmationCard: React.FC<ConfirmationCardProps> = ({
  data,
  onConfirm,
  onCancel,
  onEdit
}) => {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 my-2">
      <h4 className="font-semibold text-blue-800 mb-3">
        ✅ Xác nhận thông tin
      </h4>
      
      <div className="space-y-2 mb-4">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between">
            <span className="text-gray-600">
              {FIELD_LABELS[key] || key}:
            </span>
            <div className="flex items-center gap-2">
              <span className="font-medium">{String(value)}</span>
              {onEdit && (
                <button
                  onClick={() => onEdit(key)}
                  className="text-gray-400 hover:text-blue-600"
                >
                  <Edit className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="flex gap-2">
        <button
          onClick={onConfirm}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          <Check className="h-4 w-4" />
          Xác nhận
        </button>
        <button
          onClick={onCancel}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
        >
          <X className="h-4 w-4" />
          Hủy
        </button>
      </div>
    </div>
  );
};
```

---

## 8. SUMMARY

### Các điểm chính của Giải pháp 3:

1. **Session-based Memory**: Mỗi conversation có state riêng, lưu trữ trong memory hoặc Redis
2. **Multi-turn Support**: Tích lũy entities qua nhiều turns cho đến khi đủ thông tin
3. **Continuation Detection**: Tự động phát hiện loại message (new/continue/correct/confirm/cancel)
4. **Entity Accumulation**: Merge entities thông minh, track missing fields
5. **Confirmation Flow**: Yêu cầu xác nhận trước khi thực hiện action
6. **State Machine**: Quản lý trạng thái task rõ ràng (IDLE → COLLECTING → CONFIRMING → EXECUTED)

### Timeline Implementation:

- **Tuần 1**: conversation_state.py + session_store.py
- **Tuần 2**: continuation_detector.py + entity_accumulator.py
- **Tuần 3**: conversation_manager.py + API integration
- **Tuần 4**: Frontend components + Testing

### Dependencies:

- Cần có sẵn: `IntentClassifier`, `EntityExtractor` từ Pipeline (Giải pháp 1)
- Optional: Redis cho production session storage

---

**Tài liệu tiếp theo:**
- GIẢI PHÁP 4: Smart Fallback & Clarification
