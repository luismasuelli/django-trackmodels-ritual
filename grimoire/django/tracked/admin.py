from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _


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