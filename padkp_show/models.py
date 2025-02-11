import datetime as dt
import re
import pytz
import random

from django.db import models
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist

DON_RELEASE = dt.datetime(year=2020, month=11, day=16)

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
    FNF = 'FNF'
    status_choices = [(MAIN, 'Main'), (ALT, 'Alt'), (RECRUIT, 'Recruit'),
                      (INACTIVE, 'Inactive'), (FNF, 'FNF')]

    name = models.CharField(primary_key=True, max_length=100)
    character_class = models.CharField(
        max_length=20, choices=[(x, x) for x in EQ_CLASSES])
    status = models.CharField(max_length=3, choices=status_choices)
    leave_of_absence = models.BooleanField(default=False)
    inactive = models.BooleanField(default=False)
    date_inactive = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    def clean_name(self):
        return self.cleaned_data['name'].capitalize()

    def attendance(self, days):
        days_ago = pytz.utc.localize(
            dt.datetime.utcnow()) - dt.timedelta(days=days)
        raid_dumps = RaidDump.objects.filter(
            time__gte=days_ago).aggregate(total=Sum('attendance_value'))
        my_raid_dumps = RaidDump.objects.filter(time__gte=days_ago).filter(
            characters_present=self.name).aggregate(total=Sum('attendance_value'))
        my_awards = DkpSpecialAward.objects.filter(time__gte=days_ago).filter(
            character=self.name).aggregate(total=Sum('attendance_value'))
        my_attendance_points = (
            my_raid_dumps['total'] or 0) + (my_awards['total'] or 0)
        return 100 * float(my_attendance_points) / (raid_dumps['total'] or 1)

    def current_dkp(self):
        dumps = RaidDump.objects.filter(
            characters_present=self.name).aggregate(total=Sum('value'))
        purchases = Purchase.objects.filter(
            is_alt=False, character=self.name).aggregate(total=Sum('value'))
        extra_awards = DkpSpecialAward.objects.filter(
            character=self.name).aggregate(total=Sum('value'))

        current_dkp = (dumps['total'] or 0) + \
            (extra_awards['total'] or 0) - (purchases['total'] or 0)
        return current_dkp

    def current_alt_dkp(self):
        dumps = RaidDump.objects.filter(
            time__gte=DON_RELEASE, characters_present=self.name).aggregate(total=Sum('value'))
        purchases = Purchase.objects.filter(
            character=self.name, is_alt=True).aggregate(total=Sum('value'))
        extra_awards = DkpSpecialAward.objects.filter(
            time__gte=DON_RELEASE, character=self.name).aggregate(total=Sum('value'))

        current_dkp = (dumps['total'] or 0) + \
            (extra_awards['total'] or 0) - (purchases['total'] or 0)
        return current_dkp

    def decay_dkp(self, decay, notes, dry_run=True):
        current_dkp = self.current_dkp()
        decay_penalty = -int(decay * current_dkp)
        award = DkpSpecialAward(character=self,
                                value=decay_penalty,
                                attendance_value=0,
                                time=dt.datetime.utcnow(),
                                notes=notes)
        print('{} has {} dkp, decaying by {}'.format(
            self.name, current_dkp, decay_penalty))
        if not dry_run:
            award.save()

    def cap_dkp(self, cap, notes, dry_run=True):
        current_dkp = self.current_dkp()
        if current_dkp <= cap:
            return False
        else:
            cap_penalty = current_dkp - cap
            assert cap_penalty > 0
            award = Purchase(character=self,
                             item_name='Main DKP Cap Adjustment',
                             value=cap_penalty,
                             time=dt.datetime.now(),
                             notes = notes,
                             is_alt=0)
            print('capping {} at {} dkp (had {})'.format(
                self.name, cap, current_dkp))
            if not dry_run:
                award.save()
            return True

    def cap_alt_dkp(self, cap, dry_run=True):
        current_dkp = self.current_alt_dkp()
        if current_dkp <= cap:
            return False
        else:
            cap_penalty = current_dkp - cap
            assert cap_penalty > 0
            award = Purchase(character=self,
                             item_name='Alt DKP Cap Adjustment',
                             value=cap_penalty,
                             time=dt.datetime.now(),
                             is_alt=1)
            print('capping {} at {} dkp (had {})'.format(
                self.name, cap, current_dkp))
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

    @classmethod
    def find_character(cls, cname):
        new_name = re.sub("'s alt", "", cname, flags=re.IGNORECASE)
        is_alt = new_name != cname
        try:
            alt_obj = CharacterAlt.objects.get(pk=new_name)
            return True, alt_obj.main
        except ObjectDoesNotExist:
            try:
                character_obj = Character.objects.get(pk=new_name)
                return is_alt, character_obj
            except ObjectDoesNotExist:
                return False, None


