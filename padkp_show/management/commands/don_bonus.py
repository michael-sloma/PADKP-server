import datetime as dt
from padkp_show.models import Character, RaidDump

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'DON bonus: 25 dkp for everyone >=50% attendance'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for character in Character.objects.all():
            if character.attendance(30) >= 50:
                character.give_bonus(25, 'Bonus for >50% attendance in the last 30 days of omens', dry_run=False)

