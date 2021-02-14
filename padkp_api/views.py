"""
API used by the desktop auction manager client to charge and award DKP
"""
import datetime as dt
import random

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication, BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from . import serializers
from padkp_show import models


def _parse_dump(dump_contents):
    result = []
    for line in dump_contents.split('\n'):
        if not line.strip():
            continue
        print(line)
        split_line = line.split()
        name = split_line[1]
        character_class = split_line[3]
        result.append({'name': name, 'character_class': character_class})
    return result


def _get_or_create_characters(chars, create=True):
    char_names = [char['name'] for char in chars]
    char_obj = models.Character.objects.filter(name__in=char_names)
    char_index = {c_obj.name: c_obj for c_obj in char_obj}

    result = []
    for char in chars:
        if char['name'] in char_index:
            result.append(char_index[char['name']])
        elif create:
            new_char = models.Character(name=char['name'],
                                        character_class=char['character_class'],
                                        status='Recruit')
            new_char.save()
            result.append(new_char)
    print('character list', result)
    return result


class UploadRaidDump(viewsets.ViewSet):
    """ upload a raid dump file and award dkp """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = models.RaidDump.objects.all()

    def create(self, request):
        dump_contents = request.data['dump_contents']
        waitlist = request.data.get('waitlist', [])
        characters = _parse_dump(dump_contents)
        characters += [{'name': x, 'character_class': 'Unknown'}
                       for x in waitlist]
        characters_present = _get_or_create_characters(characters)
        characters_present = [
            c for c in characters_present if c.status != 'ALT']

        value = request.data['value']
        attendance_value = 1 if request.data['counts_for_attendance'] else 0
        filename = request.data['filename']

        if 'time' in request.data:
            time = request.data['time']
        else:
            # older client versions expect the server to decode the time from
            # the dump file name. we will continue to support this for now.
            # it does cause problems for timezone support because we don't know
            # the local time of the client
            time = dt.datetime.strptime(
                filename, 'RaidRoster_mangler-%Y%m%d-%H%M%S.txt')

        notes = request.data['notes']
        award_type = request.data['award_type']

        dump_query = models.RaidDump.objects.filter(time=time)

        if len(dump_query) == 1:
            dump = dump_query.get()
            new_characters = list(
                set([c for c in dump.characters_present.all()]) | set(characters_present))
            dump.characters_present.set(new_characters)
        else:
            dump = models.RaidDump(value=value, attendance_value=attendance_value,
                                   filename=filename, time=time, notes=notes,
                                   award_type=award_type)
            dump.save()
            dump.characters_present.set(characters_present)

        return Response('Raid dump upload successful', status=status.HTTP_201_CREATED)


class UploadCasualRaidDump(viewsets.ViewSet):
    """ upload a raid dump file and award dkp """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = models.RaidDump.objects.all()

    def create(self, request):
        dump_contents = request.data['dump_contents']
        waitlist = request.data.get('waitlist', [])
        characters = [c['name'] for c in _parse_dump(dump_contents)]
        characters += waitlist
        characters_present = models.CasualCharacter.objects.filter(
            name__in=characters)

        value = request.data['value']
        filename = request.data['filename']

        if 'time' in request.data:
            time = request.data['time']
        else:
            # older client versions expect the server to decode the time from
            # the dump file name. we will continue to support this for now.
            # it does cause problems for timezone support because we don't know
            # the local time of the client
            time = dt.datetime.strptime(
                filename, 'RaidRoster_mangler-%Y%m%d-%H%M%S.txt')

        notes = request.data['notes']

        dump = models.CasualRaidDump(
            value=value, filename=filename, time=time, notes=notes)
        dump.save()
        dump.characters_present.set(characters_present)
        return Response('Raid dump upload successful', status=status.HTTP_201_CREATED)


class ChargeDKP(viewsets.ViewSet):
    """ Charge DKP for an item """
    authentication_classes = [TokenAuthentication,
                              BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = models.Purchase.objects.all()

    def create(self, request):
        cname = request.data['character']
        try:
            alt_obj = models.CharacterAlt.objects.get(pk=cname)
            character_obj = alt_obj.main
        except ObjectDoesNotExist:
            try:
                character_obj = models.Character.objects.get(pk=cname)
            except ObjectDoesNotExist:
                return Response('{} does not exist in the database. Create the character first!'.format(cname),
                                status=status.HTTP_400_BAD_REQUEST)
        models.Purchase(
            character=character_obj,
            item_name=request.data['item_name'],
            value=request.data['value'],
            time=request.data['time'],
            notes=request.data['notes'],
            is_alt=request.data['is_alt'],
        ).save()
        return Response('DKP charge successful', status=status.HTTP_201_CREATED)


class CharacterViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CharacterSerializer
    queryset = models.Character.objects.all()


class DkpSpecialAwardViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.DkpSpecialAwardSerializer
    queryset = models.DkpSpecialAward.objects.all()


class Tiebreak(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication,
                              BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = models.Character.objects.all()

    def create(self, request):
        raw_names = request.data.get('characters', [])
        bid_names = {}
        names = []
        for name in raw_names:
            new_name = name.replace("'s alt", "")
            names.append(new_name)
            bid_names[new_name] = name

        alts = models.CharacterAlt.objects.filter(name__in=names)
        alt_names = [x.name for x in alts]
        names = [x for x in names if x not in alt_names]

        for alt in alts:
            old = bid_names.pop(alt.name)
            bid_names[alt.main.name] = old
            names.append(alt.main.name)

        characters = models.Character.objects.filter(name__in=names)
        result = tiebreak(characters, bid_names)
        return Response(result, status=status.HTTP_200_OK)


def tiebreak(characters, bid_names):
    def ordering(character, is_main):
        if is_main:
            return character.current_dkp(), character.attendance(30)
        return character.current_alt_dkp(), character.attendance(30)

    orderings = {bid_names[c.name]: ordering(
        c, c.name != bid_names[c.name]) for c in characters}

    def explain(name):
        dkp, attendance = orderings[name]
        return "{} has {} DKP and {} 30-day attendance".format(name, dkp, '%.2f' % attendance)
    names = [bid_names[c.name] for c in characters]
    random.shuffle(names)  # shuffle so unbreakable ties are decided at random
    winners = sorted(names, key=lambda name: orderings[name], reverse=True)
    return [(name, explain(name)) for name in winners]


class SecondClassCitizens(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication,
                              BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = models.Character.objects.all()

    def list(self, request):
        queryset = models.Character.objects.filter(inactive=True) | \
            models.Character.objects.filter(
                status__in=['ALT', 'INA', 'REC', 'FNF'])
        name_status_map = [{'name': c.name, 'status': c.get_status_display(
        ), 'inactive': c.inactive} for c in queryset]
        return Response(name_status_map, status=status.HTTP_200_OK)
