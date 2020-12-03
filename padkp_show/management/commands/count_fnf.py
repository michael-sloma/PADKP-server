import datetime as dt
from padkp_show.models import Character, RaidDump

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Perform planes of power decay'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        days_ago_30 = dt.datetime.utcnow() - dt.timedelta(days=30)
        rd_last_30 = RaidDump.objects.all().filter(time__gte=days_ago_30)
        counts = []
        names = []
        for rd in rd_last_30:
            count = 0
            for c in rd.characters_present.all():
                if c.status=='FNF':
                    count += 1
                    names.append(c.name)
            counts.append(count)
        print(list(set(names)))
        print(sum(counts) / float(len(counts)))
