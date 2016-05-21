from __future__ import unicode_literals
from django.conf.urls import url
from django.contrib.admin import SimpleListFilter, ModelAdmin
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from abc import ABCMeta, abstractmethod
import logging


logger = logging.getLogger(__name__)


class PeriodAgoMixin(object):
    """
    "Period Ago" means that periods to list are time ago, and not a current in-execution period.
    This is the difference: "1 month ago", being on August 15, would start on July 15, while
      "This month" started on Aug 15.
    """

    def lookups(self, request, model_admin):
        """
        List, with meanings, of dwmqhy options.
        :param request:
        :param model_admin:
        :return: list of KV pairs.
        """

        return (
            ('d', _(u'One day ago')),
            ('w', _(u'One week ago')),
            ('m', _(u'One month ago')),
            ('q', _(u'3 months ago')),
            ('h', _(u'6 months ago')),
            ('y', _(u'One year ago')),
        )


class PeriodCurrentMixin(object):
    """
    "Period Current" means that periods to list are a current in-execution period, and not a
      period ago.
    This is the difference: "1 month ago", being on August 15, would start on July 15, while
      "This month" started on Aug 15.
    """

    def lookups(self, request, model_admin):
        """
        List, with meanings, of DMQHY options.
        :param request:
        :param model_admin:
        :return: list of KV pairs.
        """

        return (
            ('D', _(u'Today')),
            ('M', _(u'This month')),
            ('Q', _(u'This quarter')),
            ('H', _(u'This semester')),
            ('Y', _(u'This year'))
        )


class PeriodAgoAndCurrentMixin(object):
    """
    This allows to check both the "Period Ago" and "Period Current" options.
    """

    def lookups(self, request, model_admin):
        """
        List, with meanings, of dwmqhyDMQHY options.
        :param request:
        :param model_admin:
        :return: list of KV pairs.
        """

        return (
            ('d', _(u'One day ago')),
            ('D', _(u'Today')),
            ('w', _(u'One week ago')),
            ('m', _(u'One month ago')),
            ('M', _(u'This month')),
            ('q', _(u'3 months ago')),
            ('Q', _(u'This quarter')),
            ('h', _(u'6 months ago')),
            ('H', _(u'This semester')),
            ('y', _(u'One year ago')),
            ('Y', _(u'This year'))
        )


class PeriodFilter(SimpleListFilter):
    """
    Period filter. This will make use of .created_on and .updated_on methods. Its subclasses
      will be the actually in-use filter classes.
    """

    PERIOD_DATE_METHOD = None

    def queryset(self, request, queryset):
        """
        Will invoke .created_on(period) or .updated_on(period) depending on how it is specified in
          each subclass (A queryset obtained from the Tracked* models will have a created_on and
          updated_on models as shortcuts).
        :param request:
        :param queryset:
        :return: filtered queryset.
        """

        return getattr(queryset, self.PERIOD_DATE_METHOD)(self.value()) if self.value() else queryset


class CreatePeriodBaseFilter(PeriodFilter):

    PERIOD_DATE_METHOD = 'created_on'
    parameter_name = 'created_on_period'
    title = _('creation period')


class UpdatePeriodBaseFilter(PeriodFilter):

    PERIOD_DATE_METHOD = 'updated_on'
    parameter_name = 'updated_on_period'
    title = _('update period')


class CreatePeriodAgoFilter(PeriodAgoMixin, CreatePeriodBaseFilter):
    pass


class CreatePeriodAgoAndCurrentFilter(PeriodAgoAndCurrentMixin, CreatePeriodBaseFilter):
    pass


class CreatePeriodCurrentFilter(PeriodCurrentMixin, CreatePeriodBaseFilter):
    pass


class UpdatePeriodAgoFilter(PeriodAgoMixin, UpdatePeriodBaseFilter):
    pass


class UpdatePeriodAgoAndCurrentFilter(PeriodAgoAndCurrentMixin, UpdatePeriodBaseFilter):
    pass


class UpdatePeriodCurrentFilter(PeriodCurrentMixin, UpdatePeriodBaseFilter):
    pass


class TrackingReport(object):
    """
    This is an abstract class to process a report for a given format, model, and period.
    Stuff must be defined like:
    1. The report key and display. It must have a meaning in the software and should be allowed to the
       user to specify it. It is specified in an instance basis.
    2. The content type. This could be defined by overriding `get_attachment_content_type` method or just
       the `content_type` member (a string).
    3. The attachment name. This MUST be defined by overriding `get_attachment_filename` method.
    4. The attachment content. This MUST be defined by overriding `get_attachment_content` method.
    """

    __metaclass__ = ABCMeta
    content_type = None

    def __init__(self, key, text):
        """
        Telling a key and a value is useful to let the report be picked
        :param key: This string value must be unique across different reports in the same admin.
        :param text: This string (or locale lazy resolver) is the display text for the option.
        """

        self._key = key
        self._text = text

    @property
    def key(self):
        return self._key

    @property
    def text(self):
        return self._text

    def get_attachment_content_type(self):
        """
        Content-Type to be used for the attachment.
        :return: A string being a MIME type.
        """

        return self.content_type

    @abstractmethod
    def get_attachment_filename(self):
        """
        Filename to be used for the attachment.
        :return: A string with the filename.
        """

        return 'override.me'

    @abstractmethod
    def get_attachment_content(self, request, model, period):
        """
        Returns the generated file content.
        :param request: The request being processed.
        :param model: The model class being processed.
        :param period: The model being processed.
        :return: The report content (usually expressed in raw bytes but could be unicode as well).
        """

        return b''

    def process(self, request, model, period):
        """
        Will process the request and return an appropriate Response object.
        :param request: The request being processed.
        :param model: The model class being processed.
        :param period: The model being processed.
        :return: The response with the report.
        """

        response = HttpResponse(content=self.get_attachment_content(request, model, period) or '',
                                content_type=self.get_attachment_content_type() or 'text/plain')
        response['Content-Disposition'] = 'attachment; filename=' + (self.get_attachment_filename() or 'report.txt')
        return response


