import datetime as dt
import pytz
from padkp_show.models import RaidDump, Character

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Remove character from dumps in a time range'

    def add_arguments(self, parser):
        parser.add_argument('name')
        parser.add_argument('date')
        parser.add_argument('start_time')
        parser.add_argument('end_time')

    def handle(self, *args, **options):
        eastern = pytz.timezone('US/Eastern')
        date = options['date']
        start_time = options['start_time']
        end_time = options['end_time']
        start = dt.datetime.strptime(' '.join([date, start_time]), '%Y-%m-%d %H:%M').replace(tzinfo=eastern)
        end = dt.datetime.strptime(' '.join([date, end_time]), '%Y-%m-%d %H:%M').replace(tzinfo=eastern)
        c_obj, = Character.objects.filter(name=options['name'])
        for raid_dump in RaidDump.objects.filter(time__gte=start, time__lte=end):
            if c_obj in raid_dump.characters_present.all():
                print('removing from dump at {}'.format(raid_dump.time))
                raid_dump.characters_present.remove(c_obj)
                raid_dump.save()
