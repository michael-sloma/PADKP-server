from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import viewsets, routers

from django.db.models import Sum
from .models import Purchase, DkpAward


def index(request):
    return HttpResponse("Hello PA!")


def character_dkp(request, character):
    character = character.capitalize()
    awards = DkpAward.objects.filter(character=character).aggregate(Sum('value'))['value__sum'] or 0
    purchases = Purchase.objects.filter(character=character).aggregate(Sum('price'))['price__sum'] or 0
    total = "{} has {} dkp".format(character, awards-purchases)
    return HttpResponse(total)


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

