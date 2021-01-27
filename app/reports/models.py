from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django import template

User = get_user_model()
register = template.Library()


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(allow_unicode=True, unique=True)
    time_interval = models.CharField(blank=False, max_length=50, default='')
    tweet_count = models.CharField(blank=False, max_length=10, default='')
    keyword = models.CharField(blank=False, max_length=50, default='')
    language = models.CharField(blank=False, max_length=10, default='')
    hashtag = models.CharField(blank=False, max_length=5, default='')

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
    tweet_id = models.CharField(blank=False, max_length=100, default='')
    creation_date = models.CharField(blank=False, max_length=100, default='')
    tweet_text = models.TextField(blank=False, default='')
    sentiment = models.CharField(blank=False, max_length=10, default='')
    lang = models.CharField(blank=False, max_length=10, default='')
    retweet_count = models.CharField(blank=False, max_length=10, default='')
    reply_count = models.CharField(blank=False, max_length=10, default='')
    like_count = models.CharField(blank=False, max_length=10, default='')
    hashtag_string = models.TextField(blank=False, default='')
    context_domain_string = models.TextField(blank=False, default='')
    context_entity_string = models.TextField(blank=False, default='')
    # category = models.CharField(blank=False, max_length=100, default='')
    # negative= models.CharField(blank=False, max_length=10, default='')
    # positive= models.CharField(blank=False, max_length=10, default='')
    # neutral= models.CharField(blank=False, max_length=10, default='')
    # compound=models.CharField(blank=False, max_length=100, default='')
    # tweet_context=models.CharField(blank=False, max_length=100, default='')


class Hashtag(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    tag = models.TextField(blank=False, default='')


class ContextAnnotation(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    domain_id = models.CharField(blank=False, max_length=100, default='')
    domain_name = models.CharField(blank=False, max_length=100, default='')
    domain_desc = models.CharField(blank=False, max_length=250, default='')
    entity_id = models.CharField(blank=False, max_length=100, default='')
    entity_name = models.CharField(blank=False, max_length=100, default='')