Character._meta.ordering = ['name']


class CharacterAlt(models.Model):
    """ Represents a member's alt """
    name = models.CharField(primary_key=True, max_length=100)
    main = models.ForeignKey(Character,  on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class RaidDump(models.Model):
    """ Represents a raid dump upload. Awards dkp and optionally attendance"""
    value = models.IntegerField()
    attendance_value = models.IntegerField()
    time = models.DateTimeField()
    characters_present = models.ManyToManyField(
        Character, related_name='raid_dumps', limit_choices_to={'inactive': False})
    filename = models.CharField(max_length=50)

    type_choices = [('Time', 'Time'),
                    ('Boss Kill', 'Boss Kill'),
                    ('Other', 'Other')]
    award_type = models.CharField(max_length=15, choices=type_choices)
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        attendance_str = '' if self.attendance_value else " -- not counted for attendance"
        notes_str = '' if not self.notes else '({}) '.format(self.notes)
        time_str = self.time.astimezone(pytz.timezone(
            'US/Eastern')).strftime('%A, %d %b %Y %I:%M %p Eastern')
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
        time_str = self.time.astimezone(pytz.timezone(
            'US/Eastern')).strftime('%A, %d %b %Y %I:%M %p Eastern')
        return '{} {}on {} {}'.format(self.value, notes_str, time_str, attendance_str)


class Auction(models.Model):
    """ Represents the raw bid data for an auction """
    fingerprint = models.CharField(max_length=64, unique=True)
    time = models.DateTimeField()
    item_name = models.CharField(max_length=200)
    item_count = models.IntegerField(default=1)
    corrected = models.BooleanField(default=False)

    class Meta:
        ordering = ['-time']

    def __str__(self):
        time_str = self.time.astimezone(pytz.timezone(
            'US/Eastern')).strftime('%A, %d %b %Y %I:%M %p Eastern')
        return 'auction for {}x{} on {}'.format(self.item_name, self.item_count, time_str)

    def process_bids(self, bids):
        warnings = []
        for bid in bids:
            if int(bid['bid']) == 0:
                continue
            is_alt, char = Character.find_character(bid['name'])
            if bid['tag'] == 'Main':
                is_alt = False
            if not char:
                warnings.append(
                    'Received bid for unknown character: {}'.format(bid['name']))
                continue
            dkp = char.current_dkp()
            attendance = char.attendance(30)
            if is_alt or bid['tag'] == 'ALT':
                bid['tag'] = 'ALT'
                dkp = char.current_alt_dkp()
            elif char.status != 'MN' and bid['tag'] not in ['INA', 'FNF', 'Recruit']:
                warnings.append('{} bid with tag "{}" but is registered as "{}"'.format(
                    bid['name'], bid['tag'], char.status))

            if dkp < int(bid['bid']):
                # warnings.append('{} bid {} dkp but only has {} on the site, lowered their bid'.format(
                warnings.append('{} bid {} dkp but only has {} on the site'.format(
                    bid['name'], bid['bid'], dkp
                ))
                # bid['bid'] = dkp

            AuctionBid(
                auction=self, bid=bid['bid'], tag=bid['tag'], character=char, dkp_snapshot=dkp, att_snapshot=attendance
            ).save()
        return warnings

    def determine_winners_english(self):
        def ordering(bid):
            char = bid.character
            max_bid = bid.bid
            if bid.tag == 'ALT':
                max_bid = min(max_bid, 5)
            if bid.tag in ['INA', 'Recruit', 'FNF']:
                max_bid = min(max_bid, 10)
            return max_bid, bid.bid, bid.dkp_snapshot, bid.att_snapshot

        bids = [b for b in self.auctionbid_set.all()]
        sorting_criteria = {b: ordering(b) for b in bids}
        random.shuffle(bids)
        winners_in_order = sorted(
            bids, key=lambda b: sorting_criteria[b], reverse=True)
        tie_losers = []
        if len(winners_in_order) > self.item_count:  # More bidders than items to hand out
            i = self.item_count
            while winners_in_order[i-1].bid == winners_in_order[i].bid:
                tie_losers.append(winners_in_order[i].character.name)
                i += 1
                if len(winners_in_order) == i:
                    break

        result = [{'char': w.character, 'bid': w.bid, 'tag': w.tag } for w in winners_in_order[0:self.item_count]]

        return [tie_losers, result]


    def determine_winners_vickrey(self):
        def max_bid(bid):
            max_bid = bid.bid
            if bid.tag == 'ALT':
                max_bid = min(max_bid, 5)
            return max_bid

        def ordering(bid):
            return max_bid(bid), bid.bid

        def offset_value(target, offset, tie_fallback):
            if offset is None:
                return 5
            if offset.tag == 'ALT' and target.tag != 'ALT':
                return max_bid(offset)+1
            if offset.bid == target.bid or offset.character == target.character:
                return min(tie_fallback, target.bid)
            return offset.bid+1


        bids = [b for b in self.auctionbid_set.all()]
        sorting_criteria = {b: ordering(b) for b in bids}
        random.shuffle(bids)
        winners_in_order = sorted(
            bids, key=lambda b: sorting_criteria[b], reverse=True)

        main_winners = [x for x in winners_in_order[0:self.item_count] if x.tag != 'ALT' ]
        alt_winners = [x for x in winners_in_order[0:self.item_count] if x.tag == 'ALT' ]
        all_winners = main_winners + alt_winners
        left_overs = [x for x in winners_in_order if x not in all_winners]
        result = []
        tie_losers = []

        effective_count = min(len(all_winners), self.item_count)

        if effective_count == 0:
            return [tie_losers, reversed(result)]

        # print('all:', all_winners)
        # print('leftovers:', left_overs)

        last_winner = all_winners[effective_count-1]
        offset_from = None
        if self.item_count > 1 and self.item_count <= len(bids):
            offset_from = last_winner
        for possible in all_winners[effective_count:]:
            if possible.character != last_winner.character:
                if possible.bid == last_winner.bid:
                    tie_losers.append(possible.character.name)
                if offset_from is None:
                    offset_from = possible
        for possible in left_overs:
            if possible.character != last_winner.character:
                if possible.bid == last_winner.bid:
                    tie_losers.append(possible.character.name)
                if offset_from is None:
                    offset_from = possible

        replacing = last_winner.bid

        def last_result_bid():
            if len(result) > 0:
                return result[len(result)-1]['bid']
            else:
                return 10000

        # print(offset_from)
        # print(last_winner)
        for winner in reversed(all_winners[0:effective_count]):
            new_bid = min(last_result_bid(), offset_value(winner, offset_from, last_result_bid()))
            # print(f'{new_bid}:{replacing}')
            offset_from = winner
            replacing = winner.bid

            result.append({'char': winner.character, 'bid': new_bid, 'tag': winner.tag })


        return [tie_losers, reversed(result)]

class AuctionBid(models.Model):
    """ Represents a bid in an auction """
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    bid = models.IntegerField()
    tag = models.CharField(max_length=8)
    character = models.ForeignKey(Character,  on_delete=models.CASCADE)
    dkp_snapshot = models.IntegerField()
    att_snapshot = models.FloatField()

    def __str__(self):
        return '{} bid {} on {}'.format(self.auction.item_name, self.bid, self.character)


class Purchase(models.Model):
    """ Represents a character spending DKP for an item"""
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=200)
    value = models.IntegerField()
    time = models.DateTimeField(default=dt.datetime.utcnow)
    notes = models.TextField(default="", blank=True)
    is_alt = models.BooleanField(default=False, null=True)
    auction = models.ForeignKey(
        Auction, blank=True, null=True, on_delete=models.SET_NULL)

    def character_display(self):
        return self.character.name+"'s alt" if self.is_alt else self.character.name

    def __str__(self):
        return "{} to {} for {} on {}".format(self.item_name,
                                              self.character_display(),
                                              self.value,
                                              self.time.astimezone(pytz.timezone(
                                                  'US/Eastern')).strftime("%m/%d/%y"))


