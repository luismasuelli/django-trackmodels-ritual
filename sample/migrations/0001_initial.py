# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SampleRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, help_text='Date and time of record creation', verbose_name='Creation Date', editable=False)),
                ('updated_on', models.DateTimeField(default=django.utils.timezone.now, help_text='Date and time of last record update', verbose_name='Update Date', editable=False)),
                ('deleted_on', models.DateTimeField(help_text='Date and time of record deletion', verbose_name='Deletion Date', null=True, editable=False)),
                ('content', models.TextField(max_length=1024)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
