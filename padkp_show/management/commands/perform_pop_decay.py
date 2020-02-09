import datetime as dt
from padkp_show.models import Character, RaidDump

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Perform planes of power decay'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        days_ago_75 = dt.datetime.utcnow() - dt.timedelta(days=75)
        characters_raided_last_75_q = RaidDump.objects.filter(time__gte=days_ago_75).values('characters_present')
        characters_raided_last_75 = set(x['characters_present'] for x in characters_raided_last_75_q)
        characters_to_cap = Character.objects.exclude(name__in=list(characters_raided_last_75))
        for character in characters_to_cap:
            capped = character.cap_dkp(50, 'cap of 50 DKP for characters inactive 75 days or more', dry_run=False)

        for character in Character.objects.all():
            character.decay_dkp(0.5, '50% DKP decay for planes of power', dry_run=False)

        for character in Character.objects.all():
            if character.attendance(30) >= 50:
                character.give_bonus(40, 'Bonus for >50% attendance in the last 30 days of luclin', dry_run=False)

