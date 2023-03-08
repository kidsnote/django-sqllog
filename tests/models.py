from django.db import models


class Category(models.Model):
    title = models.CharField(max_length=128)

    def __unicode__(self):
        return self.title


class Post(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    visible = models.BooleanField(default=True)

    def __unicode__(self):
        return self.title
