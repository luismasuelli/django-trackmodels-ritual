from django.db import models
from grimoire.django.tracked import models as tracked_models


def uppercase_content(obj):
    return (obj.content or '').upper()
uppercase_content.short_description = 'content to uppercase'


class SampleRecord(tracked_models.TrackedLiveAndDead):
    """
    A dummy sample record, ready to be included in Admin.
    """

    content = models.TextField(max_length=1024, null=False, blank=False)
