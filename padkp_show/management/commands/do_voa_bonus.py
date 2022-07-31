import datetime as dt
from padkp_show.models import Character, RaidDump

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Perform VoA 40 dkp bonus'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for character in Character.objects.all():
            bonus = int(character.attendance(30)/2.5)
            character.cap_alt_dkp(500, dry_run=False)
            if bonus > 0:
                character.give_bonus(bonus, 'VoA Bonus: 40 dkp max based on 30 day attendance', dry_run=False)
