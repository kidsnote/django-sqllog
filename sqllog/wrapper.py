from abc import ABC
from contextlib import contextmanager
from time import monotonic

from django.db.backends import utils
from django.db.backends.base import base


class BaseDatabaseWrapper(base.BaseDatabaseWrapper, ABC):
    force_debug_cursor = False

    @property
    def queries_logged(self):
        return BaseDatabaseWrapper.force_debug_cursor


class CursorDebugWrapper(utils.CursorWrapper):
    sqllog_handler = None

    def execute(self, sql, params=None):
        with self.notify(sql, params, use_last_executed_query=True):
            return super().execute(sql, params)

    def executemany(self, sql, param_list):
        with self.notify(sql, param_list, many=False):
            return super().executemany(sql, param_list)

    @contextmanager
    def notify(self, sql=None, params=None, use_last_executed_query=False, many=False):
        start = monotonic()
        try:
            yield
        finally:
            duration = monotonic() - start
            self.sqllog_handler and self.sqllog_handler(
                sql=sql,
                params=params,
                use_last_executed_query=use_last_executed_query,
                many=many,
                duration=duration,
            )
