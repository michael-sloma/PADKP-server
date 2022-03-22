import datetime as dt
from padkp_show.models import Character, RaidDump

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Merge all dumps up to N days ago into one new dump'

    def add_arguments(self, parser):
        parser.add_argument('day_range')

    def handle(self, *args, **options):
        days_ago = dt.datetime.utcnow() - dt.timedelta(days=int(options['day_range']))
        dumps = RaidDump.objects.filter(time__gte=days_ago).values('characters_present')
        character_list = set(x['characters_present'] for x in dumps)

        dump = RaidDump(value=0, attendance_value=0,
                        filename='manual_dump_merge.txt', time=dt.datetime.utcnow(), notes='Manual combined raid dump',
                        award_type='Other')
        dump.save()
        dump.characters_present.set(character_list)

