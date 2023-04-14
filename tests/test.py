import json
import random
import time
from subprocess import Popen, PIPE

from .models import (
    Post, Category,
)
from .utils import SerializeTestCase

DEVNULL = open('/dev/null', 'w')


class DisableTests(SerializeTestCase):
    def test_empty(self):
        self.assertEqual(
            0,
            Category.objects.count(),
            Post.objects.count(),
        )

    def test_disable_logging_by_modifying_env_file(self):
        # Turn off logging.
        self.save_config(
            enabled=False,
            sample_rate=1,
        )

        # Make SQL.
        print(Category.objects.all(), file=DEVNULL)

        # HACK: Wait for log messages to be written to the log file.
        time.sleep(1)

        # Since logging is disabled, the log file should be empty.
        log = self.read_log()
        self.assertTrue(not log, log)


class EnableTests(SerializeTestCase):
    def test_enable_logging_by_modifying_env_file(self):
        # Turn on logging.
        self.save_config(
            enabled=True,
            sample_rate=1,
        )

        # Make SQL.
        print(Category.objects.all()[0:10], file=DEVNULL)

        # HACK: Wait for log messages to be written to the log file.
        time.sleep(1)

        # Read logs.
        logs = self.read_log_lines()

        # There must be only one log message.
        self.assertEqual(len(logs), 1, logs)

        # Extract only SQL from the first line.
        sql = json.loads(logs[0][29:])['sql']

        self.assertEquals(
            sql,
            'SELECT "tests_category"."id", "tests_category"."title" FROM "tests_category" LIMIT 10'
        )


class TracebackTests(SerializeTestCase):
    def test_traceback_max_length_option(self):
        # Set configs.
        random.seed(time.time())
        traceback_max_length = random.randint(1, 20)

        # Turn on logging
        self.save_config(
            enabled=True,
            sample_rate=1,
            max_traceback_strlen=traceback_max_length
        )

        # Make SQL.
        print(Category.objects.all()[0:10], file=DEVNULL)
        print(Post.objects.all(), file=DEVNULL)
        print(Post.objects.select_related('category'), file=DEVNULL)

        # HACK: Wait for log messages to be written to the log file.
        time.sleep(1)

        # Read logs.
        logs = self.read_log_lines()

        for log in logs:
            obj = json.loads(log.split(' ', 3)[-1])
            assert len(obj['traceback']) <= traceback_max_length


class SampleRateTests(SerializeTestCase):
    def test_sample_rate(self):
        # Set sample rate.
        sample_rate = random.random()
        # Set how many queries to generate.
        query_count = random.randint(10, 30)
        # Set seed value for random reproduction.
        seed = time.time()

        # Turn off logging.
        self.save_config(
            enabled=True,
            sample_rate=sample_rate,
        )

        print(f'{query_count=},{sample_rate=}')

        random.seed(seed)
        expected_count = sum(random.random() < sample_rate for _ in range(query_count))

        random.seed(seed)
        for i in range(query_count):
            print(Post.objects.all(), file=DEVNULL)

        # HACK: Wait for log messages to be written to the log file.
        time.sleep(1)

        # Read logs.
        logs = self.read_log_lines()

        self.assertEqual(len(logs), expected_count, logs)


class SqlTests(SerializeTestCase):
    def test_sql_max_length_option(self):
        # Set configs.
        random.seed(time.time())
        max_sql_strlen = random.randint(1, 20)

        # Turn on logging
        self.save_config(
            enabled=True,
            sample_rate=1,
            max_sql_strlen=max_sql_strlen,
        )

        # Make SQL.
        print(Category.objects.all()[0:10], file=DEVNULL)
        print(Post.objects.all(), file=DEVNULL)
        print(Post.objects.select_related('category'), file=DEVNULL)

        # HACK: Wait for log messages to be written to the log file.
        time.sleep(1)

        # Read logs.
        logs = self.read_log_lines()

        for log in logs:
            obj = json.loads(log.split(' ', 3)[-1])
            assert len(obj['sql']) <= max_sql_strlen

    def test_generalization(self):
        # Turn on logging
        self.save_config(
            enabled=True,
            sample_rate=1,
            max_sql_strlen=None,
        )

        # Make SQL.
        print(Category.objects.filter(title='noname'), file=DEVNULL)

        # HACK: Wait for log messages to be written to the log file.
        time.sleep(1)

        # Read logs.
        logs = self.read_log_lines()
        log = logs[0]
        obj = json.loads(log.split(' ', 3)[-1])
        original_sql = obj['sql']
        generalized_sql = obj['generalized_sql']

        with Popen(['pt-fingerprint'], stdin=PIPE, stdout=PIPE) as p:
            p.stdin.write(original_sql.encode('utf-8'))
            p.stdin.write(b';\n')
            p.stdin.flush()
            desired_sql = p.stdout.readline().decode('utf-8').strip()

        self.assertEqual(
            generalized_sql,
            desired_sql
        )
