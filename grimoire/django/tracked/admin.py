from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _


class PeriodFilter(SimpleListFilter):
    """
    Period filter. This will make use of .created_on and .updated_on methods. Its subclasses
      will be the actually in-use filter classes.
    """

    PERIOD_DATE_METHOD = None

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

    def queryset(self, request, queryset):
        """
        Will invoke .created_on(period) or .updated_on(period) depending on how it is specified in
          each subclass (A queryset obtained from the Tracked* models will have a created_on and
          updated_on models as shortcuts).
        :param request:
        :param queryset:
        :return: filtered queryset.
        """

        return getattr(queryset, self.PERIOD_DATE_METHOD)(self.value())


class CreatePeriodFilter(PeriodFilter):

    PERIOD_DATE_METHOD = 'created_on'
    parameter_name = 'created_on_period'
    title = _('creation period')


class UpdatePeriodFilter(PeriodFilter):

    PERIOD_DATE_METHOD = 'updated_on'
    parameter_name = 'updated_on_period'
    title = _('update period')
