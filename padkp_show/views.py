import datetime as dt

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader

from rest_framework import viewsets, routers

from django.db.models import Sum
from .models import Purchase, Character, RaidDump, DkpSpecialAward, CharacterAlt
from .models import CasualPurchase, CasualCharacter, CasualRaidDump, CasualDkpSpecialAward
from .models import DON_RELEASE


def index(request):
    template = loader.get_template('padkp_show/index.html')

    dumps = RaidDump.objects.values(
        'characters_present').annotate(value=Sum('value'))
    total_earned = {x['characters_present']: x['value'] for x in dumps}
    print(total_earned)

    purchases = Purchase.objects.filter(is_alt=False).values(
        'character').annotate(value=Sum('value'))
    total_spent = {x['character']: x['value'] for x in purchases}
    extra_awards = DkpSpecialAward.objects.values(
        'character').annotate(value=Sum('value'))
    total_extra = {x['character']: x['value'] for x in extra_awards}

    alt_dumps = RaidDump.objects.filter(time__gte=DON_RELEASE).values(
        'characters_present').annotate(value=Sum('value'))
    alt_total_earned = {x['characters_present']: x['value'] for x in dumps}
    alt_purchases = Purchase.objects.filter(is_alt=True).values(
        'character').annotate(value=Sum('value'))
    alt_total_spent = {x['character']: x['value'] for x in purchases}
    alt_extra_awards = DkpSpecialAward.objects.filter(
        time__gte=DON_RELEASE).values('character').annotate(value=Sum('value'))
    alt_total_extra = {x['character']: x['value'] for x in extra_awards}

    result = []
    for character in Character.objects.all().filter(name__in=total_earned.keys()):
        if character.status in ('INA', 'ALT') or character.inactive or character.leave_of_absence:
            continue
        spent = total_spent.get(character.name, 0)
        earned = total_earned.get(character.name, 0) + \
            total_extra.get(character.name, 0)
        result.append({'name': character.name, 'character_class': character.character_class,
                       'character_status': character.get_status_display(), 'current_dkp': earned - spent})
    result = sorted(result, key=lambda x: x['name'])
    return HttpResponse(template.render({'records': result}, request))


def attendance_table(request):
    template = loader.get_template('padkp_show/attendance.html')

    dumps = RaidDump.objects.values('characters_present').annotate(
        attendance_value=Sum('attendance_value'))
    total_earned = {x['characters_present']: x['attendance_value'] for x in dumps}

    extra_awards = DkpSpecialAward.objects.values(
        'character').annotate(attendance_value=Sum('attendance_value'))
    total_extra = {x['character']: x['attendance_value'] for x in extra_awards}

    total_dumps = sum(dump.attendance_value for dump in RaidDump.objects.all())

    result = []
    for character in Character.objects.all().filter(name__in=total_earned.keys()):
        if character.status in ['INA', 'ALT']:
            continue
        if character.inactive or character.leave_of_absence:
            continue
        attendance = '%.1f' % (character.attendance(30))
        if attendance == '0.0':
            continue
        attendance_90 = '%.1f' % (character.attendance(90))

        result.append({'name': character.name, 'character_class': character.character_class,
                       'character_status': character.get_status_display(),
                       'attendance': attendance,
                       'attendance_90': attendance_90})
    result = sorted(result, key=lambda x: float(x['attendance']), reverse=True)

    extra = {'total_dumps': total_dumps,
             'total_earned': total_earned, 'total_extra': total_extra}
    return HttpResponse(template.render({'records': result, 'extra': extra}, request))


