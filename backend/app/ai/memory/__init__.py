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
