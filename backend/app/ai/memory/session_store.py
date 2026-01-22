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
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
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
