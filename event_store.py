"""Simple in-memory event store for resumability."""
import logging
from collections import deque
from dataclasses import dataclass
from uuid import uuid4
from mcp.server.streamable_http import EventCallback, EventId, EventMessage, EventStore, StreamId
from mcp.types import JSONRPCMessage
logger = logging.getLogger(__name__)
@dataclass
class EventEntry:
    event_id: EventId
    stream_id: StreamId
    message: JSONRPCMessage | None
class InMemoryEventStore(EventStore):
    def __init__(self, max_events_per_stream=100):
        self.max_events_per_stream = max_events_per_stream
        self.streams = {}
        self.event_index = {}
    async def store_event(self, stream_id, message):
        event_id = str(uuid4())
        entry = EventEntry(event_id=event_id, stream_id=stream_id, message=message)
        if stream_id not in self.streams:
            self.streams[stream_id] = deque(maxlen=self.max_events_per_stream)
        if len(self.streams[stream_id]) == self.max_events_per_stream:
            oldest = self.streams[stream_id][0]
            self.event_index.pop(oldest.event_id, None)
        self.streams[stream_id].append(entry)
        self.event_index[event_id] = entry
        return event_id
    async def replay_events_after(self, last_event_id, send_callback):
        if last_event_id not in self.event_index:
            return None
        last = self.event_index[last_event_id]
        events = self.streams.get(last.stream_id, deque())
        found = False
        for e in events:
            if found and e.message is not None:
                await send_callback(EventMessage(e.message, e.event_id))
            elif e.event_id == last_event_id:
                found = True
        return last.stream_id
