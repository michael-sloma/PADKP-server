import datetime as dt

from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from rest_framework import viewsets, routers

from django.db.models import Sum
from .models import Purchase, Character, RaidDump, DkpSpecialAward


def index(request):
    template = loader.get_template('padkp_show/index.html')

    dumps = RaidDump.objects.values('characters_present').annotate(value=Sum('value'))
    total_earned = {x['characters_present']: x['value'] for x in dumps}
    print(total_earned)

    purchases = Purchase.objects.values('character').annotate(value=Sum('value'))
    total_spent = {x['character']: x['value'] for x in purchases}
    print(total_spent)
    extra_awards = DkpSpecialAward.objects.values('character').annotate(value=Sum('value'))
    total_extra = {x['character']: x['value'] for x in extra_awards}

    result = []
    for character in Character.objects.all():
        spent = total_spent.get(character.name, 0)
        earned = total_earned.get(character.name, 0) + total_extra.get(character.name, 0)
        result.append({'name': character.name, 'character_class': character.character_class,
                       'character_status': character.status, 'current_dkp': earned - spent})

    return HttpResponse(template.render({'records': result}, request))


def character_dkp(request, character):
    template = loader.get_template('padkp_show/character_page.html')
    character = character.capitalize()
    c_obj = Character.objects.get(name=character)
    dumps = RaidDump.objects.filter(characters_present=character).aggregate(total=Sum('value'))
    purchases = Purchase.objects.filter(character=character).aggregate(total=Sum('value'))
    extra_awards = DkpSpecialAward.objects.filter(character=character).aggregate(total=Sum('value'))

    current_dkp = (dumps['total'] or 0) \
                  + (extra_awards['total'] or 0) \
                  - (purchases['total'] or 0)

    days_ago_60 = dt.datetime.utcnow() - dt.timedelta(days=60)
    raid_dumps_60 = RaidDump.objects.filter(time__gte=days_ago_60).aggregate(total=Sum('attendance_value'))
    my_raid_dumps_60 = RaidDump.objects.filter(time__gte=days_ago_60).filter(characters_present=character).aggregate(total=Sum('attendance_value'))
    my_awards_60 = DkpSpecialAward.objects.filter(time__gte=days_ago_60).filter(character=character).aggregate(total=Sum('attendance_value'))
    my_attendance_points = (my_raid_dumps_60['total'] or 0) + (my_awards_60['total'] or 0)
    attendance_60 = 100 * float(my_attendance_points) / raid_dumps_60['total']


    days_ago_30 = dt.datetime.utcnow() - dt.timedelta(days=30)
    raid_dumps_30 = RaidDump.objects.filter(time__gte=days_ago_30).aggregate(total=Sum('attendance_value'))
    my_raid_dumps_30 = RaidDump.objects.filter(time__gte=days_ago_30).filter(characters_present=character).aggregate(total=Sum('attendance_value'))
    my_awards_30 = DkpSpecialAward.objects.filter(time__gte=days_ago_30).filter(character=character).aggregate(total=Sum('attendance_value'))
    my_attendance_points = (my_raid_dumps_30['total'] or 0) + (my_awards_30['total'] or 0)
    attendance_30 = 100 * float(my_attendance_points) / raid_dumps_30['total']

    context = {'attendance_30': attendance_30,
               'attendance_60': attendance_60,
               'current_dkp': current_dkp,
               'name': c_obj.name,
               'character_class': c_obj.character_class,
               'rank': c_obj.status}

    return HttpResponse(template.render(context, request))


def character_awards(request, character):
    character = character.capitalize()
    awards = DkpAward.objects.filter(character=character)
    text = "\n".join(str(award) for award in awards)
    return HttpResponse(text)


def character_purchases(request, character):
    character = character.capitalize()
    purchases = Purchase.objects.filter(character=character)
    text = "\n".join(str(purchase) for purchase in purchases)
    return HttpResponse(text)


def character_page(request, character):
    name = character.capitalize()
    character = Character.objects.get(pk=name)
    awards = DkpAward.objects.filter(character=character)
    purchases = Purchase.objects.filter(character=character)
    pass

