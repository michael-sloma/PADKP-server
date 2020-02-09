import datetime as dt
from padkp_show.models import Character, RaidDump

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Set players that have not raided in a while to inactive'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        days_ago_30 = dt.datetime.utcnow() - dt.timedelta(days=30)
        characters_raided_last_30_q = RaidDump.objects.filter(time__gte=days_ago_30).values('characters_present')
        characters_raided_last_30 = set(x['characters_present'] for x in characters_raided_last_30_q)

        characters_to_check_inactive = Character.objects.exclude(name__in=list(characters_raided_last_30))
        for char in characters_to_check_inactive:
            today = dt.datetime.now().date()
            if not char.leave_of_absence:
                char.inactive = True
                char.date_inactive = today
                char.save()
            if (today - char.date_inactive) >= dt.timedelta(days=45):
                char.cap_dkp(50,
                             'Capped DKP at 50 because character went inactive on {} and was still inactive on {}'.format(char.date_inactive, today),
                             dry_run=False)

