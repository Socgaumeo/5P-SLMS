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
    awaiting_field: Optional[str] = None  # Field đang chờ input (e.g., "customer_code")

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
        self.awaiting_field = None
    
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
