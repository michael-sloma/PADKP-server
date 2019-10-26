import datetime as dt

from django.db import models
from django.db.models import Sum


class Character(models.Model):
    MAIN = 'MN'
    ALT = 'ALT'
    RECRUIT = 'REC'
    INACTIVE = 'INA'
    status_choices = [(MAIN, 'Main'), (ALT, 'Alt'), (RECRUIT, 'Recruit'),
                      (INACTIVE, 'Inactive')]

    name = models.CharField(primary_key=True, max_length=100)
    status = models.CharField(max_length=3, choices=status_choices)

    def __str__(self):
        return self.name

    def clean_name(self):
        return self.cleaned_data['name'].capitalize()

    def get_dkp(self):
        awards = DkpAward.objects.filter(character=self.name).aggregate(Sum('value'))['value__sum'] or 0
        purchases = Purchase.objects.filter(character=self.name).aggregate(Sum('value'))['value__sum'] or 0
        return awards - purchases


class DkpAward(models.Model):
    TIME_AWARD = 'TA'
    BOSS_KILL_AWARD = 'BK'
    OTHER_AWARD = '?'
    type_choices = [(TIME_AWARD, 'Time'),
                    (BOSS_KILL_AWARD, 'Boss Kill'),
                    (OTHER_AWARD, 'Other')]
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    award_type = models.CharField(max_length=2, choices=type_choices)
    value = models.IntegerField()
    time = models.DateTimeField(default=dt.datetime.utcnow())
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        return "{}: {} for {} on {}".format(self.character,
                                            self.value,
                                            self.get_award_type_display(),
                                            self.time.strftime("%m/%d/%Y at %H:%M:%S %Z"))


class Purchase(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=200)
    value = models.IntegerField()
    time = models.DateTimeField(default=dt.datetime.utcnow())
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        return "{} to {} for {} on {}".format(self.item_name,
                                              self.character,
                                              self.value,
                                              self.time.strftime("%m/%d/%y"))

