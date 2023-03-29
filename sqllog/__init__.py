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
from .parser import QueryParser
from .wrapper import BaseDatabaseWrapper, CursorDebugWrapper

THIS_MODULE_PATH = os.path.dirname(__file__)
sqllog_logger = None


def sqllog_handler(cursor_wrapper, *args, **kwargs):
    sql = kwargs.get('sql')
    params = kwargs.get('params')
    many = kwargs.get('many')
    duration = kwargs.get('duration')

    tbs = str(CallStack(
        lambda filename: not filename.startswith(THIS_MODULE_PATH) and filename.startswith(settings.BASE_DIR),
    ))

    tables = None
    generalized_query = None
    # noinspection PyBroadException
    try:
        parsed_sql = QueryParser(sql)
        tables = parsed_sql.tables
        generalized_query = parsed_sql.generalize
    except ValueError:
        # HACK: Ignore sql parsing failures(unknown errors) to continue logging.
        pass
    except Exception as e:
        # Reporting errors except sql parsing errors.
        exception(e)
        return

    if params is not None:
        # Expects the data type of params to be an enum such as list, set or tuple.
        if isinstance(params, (list, set, tuple,)):
            params = [str(x) for x in params]
        else:
            # Report for warning if the params is of unexpected data type.
            message(f'Unknown data type: {type(params)=}')

    tbs_strlen = len(tbs)
    tbs = tbs[:cursor_wrapper.db.max_traceback_strlen]

    sqllog_logger.info(json.dumps(
        dict(
            sql=sql,
            params=params,
            many=many,
            alias=cursor_wrapper.db.alias,
            duration=duration,
            config=settings.SQLLOG.get('CONFIG_NAME'),
            traceback=tbs,
            traceback_hash=md5(tbs.encode()).hexdigest(),
            tables=tables,
            generalized_sql=generalized_query,
            generalized_sql_hash=generalized_query and md5(generalized_query.encode()).hexdigest(),
            pid=os.getpid(),
            tid=threading.get_ident(),
            native_tid=threading.get_native_id(),
            traceback_strlen=tbs_strlen,
            is_truncated_traceback=tbs_strlen > len(tbs),
        ),
        default=str,
    ))


def sqllog_env_file_change_handler(event, env):
    BaseDatabaseWrapper.force_debug_cursor = env['enabled']
    BaseDatabaseWrapper.sample_rate = env['sample_rate']
    BaseDatabaseWrapper.max_traceback_strlen = env['max_traceback_strlen']


if getattr(settings, 'SQLLOG', {}):
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
