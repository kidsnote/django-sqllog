import random
from abc import ABC
from contextlib import contextmanager
from time import monotonic

from django.db.backends import utils
from django.db.backends.base import base


class BaseDatabaseWrapper(base.BaseDatabaseWrapper, ABC):
    force_debug_cursor = False
    sample_rate = 0
    max_traceback_strlen = None

    @property
    def queries_logged(self):
        return BaseDatabaseWrapper.force_debug_cursor and (random.random() < BaseDatabaseWrapper.sample_rate)


class CursorDebugWrapper(utils.CursorWrapper):
    sqllog_handler = None

    def execute(self, sql, params=None):
        with self.notify(sql, params):
            return super().execute(sql, params)

    def executemany(self, sql, param_list):
        with self.notify(sql, param_list, many=False):
            return super().executemany(sql, param_list)

    @contextmanager
    def notify(self, sql=None, params=None, many=False):
        start = monotonic()
        try:
            yield
        finally:
            sql = self.db.ops.last_executed_query(self.cursor, sql, params)
            duration = monotonic() - start
            self.sqllog_handler and self.sqllog_handler(
                sql=sql,
                many=many,
                duration=duration,
            )
