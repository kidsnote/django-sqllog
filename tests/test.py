import datetime

from django.conf import settings

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
        self.assertEqual(
            0,
            Category.objects.count(),
            Post.objects.count(),
        )
