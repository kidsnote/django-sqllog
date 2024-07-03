import json
import logging
import os
import threading
from hashlib import md5

from django.conf import settings
from django.db.backends import utils
from django.db.backends.base import base
from django.utils.log import configure_logging
from watchdog.observers import Observer

from .callstack import CallStack
from .capture import exception, message
from .handler import EnvFileEventHandler
from .sql import fingerprint
from .wrapper import BaseDatabaseWrapper, CursorDebugWrapper

THIS_MODULE_PATH = os.path.dirname(__file__)
sqllog_logger = None


def sqllog_handler(cursor_wrapper, *args, **kwargs):
    sql = kwargs.get('sql')
    many = kwargs.get('many')
    duration = kwargs.get('duration')
    command = sql.split(' ')[0].lower()

    # LONG_QUERY_TIME / LONG_QUERY_LENGTH 설정 값 확인
    # 하나라도 설정되어 있는 경우 조건에 맞을 때만 로그를 남김
    # 하나도 설정된 것이 없는 경우 모든 로그 남김
    # long_query_time = settings.SQLLOG.get('LONG_QUERY_TIME')
    # long_query_length = settings.SQLLOG.get('LONG_QUERY_LENGTH')
    if cursor_wrapper.db.long_query_time or cursor_wrapper.db.long_query_length:
        should_log = False
    else:
        should_log = True

    # LONG_QUERY_TIME 기준으로 로그가 기록되어야 하는지 체크
    if not should_log:
        if cursor_wrapper.db.long_query_time and duration < cursor_wrapper.db.long_query_time:
            should_log = False

    sql_strlen = len(sql)

    # LONG_QUERY_LENGTH 기준으로 로그가 기록되어야 하는지 검사
    if not should_log:
        if cursor_wrapper.db.long_query_length and sql_strlen >= cursor_wrapper.db.long_query_length and command not in (
        'insert', 'update'):
            should_log = True

    if not should_log:
        return

    tbs = str(CallStack(
        lambda filename: not filename.startswith(THIS_MODULE_PATH) and filename.startswith(str(settings.BASE_DIR)),
    ))
    tbs_strlen = len(tbs)
    tbs = tbs[:cursor_wrapper.db.max_traceback_strlen]

    generalized_sql = fingerprint(sql)
    generalized_sql_hash = generalized_sql and md5(generalized_sql.encode()).hexdigest()

    limited_sql = sql[:cursor_wrapper.db.max_query_length]

    sqllog_logger.info(json.dumps(
        dict(
            command=command,
            sql=limited_sql,
            many=many,
            alias=cursor_wrapper.db.alias,
            duration=duration,
            config=settings.SQLLOG.get('CONFIG_NAME'),
            traceback=tbs,
            traceback_hash=md5(tbs.encode()).hexdigest(),
            generalized_sql=generalized_sql,
            generalized_sql_hash=generalized_sql_hash,
            pid=os.getpid(),
            tid=threading.get_ident(),
            native_tid=threading.get_native_id(),
            traceback_strlen=tbs_strlen,
            is_truncated_traceback=tbs_strlen > len(tbs),
            sql_strlen=sql_strlen,
            is_truncated_sql=sql_strlen > len(limited_sql),
        ),
        default=str,
    ))


def sqllog_env_file_change_handler(event, env):
    BaseDatabaseWrapper.force_debug_cursor = env['enabled']
    BaseDatabaseWrapper.sample_rate = env['sample_rate']
    BaseDatabaseWrapper.max_traceback_strlen = env['max_traceback_strlen']
    BaseDatabaseWrapper.max_sql_strlen = env['max_query_length']
    BaseDatabaseWrapper.long_query_time = env['long_query_time']
    BaseDatabaseWrapper.long_query_length = env['long_query_length']


if getattr(settings, 'SQLLOG', {}).get('ENABLED', False):
    settings.LOGGING = settings.LOGGING or {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {},
        'handlers': {},
        'loggers': {}
    }

    for k, v in settings.SQLLOG['LOGGING'].items():
        settings.LOGGING.setdefault(k, {}).update(v)

    # Update sqllog logger
    sqllog_logger = logging.getLogger('sqllog')
    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)

    CursorDebugWrapper.sqllog_handler = sqllog_handler

    base.BaseDatabaseWrapper = BaseDatabaseWrapper
    utils.CursorDebugWrapper = CursorDebugWrapper

    handler = EnvFileEventHandler(
        settings.SQLLOG['ENV_FILE_PATH'],
        sqllog_env_file_change_handler,
    )
    obser = Observer()
    obser.schedule(handler, handler.obser_dir, recursive=True)
    obser.start()