def character_dkp(request, character):
    template = loader.get_template('padkp_show/character_page.html')
    character = character.capitalize()
    c_obj = Character.objects.get(name=character)
    dumps = RaidDump.objects.filter(
        characters_present=character).aggregate(total=Sum('value'))
    purchases = Purchase.objects.filter(
        character=character).aggregate(total=Sum('value'))
    extra_awards = DkpSpecialAward.objects.filter(
        character=character).aggregate(total=Sum('value'))

    alts = CharacterAlt.objects.filter(main=c_obj)
    alt_names = [x.name for x in alts]
    alt_string = "None." if not alt_names else ", ".join(alt_names)

    current_dkp = c_obj.current_dkp()
    alt_dkp = c_obj.current_alt_dkp()
    attendance_30 = '%.1f' % (c_obj.attendance(30))

    days_ago_30 = dt.datetime.utcnow() - dt.timedelta(days=30)
    days_ago_14 = dt.datetime.utcnow() - dt.timedelta(days=14)
    present_awards_14 = sorted([x for x in RaidDump.objects.filter(time__gte=days_ago_30, characters_present=character)] +
                               [x for x in DkpSpecialAward.objects.filter(
                                   time__gte=days_ago_30, character=character)],
                               key=lambda x: x.time, reverse=True)
    missed_awards_14 = sorted([x for x in RaidDump.objects.filter(time__gte=days_ago_30).exclude(characters_present=character)],
                              key=lambda x: x.time, reverse=True)
    awards_14 = [{'award': x, 'present': True} for x in present_awards_14] + \
                [{'award': x, 'present': False} for x in missed_awards_14]
    awards_14 = sorted(awards_14, key=lambda x: x['award'].time, reverse=True)

    purchases_30 = [str(x) for x in Purchase.objects.filter(
        time__gte=days_ago_30, character=character).order_by('-time')]

    if c_obj.inactive:
        display_rank = 'Inactive'
    elif c_obj.leave_of_absence:
        display_rank = 'Leave of Absence'
    else:
        display_rank = c_obj.get_status_display()

    context = {'attendance_30': attendance_30,
               'current_dkp': current_dkp,
               'alt_dkp': alt_dkp,
               'alt_string': alt_string,
               'name': c_obj.name,
               'character_class': c_obj.character_class,
               'rank': display_rank,
               'purchases_30': purchases_30,
               'awards_14': awards_14
               }

    return HttpResponse(template.render(context, request))


def items(request):
    template = loader.get_template('padkp_show/items.html')

    months_ago_3 = dt.datetime.utcnow() - dt.timedelta(days=90)
    purchases = Purchase.objects.filter(
        time__gt=months_ago_3).order_by('-time')
    result = list(purchases)

    return HttpResponse(template.render({'records': result, 'show_all_link': True}, request))


def all_items(request):
    template = loader.get_template('padkp_show/items.html')

    purchases = Purchase.objects.all().order_by('-time')
    result = list(purchases)

    return HttpResponse(template.render({'records': result, 'show_all_link': False}, request))


def awards(request):
    template = loader.get_template('padkp_show/awards.html')

    dumps = RaidDump.objects.all().order_by('-time')
    result = list(dumps)

    return HttpResponse(template.render({'records': result}, request))


def rules(request):
    return redirect('https://docs.google.com/document/d/1guXmdDGmH96ilpwgZGMlfc3-Moofp3y2iaAErzyeIGw')
    # template = loader.get_template('padkp_show/rules.html')
    # return HttpResponse(template.render())


def discord(request):
    return redirect('https://discord.gg/rxh36B6zSn')


