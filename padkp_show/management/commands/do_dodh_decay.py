import datetime as dt
from padkp_show.models import Character, RaidDump

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Perform DODH half decay plus bonus'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for character in Character.objects.all():
            character.decay_dkp(
                0.5, '50% DKP decay for Depths of Darkhollow', dry_run=False)
            attendance = character.attendance(30)
            character.give_bonus(
                int(attendance/2.), 'DoDH bonus: 50% of 30 day attendance', dry_run=False)
