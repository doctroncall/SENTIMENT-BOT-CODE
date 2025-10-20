"""
Status Monitor - Real-time Application Event Tracking
Tracks all data fetches, operations, failures, and successes
"""

from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
import threading


class EventType(Enum):
    """Types of events to track"""
    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    DATA_FETCH = "📊"
    ANALYSIS = "🔍"
    CONNECTION = "🔌"
    CACHE = "💾"


class StatusEvent:
    """Represents a single status event"""
    def __init__(self, event_type: EventType, message: str, details: Optional[str] = None):
        self.timestamp = datetime.now()
        self.event_type = event_type
        self.message = message
        self.details = details
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.strftime('%H:%M:%S.%f')[:-3],
            'type': self.event_type.value,
            'message': self.message,
            'details': self.details or ""
        }
    
    def __str__(self) -> str:
        time_str = self.timestamp.strftime('%H:%M:%S')
        return f"[{time_str}] {self.event_type.value} {self.message}"


class StatusMonitor:
    """
    Centralized status monitoring system
    Thread-safe singleton for tracking application events
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.events: List[StatusEvent] = []
        self.max_events = 500  # Keep last 500 events
        self.stats = {
            'total_events': 0,
            'successes': 0,
            'failures': 0,
            'warnings': 0,
            'data_fetches': 0,
            'analyses': 0
        }
        self._event_lock = threading.Lock()
        self.log_event(EventType.INFO, "Status Monitor initialized")
    
    def log_event(self, event_type: EventType, message: str, details: Optional[str] = None):
        """Log a new event"""
        with self._event_lock:
            event = StatusEvent(event_type, message, details)
            self.events.append(event)
            
            # Update stats
            self.stats['total_events'] += 1
            if event_type == EventType.SUCCESS:
                self.stats['successes'] += 1
            elif event_type == EventType.ERROR:
                self.stats['failures'] += 1
            elif event_type == EventType.WARNING:
                self.stats['warnings'] += 1
            elif event_type == EventType.DATA_FETCH:
                self.stats['data_fetches'] += 1
            elif event_type == EventType.ANALYSIS:
                self.stats['analyses'] += 1
            
            # Trim old events if needed
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]
    
    def log_info(self, message: str, details: Optional[str] = None):
        """Log an info event"""
        self.log_event(EventType.INFO, message, details)
    
    def log_success(self, message: str, details: Optional[str] = None):
        """Log a success event"""
        self.log_event(EventType.SUCCESS, message, details)
    
    def log_warning(self, message: str, details: Optional[str] = None):
        """Log a warning event"""
        self.log_event(EventType.WARNING, message, details)
    
    def log_error(self, message: str, details: Optional[str] = None):
        """Log an error event"""
        self.log_event(EventType.ERROR, message, details)
    
    def log_data_fetch(self, message: str, details: Optional[str] = None):
        """Log a data fetch event"""
        self.log_event(EventType.DATA_FETCH, message, details)
    
    def log_analysis(self, message: str, details: Optional[str] = None):
        """Log an analysis event"""
        self.log_event(EventType.ANALYSIS, message, details)
    
    def log_connection(self, message: str, details: Optional[str] = None):
        """Log a connection event"""
        self.log_event(EventType.CONNECTION, message, details)
    
    def log_cache(self, message: str, details: Optional[str] = None):
        """Log a cache event"""
        self.log_event(EventType.CACHE, message, details)
    
    def get_recent_events(self, count: int = 100) -> List[Dict]:
        """Get recent events as dictionaries"""
        with self._event_lock:
            recent = self.events[-count:] if len(self.events) > count else self.events
            return [event.to_dict() for event in reversed(recent)]
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        with self._event_lock:
            return self.stats.copy()
    
    def clear(self):
        """Clear all events and reset stats"""
        with self._event_lock:
            self.events.clear()
            self.stats = {
                'total_events': 0,
                'successes': 0,
                'failures': 0,
                'warnings': 0,
                'data_fetches': 0,
                'analyses': 0
            }
            self.log_event(EventType.CACHE, "Status Monitor cleared")
    
    def get_filtered_events(self, event_type: Optional[EventType] = None, 
                           count: int = 100) -> List[Dict]:
        """Get filtered events by type"""
        with self._event_lock:
            if event_type is None:
                return self.get_recent_events(count)
            
            filtered = [e for e in self.events if e.event_type == event_type]
            recent = filtered[-count:] if len(filtered) > count else filtered
            return [event.to_dict() for event in reversed(recent)]


# Global instance
_monitor = StatusMonitor()


def get_monitor() -> StatusMonitor:
    """Get the global status monitor instance"""
    return _monitor


# Convenience functions
def log_info(message: str, details: Optional[str] = None):
    get_monitor().log_info(message, details)


def log_success(message: str, details: Optional[str] = None):
    get_monitor().log_success(message, details)


def log_warning(message: str, details: Optional[str] = None):
    get_monitor().log_warning(message, details)


def log_error(message: str, details: Optional[str] = None):
    get_monitor().log_error(message, details)


def log_data_fetch(message: str, details: Optional[str] = None):
    get_monitor().log_data_fetch(message, details)


def log_analysis(message: str, details: Optional[str] = None):
    get_monitor().log_analysis(message, details)


def log_connection(message: str, details: Optional[str] = None):
    get_monitor().log_connection(message, details)


def log_cache(message: str, details: Optional[str] = None):
    get_monitor().log_cache(message, details)
