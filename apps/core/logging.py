"""Structured console logging for operational and security events."""

import json
import logging
from datetime import UTC, datetime


class JsonEventFormatter(logging.Formatter):
    """Emit a JSON object containing only approved, non-sensitive log fields."""

    EVENT_FIELDS = (
        'event',
        'request_id',
        'method',
        'route',
        'status_code',
        'duration_ms',
        'api_key_prefix',
        'actor_id',
        'reason',
        'throttle_scope',
    )

    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created, tz=UTC)
        payload = {
            'timestamp': timestamp.isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        for field in self.EVENT_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload['exception_type'] = record.exc_info[0].__name__
        return json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