class TrackedLiveReportingMixin(ModelAdmin):
    """
    This mixin provides additional urls to process our reports.
    """

    change_list_template = 'admin/tracked/change_list.html'
    report_error_template = None
    report_period_type = 'both'  # Report period types may be: 'current', 'ago', or 'both'
    report_generators = []  # List of available reports

    def get_reporters(self):
        """
        Converts the report_generators list to a dictionary, and caches the result.
        :return: A dictionary with such references.
        """

        if not hasattr(self, '_report_generators_by_key'):
            self._report_generators_by_key = {r.key: r for r in self.report_generators}
        return self._report_generators_by_key

    def get_period_pattern(self):
        """
        Given the current setting in report_period_type, returns a string pattern (suitable for regexp)
          of characters being the valid periods to select.
        :return: A string of period value characters.
        """

        if self.report_period_type == 'ago':
            return 'dwmqhy'
        elif self.report_period_type == 'current':
            return 'DMQHY'
        elif self.report_period_type == 'both':
            return 'dwmqhyDMQHY'
        else:
            raise ValueError("Invalid report period type. Expected: 'ago', 'current', or 'both'")

    def get_period_options(self):
        """
        Given the current setting in report_period_type, returns a list of options (suitable for select)
          as an array or pairs telling the valid periods to select.
        :return: An array of period options.
        """

        periods_ago = (
            ('d', _('One exact day ago')),
            ('w', _('One exact week ago')),
            ('m', _('One exact month ago')),
            ('q', _('One exact quarter ago')),
            ('h', _('One exact semester ago')),
            ('y', _('One exact year ago')),
        )
        periods_current = (
            ('D', _('Today')),
            ('M', _('This month')),
            ('Q', _('This quarter')),
            ('H', _('This semester')),
            ('Y', _('This year')),
        )

        if self.report_period_type == 'ago':
            return periods_ago
        elif self.report_period_type == 'current':
            return periods_current
        elif self.report_period_type == 'both':
            return periods_ago + periods_current
        else:
            raise ValueError("Invalid report period type. Expected: 'ago', 'current', or 'both'")

    def get_report_options(self):
        """
        Enumerates the report options as a list (suitable for a select) as an array of pairs
          telling the valid periods to select.
        :return: An array of period options.
        """

        return [(r.key, r.text) for r in self.report_generators]

    def report_urls(self):
        """
        Returns additional urls to add to a result of `get_urls` in a descendant ModelAdmin
        :return: A list of url declarations.
        """

        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            url(r'^report/(?P<key>\w+)/(?P<period>\w)$',
                self.admin_site.admin_view(self.report_view), name='%s_%s_tracking_report' % info)
        ]

    def changelist_view(self, request, extra_context=None):
        """
        Updates the changelist view to include settings from this admin.
        """

        return super(TrackedLiveReportingMixin, self).changelist_view(
            request, dict(extra_context,
                          url_name='%s_%s_tracking_report' % (self.model._meta.app_label, self.model._meta.model_name),
                          period_options=self.get_period_options(),
                          report_options=self.get_report_options())
        )

    def render_report_error(self, request, error, status):
        """
        Renders the report errors template.
        """

        opts = self.model._meta
        app_label = opts.app_label
        request.current_app = self.admin_site.name
        context = dict(
            self.admin_site.each_context(request),
            title=(_('Tracking report error for %s') % force_text(opts.verbose_name)),
            error=error
        )

        return TemplateResponse(request, self.report_error_template or [
            "admin/{}/{}/tracking_report_error.html".format(app_label, opts.model_name),
            "admin/{}/tracking_report_error.html".format(app_label),
            "admin/tracking_report_error.html"
        ], context, status=status)

    def report_view(self, request, key, period):
        """
        Processes the reporting action.
        """

        reporters = self.get_reporters()
        try:
            reporter = reporters[key]
        except KeyError:
            return self.render_report_error(request, _('Report not found'), 404)

        allowed_periods = [c for c in self.get_period_pattern()]
        if period and period not in allowed_periods:
            return self.render_report_error(request, _('Invalid report type'), 400)

        try:
            return reporter.process(request, self.model, period)
        except:
            logger.exception('Tracking Reports could not generate the report due to an internal error')
            return self.render_report_error(request, _('An unexpected error has occurred'), 500)
