# -*- coding: utf-8 -*-
"""
football.services.match_store - Bộ lưu trữ trạng thái trận đấu live phía server (RAM + /tmp JSON fallback cho Vercel).
Giải quyết hoàn toàn lỗi tràn cookie 4KB của Flask session và giữ trạng thái ổn định trên môi trường Serverless.
"""
import json
import os
import tempfile
import threading
import time
import uuid


class LiveMatchStore:
    """Lưu trữ state trận đấu đang diễn ra theo match_id trong RAM kèm file dự phòng trong /tmp."""

    def __init__(self, ttl_seconds=7200):
        self._lock = threading.Lock()
        self._matches = {}
        self._timestamps = {}
        self._ttl = ttl_seconds
        self._dir = os.path.join(tempfile.gettempdir(), 'fm_live_matches')
        try:
            os.makedirs(self._dir, exist_ok=True)
        except Exception:
            self._dir = None

    def _file_path(self, match_id):
        if not self._dir or not match_id or not str(match_id).isalnum():
            return None
        return os.path.join(self._dir, f"{match_id}.json")

    def _write_disk(self, match_id, match_state):
        fp = self._file_path(match_id)
        if not fp:
            return
        try:
            with open(fp, 'w', encoding='utf-8') as f:
                json.dump(match_state, f, ensure_ascii=False)
        except Exception:
            pass

    def _read_disk(self, match_id):
        fp = self._file_path(match_id)
        if not fp or not os.path.exists(fp):
            return None
        try:
            if time.time() - os.path.getmtime(fp) > self._ttl:
                os.remove(fp)
                return None
            with open(fp, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

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
            self._write_disk(match_id, match_state)
            return match_id

    def get(self, match_id):
        if not match_id:
            return None
        with self._lock:
            state = self._matches.get(match_id)
            if state is None:
                state = self._read_disk(match_id)
                if state is not None:
                    self._matches[match_id] = state
            if state is not None:
                self._timestamps[match_id] = time.time()
            return state

    def save(self, match_id, match_state):
        if not match_id:
            return
        with self._lock:
            self._matches[match_id] = match_state
            self._timestamps[match_id] = time.time()
            self._write_disk(match_id, match_state)

    def delete(self, match_id):
        if not match_id:
            return
        with self._lock:
            self._matches.pop(match_id, None)
            self._timestamps.pop(match_id, None)
            fp = self._file_path(match_id)
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass


match_store = LiveMatchStore()
