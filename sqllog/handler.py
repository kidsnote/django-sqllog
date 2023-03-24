import configparser
import os

from watchdog.events import (
    FileSystemEventHandler,
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_MOVED,
)

from .capture import exception


class EnvFileEventHandler(FileSystemEventHandler):
    def __init__(self, obser_file, handler):
        self.obser_file = os.path.realpath(obser_file)
        self.obser_dir = os.path.dirname(obser_file)
        self.mtime = 0
        self.event_handler = handler

        if not os.path.exists(self.obser_file):
            os.makedirs(os.path.dirname(self.obser_file), exist_ok=True)
            with open(self.obser_file, 'w') as f:
                conf = configparser.ConfigParser()
                conf['default'] = {
                    'enabled': False,
                    'sample_rate': 0,
                }
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
        # noinspection PyBroadException
        try:
            conf = configparser.ConfigParser()
            conf.read(self.obser_file)
            enabled = conf.getboolean('default', 'enabled', fallback=False)
            sample_rate = conf.getfloat('default', 'sample_rate', fallback=0)
        except Exception as e:
            # Reporting and disable logging when unknown exception raised.
            exception(e)
            enabled = False
            sample_rate = 0

        self.event_handler and self.event_handler(event, enabled, sample_rate)
