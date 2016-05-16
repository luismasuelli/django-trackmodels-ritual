from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from dateutils import relativedelta


class TrackedLiveQuerySet(models.QuerySet):
    """
    Takes advantage from the created_on and updated_on fields to perform many additional queries.
    """

    @classmethod
    def _quarter_month(cls, month):
        """
        For a given month, returns the corresponding month starting its quarter (1, 4, 7, 10)
        :param month: The current month
        :return: The quarter month
        """
        if month > 9:
            return 10
        if month > 6:
            return 7
        if month > 3:
            return 4
        return 1

    @classmethod
    def _semester_month(cls, month):
        """
        For a given month, returns the corresponding month starting its semester (1, 7)
        :param month: The current month
        :return: The semester month
        """
        if month > 6:
            return 7
        return 1

    @classmethod
    def _period_date(cls, period):
        """
        Computes the period to filter (d=1-day, w=1-week, m=1-month, q=3-months, h=6-months, y=1-year).
        Additional options: D=today, M=this-month, Q=this-quarter, H=this-semester, Y=this-year
        Returns an interval as a tuple (start, end) where the end date is a result of now() and the
          start date is a result of now() - (days or months before).
        :param period: A single-character value in [dwmqhy]. Any other value will raise a KeyError.
        :raises: KeyError if the period is not valid.
        :returns: a tuple (start, end) of datetime objects.
        """

        now_ = now()
        return {
            'd': now_ - relativedelta(days=1),
            'w': now_ - relativedelta(weeks=1),
            'm': now_ - relativedelta(months=1),
            'q': now_ - relativedelta(months=3),
            'h': now_ - relativedelta(months=6),
            'y': now_ - relativedelta(years=1),
            'D': now_.replace(hour=0, minute=0, second=0, microsecond=0),
            'M': now_.replace(hour=0, minute=0, second=0, microsecond=0, day=1),
            'Q': now_.replace(hour=0, minute=0, second=0, microsecond=0, day=1, month=cls._quarter_month(now_.month)),
            'H': now_.replace(hour=0, minute=0, second=0, microsecond=0, day=1, month=cls._semester_month(now_.month)),
            'Y': now_.replace(hour=0, minute=0, second=0, microsecond=0, day=1, month=1),
        }[period], now_

    def created_on(self, period):
        """
        Filters by objects being created on certain periods (d, w, m, h, y, D, M, Q, H, Y).
        Read more in _period_date(period) documentation about period meaning.
        :param period: A single-character value in [dwmqhyDMQHY]. Any other value will raise a KeyError.
        :raises: KeyError if the period is not valid.
        :returns: A queryset, filtered with creation date between now and a specific period ago.
        """

        return self.filter(created_on__range=self._period_date(period))

    def updated_on(self, period):
        """
        Filters by objects being updated on certain periods (d, w, m, h, y, D, M, Q, H, Y).
        Read more in _period_date(period) documentation about period meaning.
        :param period: A single-character value in [dwmqhyDMQHY]. Any other value will raise a KeyError.
        :raises: KeyError if the period is not valid.
        :returns: A queryset, filtered with update date between now and a specific period ago.
        """

        return self.filter(updated_on__range=self._period_date(period))


class TrackedLiveAndDeadQuerySet(TrackedLiveQuerySet):
    """
    Takes advantage of the deleted_on field to perform an additional implicit filter on all().
    With this filter on, elements being deleted will not be visible anymore by queryset.
    """

    def all(self, seriously=False):
        """
        Ask by .all() also filters by having deleted_on in null.
        If seriously, then the former behavior is called instead.
        """

        qs = super(TrackedLiveAndDeadQuerySet, self).all()
        return qs if seriously else qs.filter(deleted_on__isnull=True)

    def delete(self, seriously=False):
        """
        Marks elements as deleted.
        If seriously, then the former behavior is called instead.
        """

        return super(TrackedLiveAndDeadQuerySet, self).delete() if seriously else self.update(deleted_on=now())

    def dead(self):
        """
        Lists the dead elements. It is the opposite of all([seriously=False]).
        """

        return super(TrackedLiveAndDeadQuerySet, self).filter(deleted_on__isnull=False)


class TrackedLive(models.Model):
    """
    Models are tracked by date. It holds create and update dates.
    """

    created_on = models.DateTimeField(default=now, null=False, editable=False, verbose_name=_(u"Creation Date"),
                                      help_text=_(u"Date and time of record creation"))
    updated_on = models.DateTimeField(default=now, null=False, editable=False, verbose_name=_(u"Update Date"),
                                      help_text=_(u"Date and time of last record update"))

    objects = TrackedLiveQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        Overrides usual save() behavior to also update (unless explicitly commanded to not do so)
          the updated_on date.
        :param force_insert:
        :param force_update:
        :param using:
        :param update_fields:
        :return:
        """

        if not update_fields or '-updated_on' not in update_fields:
            self.updated_on = now()
        else:
            index = update_fields.index('-updated_on')
            update_fields = update_fields[:index] + update_fields[index+1:]
        return super(TrackedLive, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                             update_fields=update_fields)


class TrackedLiveAndDead(TrackedLive):
    """
    This class allows logical deletion instead of physical. It does so by adding a deletion date field.
    Since it extends the TrackedLive behavior, it also has those fields.
    """

    deleted_on = models.DateTimeField(null=True, editable=False, verbose_name=_(u"Deletion Date"),
                                      help_text=_(u"Date and time of record deletion"))

    objects = TrackedLiveAndDeadQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, using=None, seriously=False):
        """
        Deletes an object, but logically (not from database).
        :param using:
        :return:
        """

        if seriously:
            return super(TrackedLiveAndDead, self).delete(using=using)
        else:
            self.deleted_on = now()
            return self.save(using=using, update_fields=('deleted_on', '-updated_on'))


class TrackedUserCreated(models.Model):
    """
    This class allows specifying a creator for an object.
    """

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, editable=False, related_name="+",
                                   verbose_name=_(u"Created By"), help_text=_(u"User marked as creator of this record"))

    class Meta:
        abstract = True


class TrackedUserOwned(models.Model):
    """
    This class allows specifying an owner for an object.
    """

    owned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, related_name="+", verbose_name=_(u"Owned By"),
                                 help_text=_(u"User marked as owner of this record"))

    class Meta:
        abstract = True
