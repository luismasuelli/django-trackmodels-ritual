from django.contrib.admin import site, ModelAdmin
from django.utils.translation import ugettext_lazy as _
from grimoire.django.tracked.admin import TrackedLiveAdmin
from grimoire.django.tracked.reports import CSVReport
from .models import SampleRecord, uppercase_content


class CustomCSVReport(CSVReport):

    list_report = ('id', 'content', 'created_on', 'updated_on', uppercase_content)


class SampleAdmin(TrackedLiveAdmin, ModelAdmin):

    report_generators = [CustomCSVReport('csv', _('CSV Report'))]
    list_display = ('id', 'content', 'created_on', 'updated_on')


site.register(SampleRecord, SampleAdmin)