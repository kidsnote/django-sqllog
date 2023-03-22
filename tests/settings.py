import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'tests',
    'sqllog',
]

MIDDLEWARE = [
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

LOG_ROOT = f'{BASE_DIR}/logs'
os.makedirs(LOG_ROOT, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s] [%(asctime)s] %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'json': {
            'format': '%(levelname)s %(asctime)s %(message)s',
        },
    },
    'handlers': {
        'default': {
            'class': 'logging.FileHandler',
            'filename': f'{LOG_ROOT}/default.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'default': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

USE_TZ = True

SQLLOG = {
    'ENABLED': os.getenv('SQLLOG_ENABLED', True),
    'ENABLE_SENTRY': os.getenv('SQLLOG_ENABLE_SENTRY', False),
    'CONFIG_NAME': 'testing',
    'ENV_FILE_PATH': f'{BASE_DIR}/runtime/sqllog.ini',
    'TRACEBACK_MAX_LENGTH': 10000,
    'LOGGING': {
        'formatters': {
            'sqllog': {
                'format': '%(levelname)s %(asctime)s %(message)s',
            },
        },
        'handlers': {
            'sqllog_file': {
                'class': 'logging.FileHandler',
                'filename': f'{LOG_ROOT}/sql.log',
                'formatter': 'sqllog',
            },
            'sqllog_logstash': {
                'class': 'logstash.LogstashHandler',
                'host': 'localhost',
                'port': 5959,
            }
        },
        'loggers': {
            'sqllog': {
                'handlers': [
                    'sqllog_file',
                    'sqllog_logstash',
                ],
                'level': 'INFO',
                'propagate': False,
            },
        }
    }
}
