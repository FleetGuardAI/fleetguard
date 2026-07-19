"""
Fleet Intelligence Engine - Event Correlator
"""

import time
from typing import List, Dict
from infrastructure.intelligence.event_processing.models import BaseOperationalEvent


class EventCorrelator:
    """
    Correlates asynchronous raw operational events into cohesive transaction windows.
    
    This implementation buffers events in memory based on `correlation_id`.
    It uses a configurable time window to determine when a transaction group
    is "complete" and ready for processing.
    
    Note: Future implementations may use Redis, Kafka windows, and support 
    advanced correlation strategies (e.g. spatial proximity, vehicle identity).
    """
    
    def __init__(self, window_seconds: float = 5.0):
        self.window_seconds = window_seconds
        # dict of correlation_id -> list of events
        self._buffer: Dict[str, List[BaseOperationalEvent]] = {}
        # dict of correlation_id -> float (timestamp of first event seen)
        self._first_seen: Dict[str, float] = {}
        # dict of correlation_id -> float (timestamp of last event seen)
        self._last_seen: Dict[str, float] = {}

    def add_event(self, event: BaseOperationalEvent):
        """
        Ingests a new raw event into the correlator buffer.
        """
        cid = event.correlation_id
        now = time.perf_counter()
        
        if cid not in self._buffer:
            self._buffer[cid] = []
            self._first_seen[cid] = now
            
        # Optional deduplication based on event_id could occur here
        # For this milestone we just append.
        self._buffer[cid].append(event)
        self._last_seen[cid] = now

    def get_ready_transactions(self) -> List[List[BaseOperationalEvent]]:
        """
        Evaluates the buffer and extracts grouped events that have exceeded the time window.
        Returns a list of transactions, where each transaction is a list of correlated events.
        """
        now = time.perf_counter()
        ready_cids = []
        
        for cid, last_seen_time in self._last_seen.items():
            if (now - last_seen_time) >= self.window_seconds:
                ready_cids.append(cid)
                
        transactions = []
        for cid in ready_cids:
            transactions.append(self._buffer[cid])
            del self._buffer[cid]
            del self._first_seen[cid]
            del self._last_seen[cid]
            
        return transactions

    def clear(self):
        """Clears all buffered events."""
        self._buffer.clear()
        self._first_seen.clear()
        self._last_seen.clear()
