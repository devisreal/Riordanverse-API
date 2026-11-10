"""Linux production WSGI entrypoint: uv run --no-dev gunicorn --config gunicorn.conf.py."""

import os

wsgi_app = 'config.wsgi:application'
bind = f'0.0.0.0:{int(os.environ.get("PORT", "8000"))}'
# Start conservatively; size this explicitly for the hosting plan's memory/CPU.
workers = int(os.environ.get('WEB_CONCURRENCY', '1'))

# Django already emits structured request logs; avoid duplicate access logs.
accesslog = None
errorlog = '-'
