from django.db import models
from .common import define_all

(
    TrackedLive, TrackedLiveAndDead, TrackedLiveQuerySet, TrackedLiveAndDeadQuerySet,
    TrackedUserCreated, TrackedUserOwned
) = define_all(models.QuerySet, models.Model)