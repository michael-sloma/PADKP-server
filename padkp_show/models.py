import datetime as dt
import pytz

from django.db import models
from django.db.models import Sum

EQ_CLASSES = [
    'Warrior', 'Paladin', 'Shadow Knight',  'Beastlord', 'Berserker', 'Monk',
    'Ranger', 'Rogue', 'Magician', 'Necromancer', 'Wizard', 'Bard', 'Enchanter',
    'Cleric', 'Druid', 'Shaman'
]

class Character(models.Model):
    """ Represents a member """
    MAIN = 'MN'
    ALT = 'ALT'
    RECRUIT = 'REC'
    INACTIVE = 'INA'
    status_choices = [(MAIN, 'Main'), (ALT, 'Alt'), (RECRUIT, 'Recruit'),
                      (INACTIVE, 'Inactive')]

    name = models.CharField(primary_key=True, max_length=100)
    character_class = models.CharField(max_length=20, choices=[(x,x) for x in EQ_CLASSES])
    status = models.CharField(max_length=3, choices=status_choices)

    def __str__(self):
        return self.name

    def clean_name(self):
        return self.cleaned_data['name'].capitalize()

    def attendance(self, days):
        days_ago = dt.datetime.utcnow() - dt.timedelta(days=days)
        raid_dumps = RaidDump.objects.filter(time__gte=days_ago).aggregate(total=Sum('attendance_value'))
        my_raid_dumps = RaidDump.objects.filter(time__gte=days_ago).filter(
            characters_present=self.name).aggregate(total=Sum('attendance_value'))
        my_awards = DkpSpecialAward.objects.filter(time__gte=days_ago).filter(
            character=self.name).aggregate(total=Sum('attendance_value'))
        my_attendance_points = (my_raid_dumps['total'] or 0) + (my_awards['total'] or 0)
        return 100 * float(my_attendance_points) / raid_dumps['total']
Character._meta.ordering=['name']

class RaidDump(models.Model):
    """ Represents a raid dump upload. Awards dkp and optionally attendance"""
    value = models.IntegerField()
    attendance_value = models.IntegerField()
    time = models.DateTimeField()
    characters_present = models.ManyToManyField(Character, related_name='raid_dumps')
    filename = models.CharField(max_length=50)

    type_choices = [('Time', 'Time'),
                    ('Boss Kill', 'Boss Kill'),
                    ('Other', 'Other')]
    award_type = models.CharField(max_length=15, choices=type_choices)
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        attendance_str = '' if self.attendance_value else " -- not counted for attendance"
        notes_str = '' if not self.notes else '({}) '.format(self.notes)
        time_str = self.time.astimezone(pytz.timezone('US/Eastern')).strftime('%A, %d %b %Y %I:%M %p Eastern')
        return '{} for {} {}on {} {}'.format(self.value, self.award_type, notes_str, time_str, attendance_str)


class DkpSpecialAward(models.Model):
    """ represents a character being awarded dkp or attendance that is not attached
    to a raid dump.

    intended purpose is for dkp bonuses and decays. could also be used for quick
    and dirty fixes to dkp entry errors
    """
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    value = models.IntegerField()
    attendance_value = models.IntegerField()
    time = models.DateTimeField(default=dt.datetime.utcnow, blank=True)
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        attendance_str = '' if self.attendance_value else " -- not counted for attendance"
        notes_str = '' if not self.notes else '({}) '.format(self.notes)
        time_str = self.time.astimezone(pytz.timezone('US/Eastern')).strftime('%A, %d %b %Y %I:%M %p Eastern')
        return '{} {}on {} {}'.format(self.value, notes_str, time_str, attendance_str)


class Purchase(models.Model):
    """ Represents a character spending DKP for an item"""
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=200)
    value = models.IntegerField()
    time = models.DateTimeField(default=dt.datetime.utcnow)
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        return "{} to {} for {} on {}".format(self.item_name,
                                              self.character,
                                              self.value,
                                              self.time.strftime("%m/%d/%y"))


