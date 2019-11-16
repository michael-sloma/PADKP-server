from rest_framework import serializers

from padkp_show import models


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Purchase
        fields = ('character', 'item_name', 'value', 'time', 'notes')


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Character
        fields = ('name', 'status')

