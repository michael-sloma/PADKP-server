import datetime as dt
from padkp_show.models import Character, RaidDump, DkpSpecialAward

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'undo fuckup'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        one_hour_ago = dt.datetime.utcnow() - dt.timedelta(hours=1)
        for a in DkpSpecialAward.objects.all().filter(time__gte=one_hour_ago):

            print('deleting', a)
            a.delete()
