import os
import time

from django.conf import settings
from django.db.backends.base import base
from django.test import TestCase
from django.test.testcases import SerializeMixin

from sqllog.config import Config


class BaseTestCase(TestCase):
    env_path = None
    log_path = None
    conf = None

    def setUp(self):
        self.env_path = settings.SQLLOG['ENV_FILE_PATH']
        self.log_path = settings.SQLLOG['LOGGING']['handlers']['sqllog_file'].get('filename')

        assert (os.path.exists(self.env_path))

        # Clear log file.
        self.truncate_log()

        # Read config.
        self.conf = Config()
        self.conf.read(self.env_path)

    def tearDown(self):
        pass

    def save_config(self, section='default', **kwargs):
        setattr(base.BaseDatabaseWrapper, 'force_debug_cursor', not kwargs['enabled'])

        for k, v in kwargs.items():
            self.conf.set(section, k, str(v))
        with open(self.env_path, 'w') as fp:
            self.conf.write(fp)

        # HACK: Wait for the changed config file to take effect.
        while True:
            if getattr(base.BaseDatabaseWrapper, 'force_debug_cursor') == kwargs['enabled']:
                break
            print('Waiting...')
            time.sleep(1)

    def truncate_log(self):
        open(self.log_path, 'w').close()

    def read_log(self):
        with open(self.log_path) as fp:
            return fp.read()

    def read_log_lines(self, with_blank_line=False):
        return [x for x in self.read_log().splitlines() if x or with_blank_line]


class SerializeTestCase(SerializeMixin, BaseTestCase):
    lockfile = __file__

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().setUp()
