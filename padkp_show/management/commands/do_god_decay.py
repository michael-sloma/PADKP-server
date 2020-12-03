import datetime as dt
from padkp_show.models import Character, RaidDump

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Perform planes of power decay'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for character in Character.objects.all():
            character.decay_dkp(0.8, '80% DKP decay for gates of discord', dry_run=False)
            attendance = character.attendance(30)
            if attendance >= 50:
                character.give_bonus(int(attendance/2.), 'GoD bonus: 50% of 30 day attendance', dry_run=False)

