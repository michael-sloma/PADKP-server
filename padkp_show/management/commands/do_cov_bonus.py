import datetime as dt
from padkp_show.models import Character, RaidDump

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Perform CoV 25 dkp bonus, and apply DKP Caps'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for character in Character.objects.all():
            attendance = character.attendance(30)
            bonus = int(attendance*25/100)
            character.cap_alt_dkp(500, dry_run=False)
            character.cap_dkp(600, "CoV Cap", dry_run=False)
            if bonus > 0:
                character.give_bonus(bonus, 'CoV: 25 dkp max based on 30 day attendance', dry_run=False)
