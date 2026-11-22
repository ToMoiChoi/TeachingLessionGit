# -*- coding: utf-8 -*-
"""
football.services.match_store - Bộ lưu trữ trạng thái trận đấu live phía server.
Giải quyết hoàn toàn lỗi tràn cookie 4KB của Flask session khi trận đấu có nhiều sự kiện.
"""
import time
import uuid
import threading


class LiveMatchStore:
    """Lưu trữ state trận đấu đang diễn ra theo match_id trong RAM (có TTL dọn dẹp tự động)."""

    def __init__(self, ttl_seconds=7200):
        self._lock = threading.Lock()
        self._matches = {}
        self._timestamps = {}
        self._ttl = ttl_seconds

    def _cleanup_expired(self):
        now = time.time()
        expired = [mid for mid, ts in self._timestamps.items() if now - ts > self._ttl]
        for mid in expired:
            self._matches.pop(mid, None)
            self._timestamps.pop(mid, None)

    def create(self, match_state):
        with self._lock:
            self._cleanup_expired()
            match_id = uuid.uuid4().hex
            self._matches[match_id] = match_state
            self._timestamps[match_id] = time.time()
            return match_id

    def get(self, match_id):
        if not match_id:
            return None
        with self._lock:
            state = self._matches.get(match_id)
            if state is not None:
                self._timestamps[match_id] = time.time()
            return state

    def save(self, match_id, match_state):
        if not match_id:
            return
        with self._lock:
            self._matches[match_id] = match_state
            self._timestamps[match_id] = time.time()

    def delete(self, match_id):
        if not match_id:
            return
        with self._lock:
            self._matches.pop(match_id, None)
            self._timestamps.pop(match_id, None)


match_store = LiveMatchStore()
