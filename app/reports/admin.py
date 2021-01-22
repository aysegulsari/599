from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Report)
admin.site.register(models.Tweet)
admin.site.register(models.Hashtag)
admin.site.register(models.ContextAnnotation)
