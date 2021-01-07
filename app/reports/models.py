from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
# from accounts.models import User

from django.contrib.auth import get_user_model

User = get_user_model()

# https://docs.djangoproject.com/en/2.0/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_members check template tag
from django import template

register = template.Library()


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(allow_unicode=True, unique=True)
    description = models.TextField(blank=False, default='')
    keyword = models.TextField(blank=False, default='')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("reports:single", kwargs={"slug": self.slug})

    class Meta:
        ordering = ["name"]


class Tweet(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    tweet_id = models.TextField(blank=False, default='')
    creation_date = models.TextField(blank=False, default='')
    tweet_text = models.CharField(max_length=280, unique=True)
