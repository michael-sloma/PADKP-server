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
    for character in Character.objects.all().filter(name__in=total_earned.keys()):
        if character.status == 'INA' or character.attendance(30) == 0:
            continue
        spent = total_spent.get(character.name, 0)
        earned = total_earned.get(character.name, 0) + total_extra.get(character.name, 0)
        result.append({'name': character.name, 'character_class': character.character_class,
                       'character_status': character.get_status_display(), 'current_dkp': earned - spent})
    result = sorted(result, key=lambda x: x['name'])
    return HttpResponse(template.render({'records': result}, request))


def attendance_table(request):
    template = loader.get_template('padkp_show/attendance.html')

    dumps = RaidDump.objects.values('characters_present').annotate(attendance_value=Sum('attendance_value'))
    total_earned = {x['characters_present']: x['attendance_value'] for x in dumps}

    extra_awards = DkpSpecialAward.objects.values('character').annotate(attendance_value=Sum('attendance_value'))
    total_extra = {x['character']: x['attendance_value'] for x in extra_awards}

    total_dumps = sum(dump.attendance_value for dump in RaidDump.objects.all())

    result = []
    for character in Character.objects.all().filter(name__in=total_earned.keys()):
        if character.status in ['INA', 'ALT']:
            continue
        attendance = '%.1f' % (character.attendance(30))
        if attendance == '0.0':
            continue

        result.append({'name': character.name, 'character_class': character.character_class,
                       'character_status': character.get_status_display(), 'attendance': attendance})
    result = sorted(result, key=lambda x: float(x['attendance']), reverse=True)

    extra = {'total_dumps': total_dumps, 'total_earned': total_earned, 'total_extra': total_extra}
    return HttpResponse(template.render({'records': result, 'extra': extra}, request))


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

    attendance_30 = '%.1f' % (c_obj.attendance(30))

    days_ago_30 = dt.datetime.utcnow() - dt.timedelta(days=30)
    days_ago_14 = dt.datetime.utcnow() - dt.timedelta(days=14)
    present_awards_14 = sorted([x for x in RaidDump.objects.filter(time__gte=days_ago_30, characters_present=character)] +
                               [x for x in DkpSpecialAward.objects.filter(time__gte=days_ago_30, character=character)],
                               key = lambda x: x.time, reverse=True)
    missed_awards_14 = sorted([x for x in RaidDump.objects.filter(time__gte=days_ago_14).exclude(characters_present=character)],
                              key = lambda x: x.time, reverse=True)
    awards_14 = [{'award': x, 'present': True} for x in present_awards_14] + \
                [{'award': x, 'present': False} for x in missed_awards_14]
    awards_14 = sorted(awards_14, key=lambda x: x['award'].time, reverse=True)

    purchases_30 = [str(x) for x in Purchase.objects.filter(time__gte=days_ago_30, character=character).order_by('-time')]

    context = {'attendance_30': attendance_30,
               'current_dkp': current_dkp,
               'name': c_obj.name,
               'character_class': c_obj.character_class,
               'rank': c_obj.get_status_display(),
               'purchases_30': purchases_30,
               'awards_14': awards_14
               }

    return HttpResponse(template.render(context, request))


def items(request):
    template = loader.get_template('padkp_show/items.html')

    purchases = Purchase.objects.all().order_by('-time')
    result = list(purchases)

    return HttpResponse(template.render({'records': result}, request))


def awards(request):
    template = loader.get_template('padkp_show/awards.html')

    dumps = RaidDump.objects.all().order_by('-time')
    result = list(dumps)

    return HttpResponse(template.render({'records': result}, request))

