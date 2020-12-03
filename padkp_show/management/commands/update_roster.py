import datetime as dt
from padkp_show.models import Character, RaidDump
from django.core.exceptions import ObjectDoesNotExist

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Update DKP site roster based on a guild dump'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        roster_characters = set()
        for row in open('guild_roster.txt'):
            split = row.split('\t')
            name = split[0]
            roster_characters.add(name)
            character_class = split[2]
            rank = split[3]
            note = split[7]

            try:
                char_obj = Character.objects.get(name=name)
                alt_status = note.lower().startswith('alt')
                fnf_status = not alt_status and rank.lower().startswith('friends,')
                inactive_status = rank.lower().startswith('inactive')
                recruit_status = rank.lower().startswith('recruit')
                if alt_status:
                    alt_of = note.strip().split()[1]
                else:
                    alt_of = None
                print(name, alt_status, alt_of, fnf_status)


                if alt_status:
                    char_obj.status = 'ALT'
                elif fnf_status:
                    char_obj.status = 'FNF'
                elif inactive_status:
                    char_obj.status = 'INA'
                    char_obj.inactive = True
                elif recruit_status:
                    char_obj.status = 'REC'
                else:
                    char_obj.status = 'MN'
                char_obj.save()

            except ObjectDoesNotExist:
                pass
        for char in Character.objects.all():
            if char.name not in roster_characters:
                char.delete()
