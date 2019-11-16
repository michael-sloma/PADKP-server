from django.contrib import admin

from .models import Character, Purchase, RaidDump, DkpSpecialAward

admin.site.register(Character)
admin.site.register(Purchase)
admin.site.register(RaidDump)
admin.site.register(DkpSpecialAward)
