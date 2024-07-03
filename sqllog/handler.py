import os

from watchdog.events import (
    FileSystemEventHandler,
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_MOVED,
)

from .capture import exception
from .config import Config

DEFAULT_ENV = dict(
    enabled=False,
    sample_rate=0,
    max_traceback_strlen=None,
    max_query_length=10000,
    long_query_time=1,
    long_query_length=10000,
)


class EnvFileEventHandler(FileSystemEventHandler):
    def __init__(self, obser_file, handler):
        self.obser_file = os.path.realpath(obser_file)
        self.obser_dir = os.path.dirname(obser_file)
        self.mtime = 0
        self.event_handler = handler

        if not os.path.exists(self.obser_file):
            os.makedirs(os.path.dirname(self.obser_file), exist_ok=True)
            with open(self.obser_file, 'w') as f:
                conf = Config()
                # noinspection PyTypeChecker
                conf['default'] = DEFAULT_ENV
                conf.write(f)

        self.invoke()

    def dispatch(self, event):
        file_path: str = getattr(event, 'dest_path', getattr(event, 'src_path', None))

        if (file_path is None) or (os.path.realpath(file_path) != self.obser_file):
            return

        if event.event_type not in {
            EVENT_TYPE_CREATED,
            EVENT_TYPE_DELETED,
            EVENT_TYPE_MODIFIED,
            EVENT_TYPE_MOVED,
        }:
            return

        self.invoke(event)

    def invoke(self, event=None):
        env = DEFAULT_ENV.copy()
        # noinspection PyBroadException
        try:
            conf = Config()
            conf.read(self.obser_file)
            env.update(dict(
                enabled=conf.get_value(bool, 'default', 'enabled', default=False),
                sample_rate=conf.get_value(float, 'default', 'sample_rate', default=0),
                max_traceback_strlen=conf.get_value(int, 'default', 'max_traceback_strlen', default=None),
                max_sql_strlen=conf.get_value(int, 'default', 'max_query_length', default=10000),
                long_query_time=conf.get_value(int, 'default', 'long_query_time', default=1),
                long_query_length=conf.get_value(int, 'default', 'long_query_length', default=10000),
            ))
        except Exception as e:
            # Reporting and disable logging when unknown exception raised.
            exception(e)

        self.event_handler and self.event_handler(event, env)
