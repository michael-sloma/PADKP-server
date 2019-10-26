from rest_framework import serializers

from padkp_show import models


class DkpAwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DkpAward
        fields = ('character', 'award_type', 'value', 'time', 'notes')


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Purchase
        fields = ('character', 'item_name', 'value', 'time', 'notes')


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Character
        fields = ('name', 'status')

