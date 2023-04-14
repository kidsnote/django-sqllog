from setuptools import setup

setup(
    name='django-sqllog',
    version='0.0.2',
    description='SQL query logger for Django application.',
    url='https://github.com/kncray/django-sqllog',
    author='cray',
    author_email='cray.j@kidsnote.com',
    license='BSD',
    packages=[
        'sqllog',
    ],
    install_requires=[
        'python-logstash>=0.4.8',
        'sentry-sdk>=1.11.1',
        'watchdog>=2.1.9',
    ],
    classifiers=[
        'Development Status :: In developing',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.9.6',
        'Framework :: Django',
        'Framework :: Django :: 4.1.7',
    ],
)