from django.conf import settings
from sentry_sdk import capture_exception, capture_message

ENABLE_SENTRY = getattr(settings, 'SQLLOG', {}).get('ENABLE_SENTRY')


def exception(*args, **kwargs):
    (ENABLE_SENTRY or kwargs.get('force')) and capture_exception(*args, **kwargs)


def message(*args, **kwargs):
    (ENABLE_SENTRY or kwargs.get('force')) and capture_message(*args, **kwargs)
