# Generated by Django 2.1.15 on 2020-12-16 11:45

from django.db import migrations
from django.db.models.aggregates import Min, Max


def migrate_conference_from_to_dates(apps, schema_editor):
    """ One-Time sets the from_date and to_date for all existing conferences
        if not already set, to the dates of their min/max conference event times """
    
    CosinnusGroup = apps.get_model('cosinnus', 'CosinnusGroup')
    ConferenceEvent = apps.get_model('cosinnus_event', 'ConferenceEvent')
    for group in CosinnusGroup.objects.all():
        if group.type == 2: # is conference
            needs_save = False
            if not group.from_date:
                queryset = ConferenceEvent.objects.filter(room__group=group)
                if queryset.count() > 0:
                    group.from_date = queryset.aggregate(Min('from_date'))['from_date__min']
                    needs_save = True
            if not group.to_date:
                queryset = ConferenceEvent.objects.filter(room__group=group)
                if queryset.count() > 0:
                    group.to_date = queryset.aggregate(Max('to_date'))['to_date__max']
                    needs_save = True
                    
            if needs_save:
                group.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cosinnus', '0090_auto_20210204_1546'),
    ]

    operations = [
        migrations.RunPython(migrate_conference_from_to_dates, migrations.RunPython.noop),
    ]
