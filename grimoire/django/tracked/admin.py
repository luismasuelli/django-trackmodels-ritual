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


PERIOD_AGO_LOOKUPS = (
    ('d', _(u'One day ago')),
    ('w', _(u'One week ago')),
    ('m', _(u'One month ago')),
    ('q', _(u'3 months ago')),
    ('h', _(u'6 months ago')),
    ('y', _(u'One year ago')),
)


PERIOD_CURRENT_LOOKUPS = (
    ('D', _(u'Today')),
    ('M', _(u'This month')),
    ('Q', _(u'This quarter')),
    ('H', _(u'This semester')),
    ('Y', _(u'This year'))
)


class PeriodFilter(SimpleListFilter):
    """
    Period filter. This will make use of .created_on and .updated_on methods. Its subclasses
      will be the actually in-use filter classes.
    """

    parameter_name = 'period'
    title = _('Period')

    def lookups(self, request, model_admin):
        """
        Performs lookup in the same way the reporting tool allows to generate a report.
        :param request: Current request
        :param model_admin: Current model admin. It must implement get_period_options as returning a list of (k, v).
        :raises: AttributeError, ValueError, or any exception triggered by get_period_options.
        :return: The result of calling such method.
        """

        if model_admin.tracked_stamps in {'create', 'update', 'both'}:
            prefix = model_admin.tracked_stamps + ':'
        else:
            raise ValueError("Invalid tracked_stamps type. Expected: 'create', 'update', or 'both'")
        original = model_admin.get_period_options()
        return type(original)((prefix + k, v) for (k, v) in original)

    def queryset(self, request, queryset):
        """
        Will invoke .created_on(period) or .updated_on(period) depending on how it is specified in
          each subclass (A queryset obtained from the Tracked* models will have a created_on and
          updated_on models as shortcuts).
        :param request:
        :param queryset:
        :return: filtered queryset.
        """

        value = self.value()
        try:
            if not value:
                return queryset
            prefix, period = value.split(':')
            if prefix == 'create':
                return queryset.created_on(period)
            elif prefix == 'update':
                return queryset.updated_on(period)
            elif prefix == 'both':
                return queryset.created_or_updated_on(period)
            else:
                return queryset
        except ValueError:
            return queryset


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

    def process(self, request, queryset, period):
        """
        Will process the request and return an appropriate Response object.
        :param request: The request being processed.
        :param model: The model class being processed.
        :param period: The model being processed.
        :return: The response with the report.
        """

        response = HttpResponse(content=self.get_attachment_content(request, queryset.model, period) or '',
                                content_type=self.get_attachment_content_type() or 'text/plain')
        response['Content-Disposition'] = 'attachment; filename=' + (self.get_attachment_filename() or 'report.txt')
        return response


class TrackedLiveAdmin(ModelAdmin):
    """
    This mixin provides additional urls to process our reports.
    """

    change_list_template = 'admin/tracked/change_list.html'
    tracked_stamps = 'both'  # Tracked stamps may be: 'create', 'update', 'both'
    report_error_template = None
    report_period_type = 'both'  # Report period types may be: 'current', 'ago', or 'both'
    report_generators = []  # List of available reports

    def get_list_filter(self, request):
        """
        Adds the period filter to the filters list.
        :param request: Current request.
        :return: Iterable of filters.
        """

        original = super(TrackedLiveAdmin, self).get_list_filter(request)
        return original + type(original)([PeriodFilter])

    def get_reporters(self):
        """
        Converts the report_generators list to a dictionary, and caches the result.
        :return: A dictionary with such references.
        """

        if not hasattr(self, '_report_generators_by_key'):
            self._report_generators_by_key = {r.key: r for r in self.report_generators}
        return self._report_generators_by_key

    def get_period_options(self):
        """
        Given the current setting in report_period_type, returns a list of options (suitable for select)
          as an array or pairs telling the valid periods to select.
        :return: An array of period options.
        """

        if self.report_period_type == 'ago':
            return PERIOD_AGO_LOOKUPS
        elif self.report_period_type == 'current':
            return PERIOD_CURRENT_LOOKUPS
        elif self.report_period_type == 'both':
            return PERIOD_AGO_LOOKUPS + PERIOD_CURRENT_LOOKUPS
        else:
            raise ValueError("Invalid report period type. Expected: 'ago', 'current', or 'both'")

    def get_report_options(self):
        """
        Enumerates the report options as a list (suitable for a select) as an array of pairs
          telling the valid periods to select.
        :return: An array of period options.
        """

        return [(r.key, r.text) for r in self.report_generators]

    def get_urls(self):
        """
        Returns additional urls to add to a result of `get_urls` in a descendant ModelAdmin
        :return: A list of url declarations.
        """

        info = self.model._meta.app_label, self.model._meta.model_name
        return super(TrackedLiveAdmin, self).get_urls() + [
            url(r'^report/(?P<key>\w+)/(?P<period>\w)$',
                self.admin_site.admin_view(self.report_view), name='%s_%s_tracking_report' % info)
        ]

    def changelist_view(self, request, extra_context=None):
        """
        Updates the changelist view to include settings from this admin.
        """

        return super(TrackedLiveAdmin, self).changelist_view(
            request, dict(extra_context or {},
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

    def get_period_queryset(self, request, period):
        """
        Computes the queryset for a specific period and, perhaps, a request.
        :param request: current request being processed.
        :param period: current requested period.
        :return: a queryset
        """

        qs = self.get_queryset(request)
        if self.tracked_stamps == 'create':
            return getattr(qs, 'created_on')(period)
        elif self.tracked_stamps == 'update':
            return getattr(qs, 'updated_on')(period)
        elif self.tracked_stamps == 'both':
            return getattr(qs, 'created_or_updated_on')(period)
        else:
            raise ValueError("Invalid tracked_stamps type. Expected: 'create', 'update', or 'both'")

    def report_view(self, request, key, period):
        """
        Processes the reporting action.
        """

        reporters = self.get_reporters()
        try:
            reporter = reporters[key]
        except KeyError:
            return self.render_report_error(request, _('Report not found'), 404)

        allowed_periods = [k for (k, v) in self.get_period_options()]
        if period and period not in allowed_periods:
            return self.render_report_error(request, _('Invalid report type'), 400)

        try:
            return reporter.process(request, self.get_period_queryset(request, period), period)
        except:
            logger.exception('Tracking Reports could not generate the report due to an internal error')
            return self.render_report_error(request, _('An unexpected error has occurred'), 500)
