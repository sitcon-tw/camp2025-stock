"""
Infrastructure Events Module
"""
from .publisher import InMemoryEventPublisher, EventHandler, EventPriority, EventEnvelope

# Import InMemoryEventBus from the events.py file to resolve import conflict
import importlib.util
import os

# Get the parent directory (infrastructure)
parent_dir = os.path.dirname(os.path.dirname(__file__))
events_file = os.path.join(parent_dir, "events.py")

try:
    spec = importlib.util.spec_from_file_location("events_module", events_file)
    events_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(events_module)
    InMemoryEventBus = events_module.InMemoryEventBus
except Exception:
    # Fallback: create a dummy class to prevent import errors
    class InMemoryEventBus:
        pass

__all__ = [
    'InMemoryEventPublisher',
    'EventHandler', 
    'EventPriority',
    'EventEnvelope',
    'InMemoryEventBus'
]