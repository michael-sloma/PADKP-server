import datetime as dt
import pytz

from django.db import models
from django.db.models import Sum

EQ_CLASSES = [
    'Warrior', 'Paladin', 'Shadow Knight',  'Beastlord', 'Berserker', 'Monk',
    'Ranger', 'Rogue', 'Magician', 'Necromancer', 'Wizard', 'Bard', 'Enchanter',
    'Cleric', 'Druid', 'Shaman', 'Unknown'
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
    leave_of_absence = models.BooleanField(default=False)
    inactive = models.BooleanField(default=False)
    date_inactive = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    def clean_name(self):
        return self.cleaned_data['name'].capitalize()

    def attendance(self, days):
        days_ago = pytz.utc.localize(dt.datetime.utcnow()) - dt.timedelta(days=days)
        raid_dumps = RaidDump.objects.filter(time__gte=days_ago).aggregate(total=Sum('attendance_value'))
        my_raid_dumps = RaidDump.objects.filter(time__gte=days_ago).filter(
            characters_present=self.name).aggregate(total=Sum('attendance_value'))
        my_awards = DkpSpecialAward.objects.filter(time__gte=days_ago).filter(
            character=self.name).aggregate(total=Sum('attendance_value'))
        my_attendance_points = (my_raid_dumps['total'] or 0) + (my_awards['total'] or 0)
        return 100 * float(my_attendance_points) / raid_dumps['total']

    def current_dkp(self):
        dumps = RaidDump.objects.filter(characters_present=self.name).aggregate(total=Sum('value'))
        purchases = Purchase.objects.filter(character=self.name).aggregate(total=Sum('value'))
        extra_awards = DkpSpecialAward.objects.filter(character=self.name).aggregate(total=Sum('value'))

        current_dkp = (dumps['total'] or 0)  + (extra_awards['total'] or 0)  - (purchases['total'] or 0)
        return current_dkp

    def decay_dkp(self, decay, notes, dry_run=True):
        current_dkp = self.current_dkp()
        decay_penalty = -int(decay * current_dkp)
        award = DkpSpecialAward(character=self,
                                value=decay_penalty,
                                attendance_value=0,
                                time=dt.datetime.utcnow(),
                                notes=notes)
        print('{} has {} dkp, decaying by {}'.format(self.name, current_dkp, decay_penalty))
        if not dry_run:
            award.save()

    def cap_dkp(self, cap, notes, dry_run=True):
        current_dkp = self.current_dkp()
        if current_dkp <= cap:
            return False
        else:
            cap_penalty = cap - current_dkp
            assert cap_penalty < 0
            award = DkpSpecialAward(character=self,
                                    value=cap_penalty,
                                    attendance_value=0,
                                    time=dt.datetime.utcnow(),
                                    notes=notes)
            print('capping {} at {} dkp (had {})'.format(self.name, cap, current_dkp))
            if not dry_run:
                award.save()
            return True

    def give_bonus(self, bonus, notes, dry_run=True):
        award = DkpSpecialAward(character=self,
                                value=bonus,
                                attendance_value=0,
                                time=dt.datetime.utcnow(),
                                notes=notes)
        print('bonus of {} to {}'.format(bonus, self.name))
        if not dry_run:
            award.save()


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


def main_change(name_from, name_to):
    print('main changing {} to {}'.format(name_from, name_to))
    char_from, = Character.objects.filter(name=name_from)
    char_to, = Character.objects.filter(name=name_to)

    char_from.status = 'ALT'
    char_from.save()

    char_to.status = 'MN'
    char_to.inactive = char_from.inactive
    char_to.save()

    char_from_dkp = char_from.current_dkp()
    char_to_dkp = char_to.current_dkp()

    # zero out the old main
    DkpSpecialAward(character=char_from,
                    value=-char_from_dkp,
                    attendance_value=0,
                    time=dt.datetime.now(),
                    notes='main change to {}'.format(char_to.name)
                    ).save()

    # transfer DKP to the new main
    DkpSpecialAward(character=char_to,
                    value=char_from_dkp - char_to_dkp,
                    attendance_value=0,
                    time=dt.datetime.now(),
                    notes='main change from {}'.format(char_from.name)
                    ).save()

    # transfer attendance for last 30 days
    for dump in RaidDump.objects.filter(characters_present=char_from).exclude(characters_present=char_to):
        DkpSpecialAward(character=char_to,
                        value=0,
                        attendance_value=dump.attendance_value,
                        time=dump.time,
                        notes='transfer attendance from {}'.format(char_from.name)
                        ).save()