def class_balance_table(request):
    template = loader.get_template('padkp_show/classes.html')
    days_ago_30 = dt.datetime.utcnow() - dt.timedelta(days=30)
    days_ago_90 = dt.datetime.utcnow() - dt.timedelta(days=90)

    name_class_map = {
        c.name: c.character_class for c in Character.objects.all()}

    counts = {character_class: 0 for character_class in name_class_map.values()}
    n_dumps = 0

    for dump in RaidDump.objects.filter(time__gte=days_ago_30):
        n_dumps += 1
        for character in dump.characters_present.all():
            if character.status == 'MN':
                counts[character.character_class] += 1
    class_counts_30 = {}
    for character_class, count in counts.items():
        class_counts_30[character_class] = '%.1f' % (float(count) / n_dumps)

    for dump in RaidDump.objects.filter(time__gte=days_ago_90):
        n_dumps += 1
        for character in dump.characters_present.all():
            if character.status == 'MN':
                counts[character.character_class] += 1
    class_counts_90 = {}
    for character_class, count in counts.items():
        class_counts_90[character_class] = '%.1f' % (float(count) / n_dumps)

    result = []
    for character_class in counts:
        if character_class in ['Shadow', 'Unknown']:
            continue
        result.append({'character_class': character_class,
                       'counts_30': class_counts_30[character_class],
                       'counts_90': class_counts_90[character_class]}
                      )
    result = sorted(result, key=lambda record: record['character_class'])
    totals = {'total_30': sum(float(x['counts_30']) for x in result),
              'total_90': sum(float(x['counts_90']) for x in result)}

    return HttpResponse(template.render({'records': result, 'totals': totals}, request))


def casual_index(request):
    template = loader.get_template('padkp_show/casual_index.html')

    dumps = CasualRaidDump.objects.values(
        'characters_present').annotate(value=Sum('value'))
    total_earned = {x['characters_present']: x['value'] for x in dumps}
    print(total_earned)

    purchases = CasualPurchase.objects.values(
        'character').annotate(value=Sum('value'))
    total_spent = {x['character']: x['value'] for x in purchases}
    print(total_spent)
    extra_awards = CasualDkpSpecialAward.objects.values(
        'character').annotate(value=Sum('value'))
    total_extra = {x['character']: x['value'] for x in extra_awards}

    result = []
    for character in CasualCharacter.objects.all():
        spent = total_spent.get(character.name, 0)
        earned = total_earned.get(character.name, 0) + \
            total_extra.get(character.name, 0)
        result.append({'name': character.name,
                       'character_class': character.character_class,
                       'current_dkp': earned - spent})
    result = sorted(result, key=lambda x: x['name'])
    return HttpResponse(template.render({'records': result}, request))


def casual_character_dkp(request, character):
    template = loader.get_template('padkp_show/casual_character_page.html')
    character = character.capitalize()
    c_obj = CasualCharacter.objects.get(name=character)
    dumps = CasualRaidDump.objects.filter(
        characters_present=character).aggregate(total=Sum('value'))
    purchases = CasualPurchase.objects.filter(
        character=character).aggregate(total=Sum('value'))
    extra_awards = CasualDkpSpecialAward.objects.filter(
        character=character).aggregate(total=Sum('value'))

    current_dkp = (dumps['total'] or 0) \
        + (extra_awards['total'] or 0) \
        - (purchases['total'] or 0)

    days_ago_30 = dt.datetime.utcnow() - dt.timedelta(days=30)
    present_awards_30 = sorted([x for x in CasualRaidDump.objects.filter(time__gte=days_ago_30, characters_present=character)] +
                               [x for x in CasualDkpSpecialAward.objects.filter(
                                   time__gte=days_ago_30, character=character)],
                               key=lambda x: x.time, reverse=True)
    missed_awards_30 = sorted([x for x in CasualRaidDump.objects.filter(time__gte=days_ago_30).exclude(characters_present=character)],
                              key=lambda x: x.time, reverse=True)
    awards_30 = [{'award': x, 'present': True} for x in present_awards_30] + \
                [{'award': x, 'present': False} for x in missed_awards_30]
    awards_30 = sorted(awards_30, key=lambda x: x['award'].time, reverse=True)

    purchases_30 = [str(x) for x in CasualPurchase.objects.filter(
        time__gte=days_ago_30, character=character).order_by('-time')]

    context = {
        'current_dkp': current_dkp,
        'name': c_obj.name,
        'character_class': c_obj.character_class,
        'purchases_30': purchases_30,
        'awards_30': awards_30
    }

    return HttpResponse(template.render(context, request))
