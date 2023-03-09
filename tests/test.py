import configparser
import datetime
import json
import os
import time

from django.conf import settings
from django.db.backends.base import base

from .models import (
    Category,
    Post,
)
from .utils import BaseTestCase

SQLLOG = settings.SQLLOG


class PrimaryTests(BaseTestCase):
    def test_now(self):
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        print(now)

    def test_empty(self):
        old = getattr(base.BaseDatabaseWrapper, 'force_debug_cursor', False)
        setattr(base.BaseDatabaseWrapper, 'force_debug_cursor', True)
        self.assertEqual(
            0,
            Category.objects.count(),
            Post.objects.count(),
        )
        setattr(base.BaseDatabaseWrapper, 'force_debug_cursor', old)

    def test_disable_logging_by_modifying_env_file(self):
        env_path = settings.SQLLOG['ENV_FILE_PATH']
        log_path = settings.SQLLOG['LOGGING']['handlers']['sqllog_file'].get('filename')

        if not log_path:
            return

        # File existence check.
        self.assertTrue(os.path.exists(env_path))

        conf = configparser.ConfigParser()
        conf.read(env_path)
        # Remember current state for restoration.
        enabled = conf.getboolean('default', 'enabled')
        # Turn off logging!
        conf.set('default', 'enabled', 'false')
        # Save file to trigger logging disable event.
        with open(env_path, 'w') as fp:
            conf.write(fp)

        # Truncate log file.
        open(log_path, 'w').close()

        # Send the SQL query to the database server using the print statement.
        print(Category.objects.all())

        # Wait for the sqllog enable event by file changing.
        while True:
            if not getattr(base.BaseDatabaseWrapper, 'force_debug_cursor', True):
                break
            print('I am waiting...')
            time.sleep(1)

        # Since logging is disabled, the log file should be empty.
        self.assertTrue(len(open(log_path).read()) == 0)

        # Restore past state.
        conf.set('default', 'enabled', str(enabled))
        with open(env_path, 'w') as fp:
            conf.write(fp)

    def test_enable_logging_by_modifying_env_file(self):
        env_path = settings.SQLLOG['ENV_FILE_PATH']
        log_path = settings.SQLLOG['LOGGING']['handlers']['sqllog_file'].get('filename')

        if not log_path:
            return

        # File existence check.
        self.assertTrue(os.path.exists(env_path))

        conf = configparser.ConfigParser()
        conf.read(env_path)
        # Remember current state for restoration.
        enabled = conf.getboolean('default', 'enabled')
        # Turn off logging!
        conf.set('default', 'enabled', 'true')
        # Save file to trigger logging disable event.
        with open(env_path, 'w') as fp:
            conf.write(fp)

        # Truncate log file.
        open(log_path, 'w').close()

        # Wait for the sqllog enable event by file changing.
        while True:
            if getattr(base.BaseDatabaseWrapper, 'force_debug_cursor', False):
                break
            print('I am waiting...')
            time.sleep(1)

        # Send the SQL query to the database server using the print statement.
        print(Category.objects.all()[0:10])

        # Since logging is enabled, the log file should have contents.
        lines = open(log_path).readlines()
        # Remove empty line.
        lines = [x for x in lines if x]
        # There muse be only one leg message in the log file.
        self.assertEqual(len(lines), 1)
        # Assume that the log message starts at the 29th character, and log messages are json data type.
        obj = json.loads(lines[0][29:])

        self.assertEquals(
            obj['sql'],
            'SELECT "tests_category"."id", "tests_category"."title" FROM "tests_category" LIMIT 10'
        )

        # Restore past state.
        conf.set('default', 'enabled', str(enabled))
        with open(env_path, 'w') as fp:
            conf.write(fp)
