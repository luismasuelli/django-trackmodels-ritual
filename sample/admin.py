from django.contrib.admin import site, ModelAdmin
from grimoire.django.tracked.admin import (TrackedLiveAdmin, TrackingReport)
from .models import SampleRecord


class SampleAdmin(TrackedLiveAdmin, ModelAdmin):

    list_display = ('id', 'content', 'created_on', 'updated_on')


site.register(SampleRecord, SampleAdmin)