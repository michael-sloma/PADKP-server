"""
API used by the desktop auction manager client to charge and award DKP
"""
import datetime as dt

from django.core.exceptions import ObjectDoesNotExist

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
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
        split_line = line.split('\t')
        name = split_line[1]
        character_class = split_line[3]
        result.append({'name': name, 'character_class': character_class})
    return result


def _get_or_create_characters(chars):
    char_names = [char['name'] for char in chars]
    char_obj = models.Character.objects.filter(name__in=char_names)
    char_index = {c_obj.name: c_obj for c_obj in char_obj}

    result = []
    for char in chars:
        if char['name'] in char_index:
            result.append(char_index[char['name']])
        else:
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
        characters = _parse_dump(dump_contents)
        characters_present = _get_or_create_characters(characters)

        value = request.data['value']
        attendance_value = 1 if request.data['counts_for_attendance'] else 0
        filename = request.data['filename']
        time = dt.datetime.strptime(filename, 'RaidRoster_mangler-%Y%m%d-%H%M%S.txt')
        notes = request.data['notes']
        award_type = request.data['award_type']

        dump = models.RaidDump(value=value, attendance_value=attendance_value, filename=filename,
                               time=time, notes=notes, award_type=award_type)
        dump.save()
        dump.characters_present.set(characters_present)
        return Response('Raid dump upload successful', status=status.HTTP_201_CREATED)



class ChargeDKP(viewsets.ViewSet):
    """ Charge DKP for an item """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = models.Purchase.objects.all()

    def create(self, request):
        cname = request.data['character']
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
            notes=request.data['notes']
        ).save()
        return Response('DKP charge successful', status=status.HTTP_201_CREATED)


class CharacterViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CharacterSerializer
    queryset = models.Character.objects.all()


class DkpSpecialAwardViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.DkpSpecialAwardSerializer
    queryset = models.DkpSpecialAward.objects.all()
