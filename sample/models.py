from django.db import models
from grimoire.django.tracked import models as tracked_models


class SampleRecord(tracked_models.TrackedLiveAndDead):
    """
    A dummy sample record, ready to be included in Admin.
    """

    content = models.TextField(max_length=1024, null=False, blank=False)