def main_change(name_from, name_to):
    print('main changing {} to {}'.format(name_from, name_to))
    char_from, = Character.objects.filter(name=name_from)
    char_to, = Character.objects.filter(name=name_to)
    alt_registry = CharacterAlt.objects.filter(main__name=char_from.name)

    char_from.status = 'ALT'
    char_from.save()

    char_to.status = 'MN'
    char_to.inactive = char_from.inactive
    char_to.save()

    main_alt_relationship_exists = False
    new_alts = []
    for alt in alt_registry:
        if alt.name == name_to:
            new_alts.append([name_from, char_to])
            main_alt_relationship_exists = True
        else:
            new_alts.append([alt.name, char_to])
        alt.delete()

    if not main_alt_relationship_exists:
        new_alts.append([name_from, char_to])
    for pair in new_alts:
        CharacterAlt.objects.create(name=pair[0], main=pair[1])

    char_to_dkp = char_to.current_dkp()
    char_to_alt_dkp = char_to.current_alt_dkp()
    char_from_dkp = char_from.current_dkp()
    char_from_alt_dkp = char_from.current_alt_dkp()

    # zero out the old main
    DkpSpecialAward(character=char_from,
                    value=-char_from_dkp,
                    attendance_value=0,
                    time=dt.datetime.now(),
                    notes='main change to {}'.format(char_to.name)
                    ).save()

    # zero out the new main
    DkpSpecialAward(character=char_to,
                    value=-char_to_dkp,
                    attendance_value=0,
                    time=dt.datetime.now(),
                    notes='reset for main change from {}'.format(char_from.name)
                    ).save()

    # transfer DKP to the new main
    DkpSpecialAward(character=char_to,
                    value=char_from_dkp,
                    attendance_value=0,
                    time=dt.datetime.now(),
                    notes='main change from {}'.format(char_from.name)
                    ).save()

    # setup alt dkp correction
    Purchase(
        character=char_to,
        item_name='Main Change Alt DKP Adjustor',
        value=char_from_dkp - char_from_alt_dkp - (char_to_dkp - char_to_alt_dkp),
        time=dt.datetime.now(),
        is_alt=1,
    ).save()

    # transfer attendance for last 30 days
    for dump in RaidDump.objects.filter(characters_present=char_from).exclude(characters_present=char_to):
        DkpSpecialAward(character=char_to,
                        value=0,
                        attendance_value=dump.attendance_value,
                        time=dump.time,
                        notes='transfer attendance from {}'.format(
                            char_from.name)
                        ).save()


