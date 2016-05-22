from django.contrib.admin import site, ModelAdmin
from django.utils.translation import ugettext_lazy as _
from grimoire.django.tracked.admin import (TrackedLiveAdmin, CSVReport)
from .models import SampleRecord


class SampleAdmin(TrackedLiveAdmin, ModelAdmin):

    report_generators = [CSVReport('csv', _('CSV Report'))]
    list_display = ('id', 'content', 'created_on', 'updated_on')


site.register(SampleRecord, SampleAdmin)