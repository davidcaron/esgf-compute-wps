# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-16 17:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wps', '0002_jobstate_created'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='JobState',
            new_name='Status',
        ),
        migrations.RenameField(
            model_name='status',
            old_name='state',
            new_name='status',
        ),
    ]
