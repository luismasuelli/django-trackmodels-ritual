from __future__ import unicode_literals, absolute_import
from cantrips.features import Feature
from django.core.exceptions import ImproperlyConfigured
from .common import define_all
from django.conf import settings


class DjangoPolymorphicFeature(Feature):

    @classmethod
    def _import_it(cls):
        from polymorphic.models import PolymorphicModel
        from polymorphic.query import PolymorphicQuerySet
        return (PolymorphicModel, PolymorphicQuerySet)

    @classmethod
    def _import_error_message(cls):
        return "You need to install django-polymorphic package for this module to work (pip install django-polymorphic)"


(PolymorphicModel, PolymorphicQuerySet) = DjangoPolymorphicFeature.import_it()
if 'polymorphic' not in settings.INSTALLED_APPS or \
   'django.contrib.contenttypes' not in settings.INSTALLED_APPS:
    raise ImproperlyConfigured('For this application to work, both `polymorphic` and '
                               '`django.contrib.contenttypes` must be included in INSTALLED_APPS')


(
    TrackedLive, TrackedLiveAndDead, TrackedLiveQuerySet, TrackedLiveAndDeadQuerySet,
    TrackedUserCreated, TrackedUserOwned
) = define_all(PolymorphicQuerySet, PolymorphicModel)