class CasualCharacter(models.Model):
    """ Represents a member """
    name = models.CharField(primary_key=True, max_length=100)
    character_class = models.CharField(
        max_length=20, choices=[(x, x) for x in EQ_CLASSES])

    def __str__(self):
        return self.name

    def clean_name(self):
        return self.cleaned_data['name'].capitalize()

    def current_dkp(self):
        dumps = CasualRaidDump.objects.filter(
            characters_present=self.name).aggregate(total=Sum('value'))
        purchases = CasualPurchase.objects.filter(
            character=self.name).aggregate(total=Sum('value'))
        extra_awards = CasualDkpSpecialAward.objects.filter(
            character=self.name).aggregate(total=Sum('value'))

        current_dkp = (dumps['total'] or 0) + \
            (extra_awards['total'] or 0) - (purchases['total'] or 0)
        return current_dkp


CasualCharacter._meta.ordering = ['name']


class CasualRaidDump(models.Model):
    """ Represents a raid dump upload. Awards dkp and optionally attendance"""
    value = models.IntegerField()
    time = models.DateTimeField()
    characters_present = models.ManyToManyField(
        CasualCharacter, related_name='raid_dumps')
    filename = models.CharField(max_length=50)

    notes = models.TextField(default="", blank=True)

    def __str__(self):
        notes_str = '' if not self.notes else '({}) '.format(self.notes)
        time_str = self.time.astimezone(pytz.timezone(
            'US/Eastern')).strftime('%A, %d %b %Y %I:%M %p Eastern')
        return '{} on {} -- {}'.format(self.value, time_str, notes_str)


class CasualDkpSpecialAward(models.Model):
    """ represents a character being awarded dkp or attendance that is not attached
    to a raid dump.

    intended purpose is for dkp bonuses and decays. could also be used for quick
    and dirty fixes to dkp entry errors
    """
    character = models.ForeignKey(CasualCharacter, on_delete=models.CASCADE)
    value = models.IntegerField()
    time = models.DateTimeField(default=dt.datetime.utcnow, blank=True)
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        attendance_str = ''
        notes_str = '' if not self.notes else '({}) '.format(self.notes)
        time_str = self.time.astimezone(pytz.timezone(
            'US/Eastern')).strftime('%A, %d %b %Y %I:%M %p Eastern')
        return '{} {}on {} {}'.format(self.value, notes_str, time_str, attendance_str)


class CasualPurchase(models.Model):
    """ Represents a character spending DKP for an item"""
    character = models.ForeignKey(CasualCharacter, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=200)
    value = models.IntegerField()
    time = models.DateTimeField(default=dt.datetime.utcnow)
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        return "{} to {} for {} on {}".format(self.item_name,
                                              self.character,
                                              self.value,
                                              self.time.strftime("%m/%d/%y"))
