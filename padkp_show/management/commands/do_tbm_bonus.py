import datetime as dt
from padkp_show.models import Character, RaidDump

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Perform TBM 31 dkp bonus'
    overrides = {
        'Aggravain': 37.74,
        'Bathmatt': 0,
        'Bont': 84.91,
        'Casir': 49.06,
        'Claracal': 77.36,
        'Darkith': 5.66,
        'Dramij': 83.02,
        'Eaiamar': 0,
        'Finibar': 30.19,
        'Fixel': 30.19,
        'Flashpointe': 98.11,
        'Gobi': 92.45,
        'Grav': 56.6,
        'Hanover': 24.53,
        'Healfizzle': 52.83,
        'Ideal': 0,
        'Josida': 100,
        'Jovox': 92.45,
        'Kaitsumi': 100,
        'Kaleesi': 79.25,
        'Keghor': 64.15,
        'Kingkiller': 45.28,
        'Kudu': 100,
        'Kyfho': 73.58,
        'Lagoli': 62.26,
        'Landholder': 88.68,
        'Litning': 30.19,
        'Mago': 3.77,
        'Marley': 45.28,
        'Mcgibblets': 0,
        'Mooshiee': 96.23,
        'Myzerker': 58.49,
        'Nonia': 62.26,
        'Parabelluum': 64.15,
        'Piupiu': 86.79,
        'Raramor': 86.79,
        'Relannaa': 13.21,
        'Shaerin': 0,
        'Shalamar': 22.64,
        'Shuger': 98.11,
        'Siodan': 84.91,
        'Skute': 62.26,
        'Songeater': 100,
        'Thrombosis': 98.11,
        'Thundaer': 94.34,
        'Tyryn': 79.25,
        'Valelena': 33.96,
        'Volkert': 75.47,
        'Warrack': 84.91,
        'Wayout': 100,
        'Wetank': 100,
        'Zigee': 56.6,
        'Zingoro': 90.57
    }


    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for character in Character.objects.all():
            attendance = character.attendance(30)
            if character.name in self.overrides:
                attendance = self.overrides[character.name]
            bonus = int(attendance/5)
            character.cap_alt_dkp(500, dry_run=False)
            if bonus > 0:
                character.give_bonus(bonus, 'TDS Bonus: 31 dkp max based on 30 day attendance', dry_run=False)
