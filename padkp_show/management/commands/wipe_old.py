import datetime as dt
from padkp_show.models import Character

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Wipe out characters from the site who have been gone more than 180 days'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print('running wipe_old script')

        days_ago_30 = dt.datetime.utcnow() - dt.timedelta(days=30)
        characters_raided_last_180_q = RaidDump.objects.filter(
            time__gte=days_ago_180).values('characters_present')
        characters_raided_last_180 = set(
            x['characters_present'] for x in characters_raided_last_180_q)

        characters_to_wipe = Character.objects.exclude(
            name__in=list(characters_raided_last_180))
        for char in characters_to_wipe:
            # if char.status == 'MN':
            print(char)

        print('wipe_old script complete')
